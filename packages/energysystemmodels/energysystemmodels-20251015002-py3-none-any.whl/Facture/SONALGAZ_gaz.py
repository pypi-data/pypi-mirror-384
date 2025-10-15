from datetime import date
import json
import os
from dateutil.parser import parse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

current_directory = os.path.dirname(os.path.abspath(__file__))
coefficients_file_path = os.path.join(current_directory, 'coefficients_sonalgaz_gaz.json')

class input_Facture:
    def __init__(self, start, end, 
                 thermies=0,  # Énergie en thermies
                 DMA_thermie_h=0):  # Débit Maximal Absorbé en thermies/h
        if not isinstance(start, date):
            start = parse(start).date()
        if not isinstance(end, date):
            end = parse(end).date()
        
        self.start = start
        self.end = end
        self.thermies = thermies
        self.DMA_thermie_h = DMA_thermie_h

class input_Contrat:
    def __init__(self, code_tarif="11", DMD_thermie_h=0):  # Débit Mis à Disposition en thermies/h
        self.code_tarif = code_tarif
        self.DMD_thermie_h = DMD_thermie_h

class Sonalgaz_Gaz:
    def __init__(self, contrat, facture):
        self.contrat = contrat
        self.facture = facture
        self.coefficients = None
        self.nb_jours = (self.facture.end - self.facture.start).days + 1
        
        # Montants calculés
        self.montant_fixe = 0
        self.montant_DMD = 0
        self.montant_DMA = 0
        self.montant_energie = 0
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
                self.coefficients = coef
                return coef
                
        raise ValueError(f"Aucun coefficient trouvé pour le code tarif {self.contrat.code_tarif}")

    def calculate(self):
        """Calcule tous les éléments de la facture selon le niveau de pression."""
        coef = self.get_coefficients()
        
        if self.contrat.code_tarif == "23M" or self.contrat.code_tarif == "23NM":
            self._calculate_BP(coef)
        else:
            self._calculate_HP_MP(coef)

    def _calculate_HP_MP(self, coef):
        """Calcul pour Haute et Moyenne Pression."""
        # 1. Redevance Fixe
        self.montant_fixe = coef["fixe_DA_mois"]
        
        # 2. Facturation DMD (Débit Mis à Disposition)
        self.montant_DMD = coef["souscription_DA_thermie_h_mois"] * self.contrat.DMD_thermie_h
        
        # 3. Facturation DMA (uniquement pour tarif 11)
        if self.contrat.code_tarif == "11":
            self.montant_DMA = coef["absorbee_DA_thermie_h_mois"] * self.facture.DMA_thermie_h
        
        # 4. Energie
        self.montant_energie = coef["cDA_thermie"]/100 * self.facture.thermies

        # 5. Total HTVA
        self.montant_total = (
            self.montant_fixe +
            self.montant_DMD +
            self.montant_DMA +
            self.montant_energie
        )

        # 6. TVA (19%)
        self.montant_tva = self.montant_total * 0.19
        
        # 7. Total TTC
        self.montant_total_ttc = self.montant_total + self.montant_tva

        self._update_dataframe("mois")

    def _calculate_BP(self, coef):
        """Calcul pour Basse Pression avec système de tranches."""
        # 1. Redevance Fixe (trimestrielle)
        self.montant_fixe = coef["fixe_DA_mois"] * 3

        # 2. Energie par tranches
        energie_mensuelle = self.facture.kWh_gaz / 3  # moyenne mensuelle
        self.montant_energie = self._calculate_tranches(energie_mensuelle, coef) * 3

        # 3. Total HTVA
        self.montant_total = self.montant_fixe + self.montant_energie

        # 4. TVA (19%)
        self.montant_tva = self.montant_total * 0.19
        
        # 5. Total TTC
        self.montant_total_ttc = self.montant_total + self.montant_tva

        self._update_dataframe("trimestre")

    def _calculate_tranches(self, energie_mensuelle, coef):
        """Calcul du montant par tranches pour BP."""
        montant = 0
        energie_restante = energie_mensuelle

        # Tranche 1
        if "Tranche_1_lim_thermie_mois" in coef:
            energie_t1 = min(energie_restante, coef["Tranche_1_lim_thermie_mois"])
            montant += energie_t1 * coef["Tranche_1_cDA_thermie"]/100
            energie_restante -= energie_t1

            # Tranche 2
            if energie_restante > 0 and "Tranche_2_lim_thermie_mois" in coef:
                energie_t2 = min(energie_restante, 
                               coef["Tranche_2_lim_thermie_mois"] - coef["Tranche_1_lim_thermie_mois"])
                montant += energie_t2 * coef["Tranche_2_cDA_thermie"]/100
                energie_restante -= energie_t2

                # Tranche 3
                if energie_restante > 0 and "Tranche_3_lim_thermie_mois" in coef:
                    energie_t3 = min(energie_restante,
                                   coef["Tranche_3_lim_thermie_mois"] - coef["Tranche_2_lim_thermie_mois"])
                    montant += energie_t3 * coef["Tranche_3_cDA_thermie"]/100
                    energie_restante -= energie_t3

                    # Tranche 4 (le reste)
                    if energie_restante > 0 and "Tranche_4_cDA_thermie" in coef:
                        montant += energie_restante * coef["Tranche_4_cDA_thermie"]

        return montant

    def _update_dataframe(self, periode):
        """Mise à jour du DataFrame avec les résultats."""
        # Conversion thermies en MWh (1 thermie = 0.00116222222 MWh)
        energie_MWh = self.facture.thermies * 0.00116222222
        
        # Prix moyens
        prix_moyen_thermie = self.montant_total / self.facture.thermies if self.facture.thermies > 0 else 0
        prix_moyen_MWh = self.montant_total / energie_MWh if energie_MWh > 0 else 0
        
        composantes = [
            ("Energie Gaz (thermies)", f"{self.facture.thermies:,.2f}"),
            ("Energie Gaz (MWh)", f"{energie_MWh:,.2f}"),
            ("Prix moyen HTVA (DA/thermie)", f"{prix_moyen_thermie:,.2f}"),
            ("Prix moyen HTVA (DA/MWh)", f"{prix_moyen_MWh:,.2f}"),
            ("", ""),  # Ligne vide pour la séparation
            (f"Redevance Fixe (DA/{periode})", f"{self.montant_fixe:,.2f}"),
            (f"DMD-Débit mis à disposition (DA/{periode})", f"{self.montant_DMD:,.2f}")
        ]
        
        if self.contrat.code_tarif == "11":
            composantes.append(
                (f"DMA-Débit maximal absorbé (DA/{periode})", f"{self.montant_DMA:,.2f}")
            )
        
        composantes.extend([
            (f"Energie (DA/{periode})", f"{self.montant_energie:,.2f}"),
            (f"Total HTVA (DA/{periode})", f"{self.montant_total:,.2f}"),
            (f"TVA 19% (DA/{periode})", f"{self.montant_tva:,.2f}"),
            (f"Total TTC (DA/{periode})", f"{self.montant_total_ttc:,.2f}")
        ])
        
        self.df = pd.DataFrame(composantes, columns=["Composante", "Montant (DA)"])
        pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))

    def plot(self, title="Facture de Gaz SONALGAZ (DA)", figsize=(8, 6)):
        """Affiche un graphique en donut des composantes principales de la facture."""
        labels = ['Fixe et DMD (débit mis à disposition)', 'DMA (débit maximal absorbé)', 'Énergie', 'TVA']
        values = [
            self.montant_fixe + self.montant_DMD,
            self.montant_DMA,
            self.montant_energie,
            self.montant_tva
        ]
        colors = ['#4CAF50', '#2196F3', '#F44336', '#FFC107']

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
        ax.text(0, 0, f"{total:,.2f} DA", ha='center', va='center', fontsize=14, fontweight='bold')

        y_start = -0.05
        y_step = 0.07
        x_rect = -0.12
        x_text = -0.05

        for i, (label, val, color) in enumerate(zip(labels, values, colors)):
            y = y_start - i * y_step
            rect = Rectangle((x_rect, y - 0.02), 0.04, 0.04, facecolor=color, transform=ax.transAxes, clip_on=False)
            ax.add_patch(rect)
            ax.text(x_text, y, f"{label} : {val:,.2f} DA",
                    transform=ax.transAxes,
                    ha='left', va='center',
                    fontsize=11, weight='bold')

        plt.tight_layout()
        plt.show()

    def plot_detail(self, title="Détail des Composantes de la Facture Gaz", figsize=(12, 6)):
        """Affiche un graphique en cascade des composantes détaillées."""
        fig, ax = plt.subplots(figsize=figsize)

        labels = ['Redevance Fixe', 'DMD (débit mis à disposition)', 'DMA (débit maximal absorbé)', 'Energie', 'TVA']
        values = [
            self.montant_fixe,
            self.montant_DMD,
            self.montant_DMA,
            self.montant_energie,
            self.montant_tva
        ]

        cum_values = [0]
        for v in values:
            cum_values.append(cum_values[-1] + v)

        colors = ['green' if v >= 0 else 'red' for v in values]
        for i, (label, val) in enumerate(zip(labels, values)):
            ax.bar(i, val, bottom=cum_values[i], color=colors[i], edgecolor='black')
            y_text = cum_values[i] + val / 2
            ax.text(i, y_text, f"{val:,.2f} DA", ha='center', va='center', fontsize=9)

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.axhline(0, color='black', linewidth=0.8)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        
        plt.title(title + f"\nTotal TTC : {self.montant_total_ttc:,.2f} DA", fontsize=12, pad=20)
        plt.tight_layout()
        plt.show()