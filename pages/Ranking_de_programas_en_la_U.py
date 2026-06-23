# pages/2_University_Intelligence.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="University Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# ESTILO
# ===============================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 1rem;
    max-width: 1250px;
}

section[data-testid="stSidebar"] {
    width: 430px !important;
}

section[data-testid="stSidebar"] > div {
    width: 430px !important;
}

.main-title {
    font-size: 38px;
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
    font-size: 25px;
    font-weight: 800;
    color: #172033;
    margin-top: 35px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# CARGAR DATOS
# ===============================
@st.cache_data
def load_data():
    vars_to_keep = [
        "estu_depto_presentacion",
        "punt_global",
        "mod_competen_ciudada_punt",
        "mod_comuni_escrita_punt",
        "inst_nombre_institucion",
        "estu_prgm_academico",
        "mod_ingles_punt",
        "mod_razona_cuantitat_punt"
    ]

    return pd.read_csv(
        "https://raw.githubusercontent.com/it-ces/Datasets/refs/heads/main/SABER-PRO2024.csv",
        sep=",",
        usecols=vars_to_keep
    )

df = load_data()

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.title("Filtros")
    st.subheader("Análisis por universidad")

    score_label = st.selectbox(
        "Selecciona el puntaje:",
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
        "Inglés": "mod_ingles_punt",
        "Razonamiento cuantitativo": "mod_razona_cuantitat_punt",
        "Competencia ciudadana": "mod_competen_ciudada_punt",
        "Comunicación escrita": "mod_comuni_escrita_punt"
    }

    score_name = score_name_df[score_label]

    institution = st.selectbox(
        "Selecciona la universidad:",
        sorted(df["inst_nombre_institucion"].dropna().unique())
    )

    top_n = st.slider(
        "Top programas a mostrar:",
        min_value=5,
        max_value=50,
        value=20,
        step=5
    )

# ===============================
# FILTRO UNIVERSIDAD
# ===============================
df_inst_raw = df[df["inst_nombre_institucion"] == institution].copy()
df_inst_raw = df_inst_raw.dropna(subset=["estu_prgm_academico", score_name])

# ===============================
# RESUMEN POR PROGRAMA
# ===============================
program_stats = (
    df_inst_raw
    .groupby("estu_prgm_academico")
    .agg(
        promedio=(score_name, "mean"),
        estudiantes=(score_name, "size")
    )
    .reset_index()
)

# ===============================
# PERCENTIL NACIONAL
# ===============================
national_programs = (
    df.dropna(subset=["estu_prgm_academico", score_name])
      .groupby("estu_prgm_academico")
      .agg(
          promedio_nacional_programa=(score_name, "mean")
      )
      .reset_index()
)

national_programs["percentil_nacional"] = (
    national_programs["promedio_nacional_programa"]
    .rank(pct=True)
    .mul(100)
)

program_stats = program_stats.merge(
    national_programs[
        [
            "estu_prgm_academico",
            "percentil_nacional"
        ]
    ],
    on="estu_prgm_academico",
    how="left"
)

program_stats = program_stats.sort_values(
    "promedio",
    ascending=False
)

if program_stats.empty:
    st.warning("No hay programas disponibles para esta universidad.")
    st.stop()

# ===============================
# MÉTRICAS
# ===============================
promedio_universidad = df_inst_raw[score_name].mean()
mayor_puntaje = df_inst_raw[score_name].max()
mejor_puntaje = program_stats["promedio"].max()

# ===============================
# TÍTULO
# ===============================
st.markdown(
    '<div class="main-title">University Intelligence</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="subtitle">
    Ranking interno de programas académicos para <b>{institution}</b> usando <b>{score_label}</b>.
    </div>
    """,
    unsafe_allow_html=True
)

# ===============================
# TABLA PRIMERO
# ===============================
st.markdown(
    '<div class="section-title">Ranking de programas</div>',
    unsafe_allow_html=True
)

ranking_programs = program_stats.copy()
ranking_programs.insert(0, "Ranking", range(1, len(ranking_programs) + 1))

ranking_programs = ranking_programs.rename(columns={
    "estu_prgm_academico": "Programa",
    "promedio": "Promedio",
    "percentil_nacional": "Percentil nacional",
    "estudiantes": "Estudiantes"
})

st.dataframe(
    ranking_programs[
        [
            "Ranking",
            "Programa",
            "Promedio",
            "Percentil nacional",
            "Estudiantes"
        ]
    ].style.format({
        "Promedio": "{:.1f}",
        "Percentil nacional": "{:.1f}",
        "Estudiantes": "{:,.0f}"
    }),
    use_container_width=True,
    hide_index=True
)

# ===============================
# MÉTRICAS
# ===============================
st.markdown(
    '<div class="section-title">Resumen institucional</div>',
    unsafe_allow_html=True
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Promedio universidad", f"{promedio_universidad:.1f}")

with c2:
    st.metric("Mayor puntaje", f"{mayor_puntaje:.1f}")

with c3:
    st.metric("Mejor puntaje", f"{mejor_puntaje:.1f}")

# ===============================
# BARRAS
# ===============================
st.markdown(
    '<div class="section-title">Ranking visual de programas</div>',
    unsafe_allow_html=True
)

top_programs = program_stats.head(top_n)

fig_bar = px.bar(
    top_programs.sort_values("promedio", ascending=True),
    x="promedio",
    y="estu_prgm_academico",
    orientation="h",
    text="promedio",
    color="promedio",
    color_continuous_scale="YlOrRd",
    hover_data={
        "promedio": ":.1f",
        "percentil_nacional": ":.1f",
        "estudiantes": ":,"
    },
    labels={
        "promedio": "Puntaje promedio",
        "estu_prgm_academico": "Programa",
        "percentil_nacional": "Percentil nacional",
        "estudiantes": "Estudiantes"
    }
)

fig_bar.update_traces(
    texttemplate="%{text:.1f}",
    textposition="outside"
)

fig_bar.update_layout(
    height=max(500, len(top_programs) * 38),
    margin=dict(l=0, r=30, t=10, b=20),
    yaxis_title="",
    xaxis_title="Puntaje promedio",
    coloraxis_showscale=False,
    showlegend=False
)

st.plotly_chart(fig_bar, use_container_width=True)