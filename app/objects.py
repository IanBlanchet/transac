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
import pandas as pd

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
                dbc.DropdownMenuItem("Menu", header=True),
                dbc.DropdownMenuItem("Analyse durée", href="/analyse_duree"),
                dbc.DropdownMenuItem("Analyse par titre", href="/titre"),
                dbc.DropdownMenuItem("Positions ouvertes", href="/open"),
            ],
            nav=True,
            in_navbar=True,
            label="Menu",
            right=True,
            
        ),
        
    ],
    color="primary",
    dark=True,
)







def analyse_duree(df):
    figure = px.histogram(df, x="ratio_duree")
    df = df[df['ratio_duree'] < 2]
    stat_descrip = df.describe()
    stat_descrip.reset_index(inplace=True)
    stat_descrip[['gain', 'gain_can', 'id', 'prix_ouv', 'prix_ferm', 'risque', 'strike', 'duree']] = stat_descrip[['gain',
    'gain_can', 'id', 'prix_ouv', 'prix_ferm', 'risque', 'strike', 'duree']].round(0)
    stat_descrip[['iv_ouv', 'iv_ferm']] = stat_descrip[['iv_ouv', 'iv_ferm']].round(2)
    
    analyse_duree = html.Div([navbar,
        html.H1(children='Analyse de transactions sur options'),

        html.Div(children='''
            Un dashboard qui permet d'analyser les statistiques
        '''),

        dcc.Graph(
            id='graphique',
            figure=figure,
            ),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in stat_descrip.columns],
            data=stat_descrip.to_dict('records'),
            fixed_rows={'headers': True},
            style_table={'height': '300px', 'overflowY': 'auto'}
            ),  
    ])

    return analyse_duree

def home(df):
    today = datetime.today()
    figure = px.line(df, x=df.index, y="SMA_6", title='6 months moving average')
    mes_position_mois = df[(df['annee'] == today.year) & (df['mois'] == today.month)]
    mes_position_annee = df[(df['annee'] == today.year)]
    total_mois = mes_position_mois['gain_can'].sum()
    total_annee = mes_position_annee['gain_can'].sum()

    home = html.Div(
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
                style_table={'height': '600px', 'overflowY': 'auto'})))
            ]
                ),
        dbc.Row(dbc.Col(html.Ul(children=[
            html.Li(children="Total du mois courant : "+ str(total_mois.round(0))),
            html.Li(children="Total année courante : "+ str(total_annee.round(0)))
        ])
            ))
        ]
    )

    return home

def open_ticker(df):
    df = df[['ticker', 'strike','risque', 'gain', 'echeance','date_ouv', 'style', 'currency']]
    df['gain'] = df['gain'].round(2)
    df['date_ouv'] = df['date_ouv'].apply(lambda x : x.date())
    df['echeance'] = df['echeance'].apply(lambda x : x.date())
    open_ticker = html.Div(
        [
        navbar,
        dbc.Row(dbc.Col(html.H1(children='Positions ouvertes'))),
        dbc.Row(
            [
                dbc.Col(html.Div(children=dash_table.DataTable
                (id='table',columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                column_selectable="single",
                row_selectable="multi",
                selected_columns=[],
                page_action="native",
                style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                            },
                style_table={'height': '1000px', 'overflowY': 'auto'})))
            ]
                ),

        ]
    )
    return open_ticker

def analyse_titre(df):
    
    df['date_ouv'] = df['date_ouv'].apply(lambda x : x.date())
    df['echeance'] = df['echeance'].apply(lambda x : x.date())
    df['date_ferm'] = df['date_ferm'].apply(lambda x : x.date())
    df = df.drop(['mois', 'annee'], axis=1)
    
    analyse_titre = html.Div(
        [
        navbar,
        dcc.Dropdown(
            id='ticker',
            options=[{'label':value, 'value':value} for value in pd.unique(df.ticker)],
            placeholder='select un ticker'       
        ),

        dbc.Row(dbc.Col(html.H1(children='Positions'))),
        dbc.Row(
            [
                dbc.Col(html.Div(id='table_total', children=dash_table.DataTable
                (columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                sort_action="native",
                sort_mode="multi",
                column_selectable="single",
                row_selectable="multi",
                selected_columns=[],
                page_action="native",
                fixed_rows={'headers': True},
                style_table={'height': '800px', 'overflowY': 'auto'})))
            ]
                ),

        ]
    )
    return analyse_titre