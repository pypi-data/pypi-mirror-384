from datetime import date
import json
import os
from dateutil.parser import parse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

current_directory = os.path.dirname(os.path.abspath(__file__))
coefficients_file_path = os.path.join(current_directory, 'coefficients_sonalgaz_elec.json')

class input_Facture:
    def __init__(self, start, end, 
                 kWh_pointe=0, kWh_pleine=0, kWh_jour=0, 
                 kWh_nuit=0, kWh_hors_pointe=0, kWh_poste_unique=0,
                 kvarh_reactif=0,
                 PMA_kW=0):  # Puissance Maximale Absorbée
        if not isinstance(start, date):
            start = parse(start).date()
        if not isinstance(end, date):
            end = parse(end).date()
        
        self.start = start
        self.end = end
        self.kWh_pointe = kWh_pointe
        self.kWh_pleine = kWh_pleine
        self.kWh_jour = kWh_jour
        self.kWh_nuit = kWh_nuit
        self.kWh_hors_pointe = kWh_hors_pointe
        self.kWh_poste_unique = kWh_poste_unique
        self.kvarh_reactif = kvarh_reactif
        self.PMA_kW = PMA_kW

class input_Contrat:
    def __init__(self, code_tarif="41", PMD_kW=0):
        self.code_tarif = code_tarif
        self.PMD_kW = PMD_kW
        # La tension sera déterminée automatiquement dans get_coefficients

