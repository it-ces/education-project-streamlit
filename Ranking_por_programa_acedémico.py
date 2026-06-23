import streamlit as st
import pandas as pd
import plotly.express as px

##Functions....


st.set_page_config(
    page_title="Quality educational app",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('Quality educational app')

# 2. Carga de datos optimizada con Caché
@st.cache_data
def load_data():
    df = pd.read_csv('https://raw.githubusercontent.com/it-ces/Datasets/refs/heads/main/SABER-PRO2024.csv', sep=',')
    vars_to_keep = [
        'punt_global',
        'inst_nombre_institucion',
        'estu_prgm_academico',
        'mod_competen_ciudada_punt',
        'mod_comuni_escrita_punt',
        'mod_ingles_punt', 
        'mod_razona_cuantitat_punt'
    ]
    return df[vars_to_keep].copy()

df = load_data()

vars = ['punt_global',
         'inst_nombre_institucion',
         'estu_prgm_academico',
          'mod_competen_ciudada_punt',
          'mod_comuni_escrita_punt',
        'mod_ingles_punt', 'mod_razona_cuantitat_punt']
         
df = df[vars].copy()



with st.sidebar:
    st.title("Filtro")
    st.subheader("Filtros de Análisis")
    
    program = st.selectbox(
        '1. Selecciona el programa académico:', 
        df['estu_prgm_academico'].unique()
    )
    
    score_name = st.selectbox(
        '2. Selecciona el puntaje / módulo:',
        ['Puntaje global', 'Inglés', 'Razonamiento cuantitativo', 'Competencia ciudadana', 'Comunicación escrita']
    )
    
    score_name_df = {
        'Puntaje global': 'punt_global',  
        'Razonamiento cuantitativo': 'mod_razona_cuantitat_punt',
        'Competencia ciudadana': 'mod_competen_ciudada_punt',
        'Comunicación escrita': 'mod_comuni_escrita_punt',
        'Inglés': 'mod_ingles_punt'
    }
    score_name = score_name_df[score_name]
    



df_program = df[df['estu_prgm_academico']==program][['inst_nombre_institucion', 'estu_prgm_academico', score_name]].copy()
pct  = df_program[score_name].rank(pct=True)

df_program['Q'] = pd.cut(
    pct,
    bins=[0, 0.25, 0.50, 0.75, 1],
    labels=['Q1', 'Q2', 'Q3', 'Q4'],
    include_lowest=True
)

df_program['%Q4'] =df_program.groupby(by ='inst_nombre_institucion')['Q'].transform(
    lambda grupo: (grupo=='Q4').sum()/grupo.shape[0]*100)
df_program['mean'] = df_program.groupby(by='inst_nombre_institucion')[score_name].transform('mean')
df_program['std'] = df_program.groupby(by='inst_nombre_institucion')[score_name].transform('std')
df_program['n'] = df_program.groupby(by='inst_nombre_institucion')[score_name].transform('count')
df_program.drop_duplicates(subset=['inst_nombre_institucion'], inplace=True)
df_program.sort_values(by=['mean'], ascending=False, inplace=True)
st.dataframe(df_program[['inst_nombre_institucion',
                        'estu_prgm_academico',
                        'mean',
                        'std',
                        '%Q4',
                        'n']].reset_index(drop=True))

col1, col2, col3, col4 = st.columns(4)

col1.metric("Universidades", df_program["inst_nombre_institucion"].nunique())
col2.metric("Estudiantes", int(df_program["n"].sum()))
col3.metric("Promedio general en todas las carreras", round(df[score_name].mean(), 2))
col4.metric("Promedio general en la carrera ", round( df[df['estu_prgm_academico']==program][score_name].mean(), 2))


df_program = df_program.sort_values("mean", ascending=True)
altura_dinamica = max(300, len(df_program) * 20)

fig = px.bar(
    df_program,
    x="mean",
    y="inst_nombre_institucion",
    orientation="h",
    color="%Q4",
    error_x="std",
    color_continuous_scale="Viridis",
    title="Ranking Universidades: Promedio, Dispersión y % en Cuartil Superior",
    hover_data={
        "mean": ":.2f",
        "std": ":.2f",
        "n": True,
        "%Q4": ":.1f"
    }
)

fig.update_yaxes(
    tickmode="array",
    tickvals=df_program["inst_nombre_institucion"],
    ticktext=df_program["inst_nombre_institucion"],
    automargin=True
)

fig.update_layout(
    height=altura_dinamica,
    width = 1300,
    xaxis_title="Puntaje Promedio",
    yaxis_title="",
    coloraxis_colorbar_title="% Q4",
    margin=dict(l=500, r=80, t=100, b=80)
)

st.plotly_chart(fig,     use_container_width=True)



st.subheader("Desempeño vs dispersión")

fig2 = px.scatter(
    df_program,
    x="mean",
    y="std",
    size="n",
    color="%Q4",
    hover_name="inst_nombre_institucion",
    title="Desempeño vs Dispersión: Promedio, Riesgo y Tamaño",
    color_continuous_scale="Viridis",
    labels={
        "mean": "Puntaje promedio",
        "std": "Dispersión",
        "%Q4": "% en Q4",
        "n": "Número de estudiantes"
    }
)

fig2.update_layout(
    height=600,
    xaxis_title="Puntaje promedio",
    yaxis_title="Desviación estándar"
)

st.plotly_chart(fig2, use_container_width=True)