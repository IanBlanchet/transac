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
import pandas_profiling
from datetime import datetime, timedelta
from app.objects import home, stats_global, open_ticker

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
tendance = mes_position_ferme
tendance['mois'] = tendance['date_ferm'].apply(lambda x: x.month)
tendance['annee'] =  tendance['date_ferm'].apply(lambda x : x.year)
tendance = tendance.groupby(['annee', 'mois']).sum()
tendance['SMA_6'] = tendance.loc[:,'gain_can'].rolling(window=6).mean()
tendance.reset_index(inplace=True)
tendance = tendance[['annee', 'mois','risque','gain_can', 'SMA_6']]


#l'application DASH
external_stylesheets = external_stylesheets = [dbc.themes.SPACELAB] #['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)

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


home = home(mes_position_ferme)

stats_global = stats_global(tendance)

open_ticker = open_ticker(mes_position_ouvert)


#le callback qui route les URL
@app.callback(Output('home-page', component_property='children'),Input(component_id='url', component_property='pathname'))
def montre_home_page(pathname):
    if pathname == '/global':
        return stats_global
    elif pathname == '/titre':
        return stats_ticker
    elif pathname == '/open':
        return open_ticker
    else:
        return home



app.run_server(debug=True, port=5000)
