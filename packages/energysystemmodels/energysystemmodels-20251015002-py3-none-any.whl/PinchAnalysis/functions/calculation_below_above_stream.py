import pandas as pd

def below_above_stream(self):
    new_rows = []

    # Division de chaque ligne en deux
    for index, row in self.stream_list.iterrows():
    
        if self.stream_list.loc[index, 'StreamType']=='HS' and self.stream_list.loc[index, 'STo']<self.Pinch_Temperature:
            row_below = row.copy()
            if self.Pinch_Temperature<=row_below['STi']:
                row_below['STi'] = self.Pinch_Temperature
            new_rows.append(row_below)

        if self.stream_list.loc[index, 'StreamType']=='CS' and self.stream_list.loc[index, 'STi']<self.Pinch_Temperature:
            row_below = row.copy()
            if self.Pinch_Temperature<=row_below['STo']:
                row_below['STo'] = self.Pinch_Temperature          
            new_rows.append(row_below)

##################################################################################
        if self.stream_list.loc[index, 'StreamType']=='HS' and self.stream_list.loc[index, 'STi']>self.Pinch_Temperature:
            row_above = row.copy()
            if self.Pinch_Temperature>=self.stream_list.loc[index, 'STo']:
                row_above['STo'] = self.Pinch_Temperature
            else:
                row_above['STo'] = self.stream_list.loc[index, 'STo']
            new_rows.append(row_above)


        if self.stream_list.loc[index, 'StreamType']=='CS' and self.stream_list.loc[index, 'STo']>self.Pinch_Temperature:
            row_above = row.copy()
            if row_above['STi'] >= self.Pinch_Temperature:
                # Tout le flux est au-dessus du pinch -> garder tel quel
                pass
            else:
                # Le flux croise le pinch -> couper STi au pinch
                row_above['STi'] = self.Pinch_Temperature
            new_rows.append(row_above)
        





    

    # Création du nouveau DataFrame
    df_divided = pd.DataFrame(new_rows).sort_values(by=['id', 'STi']).reset_index(drop=True)


    for i, row in df_divided.iterrows():
        if row['StreamType'] == "CS":
            df_divided.at[i, 'Ti'] = row['STi'] - row['dTmin2']
            df_divided.at[i, 'To'] = row['STo'] - row['dTmin2']
        else:  # Pour les flux "HS"
            df_divided.at[i, 'Ti'] = row['STi'] + row['dTmin2']
            df_divided.at[i, 'To'] = row['STo'] + row['dTmin2']
    
    



    # Créer des copies indépendantes pour df_above et df_below
    self.stream_list_above = df_divided[(df_divided['STi'] >= self.Pinch_Temperature) & (df_divided['STo'] >= self.Pinch_Temperature) & (df_divided['STi'] != df_divided['STo'])].copy()
    self.stream_list_below = df_divided[(df_divided['STi'] <= self.Pinch_Temperature) & (df_divided['STo'] <= self.Pinch_Temperature) & (df_divided['STi'] != df_divided['STo'])].copy()

    # Effectuer les modifications avec .loc
    self.stream_list_above.loc[:, 'delta_H'] = self.stream_list_above['mCp'] * (self.stream_list_above['To'] - self.stream_list_above['Ti'])
    self.stream_list_below.loc[:, 'delta_H'] = self.stream_list_below['mCp'] * (self.stream_list_below['To'] - self.stream_list_below['Ti'])
