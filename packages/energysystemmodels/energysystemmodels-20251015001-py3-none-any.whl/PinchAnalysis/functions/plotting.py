import matplotlib.pyplot as plt
import numpy as np

def plot_streams_and_temperature_intervals(self, figsize=(12, 6), xticks_rotation=90):
    # Vérifier la présence des colonnes requises
    required_columns = ['StreamType', 'name', 'STi', 'STo', 'mCp', 'delta_H']
    for column in required_columns:
        if column not in self.stream_list.columns:
            raise ValueError(f"Colonne '{column}' manquante dans le DataFrame.")

    # Vérifier la non-nullité des colonnes nécessaires
    if self.stream_list[required_columns].isnull().values.any():
        raise ValueError("Le DataFrame contient des valeurs nulles dans les colonnes nécessaires.")

    # Extraire les colonnes nécessaires du DataFrame
    StreamType = self.stream_list['StreamType']
    names = self.stream_list['name']
    STi = self.stream_list['STi']
    STo = self.stream_list['STo']
    mCp = self.stream_list['mCp']
    delta_H = self.stream_list['delta_H']

    # Positions numériques sur l'axe x
    x_positions = np.arange(len(names))

    # Créer une nouvelle figure
    plt.figure(figsize=figsize)

    # Tracer les flux avec l'échelle de température décalée et la couleur en fonction du StreamType
    for i, x in enumerate(x_positions):
        if StreamType.iloc[i] == 'HS':  # Hot Stream
            plt.plot([x, x], [STi.iloc[i], STo.iloc[i]], color='red')
            plt.annotate('', xy=(x, STo.iloc[i]), xytext=(x, STo.iloc[i] + 1),
                         arrowprops=dict(arrowstyle='->', color='red', lw=1), annotation_clip=False)
        else:  # Cold Stream
            plt.plot([x, x], [STi.iloc[i], STo.iloc[i]], color='blue')
            plt.annotate('', xy=(x, STo.iloc[i]), xytext=(x, STo.iloc[i] - 1),
                         arrowprops=dict(arrowstyle='->', color='blue', lw=1), annotation_clip=False)

        # Calculer la position verticale moyenne pour l'annotation
        mid_temp = (STi.iloc[i] + STo.iloc[i]) / 2
        plt.text(x, mid_temp, f'{round(delta_H.iloc[i])} kW',
                 verticalalignment='center', horizontalalignment='center',
                 fontsize=8, color='black')

    # Configurer les ticks et labels de l'axe y
    y_ticks = sorted(set(STi) | set(STo))
    plt.yticks(y_ticks)

    # Ajouter des lignes horizontales en pointillé pour chaque valeur de température
    for temp in y_ticks:
        plt.axhline(y=temp, linestyle='--', color='gray', alpha=0.7)

    # Définir les labels des axes et le titre
    plt.xlabel('Stream name')
    plt.ylabel('Shifted temperature (°C)')
    plt.title('Streams and temperature intervals')

    # Associer les positions numériques aux labels (noms + mCp)
    plt.xticks(
        x_positions,
        [f'{name}\n($mCp={mCp_val:.2f}$)' for name, mCp_val in zip(names, mCp)],
        fontsize=8,
        rotation=xticks_rotation
    )

    # Ajuster la marge en bas pour que les labels des xticks soient bien visibles
    plt.subplots_adjust(bottom=0.25)

    # Afficher le label de la température de pincement sur l'axe y
    plt.text(0, self.Pinch_Temperature,
             f'Pinch_Temperature = {self.Pinch_Temperature} °C',
             verticalalignment='bottom', horizontalalignment='left')

    # Afficher la grille
    plt.grid(True)

    # Afficher le graphique
    plt.show()

########################################################################################

