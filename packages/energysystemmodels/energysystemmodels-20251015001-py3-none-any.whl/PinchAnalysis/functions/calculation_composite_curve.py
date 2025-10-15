import pandas as pd

def composite_curve(self):
    # Définition des fonctions d'agrégation pour chaque colonne
    agg_functions = {'delta_H': 'sum', 'mCp': 'sum', 'Tsup': 'last', 'Tinf': 'last', 'StreamName': lambda x: list(x)}

    # Groupement par IntervalName et StreamType avec application des fonctions d'agrégation
    composite_curve = self.df_intervals.groupby(['IntervalName', 'StreamType']).agg(agg_functions).reset_index()
    composite_curve = composite_curve.sort_values(by=['StreamType', 'Tsup'], ascending=[True, True])

    # Créer des copies des DataFrames résultants
    self.cold_composite_curve = composite_curve[composite_curve['StreamType'] == 'CS'].copy()
    self.hot_composite_curve = composite_curve[composite_curve['StreamType'] == 'HS'].copy()

    # Calcul de la somme cumulée par StreamType
    self.cold_composite_curve['delta_H'] =-1*self.cold_composite_curve['delta_H']
    self.cold_composite_curve['mCp'] =-1*self.cold_composite_curve['mCp']
    self.cold_composite_curve['cumulative_delta_H'] = self.cold_composite_curve['delta_H'].cumsum()
    self.hot_composite_curve['cumulative_delta_H'] = self.hot_composite_curve['delta_H'].cumsum()

    self.cold_stream=max(self.cold_composite_curve['cumulative_delta_H'])
    self.hot_stream=max(self.hot_composite_curve['cumulative_delta_H'])

    self.heat_recovery=self.hot_stream-self.Cooling_duty
    #self.heat_recovery=self.cold_stream-self.Heating_duty


    # Afficher le résultat
    self.cold_composite_curve
    self.hot_composite_curve


    # Création du nouveau dataframe avec une ligne supplémentaire
    hcc_data = {'T': [self.hot_composite_curve['Tinf'].min()] + self.hot_composite_curve['Tsup'].tolist(),
                'Q': [0] + self.hot_composite_curve['cumulative_delta_H'].tolist()}



    self.df_hcc = pd.DataFrame(hcc_data)
    self.df_hcc


    # Création du nouveau dataframe avec une ligne supplémentaire
    ccc_data = {'T': [self.cold_composite_curve['Tinf'].min()] + self.cold_composite_curve['Tsup'].tolist(),
                'Q': [0] + self.cold_composite_curve['cumulative_delta_H'].tolist()+self.Cooling_duty}

    self.df_ccc = pd.DataFrame(ccc_data)
    self.df_ccc
