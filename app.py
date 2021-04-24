import dash
import os
import time
import ezodf
import pandas as pd
import datetime
import dash_bootstrap_components as dbc
from layout import app_layout
from dash.dependencies import Input, Output, State
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import requests
import json

# === GLOBAL VARIABLES ===
CCAA_DICT = {'AN': 'Andalucía', 'AR': 'Aragón', 'AS': 'Principado de Asturias', 'CN': 'Canarias',
              'CB': 'Cantabria',
              'CM': 'Castilla-La Mancha', 'CL': 'Castilla y León', 'CT': 'Cataluña', 'EX': 'Extremadura',
              'GA': 'Galicia', 'IB': 'Islas Baleares', 'RI': 'La Rioja', 'MD': 'Comunidad de Madrid',
              'MC': 'Región de Murcia', 'NC': 'Comunidad Foral de Navarra', 'PV': 'País Vasco',
              'VC': 'Comunidad Valenciana', 'CE': 'Ciudad Autónoma de Ceuta', 'ML': 'Ciudad Autónoma de Melilla'}

CCAA_PROV_DICT = {'AN': ['AL', 'CA', 'CO', 'GR', 'H', 'J', 'MA', 'SE'],'AR': ['HU', 'TE', 'Z'],'AS': ['O'],
                          'CN': ['GC', 'TF'],'CB': ['S'],'CM': ['AB', 'CR', 'CU', 'GU','TO'],
                          'CL': ['AV', 'BU', 'LE', 'P', 'SA', 'SG', 'SO', 'VA', 'ZA'],'CT':['B', 'GI', 'L', 'T'],
                          'EX': ['BA', 'CC'],'GA': ['C', 'LU', 'OR','PO'],'IB': ['PM'],'RI': ['LO'],'MD': ['M'],
                          'MC': ['MU'],'NC': ['NA'],'PV': ['BI', 'SS', 'VI'],'VC': ['V'],'CE': ['CE'],'ML': ['ME']}
FONT_DICT = dict(family="Courier New, monospace", size=12, color="darkslategrey")
FONT_DICT_small = dict(family="Courier New, monospace", size=10, color="darkslategrey")

# Define TMPDIR and DATADIR
pwd = os.getcwd()
files = os.listdir('.')
if pwd == '/home/ecefbpi' and 'app.py' not in files:
    TMPDIR = '/home/ecefbpi/mysite/tmp/'
    DATADIR = '/home/ecefbpi/mysite/data/'
else:
    TMPDIR = os.getcwd() + '/tmp/'
    DATADIR = os.getcwd() + '/data/'


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.layout = app_layout

