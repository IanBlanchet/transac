from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
import pandas as pd
from datetime import *
from dateutil.parser import parse
import math

Base = declarative_base()


class Positions(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), index=True)
    gain = Column(Float)
    gain_can = Column(Float)
    risque = Column(Float)
    date_ouv = Column(Date)
    iv_ouv = Column(Float)
    prix_ouv = Column(Float)
    date_ferm = Column(Date)
    iv_ferm = Column(Float)
    prix_ferm = Column(Float)
    echeance = Column(Date)
    style = Column(String(10))
    strike = Column(Float)
    statut = Column(String(5))
    currency = Column(String(3))
    contrats = relationship('Contrats', backref='position')
    titres = relationship('Titres', backref='position')
    
    def ratios(self):
        rendement = round((self.gain/self.risque)*100)
        rendement_ajust = round(self.gain/(self.strike*100))*100
        if self.date_ferm:
            rendement_annuel = (rendement/abs((self.date_ferm-self.date_ouv).days))*100
        else:
            rendement_annuel = None
        duree = abs((self.date_ferm-self.date_ouv).days)
        return duree, rendement, rendement_ajust, rendement_annuel

    def calcul_gain(self):
        gain_total = 0.0
        gain_total_can = 0.0
        for contrat in self.contrats:
            if contrat.montant:
                gain_total += contrat.montant
                gain_total_can += (contrat.montant * contrat.taux_change)
            if contrat.com:
                gain_total += contrat.com
                gain_total_can += (contrat.com * contrat.taux_change)
        for titre in self.titres:
            if titre.montant:
                gain_total += titre.montant
                gain_total_can += (titre.montant * titre.taux_change)
            if titre.com:
                gain_total += titre.com
                gain_total_can += (titre.com * titre.taux_change)
        self.gain = gain_total
        self.gain_can = gain_total_can
        return gain_total
    
    def close_pos(self):
        self.statut = 'Close'
        date_contrat = []
        for contrat in self.contrats:
            if contrat.date:
                date_contrat.append(contrat.date)
        for titre in self.titres:
            if titre.date:
                date_contrat.append(titre.date)
        
        self.date_ferm = max(date_contrat)
        
        historique_df = pd.read_excel('historique.xlsx')
        historique_df = historique_df[historique_df.ticker == self.ticker]
        try:
            self.prix_ouv = historique_df[historique_df.Date == str(self.date_ouv)].iloc[0]['prix(close)']
            self.prix_ferm = historique_df[historique_df.Date == str(self.date_ferm)].iloc[0]['prix(close)']
            self.iv_ouv = historique_df[historique_df.Date == str(self.date_ouv)].iloc[0]['IV(close)']
            self.iv_ferm = historique_df[historique_df.Date == str(self.date_ferm)].iloc[0]['IV(close)']
        except:
            self.prix_ouv = None
            self.prix_ferm = None
            self.iv_ouv = None
            self.iv_ferm = None
        
        

    def set_strike(self):
        list_strike = []
        for contrat in self.contrats:
            list_strike.append(contrat.strike)
        max_strike = max(list_strike)
        min_strike = min(list_strike)
        self.strike = max_strike
        if self.style == 'Vertical':
            self.risque = (max_strike - min_strike)*100
        else :
            self.risque = max_strike*100*0.4



class Contrats(Base):
    __tablename__ = "contrats"
    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey('positions.id'))
    montant = Column(Float)
    com = Column(Float)
    side = Column(String(4)) #put ou call
    transaction = Column(Integer)#-1 sell 1 buy
    echeance = Column(Date)
    strike = Column(Float)
    date = Column(Date)
    ticker = Column(String(10))
    taux_change = Column(Float)
    currency = Column(String(3))


class Titres(Base):
    __tablename__ = "titres"
    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey('positions.id'))
    montant = Column(Float)
    com = Column(Float)
    transaction = Column(Integer)#-100 sell 100 buy
    date = Column(Date)
    ticker = Column(String(10))
    taux_change = Column(Float)
    currency = Column(String(3))

