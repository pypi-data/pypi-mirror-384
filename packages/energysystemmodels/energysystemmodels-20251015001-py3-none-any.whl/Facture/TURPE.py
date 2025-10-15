from datetime import date
import json
import os
from dateutil.parser import parse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np  # nécessaire pour cos, sin, deg2rad

current_directory = os.path.dirname(os.path.abspath(__file__))
coefficients_file_path = os.path.join(current_directory, 'coefficients_elec.json')
#print("coefficients_file_path =",coefficients_file_path )




class input_Facture:
    def __init__(self, start,end,depassement_PS_pointe=0, depassement_PS_HPH=0, depassement_PS_HCH=0, depassement_PS_HPB=0, depassement_PS_HCB=0, heures_depassement=0,kWh_pointe=0,kWh_HPH=0,
        kWh_HCH=0,    kWh_HPB=0,        kWh_HCB=0):

        # Si start n'est pas déjà un objet date, le convertir en date
        if not isinstance(start, date):
            start = parse(start).date()

        # Si end n'est pas déjà un objet date, le convertir en date
        if not isinstance(end, date):
            end = parse(end).date()

        self.start = start
        self.end = end


        self.depassement_PS_pointe = depassement_PS_pointe
        self.depassement_PS_HPH = depassement_PS_HPH
        self.depassement_PS_HCH = depassement_PS_HCH
        self.depassement_PS_HPB = depassement_PS_HPB
        self.depassement_PS_HCB = depassement_PS_HCB
        self.heures_depassement = heures_depassement
        self.kWh_pointe=kWh_pointe
        self.kWh_HPH=kWh_HPH
        self.kWh_HCH=kWh_HCH
        self.kWh_HPB=kWh_HPB
        self.kWh_HCB=kWh_HCB

class input_Tarif:
    def __init__(self, 
                 c_euro_kWh_pointe=0.0, 
                 c_euro_kWh_HPB=0.0, 
                 c_euro_kWh_HCB=0.0, 
                 c_euro_kWh_HPH=0.0, 
                 c_euro_kWh_HCH=0.0, 
                 c_euro_kwh_CSPE_TICFE=None, 
                 c_euro_kWh_certif_capacite_pointe=0.0, 
                 c_euro_kWh_certif_capacite_HPH=0.0, 
                 c_euro_kWh_certif_capacite_HCH=0.0, 
                 c_euro_kWh_certif_capacite_HPB=0.0, 
                 c_euro_kWh_certif_capacite_HCB=0.0, 
                 c_euro_kWh_ENR=0.0, 
                 c_euro_kWh_ARENH=0.0):
        self.c_euro_kWh_pointe = c_euro_kWh_pointe
        self.c_euro_kWh_HPB = c_euro_kWh_HPB
        self.c_euro_kWh_HCB = c_euro_kWh_HCB
        self.c_euro_kWh_HPH = c_euro_kWh_HPH
        self.c_euro_kWh_HCH = c_euro_kWh_HCH
        self.c_euro_kwh_CSPE_TICFE = c_euro_kwh_CSPE_TICFE
        self.c_euro_kWh_certif_capacite_pointe=c_euro_kWh_certif_capacite_pointe
        self.c_euro_kWh_certif_capacite_HPH=c_euro_kWh_certif_capacite_HPH
        self.c_euro_kWh_certif_capacite_HCH=c_euro_kWh_certif_capacite_HCH
        self.c_euro_kWh_certif_capacite_HPB=c_euro_kWh_certif_capacite_HPB
        self.c_euro_kWh_certif_capacite_HCB=c_euro_kWh_certif_capacite_HCB
        self.c_euro_kWh_ENR = c_euro_kWh_ENR
        self.c_euro_kWh_ARENH = c_euro_kWh_ARENH


class input_Contrat:
    def __init__(self, depassement_PS_pointe=None, domaine_tension=None, heures_depassement=None, PS_pointe=None, PS_HPH=None, PS_HCH=None, PS_HPB=None, PS_HCB=None, version_utilisation=None,pourcentage_ENR=0,abonnement_annuel=0,cadre_contractuel="contrat unique",nb_cellules_secours=0,km_secours_aerien=0,km_secours_souterrain=0):
        self.domaine_tension = domaine_tension
        self.PS_pointe = PS_pointe
        self.PS_HPH = PS_HPH
        self.PS_HCH = PS_HCH
        self.PS_HPB = PS_HPB
        self.PS_HCB = PS_HCB
        self.version_utilisation = version_utilisation
        self.pourcentage_ENR=pourcentage_ENR
        self.abonnement_annuel = abonnement_annuel
        self.cadre_contractuel = cadre_contractuel
        self.nb_cellules_secours=nb_cellules_secours
        self.km_secours_aerien=km_secours_aerien
        self.km_secours_souterrain=km_secours_souterrain