# === COMMON FUNCTIONS USED TO GENERATE PLOT FIGURES ===
def covid_plot(filtro_ccaa, avg7days):

    #df
    with open(TMPDIR + 'df.txt') as df_file:
        df_dictionazied = json.load(df_file)
    df = pd.DataFrame.from_dict(df_dictionazied)
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')

    #df_muertes
    with open(TMPDIR + 'df_muertes.txt') as df_muertes_file:
        df_muertes_dictionazied = json.load(df_muertes_file)
    df_muertes = pd.DataFrame.from_dict(df_muertes_dictionazied)
    df_muertes['fecha'] = pd.to_datetime(df_muertes['fecha'], format='%Y-%m-%d')


    if filtro_ccaa == 'ALL':
        df1 = df.groupby("fecha").sum()
        df1.reset_index(level=0, inplace=True)

        df2 = df_muertes.groupby("fecha").sum()
        df2.reset_index(level=0, inplace=True)

        df_final = pd.merge(df1, df2, how='outer')

        df_to_plot = df_final.copy()
        comunidad = 'España'
    else:
        comunidad = CCAA_DICT[filtro_ccaa]
        df_filtered = df[df['ccaa'] == filtro_ccaa]
        df_muertes_filtered = df_muertes[df_muertes['prov'].isin(CCAA_PROV_DICT[filtro_ccaa])]

        df_filtered_total = df_filtered.groupby('fecha').sum()
        df_filtered_total.reset_index(level=0, inplace=True)
        df_muertes_filtered_total = df_muertes_filtered.groupby('fecha').sum()
        df_muertes_filtered_total.reset_index(level=0, inplace=True)

        df_to_plot = pd.merge(df_filtered_total, df_muertes_filtered_total, how='outer')

    if avg7days:
        df_to_plot['total_7avg'] = df_to_plot.iloc[:, 1].rolling(window=7).mean()
        df_to_plot['muertes_7avg'] = df_to_plot.iloc[:, 4].rolling(window=7).mean()

    figtotal = make_subplots(specs=[[{"secondary_y": True}]])

    if avg7days:
        figtotal.add_trace(go.Scatter(x=df_to_plot['fecha'], y=df_to_plot['total_7avg'], mode='lines',
                                      name='7 days avg - <b>tested-positive</b>'), secondary_y=False)
        figtotal.add_trace(go.Scatter(x=df_to_plot['fecha'], y=df_to_plot['muertes_7avg'], mode='lines',
                                      name='7 days avg - <b>deceases</b>'), secondary_y=True)
    else:
        figtotal.add_trace(go.Scatter(x=df_to_plot['fecha'], y=df_to_plot['num_casos'],mode='lines',
                                      name='<b>tested-positive</b>'), secondary_y=False)
        figtotal.add_trace(go.Scatter(x=df_to_plot['fecha'], y=df_to_plot['muertes'],mode='lines',
                                      name='<b>deceases</b>'), secondary_y=True)

    figtotal.update_layout(
        font = FONT_DICT,
        title={
            'text': "Tested-positive vs deceases by COVID-19 - " + comunidad,
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="right",
            x=0.6
        ),
        width=1000,
        height=750,
    )
    figtotal.update_yaxes(title_text="Number of tested-positive", secondary_y=False)
    figtotal.update_yaxes(title_text="Number of deceases", secondary_y=True)

    return figtotal

