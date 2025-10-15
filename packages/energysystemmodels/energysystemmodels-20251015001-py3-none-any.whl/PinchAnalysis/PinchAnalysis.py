import pandas as pd
import numpy as np


from .functions.plotting import plot_streams_and_temperature_intervals
from .functions.plotting import plot_GCC
from .functions.plotting import plot_composites_curves
from .functions.calculation_decomposition import decomposition_flux
from .functions.calculation_surplus_deficit import surplus_deficit
from .functions.calculation_composite_curve import composite_curve
from .functions.calculation_below_above_stream import below_above_stream
from .functions.calculation_allowed_combinations import find_heat_exchange_combinations
from .functions.calculation_HEN import calculate_stream_numbers, hen_stream_list, HeatExchangerNetwork
from .functions.calculation_graphical_HEN import graphical_hen_design

class Object:
    def __init__(self, df):
        #initialisation 


        # Créer la colonne 'integration' et la remplir avec True si elle n'existe pas
        if 'integration' not in df.columns:
            df['integration'] = True
        # Remplacer les valeurs NaN par True
        df['integration'].fillna(True, inplace=True)

        # Sélectionner les flux à intégrer
        self.stream_list = df[df['integration'] == True].copy()  # Utilisez .copy() pour éviter le Warning

        self.rowCount = len(self.stream_list)

        # Créer la colonne 'StreamType'
        self.stream_list['StreamType'] = np.where(self.stream_list['Ti'] > self.stream_list['To'], 'HS', 'CS')

        # Créer de nouvelles colonnes pour les températures décalées
        self.stream_list['STi'] = np.where(self.stream_list['StreamType'] == 'HS',
                                                  self.stream_list['Ti'] - self.stream_list['dTmin2'],
                                                  self.stream_list['Ti'] + self.stream_list['dTmin2'])

        self.stream_list['STo'] = np.where(self.stream_list['StreamType'] == 'HS',
                                                  self.stream_list['To'] - self.stream_list['dTmin2'],
                                                  self.stream_list['To'] + self.stream_list['dTmin2'])

        self.stream_list['delta_H'] = self.stream_list['mCp'] * (self.stream_list['To'] - self.stream_list['Ti'])

         # Calculer T_shifted directement dans la classe
        T_shifted = np.concatenate([self.stream_list['STi'].values, self.stream_list['STo'].values])
        T_shifted = np.sort(np.unique(T_shifted))[::-1]
        self.df_T_shifted = pd.DataFrame({'T_shifted': T_shifted})



                # Créer le DataFrame df_intervals
        self.df_intervals = pd.DataFrame({'Tsup': T_shifted[:-1], 'Tinf': T_shifted[1:]})
        self.df_intervals['IntervalName'] = self.df_intervals['Tsup'].astype(str) + '-' + self.df_intervals['Tinf'].astype(str)

        self.decomposition_flux()
        self.surplus_deficit()
        self.composite_curve()
        self.below_above_stream()
        self.find_heat_exchange_combinations()
        self.calculate_stream_numbers()
        self.hen_stream_list()



    decomposition_flux=decomposition_flux

    plot_streams_and_temperature_intervals = plot_streams_and_temperature_intervals
    plot_GCC=plot_GCC
    plot_composites_curves=plot_composites_curves
    surplus_deficit=surplus_deficit
    composite_curve=composite_curve
    below_above_stream=below_above_stream

# #####################################################""""

#########################################################################################"

    find_heat_exchange_combinations=find_heat_exchange_combinations

###################"For Heat Exchanger network"
    calculate_stream_numbers=calculate_stream_numbers
    hen_stream_list=hen_stream_list
    graphical_hen_design=graphical_hen_design
    HeatExchangerNetwork=HeatExchangerNetwork
