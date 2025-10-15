import pandas as pd

from .apply_heat_exchange_above import apply_heat_exchange_above
from .apply_heat_exchange_below import apply_heat_exchange_below
from .check_additional_heat_exchanges import check_additional_heat_exchanges
from .draw_hen_from_df import draw_hen_from_df
debug_iteration = 1  # Itération pour laquelle le debug est activé

###############################"GHE########################################"""""
def graphical_hen_design(self, plot=False):
    # Initialiser une liste pour les échangeurs installés
    self.heat_exchangers = []
    self.remaining_recoverable_heat = self.heat_recovery  # Track remaining recoverable heat
    self.used_streams = set()  # Track streams that have already been used

    # Initialize remaining stream lists
    self.remain_stream_list_above = self.stream_list_above.copy()
    self.remain_stream_list_below = self.stream_list_below.copy()



    # === Échanges au-dessus du pinch ===
    if not self.combinations_above.empty:
        for i in range(len(self.combinations_above)):
            comb = self.combinations_above.iloc[i]
            one_HS_df = self.remain_stream_list_above[self.remain_stream_list_above['id'] == comb['HS_id']]
            one_CS_df = self.remain_stream_list_above[self.remain_stream_list_above['id'] == comb['CS_id']]

            # Debug: Print the combination being tested

            # print(f"\nEvaluating combination above the pinch: HS_id={comb['HS_id']}, CS_id={comb['CS_id']}")

            if not one_HS_df.empty and not one_CS_df.empty:
                one_HS_df, one_CS_df,self.remain_stream_list_above = apply_heat_exchange_above(one_HS_df, one_CS_df,self.remain_stream_list_above,self.remaining_recoverable_heat,self.used_streams,self.heat_exchangers)

    # === Échanges en-dessous du pinch ===
    if not self.combinations_below.empty:
        for i in range(len(self.combinations_below)):
            comb = self.combinations_below.iloc[i]
            one_HS_df = self.remain_stream_list_below[self.remain_stream_list_below['id'] == comb['HS_id']]
            one_CS_df = self.remain_stream_list_below[self.remain_stream_list_below['id'] == comb['CS_id']]

            # Debug: Print the combination being tested

            # print(f"\nEvaluating combination below the pinch: HS_id={comb['HS_id']}, CS_id={comb['CS_id']}")

            if not one_HS_df.empty and not one_CS_df.empty:
                one_HS_df, one_CS_df,self.remain_stream_list_below = apply_heat_exchange_below(one_HS_df, one_CS_df,self.remain_stream_list_below,self.remaining_recoverable_heat,self.used_streams,self.heat_exchangers)


    # === Vérifier et ajouter les échanges supplémentaires en boucle ===
  

    additional_heat_exchanges_above,self.remain_stream_list_above = check_additional_heat_exchanges(self.remain_stream_list_above)
    # print(additional_heat_exchanges_above)
    additional_heat_exchanges_below,self.remain_stream_list_below = check_additional_heat_exchanges(self.remain_stream_list_below)
    # print(additional_heat_exchanges_below)

    # Ajouter les échanges supplémentaires à la liste des échangeurs
    self.heat_exchangers.extend(additional_heat_exchanges_above)
    self.heat_exchangers.extend(additional_heat_exchanges_below)

    # === Construction finale du DF des échangeurs ===
    self.df_exchangers = pd.DataFrame(self.heat_exchangers)

    if not self.df_exchangers.empty:
        self.df_exchangers = self.df_exchangers[self.df_exchangers['HeatExchanged'] > 0.5]
        self.df_exchangers = self.df_exchangers.sort_values(by="HeatExchanged", ascending=False).reset_index(drop=True)

        # chaleur totale récupérée
        self.total_heat_recovered = self.df_exchangers['HeatExchanged'].sum()
        self.percent_recovered = 100 * self.total_heat_recovered / self.heat_recovery
    else:
        # Aucun échange trouvé
        self.total_heat_recovered = 0.0
        self.percent_recovered = 0.0
    if plot:
        draw_hen_from_df(self.df_exchangers)
    return self.df_exchangers