def covid_compare_plot(ccaa_comp1, ccaa_comp2, avg_on):

    #df
    with open(TMPDIR + 'df.txt') as df_file:
        df_dictionazied = json.load(df_file)
    df = pd.DataFrame.from_dict(df_dictionazied)
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')

    #df_muertes
    with open(TMPDIR + 'df_muertes.txt') as df_muertes_file:
        df_muertes_dictionazied = json.load(df_muertes_file)
    df_muertes = pd.DataFrame.from_dict(df_muertes_dictionazied)
    df_muertes['fecha'] = pd.to_datetime(df_muertes['fecha'], format='%Y-%m-%d')

    filtro_ccaa_1 = ccaa_comp1
    filtro_ccaa_2 = ccaa_comp2

    if filtro_ccaa_1 == 'ALL' or filtro_ccaa_2 == 'ALL':
        df1 = df.groupby("fecha").sum()
        df1.reset_index(level=0, inplace=True)

        df2 = df_muertes.groupby("fecha").sum()
        df2.reset_index(level=0, inplace=True)

        df_final = pd.merge(df1, df2, how='outer')

        if filtro_ccaa_1 == 'ALL':
            comunidad_1 = 'España'
            df_to_plot_1 = df_final.copy()
        if filtro_ccaa_2 == 'ALL':
            comunidad_2 = 'España'
            df_to_plot_2 = df_final.copy()

    if filtro_ccaa_1 != 'ALL' or filtro_ccaa_2 != 'ALL':
        if filtro_ccaa_1 != 'ALL':
            comunidad_1 = CCAA_DICT[filtro_ccaa_1]
            df_filtered_1 = df[df['ccaa'] == filtro_ccaa_1]
            df_muertes_filtered_1 = df_muertes[df_muertes['prov'].isin(CCAA_PROV_DICT[filtro_ccaa_1])]
            df_filtered_total_1 = df_filtered_1.groupby('fecha').sum()
            df_filtered_total_1.reset_index(level=0, inplace=True)
            df_muertes_filtered_total_1 = df_muertes_filtered_1.groupby('fecha').sum()
            df_muertes_filtered_total_1.reset_index(level=0, inplace=True)
            df_to_plot_1 = pd.merge(df_filtered_total_1, df_muertes_filtered_total_1, how='outer')

        if filtro_ccaa_2 != 'ALL':
            comunidad_2 = CCAA_DICT[filtro_ccaa_2]
            df_filtered_2 = df[df['ccaa'] == filtro_ccaa_2]
            df_muertes_filtered_2 = df_muertes[df_muertes['prov'].isin(CCAA_PROV_DICT[filtro_ccaa_2])]
            df_filtered_total_2 = df_filtered_2.groupby('fecha').sum()
            df_filtered_total_2.reset_index(level=0, inplace=True)
            df_muertes_filtered_total_2 = df_muertes_filtered_2.groupby('fecha').sum()
            df_muertes_filtered_total_2.reset_index(level=0, inplace=True)
            df_to_plot_2 = pd.merge(df_filtered_total_2, df_muertes_filtered_total_2, how='outer')

    if avg_on:
        df_to_plot_1['total_7avg'] = df_to_plot_1.iloc[:, 1].rolling(window=7).mean()
        df_to_plot_1['muertes_7avg'] = df_to_plot_1.iloc[:, 4].rolling(window=7).mean()
        df_to_plot_2['total_7avg'] = df_to_plot_2.iloc[:, 1].rolling(window=7).mean()
        df_to_plot_2['muertes_7avg'] = df_to_plot_2.iloc[:, 4].rolling(window=7).mean()

    figtotal_1 = make_subplots(specs=[[{"secondary_y": True}]])
    figtotal_2 = make_subplots(specs=[[{"secondary_y": True}]])

    if avg_on:
        figtotal_1.add_trace(go.Scatter(x=df_to_plot_1['fecha'], y=df_to_plot_1['total_7avg'], mode='lines',
                                        name='7 days avg - <b>tested-positive</b>'), secondary_y=False)
        figtotal_1.add_trace(go.Scatter(x=df_to_plot_1['fecha'], y=df_to_plot_1['muertes_7avg'], mode='lines',
                                        name='7 days avg - <b>deceases</b>'), secondary_y=True)
        figtotal_2.add_trace(go.Scatter(x=df_to_plot_2['fecha'], y=df_to_plot_2['total_7avg'], mode='lines',
                                        name='7 days avg - <b>tested-positive</b>'), secondary_y=False)
        figtotal_2.add_trace(go.Scatter(x=df_to_plot_2['fecha'], y=df_to_plot_2['muertes_7avg'], mode='lines',
                                        name='7 days avg - <b>deceases</b>'), secondary_y=True)
    else:
        figtotal_1.add_trace(go.Scatter(x=df_to_plot_1['fecha'], y=df_to_plot_1['num_casos'], mode='lines',
                                        name='<b>tested-positive</b>'), secondary_y=False)
        figtotal_1.add_trace(go.Scatter(x=df_to_plot_1['fecha'], y=df_to_plot_1['muertes'], mode='lines',
                                        name='<b>deceases</b>'), secondary_y=True)
        figtotal_2.add_trace(go.Scatter(x=df_to_plot_2['fecha'], y=df_to_plot_2['num_casos'], mode='lines',
                                        name='<b>tested-positive</b>'), secondary_y=False)
        figtotal_2.add_trace(go.Scatter(x=df_to_plot_2['fecha'], y=df_to_plot_2['muertes'], mode='lines',
                                        name='<b>deceases</b>'), secondary_y=True)

    figtotal_1.update_layout(
        font=FONT_DICT_small,
        title={
            'text': "Tested-positive vs deceases by COVID-19 - " + comunidad_1,
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="right",
            x=0.5
        ),
        width=550,
        height=425,
    )
    figtotal_1.update_yaxes(title_text="Number of tested-positive", secondary_y=False)
    figtotal_1.update_yaxes(title_text="Number of deceases", secondary_y=True)

    figtotal_2.update_layout(
        font=FONT_DICT_small,
        title={
            'text': "Tested-positive vs deceases by COVID-19 - " + comunidad_2,
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="right",
            x=0.5
        ),
        width=550,
        height=425,
    )
    figtotal_2.update_yaxes(title_text="Number of tested-positive", secondary_y=False)
    figtotal_2.update_yaxes(title_text="Number of deceases", secondary_y=True)

    return figtotal_1, figtotal_2

