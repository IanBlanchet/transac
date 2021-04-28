from app.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2
import sqlalchemy
import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from app.models import Titres, Positions, Contrats, Base
import numpy as np
from datetime import datetime, timedelta
from app.objects import home, analyse_duree, open_ticker, analyse_titre

#connection avec base de données
engine = create_engine(Config.DATABASE_URI)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session= Session()
mes_position = pd.read_sql('positions', engine)
objet_position = session.query(Positions).filter_by(statut='close').all()
session.close()

mes_position_ouvert = mes_position[mes_position.statut == 'Open']
mes_position_ferme = mes_position[mes_position.statut == 'Close']
mes_position_ferme_raw = mes_position_ferme
mes_position_ferme_raw[['gain', 'gain_can']] = mes_position_ferme_raw[['gain', 'gain_can']].round(2)
tendance = mes_position_ferme
tendance['mois'] = tendance['date_ferm'].apply(lambda x: x.month)
tendance['annee'] =  tendance['date_ferm'].apply(lambda x : x.year)
tendance = tendance.groupby(['annee', 'mois']).sum()
tendance['SMA_6'] = tendance.loc[:,'gain_can'].rolling(window=6).mean()
tendance.reset_index(inplace=True)
tendance = tendance[['annee', 'mois','gain_can', 'SMA_6']]


#l'application DASH
external_stylesheets = external_stylesheets = [dbc.themes.SPACELAB] #['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)

server = app.server

mes_position_ferme['duree'] = mes_position_ferme.date_ferm - mes_position_ferme.date_ouv
mes_position_ferme['duree'] = mes_position_ferme['duree'].apply(lambda x : x.days)
mes_position_ferme['duree_or'] = mes_position_ferme.echeance - mes_position_ferme.date_ouv
mes_position_ferme['duree_or'] = mes_position_ferme['duree_or'].apply(lambda x : x.days)
mes_position_ferme['ratio_duree'] = (mes_position_ferme['duree']/mes_position_ferme['duree_or']).round(2)


#le layout vide à meubler avec callback
app.layout = html.Div([\
    dcc.Location(id='url', refresh=False),\
        html.Div(id='home-page'),
        ])


analyse_duree = analyse_duree(mes_position_ferme)

home = home(tendance)

open_ticker = open_ticker(mes_position_ouvert)

analyse_titre = analyse_titre(mes_position_ferme_raw)

#le callback qui route les URL
@app.callback(Output('home-page', component_property='children'),Input(component_id='url', component_property='pathname'))
def montre_home_page(pathname):
    if pathname == '/analyse_duree':
        return analyse_duree
    elif pathname == '/titre':
        return analyse_titre
    elif pathname == '/open':
        return open_ticker
    else:
        return home


#le callback pour filter par ticker
@app.callback(Output('table_total', 'children'),
                Input('ticker', 'value'))
def affiche_pos(valeur):
    pos_ticker = mes_position_ferme_raw[mes_position_ferme_raw['ticker'] == valeur]
    
    table_ticker = dash_table.DataTable(columns=[{"name": i, "id": i} for i in pos_ticker.columns],
                    data=pos_ticker.to_dict('records'), style_table={'height': '800px', 'overflowY': 'auto'})
    
    return table_ticker



if __name__ == '__main__':
    app.run_server(debug=True)