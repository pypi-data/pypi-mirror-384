import pandas as pd
from .Two_flow_pinch_analysis import Two_flow_pinch_analysis  # Import the function
# === Fonction pour appliquer un échange de chaleur en-dessous du pinch ===
def apply_heat_exchange_below(one_HS_df, one_CS_df,remain_stream_list_below,remaining_recoverable_heat,used_streams,heat_exchangers):
    #nonlocal remaining_recoverable_heat, used_streams  # Access the remaining recoverable heat and used streams
    hot_stream = one_HS_df.iloc[0].to_dict()
    cold_stream = one_CS_df.iloc[0].to_dict()

    # print(f"\n------------------ Applying Two_flow_pinch_analysis function below the pinch between HS_id={hot_stream['id']} and CS_id={cold_stream['id']} ---")
    results=Two_flow_pinch_analysis(hot_stream,cold_stream)
    # print("\n ---Two_flow_pinch_analysis : flux initiaux avant échange :\n", results["initial_fluxes"])
    # print("\n ---Two_flow_pinch_analysis : propriétés des flux récupérés :\n", results["exchanger"])
    # print("\n ---Two_flow_pinch_analysis : flux restants après récupération :\n", results["remaining_fluxes"])
    # print("\n---Two_flow_pinch_analysis : Utilité chaude :", results["hot_utility"])
    # print("\n---Two_flow_pinch_analysis : Utilité froide :", results["cold_utility"])
    # print("\n---Two_flow_pinch_analysis : Chaleur récupérée :", results["heat_recovered"])

    # === Étape 1 : suppression des lignes à remplacer ===
    remain_stream_list_below.drop(
        remain_stream_list_below[remain_stream_list_below['id'].isin(results["remaining_fluxes"]['id'])].index,
        inplace=True
    )
    # === Étape 2 : concaténation des nouvelles lignes ===
    remain_stream_list_below = pd.concat(
        [remain_stream_list_below, results["remaining_fluxes"]],
        ignore_index=True
    )
   
    
    one_HS_df = results["remaining_fluxes"][results["remaining_fluxes"]['id'] == hot_stream['id']]
    one_CS_df = results["remaining_fluxes"][results["remaining_fluxes"]['id'] == cold_stream['id']]

    heat_exchangers.append(results["exchanger"])
    remaining_recoverable_heat -= heat_exchangers[-1]['HeatExchanged']


    # print("\n3. ----------------------------Heat exchanger created below the pinch:")
    # print(heat_exchangers)
    # print("\n4. ---------------------------------------------------Updated remaining streams below the pinch:")
    # print(remain_stream_list_below)
    # print(f"one_HS_df----------------------------\n,{one_HS_df}\n")
    # print(f"one_CS_df----------------------------\n,{one_CS_df}\n")

    return one_HS_df, one_CS_df,remain_stream_list_below
