import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_bootstrap_components as dbc
import plotly.express as px


COLORS = px.colors.qualitative.Plotly
# ==== NAV BAR WITH LOGO AND INFO MODAL BUTTON ====

INFO_MODAL = "Main Graph represents positive-tested number of people and decesaed." \
             " You can visualize the numbers per 'Comunidad Autónoma' or the whole country." \
             " You can visualize raw numbers or a seven-days moving rolling average.\n\n" \
             "Compare Graphs represents the same information as main graph but for two different 'Comunidad Autónoma'" \
             " side-by-side.\n\n" \
             "Vaccination Graphs show different information about vaccination figures in Spain and also compares vaccination" \
             " ratio of all the 'Comunidades Autónomas'. It also shows vaccination ratios per age range in Spain and also per" \
             "'Comunidad Autónoma' by clicking in the corresponding comunidad in the main graph.\n\n" \
             "Hospitalization Graphs show different information about patients being hospitalized and in UCI. There is " \
             "an scatter plot showing the hospitalized patients vs the patients in UCI for all the different 'Comunidades Autónomas'" \
             " and Spain per 1000 people. Also, total per age range by gender is shown as well as totals along the time.\n\n" \
             "Data Sources:\n" \
             "Centro Nacional de Epidemiología: https://cnecovid.isciii.es/covid19/\n" \
             "Ministerio de Sanidad, Consumo y Bienestar Social: https://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/vacunaCovid19.htm"

MODAL = html.Div(
    [
        dbc.Button("INFO", id="open"),
        dbc.Modal(
            [
                dbc.ModalHeader("COVID Figures in Spain"),
                dbc.ModalBody(INFO_MODAL),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            id="modal",
            size='lg',
            scrollable=True,
            style={'white-space': 'pre-line'}
        ),
    ]
)

NAVBAR = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(
                        html.A([
                            html.Img(src='./assets/dash-logo-new.png',
                                         className="logo",
                                         style={'height': '90%', 'width': '90%'})],
                                href="https://plot.ly"),
                        width=3),
                    dbc.Col(dbc.NavbarBrand("COVID Figures in Spain", className="ml-5"),width=9),
                ],
                align="center",
                no_gutters=True,
            ),
        ),
        dbc.Row(
            [
                dbc.Col(MODAL)
            ],
            className='ml-auto mr-5'
        )
    ],
    color="dark",
    dark=True,
    className="mb-2"
)

# ==== LEFT COLUMN: CONTROL TABS  ====
DATA_TAB = dbc.Tab(
    [
        html.H4(children="Load Data", className="display-6 mt-1"),
        html.Hr(className="my-2"),
        html.Label(
            children='Data last downloaded: ',
            className='mt-2 ml-2',
            style={
                'flex-grow': 2,
                'display': False
            },
            id='data-downloaded',
        ),
        html.Label(
            children=[],
            className='mt-2 ml-2',
            style={
                'flex-grow': 2,
                'display': False
            },
            id='data-downloaded_text',
        ),
        html.Br(),
        dcc.Loading(
            children = [
                html.Label(
                    children=[],
                    className='mt-2 ml-2',
                    style={
                        'flex-grow': 2,
                        'display': False,
                        'font-weight': 'bold'
                    },
                    id='data-loaded',
                )
            ],
            color=COLORS[0],
            type='dot',
            fullscreen=False
        ),
        html.H4(children="Graphs Controls", className="display-6 mt-3"),
        html.Hr(className="my-2"),
        html.Label("Select 'Comunidad Autónoma'", className="lead mb-2"),
        dcc.Loading(
            children=[
                dcc.Dropdown(
                    id='ccaa_data',
                    placeholder="Select...",
                    disabled=True,
                    style={
                        'width': '100%',
                        'marginBottom': 15,
                    }
                ),
            ],
            color=COLORS[0],
            type='dot',
            fullscreen=False
        ),
        html.Hr(className="my-2 mb-2"),
        html.Label("Select to compare", className="lead mb-2"),
        dcc.Dropdown(
            id='ccaa_compare_data_1',
            placeholder="Select first 'Comunidad Autónoma'...",
            disabled=True,
            style={
                'width': '100%',
                'marginBottom': 15,
            }
        ),
        dcc.Dropdown(
            id='ccaa_compare_data_2',
            placeholder="Select second 'Comunidad Autónoma'...",
            disabled=True,
            style={
                'width': '100%',
                'marginBottom': 15,
            }
        ),
        html.Hr(className="my-2 mb-2"),
        dbc.Row(
            [
                dbc.Col(
                    html.Label("7-days rolling average",
                               className="lead",
                               style={
                                   'marginBottom': 15,
                                   'marginTop': 10,
                                   # 'marginRight': 5
                               }
                               ),
                    md=6
                ),
                dbc.Col(
                    daq.BooleanSwitch(
                        id='rollingavg-on',
                        on=False,
                        color='#0d7cf2',
                        className="lead",
                        disabled=True,
                        style={
                            'display': 'inline-block',
                            'marginTop': 15,
                            'marginLeft': 0
                        },
                    ),
                    md=6
                )
            ]
        ),
    ],
    label="Selection",
    tab_id="tab-1"
)

LEFT_COLUMN = dbc.Card(
        [
            dbc.CardHeader(
                DATA_TAB
            )
        ]
    )

# ==== RIGHT COLUMN: PLOTS  ====

MAIN_GRAPH_TAB = dbc.Tab(
    [
        html.Div(
            [
                dcc.Loading(
                    children = [
                        dcc.Graph(id='covid-plot',
                                  style=dict(visibility='hidden'),
                                  config=dict(responsive=True),
                                  )
                    ],
                    color=COLORS[0],
                    type='dot',
                    fullscreen=False
                )
            ],
            className="p-4"
        )],
    label="Main Graph",
    tab_id="tab-graph"
)

