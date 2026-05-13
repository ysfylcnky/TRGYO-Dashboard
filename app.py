import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ---------------------------------------------------
# SAYFA AYARI
# ---------------------------------------------------

st.set_page_config(
    page_title="TRGYO Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# CSS
# ---------------------------------------------------

st.markdown("""
<style>

.main {
    background-color: #0E1117;
}

.card {
    background-color: #1c1f26;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0px 0px 15px rgba(0,255,255,0.15);
}

.card-title {
    font-size: 18px;
    color: #AAAAAA;
}

.card-value {
    font-size: 30px;
    color: #00FFFF;
    font-weight: bold;
    
.card:hover {
    transform: translateY(-5px);
    transition: 0.3s;
}
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CACHE
# ---------------------------------------------------

@st.cache_data(ttl=3600)
def load_market_data(period):

    hisse = yf.download(
        "TRGYO.IS",
        period=period,
        auto_adjust=True
        progress=False,
        threads=False
    )

    usdtry = yf.download(
        "TRY=X",
        period="1y",
        auto_adjust=True
        progress=False,
        threads=False
    )

    altin = yf.download(
        "GC=F",
        period="1y",
        auto_adjust=True
        progress=False,
        threads=False
    )

    bist100 = yf.download(
        "XU100.IS",
        period="1y",
        auto_adjust=True
        progress=False,
        threads=False
    )

    # US 10Y Treasury
    us10y = yf.download(
        "^TNX",
        period="1y",
        auto_adjust=True
        progress=False,
        threads=False
    )

    return hisse, usdtry, altin, bist100, us10y


@st.cache_data(ttl=3600)
def load_excel_data():

    enflasyon_df = pd.read_excel("data/inflation.xlsx")
    faiz_df = pd.read_excel("data/rate.xlsx")
    pd_df = pd.read_excel("data/pd_orani.xlsx")
    kar_df = pd.read_excel("data/ceyreklik_kar.xlsx")
    gsyh_df = pd.read_excel("data/gsyh.xlsx")
    konut_df = pd.read_excel("data/konut_satis.xlsx")
    yield_df = pd.read_excel("data/yield_curve.xlsx")

    return (
        enflasyon_df,
        faiz_df,
        pd_df,
        kar_df,
        gsyh_df,
        konut_df,
        yield_df
    )

# ---------------------------------------------------
# BAŞLIK
# ---------------------------------------------------

st.title("TRGYO Finans Dashboard")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

st.sidebar.title("Filtreler")

grafik_turu = st.sidebar.selectbox(
    "Grafik Türü",
    ["Çizgi Grafik", "Mum Grafik"]
)

hareketli_ortalama = st.sidebar.checkbox(
    "Hareketli Ortalamaları Göster",
    value=True
)

zaman_araligi = st.sidebar.selectbox(
    "Zaman Aralığı",
    ["1 Ay", "3 Ay", "6 Ay", "1 Yıl"],
    index=3
)

# ---------------------------------------------------
# PERIOD
# ---------------------------------------------------

if zaman_araligi == "1 Ay":
    period = "1mo"

elif zaman_araligi == "3 Ay":
    period = "3mo"

elif zaman_araligi == "6 Ay":
    period = "6mo"

else:
    period = "1y"

# ---------------------------------------------------
# VERİLER
# ---------------------------------------------------

(
    hisse,
    usdtry,
    altin,
    bist100,
    us10y
) = load_market_data(period)

(
    enflasyon_df,
    faiz_df,
    pd_df,
    kar_df,
    gsyh_df,
    konut_df,
    yield_df
) = load_excel_data()

# ---------------------------------------------------
# CLOSE PRICES
# ---------------------------------------------------

try:

    close_prices = hisse["Close"].squeeze()
    usd_close = usdtry["Close"].squeeze()
    gold_close = altin["Close"].squeeze()
    bist_close = bist100["Close"].squeeze()
    us10y_close = us10y["Close"].squeeze()

    # boş veri kontrolü
    if (
        close_prices.empty
        or usd_close.empty
        or gold_close.empty
        or bist_close.empty
        or us10y_close.empty
    ):
        st.error("Finansal veriler alınamadı. Lütfen daha sonra tekrar deneyin.")
        st.stop()

except Exception as e:

    st.error(f"Veri çekme hatası: {e}")
    st.stop()

# ---------------------------------------------------
# BETA HESABI
# ---------------------------------------------------

returns_df = pd.concat(
    [
        close_prices.pct_change(),
        bist_close.pct_change()
    ],
    axis=1
).dropna()

returns_df.columns = ["TRGYO", "BIST100"]

trgyo_returns = returns_df["TRGYO"]
bist_returns = returns_df["BIST100"]

covariance = np.cov(
    trgyo_returns,
    bist_returns
)[0][1]

market_variance = np.var(bist_returns)

beta = round(
    covariance / market_variance,
    2
)

# ---------------------------------------------------
# MOVING AVERAGES
# ---------------------------------------------------

hisse["MA50"] = close_prices.rolling(50).mean()
hisse["MA200"] = close_prices.rolling(200).mean()

# ---------------------------------------------------
# KPI
# ---------------------------------------------------

son_fiyat = round(close_prices.iloc[-1], 2)

gunluk_degisim = round(
    (
        (
            close_prices.iloc[-1]
            - close_prices.iloc[-2]
        )
        / close_prices.iloc[-2]
    ) * 100,
    2
)

# ---------------------------------------------------
# KPI KARTLARI
# ---------------------------------------------------

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "TRGYO",
        f"{son_fiyat} TL",
        f"%{gunluk_degisim}"
    )

with col2:
    st.metric(
        "En Yüksek",
        f"{round(close_prices.max(),2)} TL"
    )

with col3:
    st.metric(
        "En Düşük",
        f"{round(close_prices.min(),2)} TL"
    )

with col4:
    st.metric(
        "Beta",
        beta
    )

with col5:
    st.metric(
        "US 10Y",
        f"%{round(us10y_close.iloc[-1],2)}"
    )

# ---------------------------------------------------
# ANA FİYAT GRAFİĞİ
# ---------------------------------------------------

if grafik_turu == "Çizgi Grafik":

    fig = px.line(
        x=hisse.index,
        y=close_prices,
        title="TRGYO Fiyat Grafiği"
    )

    if hareketli_ortalama:

        fig.add_scatter(
            x=hisse.index,
            y=hisse["MA50"],
            mode='lines',
            name='MA50'
        )

        fig.add_scatter(
            x=hisse.index,
            y=hisse["MA200"],
            mode='lines',
            name='MA200'
        )

    fig.update_layout(
        template="plotly_dark",
        height=700,

        xaxis_title="Tarih",
        yaxis_title="Fiyat (TL)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=hisse.index,
            open=hisse["Open"].squeeze(),
            high=hisse["High"].squeeze(),
            low=hisse["Low"].squeeze(),
            close=close_prices,
            name="TRGYO"
        )
    )

    if hareketli_ortalama:

        fig.add_trace(
            go.Scatter(
                x=hisse.index,
                y=hisse["MA50"],
                mode='lines',
                name='MA50'
            )
        )

        fig.add_trace(
            go.Scatter(
                x=hisse.index,
                y=hisse["MA200"],
                mode='lines',
                name='MA200'
            )
        )

    fig.update_layout(
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ---------------------------------------------------
# EKONOMİ KARTLARI
# ---------------------------------------------------

eco_card1, eco_card2, eco_card3 = st.columns(3)

with eco_card1:
    st.markdown(f"""
        <div class="card">
            <div class="card-title">USD/TRY</div>
            <div class="card-value">
                {round(usd_close.iloc[-1],2)}
            </div>
        </div>
    """, unsafe_allow_html=True)

with eco_card2:
    st.markdown(f"""
        <div class="card">
            <div class="card-title">Altın</div>
            <div class="card-value">
                {round(gold_close.iloc[-1],2)} $
            </div>
        </div>
    """, unsafe_allow_html=True)

with eco_card3:
    st.markdown(f"""
        <div class="card">
            <div class="card-title">BIST100</div>
            <div class="card-value">
                {round(bist_close.iloc[-1],2)}
            </div>
        </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------
# EKONOMİK GÖSTERGELER
# ---------------------------------------------------

st.subheader("Ekonomik Göstergeler")

eco1, eco2, eco3 = st.columns(3)

with eco1:

    fig_usd = px.line(
        x=usdtry.index,
        y=usd_close,
        title="USD/TRY",
        labels={
            "x" : "Tarih",
            "y" : "USD/TRY"
        }
    )

    fig_usd.update_layout(
        template="plotly_dark",
        height=350
    )

    st.plotly_chart(
        fig_usd,
        use_container_width=True
    )

with eco2:

    fig_gold = px.line(
        x=altin.index,
        y=gold_close,
        title="Altın",
    labels = {
        "x": "Tarih",
        "y": "ALTIN/USD"
    }
    )

    fig_gold.update_layout(
        template="plotly_dark",
        height=350
    )

    st.plotly_chart(
        fig_gold,
        use_container_width=True
    )

with eco3:

    fig_bist = px.line(
        x=bist100.index,
        y=bist_close,
        title="BIST100",
        labels={
            "x": "Tarih",
            "y": "BIST100"
        }
    )

    fig_bist.update_layout(
        template="plotly_dark",
        height=350
    )

    st.plotly_chart(
        fig_bist,
        use_container_width=True
    )

# ---------------------------------------------------
# MAKROEKONOMİK GRAFİKLER
# ---------------------------------------------------

st.subheader("Makroekonomik Göstergeler")

macro1, macro2 = st.columns(2)

with macro1:

    fig_enflasyon = px.line(
        enflasyon_df,
        x="Tarih",
        y="Enflasyon",
        title="Türkiye Enflasyon Oranı"
    )

    fig_enflasyon.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig_enflasyon,
        use_container_width=True
    )

with macro2:

    fig_faiz = px.line(
        faiz_df,
        x="Tarih",
        y="Faiz",
        title="Politika Faiz Oranı"
    )

    fig_faiz.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig_faiz,
        use_container_width=True
    )

