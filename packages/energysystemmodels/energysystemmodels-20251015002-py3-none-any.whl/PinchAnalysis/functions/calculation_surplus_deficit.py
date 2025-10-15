import pandas as pd


def surplus_deficit(self):
    #print("self.df_intervals:::::!!!!!",self.df_intervals)
    # Group by 'IntervalName' and aggregate the values
    self.df_surplus_deficit = self.df_intervals.groupby('IntervalName').agg({
        'Tsup': 'first',  # Keep the first value
        'Tinf': 'first',  # Keep the first value
        'StreamName':  lambda x: list(x),  # Keep the first value
        'mCp': 'sum',  # Sum the 'mCp' values
        'StreamType': lambda x: list(x),  # Keep the first value
        'delta_T': 'first',  # Sum the 'delta_T' values
        'delta_H': 'sum'  # Sum the 'delta_H' values
    }).reset_index()

    # Sort by 'Tsup' in descending order
    #print("self.df_surplus_deficit==0===:::::",self.df_surplus_deficit)
    self.df_surplus_deficit = self.df_surplus_deficit.sort_values(by='Tsup', ascending=False)
    #print("self.df_surplus_deficit==1===:::::",self.df_surplus_deficit)
    self.df_surplus_deficit['cumulative_delta_H'] =self.df_surplus_deficit['delta_H'].cumsum()
    
    #print("self.df_surplus_deficit['cumulative_delta_H']=======::::::::",self.df_surplus_deficit['cumulative_delta_H'] )

    self.Heating_duty=pd.to_numeric(self.df_surplus_deficit['cumulative_delta_H'], errors='coerce').min()
    if self.Heating_duty>= 0:
        self.Heating_duty = 0
    else:
        self.Heating_duty = abs(self.Heating_duty)



    # Créer une ligne avec la valeur 0 pour 'cumulative_delta_H'
    self.cumulative_delta_H = pd.concat([pd.Series([0], name='cumulative_delta_H'), self.df_surplus_deficit['cumulative_delta_H']], ignore_index=True)

    # Ajouter la nouvelle ligne à self.Heating_duty
    self.cumulative_delta_H = pd.DataFrame(self.Heating_duty + self.cumulative_delta_H)

    # Concaténer les deux colonnes dans un nouveau DataFrame
    self.GCC = pd.concat([self.df_T_shifted, self.cumulative_delta_H], axis=1)

    # Récupérer la valeur de cumulative_delta_H correspondante
    self.Cooling_duty = self.GCC.loc[self.GCC['T_shifted'].idxmin(), 'cumulative_delta_H']

    # Récupérer la valeur de T_shifted correspondante à cumulative_delta_H nulle
    self.Pinch_Temperature = self.GCC.loc[self.GCC[self.GCC['cumulative_delta_H'] == 0].index, 'T_shifted'].values[0]
    