COMPARE_GRAPHS_TAB = dbc.Tab(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(
                            children = [
                                dcc.Graph(id='covid-compare-plot_1',
                                          style=dict(visibility='hidden'),
                                          config=dict(responsive=True),
                                          )
                            ],
                            color=COLORS[0],
                            type='dot',
                            fullscreen=False
                        )
                    ],
                    md=6
                ),
                dbc.Col(
                    [
                        dcc.Loading(
                            children=[
                                dcc.Graph(id='covid-compare-plot_2',
                                          style=dict(visibility='hidden'),
                                          config=dict(responsive=True),
                                          )
                            ],
                            color=COLORS[0],
                            type='dot',
                            fullscreen=False
                        )
                    ],
                    md=6
                    )
            ],
            className="p-4"
        )
    ],
    label="Compare Graphs",
    tab_id="tab-graph-compare"
)

DECEASES_GRAPH_TAB = dbc.Tab(
    [
        html.Div(
            [
                dcc.Loading(
                    children=[
                        dcc.Graph(id='deceases-plot',
                                  style=dict(visibility='hidden'),
                                  config=dict(responsive=True),
                                  ),
                    ],
                    color=COLORS[0],
                    type='dot',
                    fullscreen=False
                )
            ],
            className="p-4"
        )],
    label="Deceases Graph",
    tab_id="tab-graph-deceases"
)

VACCINATION_GRAPH_TAB = dbc.Tab(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id='vacc-plot_1',
                                  style=dict(visibility='hidden'),
                                  config=dict(responsive=True),
                                  )
                    ],
                    md=4
                ),
                dbc.Col(
                    [
                        dcc.Graph(id='vacc-plot_2',
                                style=dict(visibility = 'hidden'),
                                config=dict(responsive=True),
                                )
                    ],
                    md=4
                    ),
                dbc.Col(
                    [
                        dcc.Graph(id='vacc-plot_3',
                                  style=dict(visibility='hidden'),
                                  config=dict(responsive=True),
                                  )
                    ],
                    md=4
                )
            ],
            className="p-4"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id='vacc-plot_4',
                                  style=dict(visibility='hidden'),
                                  config=dict(responsive=True),
                                  )
                    ],
                    width={"size": 5, "offset": 0}
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dcc.Graph(id='vacc-plot_5',
                                          style=dict(visibility='hidden'),
                                          config=dict(responsive=True),
                                          )
                            ]),
                        dbc.Row([html.Br(), html.Br()]),
                        dbc.Row(
                            [
                                dcc.Graph(id='vacc-plot_6',
                                          style=dict(visibility='hidden'),
                                          config=dict(responsive=True),
                                          )
                            ])
                    ],
                    width={"size": 6, "offset": 1}
                )
            ],
            className="p-4"
        )
    ],
    label="Vaccination Graphs",
    tab_id="vacc-graph-tab"
)

HOSPITALIZATION_GRAPH_TAB = dbc.Tab(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id='hosp-plot_1',
                                  style=dict(visibility='hidden'),
                                  config=dict(responsive=True),
                                  )
                    ],
                    width={"size": 5},
                    md=4
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dcc.Graph(id='hosp-plot_2',
                                          style=dict(visibility='hidden'),
                                          config=dict(responsive=True),
                                          )
                            ],
                        ),
                        dbc.Row([html.Br(),html.Br()]),
                        dbc.Row(
                            [
                                dcc.Graph(id='hosp-plot_3',
                                          style=dict(visibility='hidden'),
                                          config=dict(responsive=True),
                                          )
                            ],
                        ),

                    ],
                    width={"size": 6, "offset": 1},
                    md=4,
                ),
            ],
            className="p-4"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id='hosp-plot_4',
                                  style=dict(visibility='hidden'),
                                  config=dict(responsive=True),
                                  )
                    ],
                    width={"size": 12, "offset": 0}
                )
            ],
            className="p-4"
        ),
    ],
    label="Hospitalization Graphs",
    tab_id="hosp-graph-tab2"
)

RIGHT_COLUMN_ROW_2 = dbc.Card(
        [
            dbc.CardHeader(
                dbc.Tabs(
                    [
                        MAIN_GRAPH_TAB,
                        COMPARE_GRAPHS_TAB,
                        DECEASES_GRAPH_TAB,
                        VACCINATION_GRAPH_TAB,
                        HOSPITALIZATION_GRAPH_TAB,
                    ],
                    id='graph-tabs',
                    card=True,
                    active_tab='tab-graph'
                )
            )
        ],
        className="w-100"
    )

# ==== BODY:  ====
# ==== ROW: LEFT COLUMN + RIGHT COLUMN ====

BODY = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        LEFT_COLUMN
                    ],
                    md=3
                ),
                dbc.Col(
                    [
                        dbc.Row(RIGHT_COLUMN_ROW_2),
                    ],
                    md=9,
                    width=True
                ),
            ]
        ),
        html.Div(id='init', style={'display': 'none'}),
        html.Div(id='df', style={'display': 'none'}),
        html.Div(id='df_muertes', style={'display': 'none'}),
        html.Div(id='df_final', style={'display': 'none'}),
        html.Div(id='df_vacunas', style={'display': 'none'}),
        html.Div(id='df_poblacion', style={'display': 'none'}),
        html.Div(id='df_hosp', style={'display': 'none'})
    ],
    className="mt-12 ml-3",
    fluid=True
)

# ==== LAYOUT: NAV BAR + BODY  ====

app_layout = html.Div(children=[NAVBAR, BODY])