def plot_vacc():
    colors_plot = px.colors.qualitative.Plotly

    #df_vacunas
    with open(TMPDIR + 'df_vacunas.txt') as df_vacunas_file:
        df_vacunas_dictionazied = json.load(df_vacunas_file)
    df_vacunas = pd.DataFrame.from_dict(df_vacunas_dictionazied)

    # fig1 data
    pfizer = df_vacunas['entregado_Pfizer'].sum()
    moderna = df_vacunas['entregado_Moderna'].sum()
    astra = df_vacunas['entregado_AstraZeneca'].sum()
    janssen = df_vacunas['entregado_Janssen'].sum()
    labels1 = ['Pfizer', 'Moderna', 'AstraZeneca', 'Janssen']
    values1 = [pfizer, moderna, astra, janssen]

    # fig2 data
    total = df_vacunas['entregado_total'].sum()
    administrado = df_vacunas['administrado'].sum()
    no_administrado = total - administrado
    labels2 = ['Administered', 'Not administ.']
    # labels2 = ['Administered', 'Not adm']
    values2 = [administrado, no_administrado]

    # fig3 data
    poblacion_total = df_vacunas['poblacion'].sum()
    vacunados = df_vacunas['personas_vacunadas_dos_dosis'].sum()
    no_vacunados = poblacion_total - vacunados
    labels3 = ['Not vaccinated', 'Vaccinated']
    values3 = [no_vacunados, vacunados]

    # fig4 data
    df_vacunas['porc_vacunado'] = round((df_vacunas['personas_vacunadas_dos_dosis'] / df_vacunas['poblacion']) * 100, 1)
    df_vacunas['porc_no_vacunado'] = round(100 - df_vacunas['porc_vacunado'], 1)

    df_vacunas.sort_values(by=['porc_vacunado'], inplace=True)
    vacunados_ccaa = df_vacunas['porc_vacunado'].tolist()
    no_vacunados_ccaa = df_vacunas['porc_no_vacunado'].tolist()
    labels4 = df_vacunas['ccaa'].apply(lambda x: CCAA_DICT[x]).tolist()

    # fig1
    fig1 = go.Figure(
        data=[go.Pie(labels=labels1, values=values1, textinfo='label+percent', insidetextorientation='radial', )])
    fig1.update_layout(
        font=FONT_DICT_small,
        title={
            'text': "Vaccinations by vendor - España",
            'y': 0.9,
            'x': 0.45,
            'xanchor': 'center',
            'yanchor': 'top'},
        # legend=dict(
        #     orientation="v",
        #     yanchor="bottom",
        #     y=-1.02,
        #     xanchor="right",
        #     x=1
        # ),
        showlegend=False,
        width=350,
        height=350,
    )
    fig1.update_traces(marker=dict(colors=colors_plot, line=dict(color='#000000', width=2)))

    # fig2
    fig2 = go.Figure(
        data=[go.Pie(labels=labels2, values=values2, textinfo='label+percent', insidetextorientation='radial', )])
    fig2.update_layout(
        font=FONT_DICT_small,
        title={
            'text': "Admins vacc - España",
            'y': 0.9,
            'x': 0.45,
            'xanchor': 'center',
            'yanchor': 'top'},
        # legend=dict(
        #     orientation="h",
        #     yanchor="bottom",
        #     y=-1.2,
        #     xanchor="center",
        #     x=0.5,
        # ),
        showlegend=False,
        width=350,
        height=350,
    )
    fig2.update_traces(marker=dict(colors=colors_plot, line=dict(color='#000000', width=2)))

    # fig3
    fig3 = go.Figure(
        data=[go.Pie(labels=labels3, values=values3, textinfo='label+percent', insidetextorientation='radial', )])
    fig3.update_layout(
        font=FONT_DICT_small,
        title={
            'text': "Vaccinated population - España",
            'y': 0.9,
            'x': 0.45,
            'xanchor': 'center',
            'yanchor': 'top'},
        # legend=dict(
        #     orientation="h",
        #     yanchor="bottom",
        #     y=-0.2,
        #     xanchor="center",
        #     x=0.5
        # ),
        showlegend=False,
        width=350,
        height=350,
    )
    fig3.update_traces(marker=dict(colors=colors_plot, line=dict(color='#000000', width=2)))

    # fig4
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        y=labels4,
        x=vacunados_ccaa,
        name='Vaccinated pop',
        orientation='h',
        marker=dict(
            color=colors_plot[0],
            # line=dict(color=colors_plot[0], width=3)
            line=dict(color='#000000', width=2)
        )
    ))
    fig4.add_trace(go.Bar(
        y=labels4,
        x=no_vacunados_ccaa,
        name='Not vaccinated pop',
        orientation='h',
        marker=dict(
            color=colors_plot[1],
            # line=dict(color=colors_plot[1], width=3)
            line=dict(color='#000000', width=2)
        )
    ))

    fig4.update_layout(
        barmode='stack',
        font=FONT_DICT,
        title={
            'text': "Vaccinated population per 'Comunidad Autónoma'",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        width=1100,
        height=850,
    )

    return fig1, fig2, fig3, fig4

def plot_hosp():
    colors_plot = px.colors.qualitative.Plotly

    #df_hosp
    with open(TMPDIR + 'df_hosp.txt') as df_hosp_file:
        df_hosp_dictionazied = json.load(df_hosp_file)
    df_hosp = pd.DataFrame.from_dict(df_hosp_dictionazied)
    df_hosp['fecha'] = pd.to_datetime(df_hosp['fecha'], format='%Y-%m-%d')

    df_sin_nc = df_hosp[df_hosp.ne('NC').all(axis=1)]
    df_sin_nc_h = df_sin_nc[df_sin_nc['sexo'] == 'H']
    df_sin_nc_m = df_sin_nc[df_sin_nc['sexo'] == 'M']
    df_sin_nc_h_edad = df_sin_nc_h.groupby('grupo_edad').sum()
    df_sin_nc_m_edad = df_sin_nc_m.groupby('grupo_edad').sum()

    df_sin_nc_h_edad.reset_index(level=0, inplace=True)
    df_sin_nc_m_edad.reset_index(level=0, inplace=True)

    grupo_edad = df_sin_nc_m_edad['grupo_edad'].tolist()

    defun_h = df_sin_nc_h_edad['num_def'].tolist()
    defun_m = df_sin_nc_m_edad['num_def'].tolist()

    hosp_h = df_sin_nc_h_edad['num_hosp'].tolist()
    hosp_m = df_sin_nc_m_edad['num_hosp'].tolist()

    uci_h = df_sin_nc_h_edad['num_uci'].tolist()
    uci_m = df_sin_nc_m_edad['num_uci'].tolist()

    fig_hosp = go.Figure()
    fig_hosp.add_trace(go.Bar(x=grupo_edad,
                              y=hosp_h,
                              name='Male',
                              marker_color=colors_plot[0]
                              ))
    fig_hosp.add_trace(go.Bar(x=grupo_edad,
                              y=hosp_m,
                              name='Female',
                              marker_color=colors_plot[1]
                              ))

    fig_hosp.update_layout(
        font=FONT_DICT,
        title={
            'text': "Hospitalized by gender and age group",
            'y': 0.9,
            'x': 0.45,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='Hospitalized patients',
            titlefont_size=16,
            tickfont_size=14,
        ),
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1, # gap between bars of the same location coordinate.
        width=1000,
        height=500,
    )

    fig_uci = go.Figure()
    fig_uci.add_trace(go.Bar(x=grupo_edad,
                             y=uci_h,
                             name='Male',
                             marker_color=colors_plot[0]
                             ))
    fig_uci.add_trace(go.Bar(x=grupo_edad,
                             y=uci_m,
                             name='Female',
                             marker_color=colors_plot[1]
                             ))

    fig_uci.update_layout(
        font=FONT_DICT,
        title={
            'text': "UCI occupancy by gender and age group",
            'y': 0.9,
            'x': 0.45,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='UCI occupancy',
            titlefont_size=16,
            tickfont_size=14,
        ),
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1,  # gap between bars of the same location coordinate.
        width = 1000,
        height = 500,
    )

    fig_def = go.Figure()
    fig_def.add_trace(go.Bar(x=grupo_edad,
                             y=defun_h,
                             name='Male',
                             marker_color=colors_plot[0]
                             ))
    fig_def.add_trace(go.Bar(x=grupo_edad,
                             y=defun_m,
                             name='Female',
                             marker_color=colors_plot[1]
                             ))

    fig_def.update_layout(
        font=FONT_DICT,
        title={
            'text': "Deceases by gender and age group",
            'y': 0.9,
            'x': 0.45,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='Number of deceases',
            titlefont_size=16,
            tickfont_size=14,
        ),
        legend=dict(
            x=0,
            y=1.0,
            bgcolor='rgba(255, 255, 255, 0)',
            bordercolor='rgba(255, 255, 255, 0)'
        ),
        barmode='group',
        bargap=0.15,  # gap between bars of adjacent location coordinates.
        bargroupgap=0.1,  # gap between bars of the same location coordinate.
        width=1000,
        height=500,
    )

    return fig_hosp, fig_uci, fig_def

def plot_deceases(avg7days):

    #df_hosp
    with open(TMPDIR + 'df_hosp.txt') as df_hosp_file:
        df_hosp_dictionazied = json.load(df_hosp_file)
    df_hosp = pd.DataFrame.from_dict(df_hosp_dictionazied)
    df_hosp['fecha'] = pd.to_datetime(df_hosp['fecha'], format='%Y-%m-%d')

    colors_plot = px.colors.qualitative.Plotly
    font_dict = dict(family="Courier New, monospace", size=12, color="darkslategrey")

    df_sin_nc = df_hosp[df_hosp.ne('NC').all(axis=1)]

    df_sin_nc_time = df_sin_nc[['fecha', 'grupo_edad', 'num_def']].groupby(['fecha', 'grupo_edad']).sum()
    df_sin_nc_time.reset_index(inplace=True)
    df_pivoted = df_sin_nc_time.pivot(index="fecha", columns="grupo_edad", values="num_def")
    df_pivoted.reset_index(inplace=True)

    if avg7days:
        df_to_plot = pd.DataFrame(df_pivoted['fecha'])
        for i, col in enumerate(df_pivoted.columns):
            if col != 'fecha':
                new_col = col + '_7avg'
                df_to_plot[new_col] = df_pivoted.iloc[:, i].rolling(window=7).mean()
    else:
        df_to_plot = df_pivoted.copy()

    def_plot = go.Figure()
    i = 0
    for col in df_to_plot.columns:
        if col != 'fecha':
            if avg7days:
                col_name = col.split('_7avg')[0]
            else:
                col_name = col
            def_plot.add_trace(
                go.Scatter(
                    x=df_to_plot['fecha'],
                    y=df_to_plot[col],
                    mode='lines',
                    name=col_name,
                    line=dict(color=colors_plot[i])

                )
            )
            i += 1

    if avg7days:
        title_text = 'Deceases by age group - 7 days avg'
        x_text = 'Number of deceases - 7 days avg'
    else:
        title_text = 'Deceases by age group'
        x_text = 'Number of deceases'

    def_plot.update_layout(
        font=font_dict,
        title={
            'text': title_text,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.1
        ),
        legend_title_text='Age Group',
        width=1000,
        height=750,
    )
    def_plot.update_yaxes(title_text=x_text)

    return def_plot

# ================================== #
# ================================== #
#            CALLBACKS               #
# ================================== #
# ================================== #

# ==== CALLBACKS FOR MODAL WINDOW ====
@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"),
     Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):

    if n1 or n2:
        return not is_open
    return is_open

