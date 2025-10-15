import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.patches as patches

def draw_hen_from_df(df):
    G = nx.DiGraph()
    pos = {}
    node_labels = {}

    # Regrouper les échangeurs par flux chaud (HS_name)
    hot_streams = defaultdict(list)
    for i, row in df.iterrows():
        hot_streams[row['HS_name']].append((i, row))

    # Pour retrouver les noeuds par flux froid et température
    cold_in_nodes = defaultdict(lambda: defaultdict(list))   # {cold_name: {temp: [node_id,...]}}
    cold_out_nodes = defaultdict(lambda: defaultdict(list))

    # Position base
    y_base = 0
    y_spacing = 5
    x_spacing = 4

    for j, (hot_name, exchangers) in enumerate(hot_streams.items()):
        y = y_base - j * y_spacing
        x = 0

        # Nœud entrée flux chaud
        hot_in_node = f"{hot_name}_Tin"
        G.add_node(hot_in_node)
        node_labels[hot_in_node] = f"{hot_name}_Tin\n{exchangers[0][1]['HS_Ti']}°C"
        pos[hot_in_node] = (x, y)
        x += x_spacing

        previous_node = hot_in_node

        for exch_index, row in exchangers:
            exch = f"E{exch_index+1}"

            # Décalage horizontal pour une ligne sur deux
            x_offset = 1  # Décalage horizontal pour les lignes impaires

            # Nœuds échangeur
            hot_out_node = f"{row['HS_name']}_Tout_{exch_index}"
            cold_in_node = f"{row['CS_name']}_Tin_{exch_index}"
            cold_out_node = f"{row['CS_name']}_Tout_{exch_index}"

            # Ajouter les nœuds
            G.add_node(exch)
            G.add_node(hot_out_node)
            G.add_node(cold_in_node)
            G.add_node(cold_out_node)

            # Labels
            node_labels[exch] = f"{exch}\nQ={round(row['HeatExchanged'], 1)} kW"  # Arrondi à 1 chiffre après la virgule
            node_labels[hot_out_node] = f"{row['HS_name']}_Tout\n{round(row['HS_To'], 1)}°C"
            node_labels[cold_in_node] = f"{row['CS_name']}_Tin\n{round(row['CS_Ti'], 1)}°C"
            node_labels[cold_out_node] = f"{row['CS_name']}_Tout\n{round(row['CS_To'], 1)}°C"

            # Positions avec décalage horizontal pour une ligne sur deux
            pos[exch] = (x + x_offset + (1.0 if j % 2 == 0 else 0), y)
            pos[hot_out_node] = (x + x_offset + (1.5 if j % 2 == 0 else 0.5) + 1.5, y)
            pos[cold_in_node] = (x + x_offset + (1.0 if j % 2 == 0 else 0), y - 1.5)
            pos[cold_out_node] = (x + x_offset + (1.0 if j % 2 == 0 else 0), y + 1.5)


            # Connexions principales
            G.add_edge(previous_node, exch)
            G.add_edge(exch, hot_out_node)
            G.add_edge(cold_in_node, exch)
            G.add_edge(exch, cold_out_node)

            previous_node = hot_out_node
            x += x_spacing

            # Stocker pour liens froids
            cold_in_nodes[row['CS_name']][row['CS_Ti']].append(cold_in_node)
            cold_out_nodes[row['CS_name']][row['CS_To']].append(cold_out_node)

    # Arrondir les températures pour éviter les problèmes de précision
    def round_temp(temp):
        return round(temp, 1)  # Arrondi à 1 chiffre après la virgule

    # Mise à jour des nœuds et connexions avec températures arrondies
    for j, (hot_name, exchangers) in enumerate(hot_streams.items()):
        for exch_index, row in exchangers:
            # Arrondir les températures
            row['HS_Ti'] = round_temp(row['HS_Ti'])
            row['HS_To'] = round_temp(row['HS_To'])
            row['CS_Ti'] = round_temp(row['CS_Ti'])
            row['CS_To'] = round_temp(row['CS_To'])

            # Mise à jour des nœuds de température
            hot_out_node = f"{row['HS_name']}_Tout_{exch_index}"
            cold_in_node = f"{row['CS_name']}_Tin_{exch_index}"
            cold_out_node = f"{row['CS_name']}_Tout_{exch_index}"

            node_labels[hot_out_node] = f"{row['HS_name']}_Tout\n{row['HS_To']}°C"
            node_labels[cold_in_node] = f"{row['CS_name']}_Tin\n{row['CS_Ti']}°C"
            node_labels[cold_out_node] = f"{row['CS_name']}_Tout\n{row['CS_To']}°C"

            # Stocker les nœuds pour connexions froides
            cold_in_nodes[row['CS_name']][row['CS_Ti']].append(cold_in_node)
            cold_out_nodes[row['CS_name']][row['CS_To']].append(cold_out_node)

    # Connexion flux froids si même flux ET même température sortie-entrée
    for cold_name in cold_out_nodes:
        for temp, out_nodes in cold_out_nodes[cold_name].items():
            in_nodes = cold_in_nodes[cold_name].get(temp, [])
            for out_node in out_nodes:
                for in_node in in_nodes:
                    G.add_edge(out_node, in_node)

    # Identifier les températures extrêmes pour chaque flux
    hot_stream_extremes = {}
    cold_stream_extremes = {}

    for hot_name, exchangers in hot_streams.items():
        temps = [row['HS_Ti'] for _, row in exchangers] + [row['HS_To'] for _, row in exchangers]
        hot_stream_extremes[hot_name] = max(temps)  # Température la plus haute pour le flux chaud

    for cold_name, temp_nodes in cold_in_nodes.items():
        temps = list(temp_nodes.keys()) + list(cold_out_nodes[cold_name].keys())
        cold_stream_extremes[cold_name] = min(temps)  # Température la plus basse pour le flux froid

    # Mise à jour des labels
    for j, (hot_name, exchangers) in enumerate(hot_streams.items()):
        for exch_index, row in exchangers:
            hot_out_node = f"{row['HS_name']}_Tout_{exch_index}"
            cold_in_node = f"{row['CS_name']}_Tin_{exch_index}"
            cold_out_node = f"{row['CS_name']}_Tout_{exch_index}"

            # Mise à jour des labels pour les nœuds de température
            if row['HS_To'] == hot_stream_extremes[row['HS_name']]:
                node_labels[hot_out_node] = f"{row['HS_name']}_Tout\n{round(row['HS_To'], 1)}°C"
            else:
                node_labels[hot_out_node] = f"{round(row['HS_To'], 1)}°C"

            if row['CS_Ti'] == cold_stream_extremes[row['CS_name']]:
                node_labels[cold_in_node] = f"{row['CS_name']}_Tin\n{round(row['CS_Ti'], 1)}°C"
            else:
                node_labels[cold_in_node] = f"{round(row['CS_Ti'], 1)}°C"

            if row['CS_To'] == cold_stream_extremes[row['CS_name']]:
                node_labels[cold_out_node] = f"{row['CS_name']}_Tout\n{round(row['CS_To'], 1)}°C"
            else:
                node_labels[cold_out_node] = f"{round(row['CS_To'], 1)}°C"

    # Séparer les nœuds par type avec une vérification stricte
    exchanger_nodes = [node for node in G.nodes if node.startswith("E") and node[1:].isdigit()]
    temperature_nodes = [node for node in G.nodes if node not in exchanger_nodes]

    # Générer une palette de couleurs suffisamment grande pour les flux froids
    num_cold_streams = len(cold_in_nodes)
    distinct_colors = cm.get_cmap('tab20', num_cold_streams)  # Palette avec 20 couleurs distinctes

    # Assigner une couleur unique à chaque flux chaud
    hot_stream_color_map = {hot_name: mcolors.to_hex(cm.get_cmap('Reds', len(hot_streams))(i)) for i, hot_name in enumerate(hot_streams)}

    # Assigner une couleur unique à chaque flux froid (sans chevauchement)
    cold_stream_color_map = {
        cold_name: mcolors.to_hex(distinct_colors(i))  # Utilisation de couleurs uniques
        for i, cold_name in enumerate(cold_in_nodes)
    }

    # Tracé
    plt.figure(figsize=(13.33, 7.5))  # Pour un bon ajustement
    ax = plt.gca()  # Obtenir l'axe pour ajouter des formes personnalisées

    # Couleur fixe pour les flux chauds
    hot_stream_color = 'red'  # Couleur rouge pour tous les flux chauds

    # Dessiner les nœuds de température avec une couleur rouge pour tous les flux chauds
    for hot_name, exchangers in hot_streams.items():
        hot_nodes = [f"{row['HS_name']}_Tout_{exch_index}" for exch_index, row in exchangers]
        hot_nodes.append(f"{hot_name}_Tin")  # Ajouter le nœud d'entrée
     
    # Dessiner les nœuds de température avec des couleurs spécifiques par flux froid
    for i, (cold_name, temp_nodes) in enumerate(cold_in_nodes.items()):
        cold_nodes = []
        for temp_nodes_list in temp_nodes.values():
            cold_nodes.extend(temp_nodes_list)
        for temp_nodes_list in cold_out_nodes[cold_name].values():
            cold_nodes.extend(temp_nodes_list)
      
    # Dessiner les nœuds d'échangeurs (rectangles arrondis)
    for node in exchanger_nodes:
        x, y = pos[node]  # Position du nœud
        label = node_labels[node]  # Texte du nœud
        width = 1.2  # Réduction de la largeur (par exemple, de 1.5 à 1.2)
        height = 0.6  # Réduction de la hauteur (par exemple, de 0.8 à 0.6)
        rect = patches.FancyBboxPatch(
            (x - width / 2, y - height / 2),  # Position du coin inférieur gauche
            width,  # Largeur
            height,  # Hauteur
            boxstyle="round,pad=0.3",  # Style de rectangle arrondi
            edgecolor="red",  # Couleur du bord
            facecolor="green",  # Couleur de remplissage
            linewidth=0.6 # Épaisseur du bord
        )
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=6, color="black")  # Ajouter le texte au centre

    # Dessiner les nœuds de température (rectangles arrondis uniquement)
    for node in temperature_nodes:
        x, y = pos[node]  # Position du nœud
        label = node_labels[node]  # Texte du nœud
        # Vérifier si la clé existe dans cold_stream_color_map
        node_key = node.split("_")[0]
        color = (
            hot_stream_color
            if node in hot_stream_color_map
            else cold_stream_color_map.get(node_key, "lightblue")  # Utiliser une couleur par défaut si la clé n'existe pas
        )
        width = 0.6  # Largeur du rectangle
        height = 0.25  # Hauteur du rectangle
        rect = patches.FancyBboxPatch(
            (x - width / 2, y - height / 2),  # Position du coin inférieur gauche
            width,  # Largeur
            height,  # Hauteur
            boxstyle="round,pad=0.3",  # Style de rectangle arrondi
            edgecolor="none",  # Couleur du bord
            facecolor=color,  # Couleur de remplissage
            linewidth=1.5,  # Épaisseur du bord
        )
        ax.add_patch(rect)
        ax.text(x, y, label, ha="center", va="center", fontsize=6, color="black")  # Ajouter le texte au centre

    # Dessiner les arêtes
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='->', arrowsize=10)

    # Ajouter les étiquettes pour les nœuds de température
    nx.draw_networkx_labels(G, pos, labels={k: v for k, v in node_labels.items() if k not in exchanger_nodes}, font_size=6)

    # Titre et mise en page
    plt.title("Réseau d'échangeurs de chaleur à partir d'un DataFrame", fontsize=10)
    plt.axis('off')
    plt.tight_layout()
    plt.show()



