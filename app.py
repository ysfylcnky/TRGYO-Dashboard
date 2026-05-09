import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Başlık
st.title("Torunlar GYO Finans Dashboard")

# SIDEBAR

st.sidebar.title("Filtreler")

# Grafik türü seçimi
grafik_turu = st.sidebar.selectbox(
    "Grafik Türü",
    ["Çizgi Grafik", "Mum Grafik"]
)

# Hareketli ortalama aç/kapat
hareketli_ortalama = st.sidebar.checkbox(
    "Hareketli Ortalamaları Göster",
    value=True
)

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
        box-shadow: 0px 0px 15px rgba(0,255,255,0.2);
    }

    .card-title {
        font-size: 20px;
        color: #AAAAAA;
    }

    .card-value {   
        font-size: 35px;
        color: #00FFFF;
        font-weight: bold;
    }

    </style>
""", unsafe_allow_html=True)

# Sayfa ayarı
st.set_page_config(
    page_title="TRGYO Dashboard",
    layout="wide"
)

# Veri çek
zaman_araligi = st.sidebar.selectbox(
    "Zaman Aralığı",
    ["1 Ay", "3 Ay", "6 Ay", "1 Yıl"],
    index = 3

)
# Seçilen zaman aralığına göre veri çekme

if zaman_araligi == "1 Ay":
    period = "1mo"

elif zaman_araligi == "3 Ay":
    period = "3mo"

elif zaman_araligi == "6 Ay":
    period = "6mo"

else:
    period = "1y"

# Veri çek
hisse = yf.download("TRGYO.IS", period=period)

# Dolar kuru
usdtry = yf.download("TRY=X", period="1y")

# Altın
altin = yf.download("GC=F", period="1y")

# BIST100
bist100 = yf.download("XU100.IS", period="1y")

# Kapanış fiyatı
close_prices = hisse["Close"].squeeze()
# USDTRY
usd_close = usdtry["Close"].squeeze()
# Altın kapanış
gold_close = altin["Close"].squeeze()
# BIST100 kapanış
bist_close = bist100["Close"].squeeze()
# Günlük getiriler
# Günlük getirileri birleştir

returns_df = pd.concat(
    [
        close_prices.pct_change(),
        bist_close.pct_change()
    ],
    axis=1
).dropna()

# Sütun isimleri

returns_df.columns = ["TRGYO", "BIST100"]

# Ayrıştır

trgyo_returns = returns_df["TRGYO"]

bist_returns = returns_df["BIST100"]
# Beta hesabı
covariance = np.cov(
    trgyo_returns,
    bist_returns
)[0][1]
market_variance = np.var(bist_returns)
beta = covariance / market_variance
beta = round(beta, 2)

# Excel verileri
enflasyon_df = pd.read_excel("data/inflation.xlsx")
faiz_df = pd.read_excel("data/rate.xlsx")
pd_df = pd.read_excel("data/pd_orani.xlsx")
kar_df = pd.read_excel("data/ceyreklik_kar.xlsx")
gsyh_df = pd.read_excel("data/gsyh.xlsx")
konut_df = pd.read_excel("data/konut_satis.xlsx")
yield_df = pd.read_excel("data/yield_curve.xlsx")


# Hareketli ortalamalar
hisse["MA50"] = close_prices.rolling(50).mean()
hisse["MA200"] = close_prices.rolling(200).mean()

# Güncel fiyat
son_fiyat = round(close_prices.iloc[-1], 2)

# Günlük değişim
gunluk_degisim = round(
    ((close_prices.iloc[-1] - close_prices.iloc[-2])
     / close_prices.iloc[-2]) * 100,
    2
)

# KPI kartları için sütunlar
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Güncel TRGYO Fiyatı",
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
        "TRGYO Beta",
        beta
    )


# Grafik türüne göre gösterim

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
            name='MA50',
            line=dict(color='orange', width=3)
        )

        fig.add_scatter(
            x=hisse.index,
            y=hisse["MA200"],
            mode='lines',
            name='MA200',
            line=dict(color='purple', width=3)
        )

    fig.update_layout(
        template="plotly_dark",
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

else:

    fig = go.Figure()

    # Mum grafik
    fig.add_trace(go.Candlestick(
        x=hisse.index,
        open=hisse["Open"].squeeze(),
        high=hisse["High"].squeeze(),
        low=hisse["Low"].squeeze(),
        close=close_prices,
        name="TRGYO"
    ))
    if hareketli_ortalama:
        # MA50
        fig.add_trace(go.Scatter(
            x=hisse.index,
            y=hisse["MA50"],
            mode='lines',
            name='MA50'
        ))

        # MA200
        fig.add_trace(go.Scatter(
            x=hisse.index,
            y=hisse["MA200"],
            mode='lines',
            name='MA200'
        ))

    fig.update_layout(
        title="TRGYO Candlestick Grafiği",
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

# Yeni sütunlar
col4, col5, col6 = st.columns(3)

with col4:
    st.markdown(f"""
        <div class="card">
            <div class="card-title">USD/TRY</div>
            <div class="card-value">
                {round(usd_close.iloc[-1],2)}
            </div>
        </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
        <div class="card">
            <div class="card-title">Altın</div>
            <div class="card-value">
                {round(gold_close.iloc[-1],2)} $
            </div>
        </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown(f"""
        <div class="card">
            <div class="card-title">BIST100</div>
            <div class="card-value">
                {round(bist_close.iloc[-1],2)}
            </div>
        </div>
    """, unsafe_allow_html=True)