class TurpeCalculator:
    def __init__(self,contrat,tarif,facture, coefficients_file="coefficients.json"):
        self.contrat = contrat
        self.tarif=tarif
        self.facture=facture
       
        self.coefficients_file = os.path.join(current_directory, coefficients_file)
       

        self.coefficients = None
        self.ajustables = []
        self.euro_CS_fixe=None

        self.euro_an_CACS=0.0 # intégrer après dans le calcul
        self.euro_an_CR=0.0# intégrer après dans le calcul
        self.euro_an_CER=0.0 # intégrer après dans le calcul
        self.euro_an_CI=0.0 # intégrer après dans le calcul
        self.euro_CTA=0.0
        self.euro_an_CTA=0.0
        self.euro_CSPE_TICFE=0.0
        self.euro_abonnement= 0.0
      



    def get_TURPE_coef(self, facture, version_utilisation, domaine_tension,cadre_contractuel="contrat unique"):
        with open(coefficients_file_path, 'r') as fichier:
            donnees = json.load(fichier)

        for coefficient in donnees["coefficients"]:
            start_date = parse(coefficient["start_date"]).date()
            expiration_date = parse(coefficient["expiration_date"]).date()
            if (start_date <= facture.start <= expiration_date and
                start_date <= facture.end <= expiration_date and
                coefficient["version_utilisation"] == version_utilisation and
                coefficient["domaine_tension"] == domaine_tension and
                coefficient["cadre_contractuel"] == cadre_contractuel):
                #print("coefficient = ",coefficient)
                return coefficient

        return None



