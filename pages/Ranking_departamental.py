import pandas as pd
import streamlit as st
import plotly.express as px
import requests
import numpy as np

# ===============================
# CONFIGURACIÓN DE LA PÁGINA
# ===============================
st.set_page_config(
    page_title="Quality educational app",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# ESTILO CSS
# ===============================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 1rem;
    max-width: 1280px;
}
.main-title {
    font-size: 40px;
    font-weight: 800;
    color: #172033;
    margin-bottom: 4px;
}
.subtitle {
    font-size: 17px;
    color: #667085;
    margin-bottom: 25px;
}
.section-title {
    font-size: 26px;
    font-weight: 800;
    color: #172033;
    margin-top: 35px;
    margin-bottom: 10px;
}
.metric-card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    text-align: center;
    min-height: 130px;
}
.metric-title {
    font-size: 14px;
    color: #344054;
    font-weight: 600;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #D92D20;
    margin-top: 8px;
}
.metric-sub {
    font-size: 14px;
    color: #667085;
}
.map-card {
    background: white;
    padding: 15px;
    border-radius: 18px;
    border: 1px solid #E5E7EB;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}
.info-box {
    background: #F9FAFB;
    padding: 18px;
    border-radius: 14px;
    border: 1px solid #E5E7EB;
    color: #344054;
    font-size: 15px;
    margin-top: 15px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# COMPONENTES DE MATEMÁTICA ESTADÍSTICA
# ===============================
def gini(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return np.nan
    if np.any(x < 0):
        raise ValueError("Gini requiere valores no negativos")
    if np.sum(x) == 0:
        return 0.0
    x = np.sort(x)
    n = len(x)
    index = np.arange(1, n + 1)
    return np.sum((2 * index - n - 1) * x) / (n * np.sum(x))


def theil_t(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return np.nan
    if np.any(x < 0):
        raise ValueError("Theil requiere valores no negativos")
    if np.sum(x) == 0:
        return 0.0
    mu = np.mean(x)
    ratios = x[x > 0] / mu
    return np.mean(ratios * np.log(ratios))

# ===============================
# CARGA DE DATOS OPTIMIZADA
# ===============================
@st.cache_data
def load_data():
    # Carga inicial y filtro estricto de columnas requeridas
    vars_to_keep = [
        "estu_depto_presentacion",
        "punt_global",
        "mod_competen_ciudada_punt",
        "mod_comuni_escrita_punt",
        "mod_ingles_punt",
        "mod_razona_cuantitat_punt"
    ]
    df = pd.read_csv("https://raw.githubusercontent.com/it-ces/Datasets/refs/heads/main/SABER-PRO2024.csv", sep=",", usecols=vars_to_keep)
    return df


@st.cache_data
def load_geojson():
    url_geojson = "https://raw.githubusercontent.com/it-ces/Datasets/main/colombia.geojson"
    return requests.get(url_geojson).json()


# ===============================
# PROCESAMIENTO CACHADO POR FILTRO
# ===============================
@st.cache_data
def process_filtered_data(df, score_name):
    # Clonar subconjunto y limpiar nulos
    sub_df = df[["estu_depto_presentacion", score_name]].dropna().copy()
    
    # Mapeo estricto para emparejar con el GeoJSON
    sub_df["estu_depto_presentacion"] = sub_df["estu_depto_presentacion"].str.strip().str.upper()
    
    mapeo_deptos = {
        "BOGOTÁ": "BogotáD.C.", "ATLANTICO": "Atlántico", "BOLIVAR": "Bolívar",
        "BOYACA": "Boyacá", "CAQUETA": "Caquetá", "CHOCO": "Chocó",
        "CORDOBA": "Córdoba", "GUAINIA": "Guainía", "LA GUAJIRA": "LaGuajira",
        "NORTE SANTANDER": "NortedeSantander", "QUINDIO": "Quindío",
        "SAN ANDRES": "SanAndrésyProvidencia", "VAUPES": "Vaupés",
        "VALLE": "ValledelCauca", "AMAZONAS": "Amazonas", "ANTIOQUIA": "Antioquia",
        "ARAUCA": "Arauca", "CALDAS": "Caldas", "CASANARE": "Casanare",
        "CAUCA": "Cauca", "CESAR": "Cesar", "CUNDINAMARCA": "Cundinamarca",
        "GUAVIARE": "Guaviare", "HUILA": "Huila", "MAGDALENA": "Magdalena",
        "META": "Meta", "NARIÑO": "Nariño", "PUTUMAYO": "Putumayo",
        "RISARALDA": "Risaralda", "SANTANDER": "Santander", "SUCRE": "Sucre",
        "TOLIMA": "Tolima", "VICHADA": "Vichada"
    }
    
    sub_df["estu_depto_presentacion"] = sub_df["estu_depto_presentacion"].map(mapeo_deptos).fillna(sub_df["estu_depto_presentacion"])

    # Agrupamiento por departamento
    dpto_score = (
        sub_df.groupby("estu_depto_presentacion")[score_name]
        .agg(
            promedio="mean",
            estudiantes="size",
            minimo="min",
            q1=lambda x: x.quantile(0.25),
            mediana="median",
            q3=lambda x: x.quantile(0.75),
            maximo="max",
            desviacion="std"
        )
        .reset_index()
    )
    
    dpto_score["rango"] = dpto_score["maximo"] - dpto_score["minimo"]
    dpto_score["rango_intercuartilico"] = dpto_score["q3"] - dpto_score["q1"]
    
    # Métricas Globales Nacionales
    metrics = {
        "promedio_nacional": sub_df[score_name].mean(),
        "mediana_nacional": sub_df[score_name].median(),
        "total_estudiantes": len(sub_df),
        "rango_total": sub_df[score_name].max() - sub_df[score_name].min(),
        "iqr_total": sub_df[score_name].quantile(0.75) - sub_df[score_name].quantile(0.25),
        "desviacion_total": sub_df[score_name].std(),
        "gini_total": gini(sub_df[score_name]),
        "theil_total": theil_t(sub_df[score_name]),
        "mayor": dpto_score.loc[dpto_score["promedio"].idxmax()].to_dict(),
        "menor": dpto_score.loc[dpto_score["promedio"].idxmin()].to_dict()
    }
    
    return dpto_score, metrics


# Carga inicial de fuentes externas
raw_df = load_data()
geojson = load_geojson()

# ===============================
# BARRA LATERAL (FILTROS)
# ===============================
with st.sidebar:
    st.title("Filtros de Análisis")
    
    score_label = st.selectbox(
        "1. Selecciona el puntaje / módulo:",
        [
            "Puntaje global",
            "Inglés",
            "Razonamiento cuantitativo",
            "Competencia ciudadana",
            "Comunicación escrita"
        ]
    )

    score_name_df = {
        "Puntaje global": "punt_global",
        "Razonamiento cuantitativo": "mod_razona_cuantitat_punt",
        "Competencia ciudadana": "mod_competen_ciudada_punt",
        "Comunicación escrita": "mod_comuni_escrita_punt",
        "Inglés": "mod_ingles_punt"
    }
    score_name = score_name_df[score_label]

# Extracción de datos procesados mediante Cache
dpto_score, metrics = process_filtered_data(raw_df, score_name)

# ===============================
# RENDERIZADO DE INTERFAZ (UI)
# ===============================
st.markdown('<div class="main-title">Quality educational app</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Análisis territorial del desempeño en <b>{score_label}</b> en Saber Pro 2024.</div>', unsafe_allow_html=True)

# Tarjetas Métricas Principales
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Promedio nacional</div><div class="metric-value">{metrics["promedio_nacional"]:.1f}</div><div class="metric-sub">{score_label}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Mayor promedio</div><div class="metric-value">{metrics["mayor"]["estu_depto_presentacion"]}</div><div class="metric-sub">{metrics["mayor"]["promedio"]:.1f} puntos</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Menor promedio</div><div class="metric-value">{metrics["menor"]["estu_depto_presentacion"]}</div><div class="metric-sub">{metrics["menor"]["promedio"]:.1f} puntos</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-title">Total estudiantes</div><div class="metric-value">{metrics["total_estudiantes"]:,.0f}</div><div class="metric-sub">Registros analizados</div></div>', unsafe_allow_html=True)

# Sección del Mapa
st.markdown('<div class="section-title">Mapa de desempeño por departamento</div>', unsafe_allow_html=True)

fig_map = px.choropleth(
    dpto_score,
    geojson=geojson,
    locations="estu_depto_presentacion",
    featureidkey="properties.NAME_1",
    color="promedio",
    color_continuous_scale="YlOrRd",
    hover_name="estu_depto_presentacion",
    hover_data={
        "promedio": ":.1f",
        "estudiantes": ":,",
        "mediana": ":.1f",
        "rango": ":.1f",
        "rango_intercuartilico": ":.1f",
        "estu_depto_presentacion": False
    },
    labels={
        "promedio": "Puntaje promedio",
        "estudiantes": "N estudiantes",
        "mediana": "Mediana",
        "rango": "Rango",
        "rango_intercuartilico": "IQR"
    }
)

fig_map.update_traces(marker_line_width=0.8, marker_line_color="white")
fig_map.update_geos(visible=False, center={"lat": 4.5, "lon": -74}, projection_scale=18)
fig_map.update_layout(
    height=600,
    margin=dict(l=0, r=0, t=0, b=0),
    coloraxis_colorbar=dict(title="Puntaje", thickness=15, len=0.7)
)

st.markdown('<div class="map-card">', unsafe_allow_html=True)
st.plotly_chart(fig_map, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Sección Dispersión Nacional
st.markdown('<div class="section-title">Dispersión y desigualdad nacional</div>', unsafe_allow_html=True)
d1, d2, d3, d4, d5 = st.columns(5)
d1.metric("Rango", f"{metrics['rango_total']:.1f}")
d2.metric("IQR", f"{metrics['iqr_total']:.1f}")
d3.metric("Desv. estándar", f"{metrics['desviacion_total']:.1f}")
d4.metric("Gini", f"{metrics['gini_total']:.4f}")
d5.metric("Theil", f"{metrics['theil_total']:.4f}")

st.markdown("""
<div class="info-box">
<b>Lectura rápida:</b><br>
El rango mide la distancia total de los puntajes. El Rango Intercuartílico (IQR) remueve valores extremos analizando el 50% central de la muestra. Los coeficientes de Gini y Theil resumen la concentración estadística: valores más elevados apuntan a brechas de desigualdad interna más acentuadas entre los examinados.
</div>
""", unsafe_allow_html=True)

# Gráfico de Barras Horizontal
st.markdown('<div class="section-title">Top departamentos por promedio</div>', unsafe_allow_html=True)
top_dpto = dpto_score.sort_values("promedio", ascending=False).head(15)

fig_bar = px.bar(
    top_dpto.sort_values("promedio", ascending=True),
    x="promedio",
    y="estu_depto_presentacion",
    orientation="h",
    text="promedio",
    labels={"promedio": "Puntaje promedio", "estu_depto_presentacion": "Departamento"}
)
fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
fig_bar.update_layout(height=480, margin=dict(l=0, r=20, t=10, b=20), xaxis_title="Puntaje promedio", yaxis_title="")
st.plotly_chart(fig_bar, use_container_width=True)

# Tabla de Rankings Completa
st.markdown('<div class="section-title">Ranking por departamento</div>', unsafe_allow_html=True)
ranking_dpto = dpto_score.sort_values("promedio", ascending=False).copy()
ranking_dpto.insert(0, "Ranking", range(1, len(ranking_dpto) + 1))

ranking_dpto = ranking_dpto.rename(columns={
    "estu_depto_presentacion": "Departamento", "promedio": "Promedio", "estudiantes": "Estudiantes",
    "minimo": "Mínimo", "q1": "Q1", "mediana": "Mediana", "q3": "Q3", "maximo": "Máximo",
    "desviacion": "Desv. estándar", "rango": "Rango", "rango_intercuartilico": "IQR"
})

st.dataframe(
    ranking_dpto.style.format({
        "Promedio": "{:.1f}", "Mínimo": "{:.1f}", "Q1": "{:.1f}", "Mediana": "{:.1f}",
        "Q3": "{:.1f}", "Máximo": "{:.1f}", "Rango": "{:.1f}", "IQR": "{:.1f}",
        "Desv. estándar": "{:.1f}", "Estudiantes": "{:,.0f}"
    }),
    use_container_width=True,
    hide_index=True
)