# ==== CALLBACKS FOR TRIGGERING INITIAL DATA LOADING ====
# Save a flag in 'init' hidden Div
@app.callback([Output('init', 'children'),
               Output('data-loaded', 'children'),],
              [Input('data-downloaded', 'children')],
              [State('data-loaded', 'children')])
def initial_load(downloaded_tag, loaded_tag):
    if downloaded_tag is not None and len(loaded_tag) == 0:
        return ['initialized','Data Loaded']
    else:
        raise dash.exceptions.PreventUpdate

@app.callback(Output('data-downloaded_text', 'children'),
             [Input('init', 'children')])
def set_download_label(init_tag):
    if init_tag == 'initialized':
        with open(DATADIR + 'last_downloaded_data.txt', 'r') as f:
            data = f.read()
        return data.rstrip('\n')
    else:
        raise dash.exceptions.PreventUpdate

# ==== CALLBACKS FOR CCAA DROPDOWN MENU ====
# Activate the ccaa dropdown menu

# Update ccaa dropdown menu with possible values
# and set initial one to ALL
@app.callback(Output('ccaa_data', 'options'),
              Input('init', 'children'),
              prevent_initial_call=True)
def update_selectCcaa_options(init_tag):

    if init_tag == 'initialized':
        with open(TMPDIR + 'ccaa_options.txt') as ccaa_options_file:
            dictionary_options = json.load(ccaa_options_file)
        return dictionary_options
    else:
        return []


