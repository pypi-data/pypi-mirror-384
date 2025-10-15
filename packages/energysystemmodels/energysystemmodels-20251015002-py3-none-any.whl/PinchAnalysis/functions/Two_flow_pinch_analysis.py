import pandas as pd
import numpy as np

def Two_flow_pinch_analysis(hot_stream, cold_stream):

    # Convertir les dictionnaires en DataFrames si nécessaire
    if isinstance(hot_stream, dict):
        hot_stream_df = pd.DataFrame([hot_stream])
    else:
        hot_stream_df = hot_stream

    if isinstance(cold_stream, dict):
        cold_stream_df = pd.DataFrame([cold_stream])
    else:
        cold_stream_df = cold_stream


    hot_stream_df['delta_H'] = hot_stream_df['mCp'] * (hot_stream_df['STi'] - hot_stream_df['STo'])
    cold_stream_df['delta_H'] = cold_stream_df['mCp'] * (cold_stream_df['STi'] - cold_stream_df['STo'])
    hot_stream_df['Ti'] = hot_stream_df['STi'] + hot_stream_df['dTmin2']   
    cold_stream_df['Ti'] = cold_stream_df['STi'] - cold_stream_df['dTmin2']
    hot_stream_df['To'] = hot_stream_df['STo'] + hot_stream_df['dTmin2']
    cold_stream_df['To'] = cold_stream_df['STo'] - cold_stream_df['dTmin2']

    combined_streams = pd.concat([hot_stream_df, cold_stream_df])
    stream_df = pd.DataFrame({'Temperature': pd.concat([combined_streams['STi'], combined_streams['STo']])}).drop_duplicates().sort_values(by='Temperature', ascending=False).reset_index(drop=True)
    delta_H = [np.nan] + [
        sum(row['mCp'] * (stream_df.loc[i, 'Temperature'] - stream_df.loc[i + 1, 'Temperature']) for _, row in hot_stream_df.iterrows() if row['STi'] > stream_df.loc[i + 1, 'Temperature'] and row['STo'] < stream_df.loc[i, 'Temperature']) -
        sum(row['mCp'] * (stream_df.loc[i, 'Temperature'] - stream_df.loc[i + 1, 'Temperature']) for _, row in cold_stream_df.iterrows() if row['STi'] < stream_df.loc[i, 'Temperature'] and row['STo'] > stream_df.loc[i + 1, 'Temperature'])
        for i in range(len(stream_df) - 1)
    ]
    stream_df['delta_H'], stream_df['cumul_delta_H'] = delta_H, pd.Series(delta_H).cumsum()
    #stream_df['cumul_delta_H']= O pour la premier lignne
    #stream_df['cumul_delta_H'].iloc[0] = 0
    stream_df.loc[0, 'cumul_delta_H'] = 0
    stream_df['offset_cumul_delta_H'] = stream_df['cumul_delta_H'] - stream_df['cumul_delta_H'].min()
    pinch_temperature = stream_df.loc[stream_df['offset_cumul_delta_H'] == 0, 'Temperature'].max()
    hot_utility, cold_utility = stream_df['offset_cumul_delta_H'].iloc[0], stream_df['offset_cumul_delta_H'].iloc[-1]
    heat_recovered = hot_stream_df['mCp'].sum() * (hot_stream_df['STi'].max() - hot_stream_df['STo'].min()) - cold_utility
    
    
    #HEX_HS_STi=float(hot_stream_df['STi'])
    HEX_HS_STi = float(hot_stream_df['STi'].iloc[0])
    HEX_HS_STo=hot_stream_df['STi'].max() - heat_recovered / hot_stream_df['mCp'].sum()
    #HEX_CS_STi=float(cold_stream_df['STi'])
    HEX_CS_STi = float(cold_stream_df['STi'].iloc[0])

    HEX_CS_STo=cold_stream_df['STi'].min() + heat_recovered / cold_stream_df['mCp'].sum()
    #cas de flux sous le pinch avec mCp du flux chaud > mCp du flux froid
    #if (float(hot_stream_df['STi'])==float(cold_stream_df['STo']) and float(hot_stream_df['mCp'])>=float(cold_stream_df['mCp'])):
    if (float(hot_stream_df['STi'].iloc[0]) == float(cold_stream_df['STo'].iloc[0]) and 
    float(hot_stream_df['mCp'].iloc[0]) >= float(cold_stream_df['mCp'].iloc[0])):   
        HEX_CS_STo=float(cold_stream_df['STo'].iloc[0])
        HEX_CS_STi=HEX_CS_STo-heat_recovered / float(cold_stream_df['mCp'].iloc[0])
    
    
    
    # Conversion explicite des types numpy en types Python natifs
    # Conversion explicite des types numpy en types Python natifs et suppression des crochets
    exchanger = {
        'HS_id': int(hot_stream_df['id'].iloc[0]), 
        'HS_name': str(hot_stream_df['name'].iloc[0]), 
        'HS_mCp': float(hot_stream_df['mCp'].sum()),
        'HS_Ti': float(HEX_HS_STi)+float(hot_stream_df['dTmin2'].iloc[0]),
        'HS_To': float(HEX_HS_STo)+float(hot_stream_df['dTmin2'].iloc[0]),
        'HS_STi': float(HEX_HS_STi), 
        'HS_STo': float(HEX_HS_STo), 

        'CS_id': int(cold_stream_df['id'].iloc[0]),
        'CS_name': str(cold_stream_df['name'].iloc[0]), 
        'CS_mCp': float(cold_stream_df['mCp'].sum()), 
        'CS_Ti': float(HEX_CS_STi)-float(cold_stream_df['dTmin2'].iloc[0]),
        'CS_To': float(HEX_CS_STo)-float(cold_stream_df['dTmin2'].iloc[0]),
        'CS_STi': float(HEX_CS_STi),
        'CS_STo': float(HEX_CS_STo), 
        'HeatExchanged': float(heat_recovered)
    }
    # Mise à jour correcte de STi pour les flux restants
    remaining_fluxes = pd.concat([hot_stream_df, cold_stream_df]).assign(
        # STi=lambda df: df.apply(lambda row: HEX_HS_STo if row['StreamType'] == 'HS' else (HEX_CS_STo if row['StreamType'] == 'CS' else row['STi']), axis=1),

        STi=lambda df: df.apply(
            lambda row: row['STi'] if row['StreamType'] == 'HS' and HEX_HS_STi >= row['STi'] and HEX_HS_STo == row['STo'] else (
                HEX_HS_STo if row['StreamType'] == 'HS' and HEX_HS_STi == row['STi'] and   row['STo']<=HEX_HS_STo else (
                    row['STi'] if row['StreamType'] == 'CS' and HEX_CS_STi >= row['STi'] and HEX_CS_STo == row['STo'] else (
                        HEX_CS_STo if row['StreamType'] == 'CS' and HEX_CS_STi == row['STi'] and HEX_CS_STo <= row['STo'] else row['STi']
                    )
                )
            ), axis=1
        ),
        STo=lambda df: df.apply(
            lambda row: HEX_HS_STi if row['StreamType'] == 'HS' and HEX_HS_STi >= row['STi'] and HEX_HS_STo == row['STo'] else (
                row['STo'] if row['StreamType'] == 'HS' and HEX_HS_STi == row['STi'] and HEX_HS_STo <= row['STo'] else (
                    HEX_CS_STi if row['StreamType'] == 'CS' and HEX_CS_STi >= row['STi'] and HEX_CS_STo == row['STo'] else (
                        row['STo'] if row['StreamType'] == 'CS' and HEX_CS_STi == row['STi'] and HEX_CS_STo <= row['STo'] else row['STo']
                    )
                )
            ), axis=1
        ),
        
      
        
        Ti=lambda df: df.apply(
            lambda row: row['STi'] + row['dTmin2'] if row['StreamType'] == 'HS' else row['STi'] - row['dTmin2'], axis=1
        ),
        To=lambda df: df.apply(
            lambda row: row['STo'] + row['dTmin2'] if row['StreamType'] == 'HS' else row['STo'] - row['dTmin2'], axis=1
        ),
        delta_H=lambda df: df['mCp'] * (df['STi'] - df['STo'])
    ).reset_index(drop=True)

    # print("----initial_fluxes:\n", pd.concat([hot_stream_df, cold_stream_df]))
    # print("----exchanger:\n", exchanger)
    # print("----remaining_fluxes:\n", remaining_fluxes)
    return {
        "stream_df": stream_df, "exchanger": exchanger, "remaining_fluxes": remaining_fluxes,
        "initial_fluxes": pd.concat([hot_stream_df, cold_stream_df]), "pinch_temperature": pinch_temperature,
        "hot_utility": hot_utility, "cold_utility": cold_utility, "heat_recovered": heat_recovered
    }