#routine pour extraire mon historique
'''
#fonction pour extraire les infos du ticker contrat
def read_info(info):
    les_info = {}
    if (len(info) > 8) and (info[-1] == '0'):
        la_date = info[-15:-9]
        date_format = datetime(int('20'+la_date[:2]), int(la_date[2:4]), int(la_date[4:6]))
        side = info[-9]
        strike = float(int(info[-8:-3]) + int(info[-3:-1])/100)

        return date_format, side, strike
    else :
        try:
            la_date = info.split()[1]
            parse_date = parse(la_date)
            date_format = parse_date.date()
            side = info[-1]
            strike = float(info.split()[2])
        except:
            date_format = None
            side = None
            strike = None
            
        return date_format, side, strike



#extraire dans un dtaframe propre tous les contrats de mon fichier excel
total_df = pd.read_excel('Stats.xlsx')
print(total_df.head(), total_df.info())
les_positions = {'id':[],'ticker':[], 'gain':[], 'risque':[], 'date_ouv':[],
                'date_ferm':[], 'echeance':[], 'statut':[], 'iv_ferm':[], 'prix_ferm':[],
                'iv_ouv':[], 'prix_ouv':[], 'style':[], 'strike':[]}
les_contrats = {'ticker':[], 'position_id': [], 'montant':[], 'com': [], 'side':[],
                'transaction':[], 'echeance':[], 'strike':[], 'date':[] }
les_titres = {'ticker':[], 'montant':[], 'position_id':[], 'com':[],
                'transaction': [], 'date':[],}
#importer l'historique des ticker dans dataframe
historique_df = pd.read_excel('historique.xlsx')

print(historique_df.info())

compteur = None
compteur = 1
for i in range(len(total_df)):
    if math.isnan(total_df.loc[i,'compteur']):
        continue
    else:
        histo_ticker = historique_df[historique_df.ticker == total_df.loc[i,'Symbole']]
        les_positions['id'].append(compteur)
        les_positions['ticker'].append(total_df.loc[i,'Symbole'])
        le_ticker = total_df.loc[i,'Symbole']
        les_positions['gain'].append(total_df.loc[i,'Profits net'])
        les_positions['date_ferm'].append(total_df.loc[i,'Date/Heure'])
        les_positions['statut'].append(total_df.loc[i,'statut'])
        les_positions['style'].append(total_df.loc[i,'type'])
        #print(histo_ticker[histo_ticker.Date == total_df.loc[i,'Date/Heure']].loc[0,'IV(close)'])
        try:
            les_positions['iv_ferm'].append(histo_ticker[histo_ticker.Date == total_df.loc[i,'Date/Heure']].iloc[0]['IV(close)'])
            les_positions['prix_ferm'].append(histo_ticker[histo_ticker.Date == total_df.loc[i,'Date/Heure']].iloc[0]['prix(close)'])
        except:
            les_positions['iv_ferm'].append(None)
            les_positions['prix_ferm'].append(None)


        x = True
        while x == True:
            i -= 1
            #ajoute un contrat au dataframe
            if len(total_df.loc[i, 'Symbole']) > 8:
                les_contrats['ticker'].append(le_ticker)
                les_contrats['position_id'].append(compteur)
                les_contrats['montant'].append(total_df.loc[i, 'Produits'])
                les_contrats['com'].append(total_df.loc[i, 'Comm/Tarif'])
                les_contrats['side'].append(read_info(total_df.loc[i, 'Symbole'])[1])
                les_contrats['transaction'].append(total_df.loc[i, 'Quantité'])
                les_contrats['echeance'].append(read_info(total_df.loc[i, 'Symbole'])[0])
                les_contrats['strike'].append(read_info(total_df.loc[i, 'Symbole'])[2])
                les_contrats['date'].append(total_df.loc[i, 'Date/Heure'])
            #ajoute un titre au dataframe
            else:
                les_titres['ticker'].append(le_ticker)
                les_titres['position_id'].append(compteur)
                les_titres['montant'].append(total_df.loc[i,'Produits'])
                les_titres['com'].append(total_df.loc[i,'Comm/Tarif'])
                les_titres['transaction'].append(total_df.loc[i,'Quantité'])
                les_titres['date'].append(total_df.loc[i,'Date/Heure'])
                

            #utilise le dernier contrat pour compléter la position
            if pd.isna(total_df.loc[i-1,'Symbole']):
                les_positions['date_ouv'].append(total_df.loc[i,'Date/Heure'])
                les_positions['risque'].append(total_df.loc[i,'risque'])
                les_positions['echeance'].append(read_info(total_df.loc[i,'Symbole'])[0])
                les_positions['strike'].append(read_info(total_df.loc[i,'Symbole'])[2])# a revoir car ce n'est pas le bon strike le contrat du haut
                try:
                    les_positions['iv_ouv'].append(histo_ticker[histo_ticker.Date == total_df.loc[i,'Date/Heure']].iloc[0]['IV(close)'])
                    les_positions['prix_ouv'].append(histo_ticker[histo_ticker.Date == total_df.loc[i,'Date/Heure']].iloc[0]['prix(close)'])
                except:
                    les_positions['iv_ouv'].append(None)
                    les_positions['prix_ouv'].append(None)

                break
        else:
            x = False
        compteur += 1

positions_df = pd.DataFrame(les_positions)
contrats_df = pd.DataFrame(les_contrats)
titres_df = pd.DataFrame(les_titres)   

contrats_df.to_excel('contrats.xlsx')           

positions_df.to_excel('positions.xlsx')

titres_df.to_excel('titres.xlsx')  '''

