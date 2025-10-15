

def decomposition_flux(self):
    # Ajouter des colonnes pour le nom du flux et la valeur de mCp à df_intervals
    self.df_intervals['StreamName'] = [[] for _ in range(len(self.df_intervals))]
    self.df_intervals['mCp'] = [[] for _ in range(len(self.df_intervals))]
    self.df_intervals['StreamType'] = [[] for _ in range(len(self.df_intervals))]  # Add this line

    #print('self.df_intervals===000=======',self.df_intervals)
    #print('self.stream_list==========',self.stream_list)
    # Parcourir chaque intervalle
    for idx, row in self.df_intervals.iterrows():

        # Parcourir chaque flux
        for i in range(self.rowCount):
            # Tester la condition spécifique (StreamType[i] == "CS")
            if (self.stream_list['StreamType'].iloc[i] == "CS") and (self.stream_list['STi'].iloc[i] < row['Tsup']) and (self.stream_list['STo'].iloc[i] > row['Tinf']):

                # Flux dans l'intervalle
                #self.df_intervals.at[idx, 'mCp'].append(-self.stream_list['mCp'][i])
                #self.df_intervals.at[idx, 'StreamName'].append(self.stream_list['name'][i])
                #self.df_intervals.at[idx, 'StreamType'].append(self.stream_list['StreamType'][i])  # Add this line
                self.df_intervals.at[idx, 'mCp'].append(-self.stream_list['mCp'].iloc[i])
                self.df_intervals.at[idx, 'StreamName'].append(self.stream_list['name'].iloc[i])
                self.df_intervals.at[idx, 'StreamType'].append(self.stream_list['StreamType'].iloc[i])





            # Tester la condition spécifique (StreamType[i] == "HS")
            #elif (self.stream_list['StreamType'][i] == "HS") and (self.stream_list['STi'][i] > row['Tinf']) and (self.stream_list['STo'][i] < row['Tsup']):
            elif (self.stream_list['StreamType'].iloc[i] == "HS") and (self.stream_list['STi'].iloc[i] > row['Tinf']) and (self.stream_list['STo'].iloc[i] < row['Tsup']):


                # Flux dans l'intervalle
                #self.df_intervals.at[idx, 'mCp'].append(self.stream_list['mCp'][i])
                self.df_intervals.at[idx, 'mCp'].append(self.stream_list['mCp'].iloc[i])
                #self.df_intervals.at[idx, 'StreamName'].append(self.stream_list['name'][i])
                self.df_intervals.at[idx, 'StreamName'].append(self.stream_list['name'].iloc[i])
                #self.df_intervals.at[idx, 'StreamType'].append(self.stream_list['StreamType'][i]) 
                self.df_intervals.at[idx, 'StreamType'].append(self.stream_list['StreamType'].iloc[i]) 


    #print('self.df_intervals====00=====',self.df_intervals)
    # Utiliser explode pour dupliquer les lignes pour chaque valeur de mCp
    self.df_intervals = self.df_intervals.explode(['StreamName', 'mCp', 'StreamType']).reset_index(drop=True)
    self.df_intervals = self.df_intervals.sort_values(by=['StreamName', 'Tsup']).reset_index(drop=True)
    self.df_intervals["delta_T"]=self.df_intervals['Tsup']-self.df_intervals['Tinf']
    self.df_intervals["delta_H"]=self.df_intervals["delta_T"]*self.df_intervals["mCp"]
    #print('self.df_intervals====0=====',self.df_intervals)