# Example usage

# cold_stream_df = pd.DataFrame({
#     'id': [2], 'name': ['PP - Gros -Pasto 3A - Lait'], 'mCp': [2], 'Ti': [60.0], 'To': [100.0], 'dTmin2': [5.0],
#     'integration': [True], 'StreamType': ['CS'], 'STi': [25], 'STo': [85], 'delta_H': [78.9]
# })

# hot_stream_df = pd.DataFrame({
#     'id': [20], 'name': ['Liquide-EC sortie - Eau'], 'mCp': [3], 'Ti': [100.0], 'To': [60.0], 'dTmin2': [5.0],
#     'integration': [True], 'StreamType': ['HS'], 'STi': [85], 'STo': [55], 'delta_H': [-46.0]
# })

# results = Two_flow_pinch_analysis(hot_stream_df, cold_stream_df)


# CS = {'id': 3, 'name': 'C2', 'mCp': 6.0, 'Ti': 140, 'To': 140, 'dTmin2': 0, 'integration': True, 'StreamType': 'CS', 'STi': 20, 'STo': 40, 'delta_H': 0.0}
# HS = {'id': 4, 'name': 'H2', 'mCp': 10.0, 'Ti': 90, 'To': 90, 'dTmin2': 0, 'integration': True, 'StreamType': 'HS', 'STi': 40, 'STo':20, 'delta_H': 0.0}


# results = Two_flow_pinch_analysis(HS, CS)


# print("DataFrame avec delta_H, cumul_delta_H et offset_cumul_delta_H :\n", results["stream_df"])
# print("\nDataFrame des flux initiaux avant échange :\n", results["initial_fluxes"])
# print("\nDataFrame des propriétés des flux récupérés :\n", results["exchanger"])
# print("\nDataFrame des flux restants après récupération :\n", results["remaining_fluxes"])
# print("\nTempérature de pincement :", results["pinch_temperature"])
# print("Utilité chaude :", results["hot_utility"])
# print("Utilité froide :", results["cold_utility"])
# print("Chaleur récupérée :", results["heat_recovered"])