@app.callback(Output('ccaa_data', 'disabled'),
              Input('ccaa_data', 'options'),
              prevent_initial_call=True)
def activate_selectCcaa_dropdown(options):

    if options is not None and options is not []:
        return False
    else:
        return True


@app.callback(Output('ccaa_data', 'value'),
              Input('ccaa_data', 'options'),
              prevent_initial_call=True)
def update_selectCcaa_options(options):

    if options is not None:
        if len(options) != 0:
            return options[[k['value'] for k in options].index('ALL')]['value']

    raise dash.exceptions.PreventUpdate

# ==== CALLBACKS FOR CCAA COMPARISON MENU ====
# Update ccaa dropdown menu with possible values
@app.callback([Output('ccaa_compare_data_1', 'options'),
               Output('ccaa_compare_data_2', 'options')],
               Input('init', 'children'),
               prevent_initial_call=True)
def update_selectCcaa_options(init_tag):

    if init_tag == 'initialized':
        with open(TMPDIR + 'ccaa_options.txt') as ccaa_options_file:
            dictionary_options = json.load(ccaa_options_file)
        return dictionary_options, dictionary_options
    else:
        return [], []

# Activate the ccaa first and second menu
@app.callback([Output('ccaa_compare_data_1', 'disabled'),
               Output('ccaa_compare_data_2', 'disabled')],
               Input('ccaa_data', 'options'),
               prevent_initial_call=True)
