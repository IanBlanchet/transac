import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta

#la bar de navigation
navbar = dbc.Navbar(
    [
        html.A(
            dbc.Row(
                [
                    dbc.Col(dbc.NavbarBrand(" Analyse trading")),                    
                ],
                align="center",
                no_gutters=True,
            ),
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.NavItem(dbc.NavLink("Accueil", href="/")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Options", header=True),
                dbc.DropdownMenuItem("Stats Globales", href="/global"),
                dbc.DropdownMenuItem("Analyse par titre", href="/titre"),
                dbc.DropdownMenuItem("Positions ouvertes", href="/open"),
            ],
            nav=True,
            in_navbar=True,
            label="Options",
            right=True,
            
        ),
        
    ],
    color="primary",
    dark=True,
)







def home(df):
    figure = px.histogram(df, x="ratio_duree")
    df = df[df['ratio_duree'] < 2]
    stat_descrip = df.describe()
    stat_descrip.reset_index(inplace=True)
    stat_descrip[['gain', 'gain_can', 'id', 'prix_ouv', 'prix_ferm', 'risque', 'strike', 'duree']] = stat_descrip[['gain',
    'gain_can', 'id', 'prix_ouv', 'prix_ferm', 'risque', 'strike', 'duree']].round(0)
    stat_descrip[['iv_ouv', 'iv_ferm']] = stat_descrip[['iv_ouv', 'iv_ferm']].round(2)
    
    home = html.Div([navbar,
        html.H1(children='Analyse de transactions sur options'),

        html.Div(children='''
            Un dashboard qui permet d'analyser les statistiques
        '''),

        dcc.Dropdown(
            id='ticker',
            options=['test'],#[{'label':value, 'value':value} for value in pd.unique(transactions.underlyingSymbol)],
            placeholder='select un ticker'       
        ),

        dcc.Graph(
            id='graphique',
            figure=figure,
            ),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in stat_descrip.columns],
            data=stat_descrip.to_dict('records'),
            style_table={'height': '300px', 'overflowY': 'auto'}
            ),  
    ])

    return home

def stats_global(df):
    today = datetime.today()
    figure = px.line(df, x=df.index, y="SMA_6", title='6 months moving average')
    mes_position_mois = df[(df['annee'] == today.year) & (df['mois'] == today.month)]
    mes_position_annee = df[(df['annee'] == today.year)]
    total_mois = mes_position_mois['gain_can'].sum()
    total_annee = mes_position_annee['gain_can'].sum()

    stats_global = html.Div(
        [
        navbar,
        dbc.Row(dbc.Col(html.H1(children='Tendance'))),
        dbc.Row(
            [
                dbc.Col(html.Div(children=dcc.Graph
                (id='graphique',figure=figure))),
                dbc.Col(html.Div(children=dash_table.DataTable
                (id='table',columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                style_table={'height': '400px', 'overflowY': 'auto'})))
            ]
                ),
        dbc.Row(dbc.Col(html.Ul(children=[
            html.Li(children="Total du mois courant : "+ str(total_mois.round(0))),
            html.Li(children="Total année courante : "+ str(total_annee.round(0)))
        ])
            ))
        ]
    )

    return stats_global

def open_ticker(df):
    open_ticker = html.Div(
        [
        navbar,
        dbc.Row(dbc.Col(html.H1(children='Positions ouvertes'))),
        dbc.Row(
            [
                dbc.Col(html.Div(children=dash_table.DataTable
                (id='table',columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                style_table={'height': '1000px', 'overflowY': 'auto'})))
            ]
                ),

        ]
    )
    return open_ticker