def plot_GCC(self):

    # Tracer la courbe de composition avec les axes inversés
    plt.plot(self.GCC['cumulative_delta_H'], self.GCC['T_shifted'], marker='o', label='Courbe de Composition')

    # Ajouter des étiquettes et un titre au graphe
    plt.xlabel('Net heat flow (kW)')
    plt.ylabel('Shifted temperature (°C)')
    plt.title('Grand composite curve')

    # Ajouter la grille
    plt.grid(True)

    # Trouver l'index du maximum de T_shifted
    max_index = self.GCC['T_shifted'].idxmax()

    # Afficher la valeur de Heating_duty au niveau du maximum de T_shifted
    plt.text(self.GCC['cumulative_delta_H'][max_index], self.GCC['T_shifted'][max_index], f'Heating_duty = {self.Heating_duty} kW', verticalalignment='bottom', horizontalalignment='left')

    # Trouver l'index du minimum de T_shifted
    min_index = self.GCC['T_shifted'].idxmin()

    # Afficher la valeur de Cooling_duty au niveau du minimum de T_shifted
    plt.text(self.GCC['cumulative_delta_H'][min_index], self.GCC['T_shifted'][min_index], f'Cooling_duty = {self.Cooling_duty} kW', verticalalignment='bottom', horizontalalignment='right')


    # Afficher la valeur de Pinch_Temperature sur l'axe des ordonnées
    plt.text(0, self.Pinch_Temperature, f'Pinch_Temperature = {self.Pinch_Temperature} °C', verticalalignment='bottom', horizontalalignment='left')


    # Afficher le graphe
    plt.show()

#########################################################################################


def plot_composites_curves(self):
        # Assurer que les deux dataframes ont la même longueur
    length = max(len(self.df_hcc), len(self.df_ccc))
    self.df_hcc = self.df_hcc.reindex(range(length)).fillna(method='ffill')
    self.df_ccc = self.df_ccc.reindex(range(length)).fillna(method='ffill')

    # Tracer les données originales
    plt.plot(self.df_hcc['Q'], self.df_hcc['T'], label='courbe composite du flux chaud', marker='o')
    plt.plot(self.df_ccc['Q'], self.df_ccc['T'], label='courbe composite du flux froid', marker='o')

    # Déterminer les limites pour la région à remplir
    q_min_fill = max(self.df_hcc['Q'].min(), self.df_ccc['Q'].min())
    q_max_fill = min(self.df_hcc['Q'].max(), self.df_ccc['Q'].max())

    # Créer une séquence linéaire pour Q dans la zone à remplir
    q_fill = np.linspace(q_min_fill, q_max_fill, 100)

    # Créer des masques pour exclure certaines parties de la zone remplie
    mask_before_ccc = q_fill < self.df_hcc['Q'].min()
    mask_after_ccf = q_fill > self.df_ccc['Q'].max()

    # Appliquer les masques pour exclure les parties indésirables
    q_fill_masked = q_fill[~(mask_before_ccc | mask_after_ccf)]
    t_ccc_fill = np.interp(q_fill_masked, self.df_hcc['Q'], self.df_hcc['T'])
    t_ccf_fill = np.interp(q_fill_masked, self.df_ccc['Q'], self.df_ccc['T'])

    # Tracer la zone remplie avec rotation
    plt.fill_between(q_fill_masked, t_ccc_fill, t_ccf_fill, color='green', alpha=0.3)


    # Ajouter des lignes pointillées
    for index, row in self.df_hcc.iterrows():
        plt.axvline(x=row['Q'], color='gray', linestyle='--')
        plt.axhline(y=row['T'], color='gray', linestyle='--')

    for index, row in self.df_ccc.iterrows():
        plt.axvline(x=row['Q'], color='gray', linestyle='--')
        plt.axhline(y=row['T'], color='gray', linestyle='--')

    # Ajouter des étiquettes et un titre
    plt.xlabel('Heat flow (kW)')
    plt.ylabel('Shifted temperature (°C)')
    plt.title('Shifted hot and cold composite curves')
    plt.legend()  # Ajouter la légende

    # Afficher le graphique
    plt.show()

