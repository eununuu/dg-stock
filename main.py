import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# ---------------------------
# 1. 페이지 기본 설정
# ---------------------------
st.set_page_config(
    page_title="한미 주식 비교",
    page_icon="📈",
    layout="wide",  # 넓은 레이아웃 (반응형의 기본)
    initial_sidebar_state="collapsed",
)

# ---------------------------
# 2. 모바일 반응형 CSS
#    (화면이 작아져도 글자/표/그래프가 찌그러지지 않게)
# ---------------------------
st.markdown(
    """
    <style>
    /* 전체 폰트와 여백을 화면 크기에 따라 자동 조절 */
    .main .block-container {
        padding: 1rem 1rem 2rem 1rem;
        max-width: 1000px;
    }
    /* 표가 화면을 넘으면 가로 스크롤 가능하게 */
    .stDataFrame { overflow-x: auto; }

    /* 스마트폰(폭 600px 이하)에서 제목 크기 줄이기 */
    @media (max-width: 600px) {
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.2rem !important; }
        .main .block-container { padding: 0.5rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# 3. 종목 사전 (이름: 티커)
#    한국 주식은 .KS(코스피), 미국은 그냥 티커
# ---------------------------
STOCKS = {
    "🇰🇷 삼성전자": "005930.KS",
    "🇰🇷 SK하이닉스": "000660.KS",
    "🇰🇷 현대차": "005380.KS",
    "🇰🇷 네이버": "035420.KS",
    "🇰🇷 카카오": "035720.KS",
    "🇺🇸 애플(Apple)": "AAPL",
    "🇺🇸 마이크로소프트": "MSFT",
    "🇺🇸 엔비디아(NVIDIA)": "NVDA",
    "🇺🇸 테슬라(Tesla)": "TSLA",
    "🇺🇸 구글(Alphabet)": "GOOGL",
}

# ---------------------------
# 4. 제목 영역
# ---------------------------
st.title("📈 한국·미국 주식 비교")
st.caption("yfinance 데이터를 활용해 수익률과 차트를 한눈에 비교해 보세요!")

# ---------------------------
# 5. 사용자 입력 영역
# ---------------------------
selected_names = st.multiselect(
    "비교할 종목을 선택하세요 (여러 개 가능)",
    options=list(STOCKS.keys()),
    default=["🇰🇷 삼성전자", "🇺🇸 애플(Apple)"],
)

period = st.selectbox(
    "조회 기간",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,  # 기본값 1년
    format_func=lambda x: {
        "1mo": "1개월", "3mo": "3개월", "6mo": "6개월",
        "1y": "1년", "2y": "2년", "5y": "5년",
    }[x],
)

# ---------------------------
# 6. 데이터 불러오기 함수
#    @st.cache_data 로 같은 요청은 다시 받지 않게 함 (속도 향상)
# ---------------------------
@st.cache_data(ttl=600)  # 10분 동안 데이터 캐시
def load_data(ticker, period):
    df = yf.download(ticker, period=period, progress=False)
    return df

# ---------------------------
# 7. 선택한 종목이 있을 때 실행
# ---------------------------
if not selected_names:
    st.info("👆 위에서 비교할 종목을 하나 이상 선택해 주세요.")
else:
    summary_rows = []          # 수익률 표에 들어갈 데이터
    fig = go.Figure()          # 비교 차트

    for name in selected_names:
        ticker = STOCKS[name]
        df = load_data(ticker, period)

        # 데이터가 비어 있으면 건너뛰기
        if df.empty:
            st.warning(f"{name} 데이터를 불러오지 못했습니다.")
            continue

        # 종가(Close) 추출 (yfinance 버전에 따라 컬럼 구조가 달라 안전하게 처리)
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        start_price = float(close.iloc[0])
        end_price = float(close.iloc[-1])
        change_pct = (end_price - start_price) / start_price * 100

        # 표에 넣을 행 추가
        summary_rows.append({
            "종목": name,
            "시작가": round(start_price, 2),
            "현재가": round(end_price, 2),
            "수익률(%)": round(change_pct, 2),
        })

        # 그래프는 '시작일 = 100' 기준으로 정규화해 함께 비교
        normalized = close / start_price * 100
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized.values,
            mode="lines",
            name=name,
        ))

    # ---------------------------
    # 8. 수익률 요약 표 출력
    # ---------------------------
    if summary_rows:
        st.subheader("💰 수익률 요약")
        summary_df = pd.DataFrame(summary_rows)

        # 수익률이 양수면 빨강, 음수면 파랑 (한국식 색상)
        def color_change(val):
            color = "red" if val > 0 else ("blue" if val < 0 else "black")
            return f"color: {color}; font-weight: bold;"

        # pandas 버전 호환 처리 (최신은 map, 구버전은 applymap)
        if hasattr(summary_df.style, "map"):
            styled = summary_df.style.map(color_change, subset=["수익률(%)"])
        else:
            styled = summary_df.style.applymap(color_change, subset=["수익률(%)"])

        # use_container_width=True 가 반응형의 핵심!
        st.dataframe(styled, use_container_width=True, hide_index=True
                    
        # ---------------------------
        # 9. 비교 차트 출력
        # ---------------------------
        st.subheader("📊 주가 변동 비교 (시작일=100 기준)")
        fig.update_layout(
            autosize=True,           # 화면 크기에 맞게 자동 조절
            height=450,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", y=-0.2),  # 범례를 아래로 (모바일 친화적)
            hovermode="x unified",
            yaxis_title="기준 지수 (시작=100)",
        )
        # use_container_width=True 로 모바일에서도 꽉 차게
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("⚠️ 본 정보는 학습용이며 투자 권유가 아닙니다.")
