from requests.packages import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# from bs4 import BeautifulSoup
import pandas as pd
# from datetime import datetime

from MeteoCiel.MeteoCiel_dayScraping import MeteoCiel_dayScraping
from MeteoCiel.DJU_costic import DJU_costic

#############"aller chercher toutes les données historique########################
def MeteoCiel_histoScraping(code2,date_debut,date_fin,base_chauffage=18, base_refroidissement=23):
    from tqdm import tqdm
    from datetime import datetime

    df_histo=pd.DataFrame([])
    date_reference=datetime(1970,1,1,1,0,0,0)
    Timestamp_debut=round((date_debut-date_reference).total_seconds())
    Timestamp_fin=round((date_fin-date_reference).total_seconds())

    #for annee2 in range(date_debut.year, date_fin.year+1):
    for current_Timestamp in tqdm(range(Timestamp_debut, Timestamp_fin,3600*24),desc='Evolution du temps de scraping'):
        current_date=datetime.fromtimestamp(current_Timestamp)
        try:
            df=MeteoCiel_dayScraping(code2,current_date.year,current_date.month,current_date.day)
            #print("df=====MeteoCiel_dayScraping================",df)
            
            df_histo=df_histo.append(df)       
        except:
            print("erreur dans le scraping de la journée :"+str(current_date))
            df=MeteoCiel_dayScraping(code2,current_date.year,current_date.month,current_date.day)
            df_histo=df_histo._append(df) 
                
        #print("df_histo=====",df_histo)
    #df_histo.to_excel("fichier_meteociel_scap.xlsx", index=False) 
    print("fin du scrapping...........")


    date='Timestamp'
    # Convert the column to numeric with errors='coerce'
    #print(df_histo)
    try:
        df_histo['Température'] = pd.to_numeric(df_histo['Température'], errors='coerce')
    except:
        print("les données de température n'ont pas été numérisées")
    print(df_histo.columns)

    try:
        df_histo = df_histo.dropna(subset=['Température'])
    except KeyError:
        print("Erreur: La colonne 'Température' n'existe pas dans df_histo.")

    # Identify the rows containing NaN values
    #problematic_rows = df[df['Température'].isna()]
    # Print the problematic rows
    #print(problematic_rows)

    #créer un index pour l'agregation
    #df_histo['date_only'] = df_histo[date].dt.strftime('%Y-%m-%d')
    df_histo['date_only']=df_histo.index
    df_histo['month_only']=df_histo.index
    df_histo['year_only']=df_histo.index

    df_histo['date_only'] =df_histo['date_only'].apply(lambda x: x.replace(hour=0, minute=0, second=0))
    #df_histo['month_only'] = df_histo[date].dt.strftime('%Y-%m')
    df_histo['month_only'] =df_histo['date_only'].apply(lambda x: x.replace(day=1,hour=0, minute=0, second=0))
    #df_histo['year_only'] = df_histo[date].dt.strftime('%Y')
    df_histo['year_only'] =df_histo['date_only'].apply(lambda x: x.replace(month=1,day=1,hour=0, minute=0, second=0))

    #print("df_histo.head()=====",df_histo.head())

    #calcul DJU 
    df_day=pd.DataFrame([])
    df_month=pd.DataFrame([])
    df_year=pd.DataFrame([])
    #calcul de la table jour
    if not df_histo.empty:
        df_day = df_histo.groupby('date_only').agg({'Température': ['mean','min', 'max']}) 
        df_day['DJU_Chauffage'], df_day['DJU_Rafraichissement'] = zip(*df_day.apply(
            lambda row: DJU_costic(row[('Température', 'min')], row[('Température', 'max')],base_chauffage=base_chauffage, base_refroidissement=base_refroidissement),
            axis=1
        ))

        df_day['month_only']=df_histo.groupby('date_only').agg({'month_only': ['first']})
        df_day['year_only']=df_histo.groupby('date_only').agg({'year_only': ['first']})
    
        #print(df_day.columns)

        #calcul de la table mois
        #df_month= df_day.groupby('month_only').agg({('DJU_Chauffage',''): ['sum']})
        df_month = df_day.groupby('month_only').agg({('DJU_Chauffage',''): ['sum'],('DJU_Rafraichissement',''): ['sum']})
        df_month['Température']=df_histo.groupby('month_only').agg({'Température': ['mean']})

        #print(df_month)

        #calcul de la table année
        #df_year= df_day.groupby('year_only').agg({('DJU_Chauffage',''): ['sum']})
        df_year= df_day.groupby('year_only').agg({('DJU_Chauffage',''): ['sum'],('DJU_Rafraichissement',''): ['sum']})
        df_year['Température']=df_histo.groupby('year_only').agg({'Température': ['mean']})

        #print(df_year)

        df_day.columns = [ 'Température_moyenne', 'Température_min', 'Température_max',
    'DJU_Chauffage', 'DJU_Rafraichissement', 'Month_only', 'Year_only']
        df_month.columns = ['DJU_Chauffage', 'DJU_Rafraichissement', 'Température']


   

 
    return df_histo,df_day, df_month, df_year
    