def activate_selectCcaa_dropdown(options):

    if options is not None and options is not []:
        return False, False
    else:
        return True, True

# ==== CALLBACKS FOR 7 DAYS AVERAGE SWITCH ====
# Update disabled status
@app.callback([Output('rollingavg-on', 'disabled'),
               Output('rollingavg-on', 'on')],
               Input('ccaa_data', 'value'),
               prevent_initial_call=True)
def update_offset_disabled(ccaa):
    if ccaa is not None:
        return False, dash.no_update
    else:
        return True, False

# ==== CALLBACKS FOR COVID PLOT ====
@app.callback(Output('covid-plot', 'figure'),
              [Input('ccaa_data', 'value'),
               Input('rollingavg-on', 'on')],
              [State('rollingavg-on', 'on'),
               State('ccaa_data', 'value')],
               prevent_initial_call=True)
def update_main_plot(ccaa, avg_on, avg_old_on, ccaa_old):
    if ccaa is not None:
        ctx = dash.callback_context
        if ctx.triggered[0]['prop_id'] == 'ccaa_data.value':
            filtro_ccaa = ccaa
            avg7days = avg_old_on
        else:
            filtro_ccaa = ccaa_old
            avg7days = avg_on

        figure = covid_plot(filtro_ccaa, avg7days)

        return figure
    else:
        return {}

@app.callback(Output('covid-plot', 'style'),
              Input('covid-plot', 'figure'),
              prevent_initial_call=True)
def show_main_plot(figure):
    if figure is not None:
        if len(figure) != 0:
            return dict()

    return dict(visibility = 'hidden')

# ==== CALLBACKS FOR COVID COMPARISON PLOT ====
@app.callback([Output('covid-compare-plot_1', 'figure'),
               Output('covid-compare-plot_2', 'figure')],
              [Input('ccaa_compare_data_1', 'value'),
               Input('ccaa_compare_data_2', 'value'),
               Input('rollingavg-on', 'on')],
               prevent_initial_call=True)
