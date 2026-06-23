import pandas as pd
import streamlit as st
import plotly.express as px

st.title('Quality educational app')

df = pd.read_csv('Examen_Saber_Pro_Genericas_2024.txt', sep=';')

vars = ['punt_global',
         'inst_nombre_institucion',
         'estu_prgm_academico',
          'mod_competen_ciudada_punt',
          'mod_comuni_escrita_punt',
        'mod_ingles_punt', 'mod_razona_cuantitat_punt']
         
df = df[vars]


# list to select the program
program = st.selectbox(      'please select the program to run analysis', df['estu_prgm_academico'].unique())

score_name = st.selectbox( 'select the score',
    ['puntaje global', 'inglés', 'razonamiento cuantitativo', 'compentencia ciudadana']
)

score_name_df = {'puntaje global': 'punt_global',  
                 'razonamiento cuantitativo': 'mod_razona_cuantitat_punt',
                  'compentencia ciudadana':  'mod_competen_ciudada_punt',
                 'inglés':  'mod_ingles_punt'}

score_name  = score_name_df[score_name]

program_df = df[df['estu_prgm_academico'] == program].copy()
program_df['mean_score'] = program_df.groupby(by=['inst_nombre_institucion'])[score_name].transform('mean')
program_df = program_df[['inst_nombre_institucion', 'mean_score']]
program_df = program_df.drop_duplicates(subset= ['inst_nombre_institucion']).sort_values(by = ['mean_score'], ascending=False).reset_index(drop=True)
st.dataframe(program_df)
mean_score_val = program_df['mean_score']


# calcular gini o theil...

import numpy as np

def gini(x):
    """
    Coeficiente de Gini.
    Retorna un valor entre 0 (igualdad perfecta) y 1 (desigualdad máxima).
    """
    x = np.asarray(x, dtype=float)

    # Eliminar NaN
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
    """
    Índice de Theil T.
    Retorna 0 para igualdad perfecta y valores mayores para mayor desigualdad.
    """
    x = np.asarray(x, dtype=float)

    # Eliminar NaN
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



st.header('inequality measures')

st.subheader('select metrics')
# we can make about all studens or by programs..
gini_box = st.checkbox('Gini index')
theil_box = st.checkbox('Theil index')
range_box = st.checkbox('Range(Max-Min)')
cv_box = st.checkbox('Coeficiente de variación')

st.subheader('select by all individuals or by program')


unidad = st.radio('which is the best song', ('University', 
                                                  'All students'))


calculate = st.button('calculate')
if calculate:
    if unidad == 'University':
        if gini_box:
            st.write('gini', gini(mean_score_val))
        if theil_box:
            st.write('theil', theil_t(mean_score_val))
        if range_box:
            st.write('Range', mean_score_val.max() - mean_score_val.min())    
        if cv_box:
            st.write('CV', mean_score_val.std()/ mean_score_val.mean()) 
    else:
        mean_score_val = df[df['estu_prgm_academico'] == program][score_name]
        if gini_box:
            st.write('gini', gini(mean_score_val))
        
        if theil_box:
            st.write('theil', theil_t(mean_score_val))
        if range_box:
            st.write('Range', mean_score_val.max() - mean_score_val.min())    
        if cv_box:
            st.write('CV', mean_score_val.std()/ mean_score_val.mean()) 



# add in each university which are the better programs..

st.header('Top pograms by univeristy')


st.write('Now we are going to see for each univeristy wich is the better program')



institution = st.selectbox('Select university ', df['inst_nombre_institucion'].unique())


score_name_institution = st.selectbox( 'select the score ',
    ['puntaje global', 'inglés', 'razonamiento cuantitativo', 'compentencia ciudadana'])


score_name_institution  = score_name_df[score_name_institution]



df_inst = df[df['inst_nombre_institucion']  == institution] .copy()
df_inst['mean-score']  = df_inst.groupby(by=['estu_prgm_academico'])[score_name_institution].transform('mean')
df_inst = df_inst[['inst_nombre_institucion','estu_prgm_academico',  'mean-score']]
df_inst = df_inst.drop_duplicates(subset=['estu_prgm_academico']).reset_index(drop=True)

st.dataframe(df_inst.sort_values(by=['mean-score'], ascending=False))






# add a functionality with multiselect...


# wich is the better program with multiselect.. for university i could make a dataframe!



# which is the better univeristy to study some programs..   
# add slider possible
programs_elite = st.multiselect('choose program(s)',  df['estu_prgm_academico'].unique())
# what rank we need show?
rank_val = st.slider('select rank', min_value=1, max_value=10)

df_elite = df[df['estu_prgm_academico'].isin(programs_elite)].copy()
df_elite['mean-score'] = df_elite.groupby(by=['estu_prgm_academico', 'inst_nombre_institucion'])['mod_razona_cuantitat_punt'].transform('mean')
df_elite.drop_duplicates(subset=['inst_nombre_institucion','estu_prgm_academico' ], inplace=True)
df_elite['rank'] = df_elite.groupby(by=['estu_prgm_academico'])['mean-score'].rank(ascending=False, method='dense')
df_elite[df_elite['estu_prgm_academico']=='ECONOMIA'].sort_values(by='rank')
df_elite = df_elite[df_elite['rank'] <= rank_val]
st.dataframe(df_elite.sort_values(by=['estu_prgm_academico', 'rank']))
