"""
Dashboard IoT - Streamlit
Conecta con ThingSpeak para visualizar datos del ESP32
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# Configuración
st.set_page_config(page_title="IoT Dashboard", page_icon="🌡️", layout="wide")

# Credenciales de ThingSpeak
try:
    API_KEY = st.secrets["THINGSPEAK_API_KEY"]
    CHANNEL_ID = st.secrets["THINGSPEAK_CHANNEL_ID"]
except:
    API_KEY = "XXXXXXXXXXXXXXXX"
    CHANNEL_ID = "1234567"

def obtener_datos(num_puntos=100):
    """Obtiene datos desde ThingSpeak"""
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json"
    params = {"api_key": API_KEY, "results": num_puntos}
    respuesta = requests.get(url, params=params, timeout=10)
    datos = respuesta.json()
    df = pd.DataFrame(datos["feeds"])
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.rename(columns={"field1": "Temperatura", "field2": "Humedad"})
    df["Temperatura"] = pd.to_numeric(df["Temperatura"], errors="coerce")
    df["Humedad"] = pd.to_numeric(df["Humedad"], errors="coerce")
    return df.dropna()

# Título
st.title("🌡️ Dashboard IoT - Estación Meteorológica")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    num_puntos = st.slider("Lecturas", 10, 500, 100, 10)
    temp_max = st.number_input("Temp. máxima", value=30)
    temp_min = st.number_input("Temp. mínima", value=15)
    hum_max = st.number_input("Humedad máxima", value=80)
    hum_min = st.number_input("Humedad mínima", value=30)
    auto_refresh = st.checkbox("⚡ Auto-refresh (30s)")
    if st.button("🔄 Actualizar"):
        st.cache_data.clear()

# Cargar datos
@st.cache_data(ttl=30)
def cargar(n):
    return obtener_datos(n)

df = cargar(num_puntos)

if df.empty:
    st.error("❌ Sin datos. Verifica API Key y Channel ID.")
    st.stop()

# Métricas
ultima = df.iloc[-1]
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌡️ Temperatura", f"{ultima['Temperatura']:.1f}°C")
with col2:
    st.metric("💧 Humedad", f"{ultima['Humedad']:.0f}%")
with col3:
    st.metric(" Temp. Promedio", f"{df['Temperatura'].mean():.1f}°C")
with col4:
    st.metric("📊 Hum. Promedio", f"{df['Humedad'].mean():.0f}%")

# Alarmas
st.markdown("### 🔔 Alarmas")
alertas = []
if ultima["Temperatura"] > temp_max:
    alertas.append(f"️ Temp alta: {ultima['Temperatura']:.1f}°C")
if ultima["Temperatura"] < temp_min:
    alertas.append(f"❄️ Temp baja: {ultima['Temperatura']:.1f}°C")
if ultima["Humedad"] > hum_max:
    alertas.append(f"💧 Humedad alta: {ultima['Humedad']:.0f}%")
if ultima["Humedad"] < hum_min:
    alertas.append(f"🏜️ Humedad baja: {ultima['Humedad']:.0f}%")

if alertas:
    for a in alertas:
        st.warning(a)
else:
    st.success("✅ Todo normal")

# Gráficas
st.markdown("### 📈 Gráficas")
tab1, tab2 = st.tabs(["️ Temperatura", "💧 Humedad"])

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["Temperatura"],
                            mode="lines+markers", name="Temp",
                            line=dict(color="#ff6b6b", width=3)))
    fig.add_hline(y=temp_max, line_dash="dash", line_color="red")
    fig.add_hline(y=temp_min, line_dash="dash", line_color="blue")
    fig.update_layout(title="Temperatura (°C)", template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["Humedad"],
                            mode="lines+markers", name="Hum",
                            line=dict(color="#4ecdc4", width=3),
                            fill="tozeroy"))
    fig.add_hline(y=hum_max, line_dash="dash", line_color="red")
    fig.add_hline(y=hum_min, line_dash="dash", line_color="blue")
    fig.update_layout(title="Humedad (%)", template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

# Descarga CSV
st.markdown("### 📥 Descarga")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📄 Descargar CSV", csv,
                   f"datos_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

# Auto-refresh
if auto_refresh:
    time.sleep(30)
    st.rerun()