class Sonalgaz_Elec:
    def __init__(self, contrat, facture):
        self.contrat = contrat
        self.facture = facture
        self.coefficients = None
        self.nb_jours = (self.facture.end - self.facture.start).days + 1
        
        # Montants calculés
        self.montant_fixe = 0
        self.montant_PMD = 0
        self.montant_PMA = 0
        self.montant_energie = 0
        self.montant_reactif = 0
        self.montant_total = 0
        self.montant_tva = 0
        self.montant_total_ttc = 0
        
        # DataFrame pour le résumé
        self.df = pd.DataFrame(columns=["Composante", "Montant (DA)"])

    def get_coefficients(self):
        """Récupère les coefficients selon le code tarif."""
        with open(coefficients_file_path, 'r') as f:
            data = json.load(f)
            
        for coef in data["coefficients"]:
            if (coef["code_tarif"] == self.contrat.code_tarif and
                parse(coef["date_debut"]).date() <= self.facture.start <= parse(coef["date_fin"]).date()):
                # Détermine la tension à partir du code tarif trouvé
                self.contrat.tension = coef["tension"]
                self.coefficients = coef  # Stocke les coefficients
                return coef
                
        raise ValueError(f"Aucun coefficient trouvé pour le code tarif {self.contrat.code_tarif}")

    def calculate(self):
        """Calcule tous les éléments de la facture selon le niveau de tension."""
        coef = self.get_coefficients()
        tension = coef["tension"]  # Récupère la tension depuis les coefficients
        
        if tension == "BT":
            self._calculate_BT(coef)
        elif tension in ["HTA", "HTB"]:
            self._calculate_HT(tension, coef)
        else:
            raise ValueError(f"Niveau de tension non reconnu : {tension}")

    def _calculate_BT(self, coef):
        """Calcul spécifique pour la Basse Tension."""
        # 1. Redevance Fixe (trimestrielle)
        self.montant_fixe = coef["fixe_DA_mois"] * 3  # Trimestre

        # 2. Facturation PMD
        self.montant_PMD = coef["souscription_DA_kW_mois"] * self.contrat.PMD_kW * 3  # Trimestre

        # 3. Energie Active selon code tarif
        if self.contrat.code_tarif in ["51M", "51NM", "52M", "52NM", "53M", "53NM"]:
            # Calcul par poste horaire
            self.montant_energie = (
                coef["point_cDA_kWh"]/100 * self.facture.kWh_pointe +
                coef["Pleine_cDA_kWh"]/100 * self.facture.kWh_pleine +
                coef["jour_cDA_kWh"]/100 * self.facture.kWh_jour +
                coef["hors_pointe_cDA_kWh"]/100 * self.facture.kWh_hors_pointe +
                coef["Nuit_cDA_kWh"]/100 * self.facture.kWh_nuit +
                coef["Poste_unique_cDA_kWh"]/100 * self.facture.kWh_poste_unique
            )
        elif self.contrat.code_tarif in ["54M", "54NM"]:
            # Calcul par tranches
            energie_mensuelle = self.facture.kWh_poste_unique / 3  # moyenne mensuelle
            self.montant_energie = self._calculate_tranches(energie_mensuelle, coef) * 3

        # 4. Total trimestriel
        self.montant_total = (
            self.montant_fixe +
            self.montant_PMD +
            self.montant_energie
        )

        # Mise à jour du DataFrame de résumé
        self._update_dataframe()

    def _calculate_HT(self, niveau, coef):
        """Calcul spécifique pour la Haute et Très Haute Tension (HTA/HTB)."""
        # 1. Redevance Fixe
        self.montant_fixe = coef["fixe_DA_mois"]
        
        # 2. Facturation PMD (Puissance Mise à Disposition)
        self.montant_PMD = coef["souscription_DA_kW_mois"] * self.contrat.PMD_kW
        
        # 3. Facturation PMA (Puissance Maximale Absorbée)
        self.montant_PMA = coef["absorbee_DA_kW_mois"] * self.facture.PMA_kW
        
        # 4. Energie Active selon le code tarif
        self.montant_energie = 0
        if niveau == "HTB" and self.contrat.code_tarif == "31":
            self.montant_energie = (
                coef["point_cDA_kWh"]/100 * self.facture.kWh_pointe +
                coef["Pleine_cDA_kWh"]/100 * self.facture.kWh_pleine +
                coef["Nuit_cDA_kWh"]/100 * self.facture.kWh_nuit
            )
        elif niveau == "HTB" and self.contrat.code_tarif == "32":
            self.montant_energie = coef["Poste_unique_cDA_kWh"]/100 * self.facture.kWh_poste_unique
        elif niveau == "HTA":
            self.montant_energie = (
                coef["point_cDA_kWh"]/100 * self.facture.kWh_pointe +
                coef["Pleine_cDA_kWh"]/100 * self.facture.kWh_pleine +
                coef["jour_cDA_kWh"]/100 * self.facture.kWh_jour +
                coef["hors_pointe_cDA_kWh"]/100 * self.facture.kWh_hors_pointe +
                coef["Nuit_cDA_kWh"]/100 * self.facture.kWh_nuit +
                coef["Poste_unique_cDA_kWh"]/100 * self.facture.kWh_poste_unique
            )

        # 5. Energie Réactive (uniquement pour HTA et HTB)
        energie_totale = (
            self.facture.kWh_pointe +
            self.facture.kWh_pleine +
            self.facture.kWh_jour +
            self.facture.kWh_nuit +
            self.facture.kWh_hors_pointe +
            self.facture.kWh_poste_unique
        )
        
        # Calcul du seuil de dépassement (50% de l'énergie active)
        seuil_reactif = 0.5 * energie_totale
        
        # Calcul du dépassement ou du non-dépassement
        depassement = self.facture.kvarh_reactif - seuil_reactif
        print(f"dépassement réactif : {depassement} kvarh (seuil : {seuil_reactif} kvarh)")
        
        # Application du tarif selon dépassement ou non
        if depassement > 0:
            # Malus sur le dépassement
            self.montant_reactif = depassement * coef["reactive_malus_cDA_kvarh"]/100
        else:
            # Bonus sur l'énergie réactive en dessous du seuil
            self.montant_reactif = depassement * coef["reactive_bonus_cDA_kvarh"]/100

        # 6. Total
        self.montant_total = (
            self.montant_fixe +
            self.montant_PMD +
            self.montant_PMA +
            self.montant_energie +
            self.montant_reactif
        )

        # Calcul de la TVA (19% sur l'énergie HT)
        self.montant_tva = self.montant_total * 0.19
        
        # Calcul du total TTC
        self.montant_total_ttc = self.montant_total + self.montant_tva

        # Mise à jour du DataFrame
        periode = "mois"
        self._update_dataframe(periode)

    def _update_dataframe(self, periode="mois"):
        """Mise à jour du DataFrame avec les résultats."""
        # Calcul des énergies totales en MWh/Mvarh
        energie_active_MWh = (
            self.facture.kWh_pointe +
            self.facture.kWh_pleine +
            self.facture.kWh_jour +
            self.facture.kWh_nuit +
            self.facture.kWh_hors_pointe +
            self.facture.kWh_poste_unique
        ) / 1000  # Conversion en MWh
        
        energie_reactive_Mvarh = self.facture.kvarh_reactif / 1000  # Conversion en Mvarh
        
        # Début du DataFrame avec les consommations
        composantes = [
            ("Energie Active totale (MWh)", f"{energie_active_MWh:,.2f}"),
            ("Energie Réactive totale (Mvarh)", f"{energie_reactive_Mvarh:,.2f}"),
            ("", "")  # Ligne vide pour la séparation
        ]
        
        # Reste des composantes
        composantes.extend([
            (f"Redevance Fixe (DA/{periode})", f"{self.montant_fixe:,.2f}"),
            (f"PMD-Puissance mise à disposition (DA/{periode})", f"{self.montant_PMD:,.2f}")
        ])
        
        if self.contrat.tension in ["HTA", "HTB"]:
            composantes.extend([
                (f"PMA-Puissance maximale atteinte (DA/{periode})", f"{self.montant_PMA:,.2f}")
            ])
            
            # Détail de l'énergie active selon le niveau de tension et code tarif
            coef = self.coefficients
            if self.contrat.tension == "HTB" and self.contrat.code_tarif == "31":
                for poste, kWh in [
                    ("Pointe", self.facture.kWh_pointe),
                    ("Pleine", self.facture.kWh_pleine),
                    ("Nuit", self.facture.kWh_nuit)
                ]:
                    if kWh > 0:
                        montant = coef[f'{poste.lower()}_cDA_kWh' if poste == "Nuit" 
                                     else f'{"point" if poste == "Pointe" else poste.lower()}_cDA_kWh']/100 * kWh
                        composantes.append((f"Energie {poste} (DA/mois)", f"{montant:,.2f}"))
                        
            elif self.contrat.tension == "HTB" and self.contrat.code_tarif == "32":
                if self.facture.kWh_poste_unique > 0:
                    montant = coef['Poste_unique_cDA_kWh']/100 * self.facture.kWh_poste_unique
                    composantes.append(("Energie Poste Unique (DA/mois)", f"{montant:,.2f}"))
                    
            elif self.contrat.tension == "HTA":
                # Mapping des postes horaires selon le code tarif
                postes_tarif = {
                    "41": ["Pointe", "Pleine", "Jour", "Hors Pointe", "Nuit", "Poste Unique"],
                    "42": ["Pointe", "Hors Pointe"],  # Uniquement Pointe et Hors Pointe
                    "43": ["Pointe", "Jour", "Nuit"],
                    "44": ["Poste Unique"]
                }
                
                mapping_coef = {
                    "Pointe": ("point_cDA_kWh", "kWh_pointe"),
                    "Pleine": ("Pleine_cDA_kWh", "kWh_pleine"),
                    "Jour": ("jour_cDA_kWh", "kWh_jour"),
                    "Hors Pointe": ("hors_pointe_cDA_kWh", "kWh_hors_pointe"),
                    "Nuit": ("Nuit_cDA_kWh", "kWh_nuit"),
                    "Poste Unique": ("Poste_unique_cDA_kWh", "kWh_poste_unique")
                }
                
                for poste in postes_tarif.get(self.contrat.code_tarif, []):
                    coef_name, attr_name = mapping_coef[poste]
                    kWh = getattr(self.facture, attr_name)
                    if kWh > 0:
                        montant = coef[coef_name]/100 * kWh
                        composantes.append((f"Energie {poste} (DA/mois)", f"{montant:,.2f}"))
            
            if self.montant_reactif != 0:
                composantes.extend([
                    (f"Energie Réactive (DA/{periode})", f"{self.montant_reactif:,.2f}")
                ])
        
        # Calcul du prix moyen par MWh
        energie_totale_MWh = (
            self.facture.kWh_pointe +
            self.facture.kWh_pleine +
            self.facture.kWh_jour +
            self.facture.kWh_nuit +
            self.facture.kWh_hors_pointe +
            self.facture.kWh_poste_unique
        ) / 1000  # Conversion en MWh
        
        prix_moyen_MWh = self.montant_total / energie_totale_MWh if energie_totale_MWh > 0 else 0
       
        composantes.extend([
            (f"Energie Active Total (DA/{periode})", f"{self.montant_energie:,.2f}"),
            (f"Prix moyen énergie active (DA HTVA/MWh)", f"{prix_moyen_MWh:,.2f}"),
            (f"Total HTVA (DA/{periode})", f"{self.montant_total:,.2f}"),
            (f"TVA 19% (DA/{periode})", f"{self.montant_tva:,.2f}"),
            (f"Total TTC (DA/{periode})", f"{self.montant_total_ttc:,.2f}")
        ])
        
        self.df = pd.DataFrame(composantes, columns=["Composante", "Montant (DA)"])
        pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))

    def plot(self, title="Facture d'Électricité SONALGAZ (DA)", figsize=(8, 6)):
        """Affiche un graphique en donut des composantes principales de la facture."""
        # Séparation de l'énergie réactive en bonus/malus
        reactif_bonus = min(0, self.montant_reactif)  # Valeur négative ou 0
        reactif_malus = max(0, self.montant_reactif)  # Valeur positive ou 0
        
        # Ajuster les labels et valeurs selon le type d'énergie réactive
        if reactif_bonus < 0:
            labels = ['Fixe et PMD(Puissance mise à disposition)', 'PMA(Puissance maximale atteinte)', 'Énergie', 'Réactif (bonus)', 'TVA']
            values = [
                self.montant_fixe + self.montant_PMD,
                self.montant_PMA,
                self.montant_energie,
                abs(reactif_bonus),  # Conversion en positif pour l'affichage
                self.montant_tva
            ]
        else:
            labels = ['Fixe et PMD(Puissance mise à disposition)', 'PMA(Puissance maximale atteinte)', 'Énergie', 'Réactif (malus)', 'TVA']
            values = [
                self.montant_fixe + self.montant_PMD,
                self.montant_PMA,
                self.montant_energie,
                reactif_malus,
                self.montant_tva
            ]
        
        colors = ['#4CAF50', '#2196F3', '#F44336', '#9C27B0', '#FFC107']
        
        total = self.montant_total_ttc
        
        fig, ax = plt.subplots(figsize=figsize)
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops=dict(width=0.4, edgecolor='w'),
            pctdistance=0.8,
            textprops={'fontsize': 12}
        )
        
        ax.axis('equal')
        plt.title(title, fontsize=12, pad=16)
        
        # Ajout du total au centre du donut
        ax.text(0, 0, f"{total:,.2f} DA", ha='center', va='center', fontsize=14, fontweight='bold')
        
        # Légende en bas à gauche avec indication bonus/malus
        y_start = -0.05
        y_step = 0.07
        x_rect = -0.12
        x_text = -0.05
        
        for i, (label, val, color) in enumerate(zip(labels, values, colors)):
            y = y_start - i * y_step
            rect = Rectangle((x_rect, y - 0.02), 0.04, 0.04, facecolor=color, transform=ax.transAxes, clip_on=False)
            ax.add_patch(rect)
            # Affichage du signe négatif pour le bonus
            if "bonus" in label:
                ax.text(x_text, y, f"{label} : -{val:,.2f} DA",
                       transform=ax.transAxes,
                       ha='left', va='center',
                       fontsize=11, weight='bold')
            else:
                ax.text(x_text, y, f"{label} : {val:,.2f} DA",
                       transform=ax.transAxes,
                       ha='left', va='center',
                       fontsize=11, weight='bold')
        
        plt.tight_layout()
        plt.show()

    def plot_detail(self, title="Détail des Composantes de la Facture SONALGAZ", figsize=(16, 6)):
        """Affiche un graphique en cascade (waterfall) des composantes détaillées."""
        fig, axs = plt.subplots(1, 2, figsize=figsize)  # Changé de 3 à 2 graphiques

        def plot_waterfall(ax, labels, values, title):
            cum_values = [0]
            for v in values:
                cum_values.append(cum_values[-1] + v)

            colors = ['green' if v >= 0 else 'red' for v in values]
            for i, (label, val) in enumerate(zip(labels, values)):
                ax.bar(i, val, bottom=cum_values[i], color=colors[i], edgecolor='black')
                y_text = cum_values[i] + val / 2
                ax.text(i, y_text, f"{val:.2f} DA", ha='center', va='center', fontsize=9,
                        color='black' if abs(val) > 20 else 'black')

            total = sum(values)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.axhline(0, color='black', linewidth=0.8)
            ax.set_title(f"{title}\nTotal : {total:,.2f} DA", fontsize=12)
            ax.grid(axis='y', linestyle='--', alpha=0.5)

        # Composantes fixes
        fixes_labels = ['Redevance Fixe', 'PMD-Puissance mise à disposition', 'PMA-Puissance maximale atteinte']
        fixes_values = [
            self.montant_fixe,
            self.montant_PMD,
            self.montant_PMA
        ]
        plot_waterfall(axs[0], fixes_labels, fixes_values, "Composantes Fixes")

        # Énergie active et réactive
        energie_labels = []
        energie_values = []
        
        # Ajout des composantes d'énergie active selon le code tarif
        if self.contrat.code_tarif == "42":
            energie_labels.extend(['Pointe', 'Hors Pointe'])
            energie_values.extend([
                self.coefficients['point_cDA_kWh']/100 * self.facture.kWh_pointe,
                self.coefficients['hors_pointe_cDA_kWh']/100 * self.facture.kWh_hors_pointe
            ])
        else:
            energie_labels.extend(['Pointe', 'Pleine', 'Jour', 'Nuit', 'Hors Pointe'])
            energie_values.extend([
                self.coefficients['point_cDA_kWh']/100 * self.facture.kWh_pointe,
                self.coefficients['Pleine_cDA_kWh']/100 * self.facture.kWh_pleine,
                self.coefficients['jour_cDA_kWh']/100 * self.facture.kWh_jour,
                self.coefficients['Nuit_cDA_kWh']/100 * self.facture.kWh_nuit,
                self.coefficients['hors_pointe_cDA_kWh']/100 * self.facture.kWh_hors_pointe
            ])
        
        # Ajout de l'énergie réactive
        energie_labels.append('Réactive')
        energie_values.append(self.montant_reactif)
        
        plot_waterfall(axs[1], energie_labels, energie_values, "Énergies Active et Réactive")

        plt.suptitle(title, fontsize=16, y=0.97)
        plt.tight_layout(rect=[0, 0, 1, 0.93])
        plt.show()