# Example usage:
    def calculate_taxes_contrib(self,coeff):
        #coeff = self.get_TURPE_coef(self.facture, self.contrat.version_utilisation, self.contrat.domaine_tension)
        self.calculate_euro_CTA(coeff)
        self.calculate_euro_CSPE_TICFE(coeff)
        self.euro_taxes_contrib=round(self.euro_CTA+self.euro_CSPE_TICFE,2)
        #print("euro_taxes_contrib = ",self.euro_taxes_contrib)

    def calculate_turpe(self):
        self.df=None
        self.euro_an_CS=None
        self.euro_an_TURPE_CTA=None
        coeff = self.get_TURPE_coef(self.facture, self.contrat.version_utilisation, self.contrat.domaine_tension,self.contrat.cadre_contractuel)
        self.kWh_Total = self.facture.kWh_HPH +self.facture.kWh_HCH + self.facture.kWh_HPB + self.facture.kWh_HCB + self.facture.kWh_pointe
        #print("kWh_Total = " ,self.kWh_Total )

        if self.contrat.domaine_tension == "HTA":
            self.calculate_euro_an_CS_fixe(coeff, self.contrat)
            self.calculate_euro_CS_variable(coeff, self.facture)
      
     
            self.euro_mois_CMDPS = self.calculate_euro_mois_CMDPS(coeff, self.facture)

        elif self.contrat.domaine_tension == "BT > 36 kVA":
            self.calculate_euro_an_CS_fixe(coeff, self.contrat)
            self.calculate_euro_CS_variable(coeff, self.facture)
            self.heures_depassement = 0  # Vous devrez définir cela correctement
            self.euro_mois_CMDPS = round(11.21 * self.heures_depassement, 2)
        
        elif self.contrat.domaine_tension == "BT < 36 kVA":
            self.calculate_euro_an_CS_fixe(coeff, self.contrat)
            self.calculate_euro_CS_variable(coeff, self.facture)
            self.heures_depassement = 0  # Vous devrez définir cela correctement
            self.euro_mois_CMDPS = round(11.21 * self.heures_depassement, 2)
        
        # self.euro_CS_fixe = self.calculate_euro_CS_fixe(self.euro_an_CS_fixe, self.facture)
        
        self.calculate_nb_jour()  # Appel de la méthode pour calculer le nombre de jours
        self.calculate_euro_CS_fixe()
        self.calculate_euro_CC(coeff)
        self.calculate_euro_CG(coeff)
        self.calculate_euro_CACS(coeff)
        self.calculate_taxes_contrib(coeff)
        self.calculate_euro_TURPE()
        self.calculate_euro_an_TURPE()
        # self.calculate_euro_total()
        self.calculate_montant(coeff)
        


        self.euro_an_CS=self.euro_an_CS_fixe + self.euro_CS_variable
        self.euro_CS= self.euro_CS_fixe + self.euro_CS_variable
        self.euro_an_TURPE_CTA=self.euro_an_TURPE + self.euro_an_CTA

        df_data_cout = [
            ("Nombre de jours", self.nb_jour),
            ("Fourniture (€)", self.euro_fourniture),
            ("Distribution (TURPE) (€)", self.euro_TURPE),
            ("Taxes et contributions (€)", self.euro_taxes_contrib),
            ("Facture HTVA (€)", self.euro_total),
            ("Facture TTC (€)", self.euro_total*1.2),
            ("MWh Total", self.kWh_Total / 1000.0),
            ("cout du MWh (€HTVA/MWh)", round(self.euro_total / (self.kWh_Total / 1000.0), 2)),
            ("cout du MWh (€Hors taxes et contributions /MWh)", round((self.euro_total - self.euro_taxes_contrib) / (self.kWh_Total / 1000.0), 2)),
            ("cout du MWh (€ fourniture /MWh)", round(self.euro_fourniture / (self.kWh_Total / 1000.0), 2)),
            ("cout du MWh (€ distribution /MWh)", round((self.euro_total - self.euro_fourniture - self.euro_taxes_contrib) / (self.kWh_Total / 1000.0), 2))
        ]

        df_index_cout = [
            "self.nb_jour",
            "self.euro_fourniture",
            "self.euro_TURPE",
            "self.euro_taxes_contrib",
           
            "self.euro_total",
            "self.euro_total * 1.2",
            "self.kWh_Total / 1000.0",
            "cout du MWh (€HTVA/MWh)",
            "cout du MWh (€Hors taxes et contributions /MWh)",
            "cout du MWh (€ fourniture /MWh)",
            "cout du MWh (€ distribution /MWh)"


        ]

        self.df_couts = pd.DataFrame(df_data_cout, index=df_index_cout, columns=["Nom de variable", "Valeur"])
        df_data_fourniture = [
            ("Heures pleines été",self.euro_HPB),
            ("Heures creuses été",self.euro_HCB),
            ("Heure pleines hiver",self.euro_HPH),
            ("heure creuse hiver",self.euro_HCH),
            ("heures pointe",self.euro_pointe),
            ("self.euro_capacite", self.euro_capacite),
            ("self.euro_abonnement", self.euro_abonnement),
            ("Accès Régulé à l'Électricité Nucléaire Historique-ARENH", self.euro_ARENH),
            ("Distribution (sans ARENH)", self.euro_fourniture),
            ("Distribusiton (avec ARENH)", self.euro_fourniture)]
        df_index_fourniture = [
            "self.euro_HPB",
            "self.euro_HCB",
            "self.euro_HPH",
            "self.euro_HCH",
            "self.euro_pointe",
            "self.euro_capacite",
            "self.euro_abonnement",
            "self.euro_ARENH",
            "self.euro_fourniture (sans ARENH)",
            "self.euro_fourniture (avec ARENH)"
        ]
        self.df_fourniture = pd.DataFrame(df_data_fourniture, index=df_index_fourniture, columns=["Nom de variable", "Valeur"])
        df_data_distribution = [
            ("Composante de gestion - CG (€)", self.euro_CG),
            ("Composante de comptage - CC (€)", self.euro_CC),
            ("Part Puissance - CS Fixe (€)", self.euro_CS_fixe),
            ("Part Énergie - CS Variable (€)", self.euro_CS_variable),
            ("Alimentation de secours - CACS (€)", self.euro_CACS),
            ("Distribustion : TURPE (€)", self.euro_TURPE)]
        df_index_distribution = [
            "self.euro_CG",
            "self.euro_CC",
            "self.euro_CS_fixe",
            "self.euro_CS_variable",
            "self.euro_CACS",
            "self.euro_TURPE"
        ]
        self.df_distribution = pd.DataFrame(df_data_distribution, index=df_index_distribution, columns=["Nom de variable", "Valeur"])
        df_data_taxes_contrib = [
            ("CTA (€)", self.euro_CTA),
            ("TICFE/CSPE (€)", self.euro_CSPE_TICFE),
            ("Taxes et contributions (€)", self.euro_taxes_contrib)]
        df_index_taxes_contrib = [
            "self.euro_CTA",
            "self.euro_CSPE_TICFE",
            "self.euro_taxes_contrib"
        ]
        self.df_taxes_contributions = pd.DataFrame(df_data_taxes_contrib, index=df_index_taxes_contrib, columns=["Nom de variable", "Valeur"])

        df_data_annuel = [
            ("Composante de gestion - CG (€/an)", self.euro_an_CG),
            ("Composante de comptage - CC (€/an)", self.euro_an_CC),
            ("Composante de soutirage - fixe + variable (€/an)", self.euro_an_CS),
            ("Part Puissance - CS Fixe (€/an)", self.euro_an_CS_fixe),
            ("Part Énergie - CS Variable (€/an)", self.euro_CS_variable),
            ("Alimentation de secours - CACS (€/an)", self.euro_an_CACS),
            ("Distribustion : TURPE (€/an)", self.euro_an_TURPE),
            ("CTA annuel (€/an)", self.euro_an_CTA),
            ("Distribustion + CTA  (€/an)", self.euro_an_TURPE_CTA),
            ("TICFE/CSPE annuel (€/an)", self.euro_an_CSPE_TICFE)]
        df_index_annuel = [
            "self.euro_an_CG",
            "self.euro_an_CC",
            "self.euro_an_CS",
            "self.euro_an_CS_fixe",
            "self.euro_CS_variable",
            "self.euro_an_CACS",
            "self.euro_an_TURPE",
            "self.euro_an_CTA",
            "self.euro_an_TURPE_CTA",
            "self.euro_an_CSPE_TICFE"
        ]
        self.df_annuel = pd.DataFrame(df_data_annuel, index=df_index_annuel, columns=["Nom de variable", "Valeur"])
        
 
       
        



    def plot(self, title="Facture d'Électricité en € HTVA", figsize=(8, 6)):
        # Vérification des données nécessaires
        if self.euro_fourniture is None or self.euro_TURPE is None or self.euro_taxes_contrib is None:
            print("Certaines composantes nécessaires au graphique ne sont pas définies.")
            return

        labels = ['Fourniture', 'Distribution (TURPE)', 'Taxes et Contributions']
        values = [self.euro_fourniture, self.euro_TURPE, self.euro_taxes_contrib]
        colors = ['#4CAF50', '#2196F3', '#FFC107']  # Vert, Bleu, Jaune

        total = sum(values)

        fig, ax = plt.subplots(figsize=figsize)

        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,  # Pas de labels autour du cercle
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops=dict(width=0.4, edgecolor='w'),
            pctdistance=0.8,
            textprops={'fontsize': 12}
        )

        ax.axis('equal')  # Cercle parfait
        plt.title(title, fontsize=12, pad=16)

        # Ajout du total au centre du donut
        ax.text(0, 0, f"{total:,.2f} €", ha='center', va='center', fontsize=14, fontweight='bold')

        # Positionnement de la légende en bas à gauche du donut
        y_start = -0.05  # plus bas dans l'axe (peut être négatif)
        y_step = 0.07    # plus petit pour réduire l'espacement
        x_rect = -0.12   # carré un peu plus à gauche
        x_text = -0.05   # texte un peu plus à gauche aussi

        for i, (label, val, color) in enumerate(zip(labels, values, colors)):
            y = y_start - i * y_step
            rect = Rectangle((x_rect, y - 0.02), 0.04, 0.04, facecolor=color, transform=ax.transAxes, clip_on=False)
            ax.add_patch(rect)
            ax.text(x_text, y, f"{label} : {val:,.2f} €",
                    transform=ax.transAxes,
                    ha='left', va='center',
                    fontsize=11, weight='bold')

        plt.tight_layout()
        plt.show()



    def plot_detail(self, title="Détail des Composantes de la Facture d'Électricité", figsize=(16, 6)):
        # Vérification des données nécessaires
        necessary_attrs = [
            'euro_HPB', 'euro_HCB', 'euro_HPH', 'euro_HCH', 'euro_pointe', 'euro_capacite', 'euro_abonnement', 'euro_ARENH',
            'euro_CG', 'euro_CC', 'euro_CS_fixe', 'euro_CS_variable', 'euro_CACS',
            'euro_CSPE_TICFE', 'euro_CSPE_TICFE', 'euro_CTA'
        ]
        for attr in necessary_attrs:
            if getattr(self, attr, None) is None:
                print(f"Attribut {attr} non défini.")
                return

        # === Fourniture ===
        fourniture_labels = ['HPB', 'HCB', 'HPH', 'HCH', 'Pointe', 'Capacité', 'Abonnement', 'ARENH (déduction)']
        fourniture_values = [
            self.euro_HPB,
            self.euro_HCB,
            self.euro_HPH,
            self.euro_HCH,
            self.euro_pointe,
            self.euro_capacite,
            self.euro_abonnement,
            self.euro_ARENH
        ]

        # === Distribution (TURPE) ===
        turpe_labels = ['Gestion (CG)', 'Comptage (CC)', 'Soutirage Fixe', 'Soutirage Variable', 'Alimentation Secours']
        turpe_values = [
            self.euro_CG,
            self.euro_CC,
            self.euro_CS_fixe,
            self.euro_CS_variable,
            self.euro_CACS
        ]

        # === Taxes et Contributions ===
        taxes_labels = ['TICFE/CSPE', 'CTA']
        taxes_values = [
            self.euro_CSPE_TICFE,
            self.euro_CTA
        ]

        fig, axs = plt.subplots(1, 3, figsize=figsize)

        def plot_waterfall(ax, labels, values, title):
            cum_values = [0]
            for v in values:
                cum_values.append(cum_values[-1] + v)

            colors = ['green' if v >= 0 else 'red' for v in values]
            for i, (label, val) in enumerate(zip(labels, values)):
                ax.bar(i, val, bottom=cum_values[i], color=colors[i], edgecolor='black')
                y_text = cum_values[i] + val / 2
                ax.text(i, y_text, f"{val:.2f} €", ha='center', va='center', fontsize=9,
                        color='black' if abs(val) > 20 else 'black')

            total = sum(values)

            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.axhline(0, color='black', linewidth=0.8)
            ax.set_title(f"{title}\nTotal : {total:.2f} €", fontsize=12)
            ax.grid(axis='y', linestyle='--', alpha=0.5)

        # Tracer les 3 cascades
        plot_waterfall(axs[0], fourniture_labels, fourniture_values, "Fourniture")
        plot_waterfall(axs[1], turpe_labels, turpe_values, "Distribution (TURPE)")
        plot_waterfall(axs[2], taxes_labels, taxes_values, "Taxes et Contributions")

        plt.suptitle(title, fontsize=16, y=0.97)
        plt.tight_layout(rect=[0, 0, 1, 0.93])
        plt.show()


