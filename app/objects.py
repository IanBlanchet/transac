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
import base64



#utiliser données de onedrive
def create_onedrive_directdownload (onedrive_link):
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
    return resultUrl
direct_download_url = create_onedrive_directdownload('https://1drv.ms/x/s!Agh6McKMUEEEgo1FsMjWEc-1zG0N7A?e=cW0nn4')
historique = pd.read_excel(direct_download_url, engine='openpyxl')
historique = historique[['Date', 'ticker', 'prix(close)', 'IV(close)']]
historique.drop_duplicates(inplace=True, ignore_index=True)

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

        html.Div(children='Un dashboard qui permet analyser les statistiques'),

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

def home(df, df_account):
    today = datetime.today()
    figure = px.line(df, x=df.index, y="SMA_6", title='6 months moving average')
    mes_position_mois = df[(df['annee'] == today.year) & (df['mois'] == today.month)]
    account_mois = df_account[(df_account['annee'] == today.year) & (df_account['mois'] == today.month)]
    mes_position_annee = df[(df['annee'] == today.year)]
    account_annee = df_account[(df_account['annee'] == today.year)]
    total_mois = mes_position_mois['gain_can'].sum()
    total_annee = mes_position_annee['gain_can'].sum()
    total_mois_marge_ian = account_mois[account_mois.account == 'U2517832'].gain_can.sum()
    total_mois_celi_ian = account_mois[account_mois.account == 'U2874626'].gain_can.sum()
    total_mois_marge_bibi = account_mois[account_mois.account == 'U6214437'].gain_can.sum()
    total_mois_celi_bibi = account_mois[account_mois.account == 'U4767346'].gain_can.sum()
    total_annee_marge = account_annee[(account_annee.account == 'U2517832') | (account_annee.account == 'U6214437')].gain_can.sum()
    total_annee_celi = account_annee[(account_annee.account == 'U2874626')| (account_annee.account == 'U4767346')].gain_can.sum()

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
            html.Ul(children="Total du mois marge Ian: "+ str(total_mois_marge_ian.round(0))),
            html.Ul(children="Total du mois CELI Ian: "+ str(total_mois_celi_ian.round(0))),
            html.Ul(children="Total du mois marge Bibi: "+ str(total_mois_marge_bibi.round(0))),
            html.Ul(children="Total du mois CELI: Bibi"+ str(total_mois_celi_bibi.round(0))),
            html.Li(children="Total année courante : "+ str(total_annee.round(0))),
            html.Ul(children="Total année marge: "+ str(total_annee_marge.round(0))),
            html.Ul(children="Total année CELI: "+ str(total_annee_celi.round(0))),
        ])
            ))
        ]
    )

    return home

def open_ticker(df):
    df = df[['ticker', 'strike','risque', 'gain', 'echeance','date_ouv', 'style', 'currency', 'gain_can']]
    df['gain'] = df['gain'].round(2)
    df['date_ouv'] = df['date_ouv'].apply(lambda x : x.date())
    df['echeance'] = df['echeance'].apply(lambda x : x.date())
    df['taux_change'] = df.gain_can/df.gain
    df['risque_tot'] = df.strike * df.taux_change
    risque_total = (df.risque_tot.sum() *100).round(0)
    df = df[['ticker', 'strike','risque', 'gain', 'echeance','date_ouv', 'style']]
    open_ticker = html.Div(
        [
        navbar,
        dbc.Row(dbc.Col(html.H1(children='Positions ouvertes'))),
        dbc.Row(dbc.Col(html.Div(children='Risque Total CAD = ' + str(risque_total)))),
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

def PlotContrat(fig, contrat_df, ticker):
    #trace l'historique du titre (volatilité et prix)
    histo = historique[historique.ticker == ticker]
    contrat_df.reset_index(inplace=True)
    fig.data = []
    fig.add_trace(go.Scatter(x=histo.Date,
                            y=histo['prix(close)'],
                            mode='lines',
                            name='Prix',
                            marker_color='blue'
                            ), secondary_y=False)
    fig.add_trace(go.Scatter(x=histo.Date,
                            y=histo['IV(close)'],
                            mode='lines',
                            name='IV',
                            marker_color='purple'
                            ), secondary_y=True)


    for j in range(len(contrat_df)):
            
            fig.add_trace(go.Scatter(
                                name=str(contrat_df.loc[j,'id']),
                                x=[contrat_df.loc[j, 'date_ouv']],
                                y=[(contrat_df.loc[j,'strike'])],
                                text=str(contrat_df.loc[j,'strike']),
                                ))
            if contrat_df.loc[j,'statut'] == 'Close':
                fig.add_trace(go.Scatter(
                                name=str(contrat_df.loc[j,'id'])+'close',
                                x=[contrat_df.loc[j, 'date_ferm']],
                                y=[(contrat_df.loc[j,'strike'])],
                                text='Gain :'+str(int(contrat_df.loc[j,'gain'])),
                                marker_color='green'
                                ))
            fig.add_trace(go.Scatter(
                                x=[contrat_df.loc[j, 'date_ouv'],contrat_df.loc[j, 'echeance']],
                                y=[contrat_df.loc[j,'strike'],contrat_df.loc[j,'strike']],
                                mode='lines',
                                marker_color='yellow',
                                opacity=0.5
                                ))
    return fig


def analyse_titre(df):
    
    df['date_ouv'] = df['date_ouv'].apply(lambda x : x.date())
    df['echeance'] = df['echeance'].apply(lambda x : x.date())
    df['date_ferm'] = df['date_ferm'].apply(lambda x : x.date())
    df = df.drop(['mois', 'annee', 'currency'], axis=1)
    totaux = df.gain_can.sum().round(2)
    compte_sur_marge = df[df.account == 'U2517832'].gain_can.sum().round(2)
    celi = df[df.account == 'U2874626'].gain_can.sum().round(2)
    
    analyse_titre = html.Div(
        [
        navbar,
        dbc.Row(dbc.Col(html.Div(children='Gain totaux = ' + str(totaux)))),
        dbc.Row(dbc.Col(html.Div(children='compte sur marge = ' + str(compte_sur_marge)))),
        dbc.Row(dbc.Col(html.Div(children='CELI = ' + str(celi)))),
        dcc.Dropdown(
            id='ticker',
            options=[{'label':value, 'value':value} for value in pd.unique(df.ticker)],
            placeholder='select un ticker'       
        ),
        dbc.Row(dbc.Col(html.H2(id='total_titre' , children='Total avec ce titre :'+ str(df.gain_can.sum().round(2))))),
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
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='graphTicker'))

        ]

                ),

        ]
    )
    return analyse_titre