# ---------------------------------------------------
# TRGYO vs 10Y ANALİZİ
# ---------------------------------------------------

st.subheader("TRGYO vs ABD 10Y Tahvil Analizi")

fig_compare = go.Figure()

fig_compare.add_trace(
    go.Scatter(
        x=hisse.index,
        y=close_prices,
        mode='lines',
        name='TRGYO',
        yaxis='y1'
    )
)

fig_compare.add_trace(
    go.Scatter(
        x=us10y.index,
        y=us10y_close,
        mode='lines',
        name='US 10Y',
        yaxis='y2'
    )
)

fig_compare.update_layout(
    template="plotly_dark",
    height=500,

    yaxis=dict(
        title="TRGYO"
    ),

    yaxis2=dict(
        title="US 10Y",
        overlaying='y',
        side='right'
    )
)

st.plotly_chart(
    fig_compare,
    use_container_width=True
)

# ---------------------------------------------------
# FİNANSAL ANALİZ
# ---------------------------------------------------

st.subheader("Şirket Finansal Analizi")

fin1, fin2 = st.columns(2)

with fin1:

    fig_pd = px.line(
        pd_df,
        x="Tarih",
        y="PD",
        title="TRGYO P/D Oranı",
        markers=True
    )

    fig_pd.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig_pd,
        use_container_width=True
    )