######################Fonctions pour le calcul du TURPE#######################################""
    def calculate_euro_an_CS_fixe(self, coeff, contrat):
        b = coeff.get("b")

        if len(b) < 5:
            self.euro_an_CS_fixe = round(
                b[0] * contrat.PS_HPH +
                b[1] * (contrat.PS_HCH - contrat.PS_HPH) +
                b[2] * (contrat.PS_HPB - contrat.PS_HCH) +
                b[3] * (contrat.PS_HCB - contrat.PS_HPB),
                2
            )
        else:
            self.euro_an_CS_fixe = round(
                b[0] * contrat.PS_pointe +
                b[1] * (contrat.PS_HPH - contrat.PS_pointe) +
                b[2] * (contrat.PS_HCH - contrat.PS_HPH) +
                b[3] * (contrat.PS_HPB - contrat.PS_HCH) +
                b[4] * (contrat.PS_HCB - contrat.PS_HPB), 2)
        
            print("euro_an_CS_fixe =",self.euro_an_CS_fixe," = ",b[0],"*", contrat.PS_pointe,"+",b[1], "* (",contrat.PS_HPH, "-", contrat.PS_pointe,")+",b[2], 
                "* (",contrat.PS_HCH, "-" ,contrat.PS_HPH,") +", b[3], "* (",contrat.PS_HPB, "-" ,contrat.PS_HCH,") +",  b[4], "* (",contrat.PS_HCB, "-" ,contrat.PS_HPB,")"         
                )


    def calculate_euro_CS_variable(self, coeff, facture):
        c = coeff.get("c")

        if len(c) < 5:
            self.euro_CS_variable_HPH = round(c[0] * facture.kWh_HPH, 2)
            self.euro_CS_variable_HCH = round(c[1] * facture.kWh_HCH, 2)
            self.euro_CS_variable_HPB = round(c[2] * facture.kWh_HPB, 2)
            self.euro_CS_variable_HCB = round(c[3] * facture.kWh_HCB, 2)

            self.euro_CS_variable = (
                + self.euro_CS_variable_HPH
                + self.euro_CS_variable_HCH
                + self.euro_CS_variable_HPB
                + self.euro_CS_variable_HCB
            )
        
        else:
            self.euro_CS_variable_pointe = round(c[0] * facture.kWh_pointe, 2)
            self.euro_CS_variable_HPH = round(c[1] * facture.kWh_HPH, 2)
            self.euro_CS_variable_HCH = round(c[2] * facture.kWh_HCH, 2)
            self.euro_CS_variable_HPB = round(c[3] * facture.kWh_HPB, 2)
            self.euro_CS_variable_HCB = round(c[4] * facture.kWh_HCB, 2)

            self.euro_CS_variable = (
                self.euro_CS_variable_pointe
                + self.euro_CS_variable_HPH
                + self.euro_CS_variable_HCH
                + self.euro_CS_variable_HPB
                + self.euro_CS_variable_HCB
            )

            print("euro_CS_variable_pointe = ",self.euro_CS_variable_pointe, " = round(", c[0], " * ", facture.kWh_pointe, ", 2)"        )
            print("euro_CS_variable_HPH = ",self.euro_CS_variable_HPH, " = round(", c[1], " * ", facture.kWh_HPH, ", 2)"        )
            print("euro_CS_variable_HCH = ",self.euro_CS_variable_HCH, " = round(", c[2], " * ", facture.kWh_HCH, ", 2)"        )
            print("euro_CS_variable_HPB = ", self.euro_CS_variable_HPB, " = round(", c[3], " * ", facture.kWh_HPB, ", 2)"        )
            print("euro_CS_variable_HCB = ", self.euro_CS_variable_HCB, " = round(", c[4], " * ", facture.kWh_HCB, ", 2)"        )
            # print("euro_CS_variable = ",self.euro_CS_variable, " = (",
            #     self.euro_CS_variable_pointe,
            #     " + ",
            #     self.euro_CS_variable_HPH,
            #     " + ",
            #     self.euro_CS_variable_HCH,
            #     " + ",
            #     self.euro_CS_variable_HPB,
            #     " + ",
            #     self.euro_CS_variable_HCB,
            #     ")"
            # )

    def calculate_euro_mois_CMDPS(self, coeff, facture):
        b = coeff.get("b")
        sum_delta_P2 = [
            facture.depassement_PS_pointe, facture.depassement_PS_HPH,
            facture.depassement_PS_HCH, facture.depassement_PS_HPB,
            facture.depassement_PS_HCB
        ]
        euro_mois_CMDPS = round(
            sum(b[i] * 0.04 * (sum_delta_P2[i] ** 0.5) for i in range(5)), 2
        )
        #print("euro_mois_CMDPS = ",euro_mois_CMDPS)
        return euro_mois_CMDPS

    def calculate_nb_jour(self):
        if isinstance(self.facture.start, str):
            self.facture.start = parse(self.facture.start).date()
        if isinstance(self.facture.end, str):
            self.facture.end = parse(self.facture.end).date()
        try:
            self.nb_jour = (self.facture.end - self.facture.start).days + 1  # Calculate the number of days between start and end
        except:
            self.nb_jour = 0.0

    def calculate_euro_CS_fixe(self):
        self.calculate_nb_jour()  # Appel de la méthode pour calculer le nombre de jours
        self.euro_CS_fixe = round(self.euro_an_CS_fixe * (self.nb_jour / 365.0), 2)
        #print("euro_CS_fixe = ",self.euro_CS_fixe)

    def calculate_euro_CC(self,coeff):
        self.euro_an_CC = coeff.get("euro_an_CC")
        self.calculate_nb_jour()  # Appel de la méthode pour calculer le nombre de jours
        self.euro_CC = round(self.euro_an_CC * (self.nb_jour / 365.0), 2)
        #print("euro_CC = ",self.euro_CC)

    def calculate_euro_CG(self,coeff):
        self.euro_an_CG = coeff.get("euro_an_CG")
        
        self.calculate_nb_jour()  # Appel de la méthode pour calculer le nombre de jours
        self.euro_CG = round(self.euro_an_CG * (self.nb_jour / 365.0), 2)
        #print("euro_CG = ",self.euro_CG)

    def calculate_euro_TURPE(self):
        self.calculate_nb_jour()  # Appel de la méthode pour calculer le nombre de jours
        # Imprimez les valeurs qui étaient initialement None pour l'utilisateur
        if self.euro_an_CG is None:
            print("euro_an_CG est None.")
        if self.euro_an_CC is None:
            print("euro_an_CC est None.")
        if self.euro_an_CS_fixe is None:
            print("euro_an_CS_fixe est None.")
        if self.euro_CS_variable is None:
            print("euro_CS_variable est None.")
        if self.euro_mois_CMDPS is None:
            print("euro_mois_CMDPS est None.")
        if self.euro_an_CACS is None:
            print("euro_an_CACS est None.")
        if self.euro_an_CR is None:
            print("euro_an_CR est None.")
        if self.euro_an_CER is None:
            print("euro_an_CER est None.")
        if self.euro_an_CI is None:
            print("euro_an_CI est None.")
        if self.nb_jour is None:
            print("nb_jour est None.")

        # Assurez-vous que toutes les valeurs sont définies ou mises à 0 si elles sont None
        self.euro_an_CG = self.euro_an_CG if self.euro_an_CG is not None else 0
        self.euro_an_CC = self.euro_an_CC if self.euro_an_CC is not None else 0
        self.euro_an_CS_fixe = self.euro_an_CS_fixe if self.euro_an_CS_fixe is not None else 0
        self.euro_CS_variable = self.euro_CS_variable if self.euro_CS_variable is not None else 0
        self.euro_mois_CMDPS = self.euro_mois_CMDPS if self.euro_mois_CMDPS is not None else 0
        self.euro_an_CACS = self.euro_an_CACS if self.euro_an_CACS is not None else 0
        self.euro_an_CR = self.euro_an_CR if self.euro_an_CR is not None else 0
        self.euro_an_CER = self.euro_an_CER if self.euro_an_CER is not None else 0
        self.euro_an_CI = self.euro_an_CI if self.euro_an_CI is not None else 0
        self.nb_jour = self.nb_jour if self.nb_jour is not None else 0

        try:
            self.euro_TURPE= round(self.euro_an_CG * (self.nb_jour / 365.0) + self.euro_an_CC * (self.nb_jour / 365.0) + self.euro_an_CS_fixe * (self.nb_jour / 365.0) + self.euro_CS_variable + self.euro_mois_CMDPS + self.euro_an_CACS * (self.nb_jour / 365.0) + self.euro_an_CR * (self.nb_jour / 365.0) + self.euro_an_CER * (self.nb_jour / 365.0) + self.euro_an_CI * (self.nb_jour / 365.0), 2)
        except:
            self.euro_TURPE = None
        #print("euro_TURPE = ",self.euro_TURPE)
    
    def calculate_euro_an_TURPE(self):
        try:
            self.euro_an_TURPE=round(self.euro_an_CG+self.euro_an_CC+self.euro_an_CS_fixe+12*self.euro_CS_variable+12*self.euro_mois_CMDPS+self.euro_an_CACS+self.euro_an_CR+self.euro_an_CER+self.euro_an_CI,2) #à modifier pour trater le cas de self.euro_mois_CMDPS
            
        except:
            self.euro_an_TURPE=None

    def calculate_euro_CACS(self, coeff):
        euro_cellules = coeff.get("euro_cellules")
        euro_km_aerien = coeff.get("euro_km_aerien")
        euro_km_souterrain = coeff.get("euro_km_souterrain")
        self.euro_an_CACS = round(
            euro_cellules * self.contrat.nb_cellules_secours +
            euro_km_aerien * self.contrat.km_secours_aerien +
            euro_km_souterrain * self.contrat.km_secours_souterrain, 2
        )
        self.euro_CACS= round(self.euro_an_CACS * (self.nb_jour / 365.0), 2)
        # print("euro_CACS = ",self.euro_CACS)
        # print("euro_an_CACS = ",self.euro_an_CACS)

    def calculate_euro_CTA(self,coeff):
        coef_CTA = coeff.get("coef_CTA")
        self.calculate_nb_jour()  # Appel de la méthode pour calculer le nombre de jours
        #print(coef_CTA)
        # euro éligible au CTA
        self.euro_eligible_CTA =(self.euro_CC + self.euro_CS_fixe + self.euro_CG+self.euro_CACS)
        self.euro_CTA = round(self.euro_eligible_CTA * coef_CTA, 6)
        #print("euro_CTA = ",self.euro_CTA)
        self.euro_an_CTA = round(self.euro_CTA /self.nb_jour*365, 2)
    
    def calculate_euro_CSPE_TICFE(self,coeff):
        c_euro_kwh_CSPE_TICFE = coeff.get("c_euro_kwh_CSPE_TICFE")
        self.euro_CSPE_TICFE = round(self.kWh_Total * c_euro_kwh_CSPE_TICFE, 2)
        #print("euro_CSPE_TICFE",self.euro_CSPE_TICFE)

    # def calculate_euro_total(self):
    #     self.calculate_nb_jour()  # Appel de la méthode pour calculer le nombre de jours
    #     try:
    #         self.euro_total = round(self.euro_HPB + self.euro_HCB + self.euro_HPH + self.euro_HCH + self.euro_pointe + self.euro_ENR + self.euro_ARENH + self.euro_TURPE + self.euro_CTA + self.euro_CSPE_TICFE + self.euro_CSPE_TICFE + self.euro_capacite_pointe + self.euro_capacite_HPH, 2)
    #     except:
    #         self.euro_total = None
    #     print("euro_total = ",self.euro_total)

    def calculate_montant(self, coeff):

        # self.kWh_Total = self.facture.kWh_HPH + self.facture.kWh_HCH + self.facture.kWh_HPB + self.facture.kWh_HCB + self.facture.kWh_pointe

        self.kWh_ENR = (self.contrat.pourcentage_ENR / 100) * self.kWh_Total if self.contrat.pourcentage_ENR and self.kWh_Total else 0.0
        #print("kWh_ENR = ",self.kWh_ENR," = ","(",self.contrat.pourcentage_ENR," / 100) * ",self.kWh_Total)
        self.euro_pointe = round(self.facture.kWh_pointe * self.tarif.c_euro_kWh_pointe, 2)
        #print("euro_pointe = ",self.euro_pointe)
        self.euro_HPB = round(self.facture.kWh_HPB * self.tarif.c_euro_kWh_HPB, 2)
        #print("euro_HPB = ",self.euro_HPB)
        self.euro_HCB = round(self.facture.kWh_HCB * self.tarif.c_euro_kWh_HCB, 2)
        #print("euro_HCB = ",self.euro_HCB)
        self.euro_HPH = round(self.facture.kWh_HPH * self.tarif.c_euro_kWh_HPH, 2)
        #print("euro_HPH = ",self.euro_HPH)
        self.euro_HCH = round(self.facture.kWh_HCH * self.tarif.c_euro_kWh_HCH, 2)
        #print("euro_HCH = ",self.euro_HCH)

        if self.tarif.c_euro_kwh_CSPE_TICFE is None:
            self.tarif.c_euro_kwh_CSPE_TICFE=coeff.get("c_euro_kwh_CSPE_TICFE")

        self.euro_CSPE_TICFE = round(self.kWh_Total * self.tarif.c_euro_kwh_CSPE_TICFE, 2)
        self.euro_an_CSPE_TICFE = round(self.euro_CSPE_TICFE / self.nb_jour * 365, 2) if self.nb_jour else None
        #print("euro_CSPE_TICFE = ",self.euro_CSPE_TICFE)
        try:
            self.euro_capacite_pointe = round(self.facture.kWh_pointe * self.tarif.c_euro_kWh_certif_capacite_pointe, 2)
            #print("euro_capacite_pointe = ",self.euro_capacite_pointe)
        except:
            pass
        self.euro_capacite_HPH = round(self.facture.kWh_HPH * self.tarif.c_euro_kWh_certif_capacite_HPH, 2)
        #print("euro_capacite_HPH = ",self.euro_capacite_HPH)
        self.euro_capacite_HCH = round(self.facture.kWh_HCH * self.tarif.c_euro_kWh_certif_capacite_HCH, 2)
        #print("euro_capacite_HCH = ",self.euro_capacite_HCH)
        self.euro_capacite_HPB = round(self.facture.kWh_HPB * self.tarif.c_euro_kWh_certif_capacite_HPB, 2)
        #print("euro_capacite_HPB = ",self.euro_capacite_HPB)
        self.euro_capacite_HCB = round(self.facture.kWh_HCB * self.tarif.c_euro_kWh_certif_capacite_HCB, 2)
        #print("euro_capacite_HCB = ",self.euro_capacite_HCB)

        self.euro_capacite = (self.euro_capacite_pointe + self.euro_capacite_HPH + self.euro_capacite_HCH + self.euro_capacite_HPB + self.euro_capacite_HCB)
        #print("euro_capacite = ",self.euro_capacite)
        self.euro_ENR = 0 if (self.kWh_Total is None or self.tarif.c_euro_kWh_ENR is None) else round(self.kWh_Total * self.tarif.c_euro_kWh_ENR, 2)
        # self.euro_ENR = round(self.kWh_Total * self.tarif.c_euro_kWh_ENR, 2)
        #print("euro_ENR = ",self.euro_ENR)
        self.euro_ARENH = round(self.kWh_Total * self.tarif.c_euro_kWh_ARENH, 2)
        #print("euro_ARENH  = ",self.euro_ARENH)
        self.euro_abonnement= self.contrat.abonnement_annuel/365* self.nb_jour if self.contrat.abonnement_annuel and self.nb_jour else 0.0
        #print("euro_abonnement = ",self.euro_abonnement)
        self.euro_fourniture = round(self.euro_HPB + self.euro_HCB + self.euro_HPH + self.euro_HCH + self.euro_pointe + self.euro_ENR + self.euro_ARENH+self.euro_capacite+self.euro_abonnement, 2)
        #print("euro_fourniture  = ",self.euro_fourniture)

        try:
            #self.euro_an_TURPE = round(self.euro_an_CG + self.euro_an_CC + self.euro_an_CS_fixe + 12 * self.euro_CS_variable + 12 * self.euro_mois_CMDPS + self.euro_an_CACS + self.euro_an_CR + self.euro_an_CER + self.euro_an_CI, 2)
            self.euro_an_TURPE=self.euro_an_CG+self.euro_an_CC+self.euro_an_CS_fixe+self.euro_CS_variable
        except:
            self.euro_an_TURPE = None
        #print("euro_an_TURPE = ",self.euro_an_TURPE)

        try: 
            self.euro_total = round(self.euro_HPB + self.euro_HCB + self.euro_HPH + self.euro_HCH + self.euro_pointe + self.euro_ENR + self.euro_ARENH + self.euro_TURPE + self.euro_CTA + self.euro_CSPE_TICFE + self.euro_capacite_pointe + self.euro_capacite_HPH, 2)
        except:
            self.euro_total = None
        #print(self.euro_HPB ,"+", self.euro_HCB ,"+", self.euro_HPH ,"+", self.euro_HCH ,"+", self.euro_pointe ,"+", self.euro_ENR ,"+", self.euro_ARENH ,"+", self.euro_TURPE ,"+", self.euro_CTA ,"+", self.euro_CSPE_TICFE ,"+", self.euro_capacite_pointe ,"+", self.euro_capacite_HPH)
        #print("euro_total = ",self.euro_total)


   
