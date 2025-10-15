import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


def MeteoCiel_dayScraping(code2,annee2,mois2,jour2):

    url='https://www.meteociel.fr/temps-reel/obs_villes.php?jour2='+str(jour2)+'&mois2='+str(mois2-1)+'&annee2='+str(annee2)+'&code2='+str(code2)
    #print('url',url)

##########récupérer les données en format HTML
    response = requests.get(url,verify=False)
    soup = BeautifulSoup ( response.content , "html.parser" )
    soup.prettify()
    #print(soup.findAll('table', attrs={'bgcolor': "#EBFAF7"}))
    if soup.findAll('table', attrs={'bgcolor': "#EBFAF7"})==[]:
        print("pas de tableau de données")
        return df
    else:
        for table in soup.findAll('table', attrs={'bgcolor': "#EBFAF7"}):
            #print("TABLE",table)
            col=-1
            col_array = []
            columns=[]
            
            #print(table.text)
            for tr in table.findAll('tr'):
                #print(tr.text)
                col=col+1
                #print("col",col)
                
                row=-1
                row_array = []
                
                for td in tr.findAll('td'):
                    row=row+1
                    #print("row",row)
                    #print(td.text)

                    if row!=8 and col!=0 :
                        row_array.append(td.text)
                    if col==0:
                        columns.append(td.text)
                
                #print(row_array)

                if col!=0:
                    col_array.append(row_array)
                    
                
                #ligne_tr=td.text
                #print(ligne_tr)

                
        #print("col_array",col_array)
        #print("entête",columns)

    ###############récupérer le tableau sous forme d'un DataFrame
        df=pd.DataFrame(col_array,columns=columns)
        #print("df_brut:",df)

        if df.empty:  # Vérifie si le DataFrame est vide
            print("DataFrame is empty. Exiting the function.")
            return pd.DataFrame()
        else:
    ############### Transformer le tableau en colonnes de valeurs et unités
            try:
                df[['Visi','Unité Visi']] = df['Visi'].str.split(' ',expand=True)
            except:
                pass
            try:
                df = df.rename(columns={'HeureUTC': 'Heurelocale'})
                print("attention : changement de nom de la colonne date")
            except:
                df[['Heurelocale','Unité Heurelocale']] = df['Heurelocale'].str.split(' ',expand=True)
                df['Heurelocale']=df.apply(lambda row: ('0'+row.Heurelocale) if int(row.Heurelocale) <= 9 else row.Heurelocale, axis = 1)

            #ajouter un 0 devant les heures
            try:
                df[['Température','Unité Température']] = df['Température'].str.split(' ',expand=True)
            except:
                try:
                    df[['Température','Unité Température']] = df['Température'].str.split(' ',expand=True).drop(columns=[2])
                except:
                    pass


            df['Température'] = df['Température'].str.strip()
            print("df['Température']=====",df['Température'])

        

            try:
                df[['Pression','Unité Pression']] = df['Pression'].str.split(' ',expand=True)
            except:
                df[['Pression','Unité Pression']] = df['Pression'].str.split(' ',expand=True).drop(columns=[2])

            
            try:
                df[['Vent','rafales']] = df['Vent (rafales)'].str.split('(',expand=True)
            except:
                pass

            try:
                df[['Vent','Unité Vent']] = df['Vent'].str.split(' ',expand=True).drop(columns=[2,3])
            except:
                pass
            try:
                df[['rafales','Unité rafales']] = df['rafales'].str.split(' ',expand=True)
            except:
                pass
            try:
                df[['Unité rafales']] = df['Unité rafales'].str.split(')',expand=True).drop(columns=[1])
            except:
                pass
            try:
                df=df.drop(columns=['Vent (rafales)'])
            except:
                pass

            
            #print("df_brut 5",df)
            df["Heurelocale"] = df["Heurelocale"].str.replace(' ', '')
            
            try:
                df["Timestamp"]=df.apply(lambda row: datetime(annee2,mois2, jour2, hour=int(row.Heurelocale), minute=0, second=0, microsecond=0)  , axis = 1)
            except:
                try:
                    df["Timestamp"]=df.apply(lambda row: datetime(annee2,mois2, jour2, hour=int(row.Heurelocale.split("h")[0]), minute=int(row.Heurelocale.split("h")[1]), second=0, microsecond=0)  , axis = 1)
                except:
                    df["Timestamp"]=df.apply(lambda row: datetime(annee2,mois2, jour2, hour=int(row.Heurelocale.split("h")[0]), minute=0, second=0, microsecond=0)  , axis = 1)
                
            try:
                df = df.rename(columns={'Humi.': 'Humidité'})
                df['Humidité'] = df['Humidité'].apply(lambda x: int(x.replace('%', '')))
            except:
                pass
            

            df.set_index('Timestamp', inplace=True)
            df=df.sort_index(ascending=True)

            #df.to_excel("output_meteociel.fr.xlsx")
            #print("df Outlet MeteoCiel_dayScraping",df)


        return df