with fin2:

    fig_kar = px.bar(
        kar_df,
        x="Tarih",
        y="NetKar",
        title="TRGYO Çeyreklik Net Kar"
    )

    fig_kar.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig_kar,
        use_container_width=True
    )

# ---------------------------------------------------
# MAKRO + SEKTÖR
# ---------------------------------------------------

st.subheader("Makroekonomik ve Sektörel Analiz")

sec1, sec2 = st.columns(2)

with sec1:

    fig_gsyh = px.line(
        gsyh_df,
        x="Tarih",
        y="GSYH",
        title="Türkiye GSYH Büyüme Oranı",
        markers=True
    )

    fig_gsyh.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig_gsyh,
        use_container_width=True
    )

with sec2:

    fig_konut = px.bar(
        konut_df,
        x="Tarih",
        y="KonutSatis",
        title="Türkiye Konut Satışları"
    )

    fig_konut.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig_konut,
        use_container_width=True
    )

# ---------------------------------------------------
# GETİRİ EĞRİSİ
# ---------------------------------------------------

st.subheader("Tahvil ve Getiri Eğrisi Analizi")

fig_yield = go.Figure()

fig_yield.add_trace(
    go.Scatter(
        x=yield_df["Vade"],
        y=yield_df[2024],
        mode='lines+markers',
        name='2024'
    )
)

fig_yield.add_trace(
    go.Scatter(
        x=yield_df["Vade"],
        y=yield_df[2025],
        mode='lines+markers',
        name='2025'
    )
)

fig_yield.add_trace(
    go.Scatter(
        x=yield_df["Vade"],
        y=yield_df[2026],
        mode='lines+markers',
        name='2026'
    )
)

fig_yield.update_layout(
    template="plotly_dark",
    height=500
)

st.plotly_chart(
    fig_yield,
    use_container_width=True
)
