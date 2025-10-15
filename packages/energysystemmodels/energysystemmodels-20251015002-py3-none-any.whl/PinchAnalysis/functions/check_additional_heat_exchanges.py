from .Two_flow_pinch_analysis import Two_flow_pinch_analysis  # Import the function
import pandas as pd

def check_additional_heat_exchanges(remain_streams):
    possible_exchanges = []
    tested_combinations = set()  # Set to track tested combinations
    # Debug: Print the actual remaining streams being passed
    # print("\n1. Remaining streams before testing:=============check_additional_heat_exchanges=====================================\n")
    # print(remain_streams)

    # Créer une copie de remain_streams pour éviter les modifications en place
    updated_remain_streams = remain_streams.copy()

    # Boucle sur toutes les combinaisons possibles de flux chauds et froids
    while True:
        # Filtrer les flux chauds et froids restants
        hot_streams = updated_remain_streams[updated_remain_streams['StreamType'] == 'HS']
        cold_streams = updated_remain_streams[updated_remain_streams['StreamType'] == 'CS']

        # Si aucun flux chaud ou froid n'est disponible, arrêter la boucle
        if hot_streams.empty or cold_streams.empty:
            break

        # Variable pour suivre si un échange a été trouvé dans cette itération
        exchange_found = False

        for _, hot_stream in hot_streams.iterrows():
            for _, cold_stream in cold_streams.iterrows():

                                # Identifier la combinaison actuelle
                combination = (hot_stream['id'], cold_stream['id'])

                # Vérifier si la combinaison a déjà été testée
                if combination in tested_combinations:
                    continue  # Passer à la prochaine combinaison

                # Ajouter la combinaison au set des combinaisons testées
                tested_combinations.add(combination)
                
                # Convertir les Series en DataFrames à une seule ligne
                hot_stream_df = hot_stream.to_frame().T
                cold_stream_df = cold_stream.to_frame().T
                #print(f"Testing exchange between HS_id={hot_stream['id']} and CS_id={cold_stream['id']}")
                # Appeler Two_flow_pinch_analysis avec les DataFrames
                try:
                    results = Two_flow_pinch_analysis(hot_stream_df, cold_stream_df)
                    if results["exchanger"]["HeatExchanged"] > 0.0:
                        possible_exchanges.append(results["exchanger"])
                        exchange_found = True

                        # === Mise à jour de updated_remain_streams ===
                        # Étape 1 : suppression des lignes à remplacer
                        updated_remain_streams.drop(
                            updated_remain_streams[updated_remain_streams['id'].isin(results["remaining_fluxes"]['id'])].index,
                            inplace=True
                        )

                        # Étape 2 : concaténation des nouvelles lignes
                        updated_remain_streams = pd.concat(
                            [updated_remain_streams, results["remaining_fluxes"]],
                            ignore_index=True
                        )
                        break  # Sortir de la boucle interne après un échange réussi
                except Exception as e:
                    print(f"Error during analysis for HS_id={hot_stream['id']} and CS_id={cold_stream['id']}: {e}")
            if exchange_found:
                break  # Sortir de la boucle externe après un échange réussi

        # Si aucun échange n'a été trouvé, arrêter la boucle
        if not exchange_found:
            break

    # Filtrer les échanges avec HeatExchanged > 0.0
    possible_exchanges = [exchange for exchange in possible_exchanges if exchange["HeatExchanged"] > 0.0]

    # Debug: Print all possible exchanges found
    # print("\n2. Possible additional exchanges found:=============check_additional_heat_exchanges=====================================\n")
    # print(possible_exchanges)
    # print("\n")
        
    return possible_exchanges, updated_remain_streams
