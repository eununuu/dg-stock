import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# ---------------------------
# 1. 페이지 기본 설정
# ---------------------------
st.set_page_config(
    page_title="AI 관련주 대시보드",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------
# 2. 모바일 반응형 CSS
# ---------------------------
st.markdown(
    """
    <style>
    .main .block-container {
        padding: 1rem 1rem 2rem 1rem;
        max-width: 1000px;
    }
    .stDataFrame { overflow-x: auto; }
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
# 3. AI 관련 종목 사전
#    (반도체 / 빅테크 / 한국 AI 관련주)
# ---------------------------
STOCKS = {
    "🇺🇸 엔비디아(NVIDIA)": "NVDA",       # AI 반도체 대표주
    "🇺🇸 마이크로소프트": "MSFT",          # OpenAI 투자
    "🇺🇸 구글(Alphabet)": "GOOGL",        # Gemini AI
    "🇺🇸 메타(Meta)": "META",             # Llama AI
    "🇺🇸 AMD": "AMD",                     # AI 반도체
    "🇺🇸 팔란티어(Palantir)": "PLTR",     # AI 데이터 분석
    "🇰🇷 삼성전자": "005930.KS",          # AI 반도체(HBM)
    "🇰🇷 SK하이닉스": "000660.KS",        # AI 메모리(HBM)
    "🇰🇷 네이버": "035420.KS",            # 하이퍼클로바 AI
    "🇰🇷 카카오": "035720.KS",            # 카카오 AI
}

# ---------------------------
# 4. 제목 영역
# ---------------------------
st.title("🤖 AI 관련주 대시보드")
st.caption("인공지능 관련 주요 기업들의 수익률과 주가 흐름을 비교해 보세요!")

# ---------------------------
# 5. 사용자 입력 영역
# ---------------------------
selected_names = st.multiselect(
    "비교할 종목을 선택하세요 (여러 개 가능)",
    options=list(STOCKS.keys()),
    default=["🇺🇸 엔비디아(NVIDIA)", "🇰🇷 SK하이닉스", "🇺🇸 마이크로소프트"],
)

period = st.selectbox(
    "조회 기간",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,
    format_func=lambda x: {
        "1mo": "1개월", "3mo": "3개월", "6mo": "6개월",
        "1y": "1년", "2y": "2년", "5y": "5년",
    }[x],
)

# ---------------------------
# 6. 데이터 불러오기 함수
# ---------------------------
@st.cache_data(ttl=600)
def load_data(ticker, period):
    df = yf.download(ticker, period=period, progress=False)
    return df

# ---------------------------
# 7. 선택한 종목이 있을 때 실행
# ---------------------------
if not selected_names:
    st.info("👆 위에서 비교할 종목을 하나 이상 선택해 주세요.")
else:
    summary_rows = []
    fig = go.Figure()

    for name in selected_names:
        ticker = STOCKS[name]
        df = load_data(ticker, period)

        if df.empty:
            st.warning(f"{name} 데이터를 불러오지 못했습니다.")
            continue

        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        start_price = float(close.iloc[0])
        end_price = float(close.iloc[-1])
        change_pct = (end_price - start_price) / start_price * 100

        summary_rows.append({
            "종목": name,
            "시작가": round(start_price, 2),
            "현재가": round(end_price, 2),
            "수익률(%)": round(change_pct, 2),
        })

        # 시작일=100 기준으로 정규화해 비교
        normalized = close / start_price * 100
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized.values,
            mode="lines",
            name=name,
        ))

    # ---------------------------
    # 8. 핵심 지표 카드 (대시보드 느낌!)
    # ---------------------------
    if summary_rows:
        st.subheader("📌 한눈에 보는 수익률")

        # 종목 수에 맞춰 컬럼을 나눠 카드처럼 배치 (최대 3개씩 한 줄)
        cols = st.columns(min(len(summary_rows), 3))
        for i, row in enumerate(summary_rows):
            col = cols[i % 3]
            col.metric(
                label=row["종목"],
                value=f"{row['현재가']:,}",
                delta=f"{row['수익률(%)']}%",  # 양수=초록, 음수=빨강 자동 표시
            )

        # ---------------------------
        # 9. 수익률 요약 표
        # ---------------------------
        st.subheader("💰 수익률 요약 표")
        summary_df = pd.DataFrame(summary_rows)

        def color_change(val):
            color = "red" if val > 0 else ("blue" if val < 0 else "black")
            return f"color: {color}; font-weight: bold;"

        if hasattr(summary_df.style, "map"):
            styled = summary_df.style.map(color_change, subset=["수익률(%)"])
        else:
            styled = summary_df.style.applymap(color_change, subset=["수익률(%)"])

        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ---------------------------
        # 10. 비교 차트
        # ---------------------------
        st.subheader("📊 주가 변동 비교 (시작일=100 기준)")
        fig.update_layout(
            autosize=True,
            height=450,
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", y=-0.2),
            hovermode="x unified",
            yaxis_title="기준 지수 (시작=100)",
        )
        st.plotly_chart(fig, use_container_width=True)