def update_compare_plots(ccaa_comp1, ccaa_comp2, avg_on):
    if ccaa_comp1 is not None and ccaa_comp2 is not None:
        figure1, figure2 = covid_compare_plot(ccaa_comp1, ccaa_comp2, avg_on)
        return figure1, figure2
    else:
        return {}, {}

@app.callback([Output('covid-compare-plot_1', 'style'),
               Output('covid-compare-plot_2', 'style')],
              [Input('covid-compare-plot_1', 'figure'),
               Input('covid-compare-plot_2', 'figure')],
               prevent_initial_call=True)
def show_visualizations_compare(figure1, figure2):
    if figure1 is not None and figure2 is not None:
        if len(figure1) != 0 and len(figure2) != 0:
            return dict(), dict()

    return dict(visibility = 'hidden'), dict(visibility = 'hidden')

# ==== CALLBACKS FOR VACCINATION PLOTS ====
@app.callback([Output('vacc-plot_1', 'figure'),
               Output('vacc-plot_2', 'figure'),
               Output('vacc-plot_3', 'figure'),
               Output('vacc-plot_4', 'figure')],
              [Input('init', 'children')],
               prevent_initial_call=True)
def update_plot_vacunas(init_tag):
    if init_tag == 'initialized':
        fig1, fig2, fig3, fig4 = plot_vacc()
        return fig3, fig2, fig1, fig4
    else:
        return {}, {}, {}, {}

@app.callback([Output('vacc-plot_1', 'style'),
               Output('vacc-plot_2', 'style'),
               Output('vacc-plot_3', 'style'),
               Output('vacc-plot_4', 'style')],
              [Input('vacc-plot_1', 'figure'),
               Input('vacc-plot_2', 'figure'),
               Input('vacc-plot_3', 'figure'),
               Input('vacc-plot_4', 'figure')],
               prevent_initial_call=True)
def show_visualizations_vacunas(figure1, figure2, figure3, figure4):
    if figure1 is not None and figure2 is not None and figure3 is not None and figure4 is not None:
        if len(figure1) != 0 and len(figure2) != 0 and len(figure3) != 0 and len(figure4) != 0:
            return dict(), dict(), dict(), dict()

    return dict(visibility = 'hidden'), dict(visibility = 'hidden'), dict(visibility = 'hidden'), dict(visibility = 'hidden')

# Callback for hospitalization graphs
@app.callback([Output('hosp-plot_1', 'figure'),
               Output('hosp-plot_2', 'figure'),
               Output('hosp-plot_3', 'figure')],
              [Input('init', 'children')],
               prevent_initial_call=True)
def update_plot_hosp(init_tag):
    if init_tag == 'initialized':
        fig1, fig2, fig3 = plot_hosp()
        return fig1, fig2, fig3
    else:
        return {}, {}, {}


@app.callback([Output('hosp-plot_1', 'style'),
               Output('hosp-plot_2', 'style'),
               Output('hosp-plot_3', 'style')],
              [Input('hosp-plot_1', 'figure'),
               Input('hosp-plot_2', 'figure'),
               Input('hosp-plot_3', 'figure')],
               prevent_initial_call=True)
def show_visualizations_hosp(figure1, figure2, figure3):
    if figure1 is not None and figure2 is not None and figure3 is not None:
        if len(figure1) != 0 and len(figure2) != 0 and len(figure3) != 0:
            return dict(), dict(), dict()

    return dict(visibility = 'hidden'), dict(visibility = 'hidden'), dict(visibility = 'hidden')

# Callback for deceases graphs
@app.callback(Output('deceases-plot', 'figure'),
              [Input('init', 'children'),
               Input('rollingavg-on', 'on')],
               prevent_initial_call=True)
def update_plot_deceases(init_tag, avg7days):
    if init_tag == 'initialized':
        figure = plot_deceases(avg7days)
        return figure
    else:
        return {}

@app.callback(Output('deceases-plot', 'style'),
              [Input('deceases-plot', 'figure')])
def show_visualizations_hosp(figure):
    if figure is not None:
        if len(figure) != 0:
            return dict()

    return dict(visibility = 'hidden')


if __name__ == "__main__":
    app.run_server(debug=False, host="127.0.0.1")