st.subheader("Ekonomik Göstergeler")

# İki sütun
left, right = st.columns(2)

# USDTRY grafik
with left:

    fig_usd = px.line(
        x=usdtry.index,
        y=usd_close,
        title="USD/TRY Grafiği"
    )

    fig_usd.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(fig_usd, use_container_width=True)

# Altın grafik
with right:

    fig_gold = px.line(
        x=altin.index,
        y=gold_close,
        title="Altın USD Grafiği"
    )

    fig_gold.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(fig_gold, use_container_width=True)

st.subheader("Makroekonomik Göstergeler")

col7, col8 = st.columns(2)

# ENFLASYON GRAFİĞİ
with col7:

    fig_enflasyon = px.line(
        enflasyon_df,
        x="Date",
        y="Inflation",
        title="Türkiye Enflasyon Oranı"
    )

    fig_enflasyon.update_layout(
        template="plotly_dark",
        height=400,
        yaxis=dict(range=[0, 100])
    )

    st.plotly_chart(
        fig_enflasyon,
        use_container_width=True
    )

# FAİZ GRAFİĞİ
with col8:

    fig_faiz = px.line(
        faiz_df,
        x="Date",
        y="Rate",
        title="Politika Faiz Oranı"
    )

    fig_faiz.update_layout(
        template="plotly_dark",
        height=400,
        yaxis=dict(range=[0, 100])
    )

    st.plotly_chart(
        fig_faiz,
        use_container_width=True
    )

st.subheader("Şirket Finansal Analizi")

col9, col10 = st.columns(2)

# P/D GRAFİĞİ
with col9:

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

# Çeyreklik Kar
with col10:

    fig_kar = px.bar(
        kar_df,
        x="Donem",
        y="NetKar",
        title="TRGYO Çeyreklik Net Kar Büyümesi"
    )

    fig_kar.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(
        fig_kar,
        use_container_width=True
    )

st.subheader("Makroekonomik ve Sektörel Analiz")

col11, col12 = st.columns(2)

# GSYH GRAFİĞİ
with col11:

    fig_gsyh = px.line(
        gsyh_df,
        x="Tarih",
        y="GSYH",
        title="Türkiye GSYH Büyüme Oranı",
        markers=True
    )

    fig_gsyh.update_layout(
        template="plotly_dark",
        height=400,
        yaxis=dict(range=[0,10])
    )

    st.plotly_chart(
        fig_gsyh,
        use_container_width=True
    )

# KONUT SATIŞLARI
with col12:

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

st.subheader("Tahvil ve Getiri Eğrisi Analizi")

fig_yield = go.Figure()

# 2024
fig_yield.add_trace(go.Scatter(
    x=yield_df["Vade"],
    y=yield_df[2024],
    mode='lines+markers',
    name='2024'
))

# 2025
fig_yield.add_trace(go.Scatter(
    x=yield_df["Vade"],
    y=yield_df[2025],
    mode='lines+markers',
    name='2025'
))

# 2026
fig_yield.add_trace(go.Scatter(
    x=yield_df["Vade"],
    y=yield_df[2026],
    mode='lines+markers',
    name='2026'
))

fig_yield.update_layout(
    template="plotly_dark",
    height=500,
    yaxis=dict(range=[0,50])
)

st.plotly_chart(
    fig_yield,
    use_container_width=True
)