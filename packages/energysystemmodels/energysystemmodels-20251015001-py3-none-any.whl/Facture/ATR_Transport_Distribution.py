from datetime import date
import json
import os
from dateutil.parser import parse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

current_directory = os.path.dirname(os.path.abspath(__file__))
coeffs_atrd_path = os.path.join(current_directory, 'coefficients_gaz_ATRD.json')
coeffs_atrt_path = os.path.join(current_directory, 'coefficients_gaz_ATRT.json')
coeffs_ticgn_path = os.path.join(current_directory, 'coefficients_gaz_TICGN.json')

class input_Facture:
    def __init__(self, start, end, kWh_total=0):
        if not isinstance(start, date):
            start = parse(start).date()
        if not isinstance(end, date):
            end = parse(end).date()
        self.start = start
        self.end = end
        self.kWh_total = kWh_total

class input_Tarif:
    def __init__(self, prix_kWh=0.0, abonnement_annuel_fournisseur=0.0, distribution_cta_rate=0.0771, ticgn_rate=0.00837):
        self.prix_kWh = prix_kWh
        self.abonnement_annuel_fournisseur = abonnement_annuel_fournisseur
        self.distribution_cta_rate = distribution_cta_rate
        self.ticgn_rate = ticgn_rate

class input_Contrat:
    def __init__(self, type_tarif_acheminement='T1',CJA_MWh_j=0,CJN_MWh_j=None,modulation_MWh_j=None,CAR_MWh=0,station_meteo="PARIS-MONTSOURIS",profil="P016",reseau_transport="GRTgaz",niv_tarif_region=2, distance=None):
        self.type_tarif_acheminement = type_tarif_acheminement
        self.profil=profil
     
        self.distance = distance  # en km
        self.CJA_MWh_j=CJA_MWh_j #Capacité Journalière Annualisée
        self.CJN_MWh_j=CJN_MWh_j  # Capacité Journalière Normalisée (CJN) en MWh
        self.modulation_MWh_j = modulation_MWh_j  # Modulation journalière en MWh
        self.CAR_MWh=CAR_MWh  # Capacité Annuelle Réservée en MWh
        self.station_meteo = station_meteo  # Station météo pour le calcul des coefficients
        self.niv_tarif_region = niv_tarif_region  # Niveau tarifaire de la région (1, 2 ou 3)
        self.reseau_transport = reseau_transport  # Réseau de transport (GRTgaz ou Terega)  

def find_ticgn_rate(facture):
    with open(coeffs_ticgn_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for coef in data["coefficients"]:
        if parse(coef["start_date"]).date() <= facture.start <= parse(coef["end_date"]).date():
            return coef["ticgn_rate"]
    raise ValueError("Aucun taux TICGN trouvé pour cette période.")      

def find_atrd_coeff(contrat, facture):
    with open(coeffs_atrd_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for coef in data["coefficients"]:
        if (
            coef["type_tarif_acheminement"] == contrat.type_tarif_acheminement
            and parse(coef["start_date"]).date() <= facture.start <= parse(coef["end_date"]).date()
        ):
            return coef
    raise ValueError("Aucun coefficient ATRD trouvé pour cette période et ce type de tarif.")

def find_atrt_coeff(contrat, facture):
    with open(coeffs_atrt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for coef in data["coefficients"]:
        if (
            "start_date" in coef and "end_date" in coef
            and parse(coef["start_date"]).date() <= facture.start <= parse(coef["end_date"]).date()
        ):
            # Recherche du coefficient Zi
            station = getattr(contrat, "station_meteo", None)
            profil = getattr(contrat, "profil", None)
            zi_value = None
            for zi in coef.get("coefficient_zi", []):
                if zi.get("station_meteo") == station and profil in zi:
                    zi_value = zi[profil]
                    break
            if zi_value is None:
                raise ValueError(f"Pas de coefficient Zi pour la station {station} et le profil {profil}.")
            return coef, zi_value
    raise ValueError("Aucun coefficient ATRT trouvé pour cette période.")

def calcul_prix_molecule_gaz(facture, tarif):
    """
    Calcule le prix de la molécule de gaz (part fournisseur) en euros.
    :param facture: instance de input_Facture
    :param tarif: instance de input_Tarif (prix_kWh doit être renseigné)
    :return: montant en euros
    """
    return round(facture.kWh_total * tarif.prix_kWh, 2)





class ATR_calculation:
    """Calcul simultané de la part distribution (ATRD) et transport (ATRT) pour le gaz naturel."""

    def __init__(self, contrat, facture, tarif=None):
        self.contrat = contrat
        self.facture = facture
        self.tarif = tarif
        self.nb_jour = (self.facture.end - self.facture.start).days + 1

        # --- ATRD ---
        self.coeff_atrd = find_atrd_coeff(contrat, facture)
        self.euro_molecule_gaz = 0.0
        self.euro_terme_distance = 0.0
        self.euro_CTA = 0.0
        self.euro_an_CTA = 0.0
        self.euro_TICGN = 0.0
        self.euro_total_HTVA = 0.0
        self.euro_total_TTC = 0.0
        self.taxes_contributions = 0.0
        self.euro_ATRD_fixe_hors_capacite= 0.0
        self.euro_ATRD_variable = 0.0
        self.euro_ATRD_souscript_capa_CJA = 0.0
        self.euro_ATRD_fixe_total = 0.0
        self.euro_an_ATRD_souscript_capa_CJA = 0.0
        self.euro_ATRD_fixe_hors_capacite = 0.0
        self.euro_an_ATRD_fixe_total = 0.0
        self.euro_an_ATRD_variable = 0.0
        self.euro_an_ATRD_total = 0.0

        # --- ATRT ---
        self.coeff_atrt, self.zi = find_atrt_coeff(contrat, facture)
        self.coef_A_GRTgaz = self.coeff_atrt.get("coef_A_GRTgaz", 1.0)
        self.coef_A_Terega = self.coeff_atrt.get("coef_A_Terega", 1.0)
        self.coef_A = None
        self.modulation_hivernale = 0.0
        self.TCS = 0.0
        self.TCR = 0.0
        self.TCL = 0.0
        self.NTR = 0.0
        self.euro_fixe_transport = 0.0
        self.euro_variable_transport = 0.0
        self.euro_an_compensation_stockage = 0.0
        self.euro_an_ATRT_TCS = 0.0
        self.euro_an_ATRT_TCR = 0.0
        self.euro_an_ATRT_TCL = 0.0
        self.euro_an_total_ATRT = 0.0
        self.euro_ATRT_compensation_stockage = 0.0
        self.euro_ATRT_TCS = 0.0
        self.euro_ATRT_TCR = 0.0
        self.euro_ATRT_TCL = 0.0
        self.euro_total_ATRT = 0.0

        self.df = pd.DataFrame(columns=["Composante", "Montant (€)"])
        self.df_transport = pd.DataFrame(columns=["Composante", "Montant (€)"])
        self.df_distribution = pd.DataFrame(columns=["Composante", "Montant (€)"])
        self.df_taxes_contributions = pd.DataFrame(columns=["Composante", "Montant (€)"])
        self.df_molecule = pd.DataFrame(columns=["Composante", "Montant (€)"])
        self.df_annuel = pd.DataFrame(columns=["Composante", "Montant (€)"])


    def calculate(self):
        if self.contrat.reseau_transport == "GRTgaz":
            self.coef_A = self.coef_A_GRTgaz
            self.TCR = self.coeff_atrt.get("TCR_GRTgaz", 0.0)
            self.TCL = self.coeff_atrt.get("TCL_GRTgaz", 0.0)
        elif self.contrat.reseau_transport == "Terega":
            self.coef_A = self.coef_A_Terega
            self.TCR = self.coeff_atrt.get("TCR_Terega", 0.0)
            self.TCL = self.coeff_atrt.get("TCL_Terega", 0.0)
        else:
            self.coef_A = 1
        
        
        if self.contrat.CAR_MWh is not None and self.contrat.CAR_MWh > 0 and self.contrat.CJN_MWh_j is None:
            self.CJN_MWh_j = self.contrat.CAR_MWh * self.zi * self.coef_A
        else:
            self.CJN_MWh_j = self.contrat.CJN_MWh_j if self.contrat.CJN_MWh_j is not None else 0.0




        self.euro_an_ATRD_fixe_hors_capacite = self.coeff_atrd["ATRD_fixe"]
        #print("self.euro_an_ATRD_fixe_hors_capacite", self.euro_an_ATRD_fixe_hors_capacite)

        if self.nb_jour>31:
            self.euro_ATRD_fixe_hors_capacite = round(self.euro_an_ATRD_fixe_hors_capacite * self.nb_jour / 365.0, 2)
        else:
            self.euro_ATRD_fixe_hors_capacite= round(self.euro_an_ATRD_fixe_hors_capacite / 12, 2)  # Mensuel


        self.euro_an_ATRD_variable = self.coeff_atrd["prix_proportionnel_euro_kWh"] * self.facture.kWh_total

        if self.contrat.type_tarif_acheminement in ["T1", "T2", "T3"]:
            self.euro_terme_distance = 0.0
            self.euro_cta_base = self.euro_ATRD_fixe_hors_capacite
            self.euro_an_cta_base = self.euro_an_ATRD_fixe_total
            self.euro_an_ATRD_souscript_capa_CJA = 0.0
            self.euro_an_ATRD_fixe_total = self.euro_an_ATRD_fixe_hors_capacite
            self.euro_ATRD_souscript_capa_CJA = 0.0
        elif self.contrat.type_tarif_acheminement == "T4":
            #CJN_MWh_j = self.contrat.CJN_MWh_j or 0
            if self.CJN_MWh_j > 500:
                tarif_capacite = self.coeff_atrd["souscription_annuelle_capacite_euro_kWh_j_supp500"]
            else:
                tarif_capacite = self.coeff_atrd["souscription_annuelle_capacite_euro_kWh_j_inf500"]
            self.euro_an_ATRD_souscript_capa_CJA = round(self.CJN_MWh_j * 1000 * tarif_capacite, 2)
            self.euro_an_ATRD_fixe_total = self.euro_an_ATRD_fixe_hors_capacite + self.euro_an_ATRD_souscript_capa_CJA
            
            if self.nb_jour>31:
                self.euro_ATRD_souscript_capa_CJA = round(self.euro_an_ATRD_souscript_capa_CJA * self.nb_jour / 365.0, 2)
                self.euro_ATRD_fixe_total = round(self.euro_an_ATRD_fixe_total * self.nb_jour / 365.0, 2)
            else:
                self.euro_ATRD_souscript_capa_CJA=round(self.euro_an_ATRD_souscript_capa_CJA / 12, 2)  # Mensuel
                self.euro_ATRD_fixe_total=round(self.euro_an_ATRD_fixe_total / 12, 2)  # Mensuel

            self.euro_terme_distance = 0.0
            self.euro_cta_base = self.euro_ATRD_fixe_hors_capacite
            self.euro_an_cta_base = self.euro_an_ATRD_fixe_total
        elif self.contrat.type_tarif_acheminement == "TP":
            self.CJN_MWh_j = self.contrat.CJN_MWh_j or 0
            dist = self.contrat.distance or 0
            tarif_capacite = self.coeff_atrd["tarif_capacite"]
            tarif_distance = self.coeff_atrd["tarif_distance"]
            self.euro_an_ATRD_souscript_capa_CJA = round(self.CJN_MWh_j * tarif_capacite * self.nb_jour, 2)
            self.euro_terme_distance = round(dist * (tarif_distance / 365) * self.nb_jour, 2)
            self.euro_an_ATRD_fixe_total = self.euro_an_ATRD_fixe_total + self.euro_an_ATRD_souscript_capa_CJA
            self.euro_cta_base = self.euro_ATRD_fixe_hors_capacite + self.euro_terme_distance
            self.euro_an_cta_base = self.euro_an_ATRD_fixe_total + self.euro_terme_distance
        else:
            raise ValueError("Type de tarif inconnu")

        if self.tarif is not None:
            self.euro_molecule_gaz = round(self.facture.kWh_total * self.tarif.prix_kWh, 2)

        self.euro_an_ATRD_total = self.euro_an_ATRD_fixe_total + self.euro_an_ATRD_variable
        self.euro_ATRD_variable = round(self.coeff_atrd["prix_proportionnel_euro_kWh"] * self.facture.kWh_total, 2)
        self.euro_ATRD_total = round(self.euro_ATRD_fixe_total + self.euro_ATRD_variable, 2)

        self.ticgn_rate = find_ticgn_rate(self.facture)
        print("TICGN Rate:", self.ticgn_rate)
        self.euro_TICGN = round(self.facture.kWh_total * self.ticgn_rate, 2)

    
       
        

        # --- ATRT ---
 

               #Modulation Hivernale = Capacité de transport – (CAR/365)
        #print("self.modulation_MWh_j", self.contrat.modulation_MWh_j)
        if self.contrat.modulation_MWh_j is None:
            self.modulation_hivernale = self.CJN_MWh_j - (self.contrat.CAR_MWh / 365.0) if self.contrat.CAR_MWh else 0.0
            #self.modulation_hivernale = self.CJN_MWh_j - (self.contrat.CAR_MWh / 365.0) if self.contrat.CAR_MWh else 0.0
        else:
            self.modulation_hivernale=self.contrat.modulation_MWh_j

        #print("self.modulation_hivernale", self.modulation_hivernale)
        
        
        self.TCS = self.coeff_atrt["TCS"]
        self.NTR = self.contrat.niv_tarif_region
        self.coef_stockage = self.coeff_atrt.get("coef_compensation_stockage", 0)
        self.euro_an_compensation_stockage = round(self.modulation_hivernale * self.coef_stockage, 2) if self.modulation_hivernale else 0.0
        #print("self.euro_an_compensation_stockage=", self.modulation_hivernale, "*", self.coef_stockage, "=", self.euro_an_compensation_stockage)
        
        self.euro_an_ATRT_TCS = self.CJN_MWh_j * self.TCS
        self.euro_an_ATRT_TCR = self.CJN_MWh_j * (self.TCR * self.NTR)
        self.euro_an_ATRT_TCL = self.CJN_MWh_j * self.TCL
        self.euro_MWh_ATRT=self.TCS+(self.TCR * self.NTR)+self.TCL
        self.euro_MWh_mois_ATRT=self.euro_MWh_ATRT/12
        #print("self.euro_MWh_ATRT",self.euro_MWh_ATRT)
        #print("self.euro_MWh_mois_ATRT",self.euro_MWh_mois_ATRT)
        self.euro_an_total_ATRT = self.euro_an_ATRT_TCS + self.euro_an_ATRT_TCR + self.euro_an_ATRT_TCL + self.euro_an_compensation_stockage
        self.euro_an_total_ATRT_hors_compensation = self.euro_an_ATRT_TCS + self.euro_an_ATRT_TCR + self.euro_an_ATRT_TCL
        #self.euro_ATRT_compensation_stockage = self.euro_an_compensation_stockage * self.nb_jour / 365.0 if self.euro_an_compensation_stockage else 0.0
        self.euro_ATRT_compensation_stockage = round(self.euro_an_compensation_stockage /12,2) if self.euro_an_compensation_stockage else 0.0
        
        if self.nb_jour>31:
            self.euro_ATRT_TCS = self.euro_an_ATRT_TCS * self.nb_jour / 365.0 if self.euro_an_ATRT_TCS else 0.0
            self.euro_ATRT_TCR = self.euro_an_ATRT_TCR * self.nb_jour / 365.0 if self.euro_an_ATRT_TCR else 0.0
            self.euro_ATRT_TCL = self.euro_an_ATRT_TCL * self.nb_jour / 365.0 if self.euro_an_ATRT_TCL else 0.0
        
        else:
            self.euro_ATRT_TCS = self.euro_an_ATRT_TCS/12 if self.euro_an_ATRT_TCS else 0.0
            self.euro_ATRT_TCR = self.euro_an_ATRT_TCR/12 if self.euro_an_ATRT_TCR else 0.0
            self.euro_ATRT_TCL = self.euro_an_ATRT_TCL/12 if self.euro_an_ATRT_TCL else 0.0

        self.euro_total_ATRT = self.euro_ATRT_TCS + self.euro_ATRT_TCR + self.euro_ATRT_TCL + self.euro_ATRT_compensation_stockage
        self.euro_total_ATRT_hors_compensation = round(self.euro_ATRT_TCS + self.euro_ATRT_TCR + self.euro_ATRT_TCL,2)
        #Formule : CTA = [Quote-part distribution] × (20,80 % + [Coefficient] × 4,71 %).
        #    "distribution_cta_rate": 0.2080,
        #   "transport_cta_rate": 0.0471,
        #   "coefficient_proportionnalite_cta":83.21,

        self.euro_an_CTA = round(self.euro_an_ATRD_fixe_total * (self.coeff_atrd["distribution_cta_rate"]+self.coeff_atrd["coefficient_proportionnalite_cta"]*self.coeff_atrd["transport_cta_rate"]), 2) #corriger
        
        if self.nb_jour>31:
            self.euro_CTA = self.euro_an_CTA * self.nb_jour / 365.
        else:
            self.euro_CTA = round(self.euro_an_CTA / 12, 3)  # Mensuel

        self.taxes_contributions = round(self.euro_CTA + self.euro_TICGN, 2)

        self.euro_acheminement_transport_distribution = self.euro_total_ATRT_hors_compensation + self.euro_ATRT_compensation_stockage+ self.euro_ATRD_fixe_hors_capacite+self.euro_ATRD_souscript_capa_CJA+self.euro_ATRD_variable
     
        self.euro_total_HTVA = round(
            self.euro_acheminement_transport_distribution+
            self.euro_molecule_gaz+
            self.taxes_contributions, 2
        )

        self.euro_TVA_5_5 = round((self.euro_total_ATRT_hors_compensation +
            self.euro_ATRT_compensation_stockage+
                                   
            self.euro_ATRD_fixe_hors_capacite 
            +self.euro_ATRD_souscript_capa_CJA
            + self.euro_CTA) * 0.055, 2)

        self.euro_TVA_20 = round((self.euro_ATRD_variable 
                                  + self.euro_molecule_gaz 
                                  + self.euro_TICGN
                                  ) * 0.20, 2)
        
        self.euro_TVA = self.euro_TVA_5_5 + self.euro_TVA_20
        self.euro_total_TTC = round(self.euro_total_HTVA + self.euro_TVA, 2)

        self.cout_variable_ATRD_euro_par_MWh=round(self.euro_ATRD_variable / (self.facture.kWh_total / 1000),2) if self.facture.kWh_total else 0
        self.cout_TICGN_euro_par_MWh=round(self.euro_TICGN / (self.facture.kWh_total / 1000),2) if self.facture.kWh_total else 0
        self.cout_variable_ATRD_plus_TICGN_euro_par_MWh=round(self.cout_variable_ATRD_euro_par_MWh + self.cout_TICGN_euro_par_MWh,2)
        self.cout_molecule_gaz_euro_par_MWh = round(self.euro_molecule_gaz / (self.facture.kWh_total / 1000),2) if self.facture.kWh_total else 0
        self.cout_euro_HTVA_par_MWh =round(self.euro_total_HTVA / (self.facture.kWh_total / 1000),2) if self.facture.kWh_total else 0
        # print("cout_variable_ATRD_euro_par_MWh", self.cout_variable_ATRD_euro_par_MWh)
        # print("cout_TICGN_euro_par_MWh", self.cout_TICGN_euro_par_MWh)
        # print("cout_molecule_gaz_euro_par_MWh", self.cout_molecule_gaz_euro_par_MWh)
        # print("cout_variable_ATRD_plus_TICGN_euro_par_MWh", self.cout_variable_ATRD_plus_TICGN_euro_par_MWh)
        # print("cout_euro_HTVA_par_MWh", self.cout_euro_HTVA_par_MWh)
         
        

        self.resume_all()

    def resume_all(self):
        import pandas as pd
        self.df_euro_MWh=pd.DataFrame([
            ("Cout variable ATRD (€ par MWh) : ", self.cout_variable_ATRD_euro_par_MWh),
            ("Cout TICGN (€ par MWh) : ", self.cout_TICGN_euro_par_MWh),
            ("Cout variable ATRD + TICGN (€ par MWh) : ", self.cout_variable_ATRD_plus_TICGN_euro_par_MWh),
            ("Cout de la molécule de gaz (€ par MWh) : ", self.cout_molecule_gaz_euro_par_MWh),
            ("Cout HTVA (€ par MWh) : ", self.cout_euro_HTVA_par_MWh),
        ], columns=["Composante", "Montant (€)"])

        self.df=pd.DataFrame([
            ("self.euro_acheminement_transport_distribution (€/mois) : ", self.euro_acheminement_transport_distribution),
            
            ("-ATRD mensuel total (€/mois) : ", self.euro_ATRD_total),
            ("-Total ATRT (€/mois)", self.euro_total_ATRT),

            ("Prix de la molécule de gaz (€) : ", self.euro_molecule_gaz),
            ("Taxes et contributions (€) : ", self.taxes_contributions),

            ("Total HTVA (€) : ", self.euro_total_HTVA),
            ("TVA 5,5% (€) : ", self.euro_TVA_5_5),
            ("TVA 20% (€) : ", self.euro_TVA_20),
            ("Total TVA (€) : ", self.euro_TVA),
            ("Total TTC (€) : ", self.euro_total_TTC),
            
        ], columns=["Composante", "Montant (€)"])

        #self.df_transport = pd.DataFrame(columns=["Composante", "Montant (€)"])
        #mois
        self.df_transport=pd.DataFrame([
                ("Total ATRT (€/mois)", self.euro_total_ATRT),
                ("-ATRT - Réseau principal (€/mois)", self.euro_ATRT_TCS),
                ("-ATRT - Réseau régional (€/mois)", self.euro_ATRT_TCR),
                ("-ATRT - Souscription de capacité journalière de livraison (€/mois)", self.euro_ATRT_TCL),
                ("ATRT_hors_compensation (€/mois)", self.euro_total_ATRT_hors_compensation),
                ("-ATRT - Compensation stockage (€/mois)", self.euro_ATRT_compensation_stockage),
                
             
               
            ], columns=["Composantes ATRT", "Montant (€)"])


        #self.df_distribution = pd.DataFrame(columns=["Composante", "Montant (€)"])
        #mois
        self.df_distribution=pd.DataFrame([
                ("ATRD fixe total (€/mois)", self.euro_ATRD_fixe_total),
                ("- ATRD fixe (€/mois)-hors souscrip cap.", self.euro_ATRD_fixe_hors_capacite),
                ("- ATRD Souscription de capacité  (€/mois)", self.euro_ATRD_souscript_capa_CJA),
                ("- ATRD variable (€/mois)", self.euro_ATRD_variable),
            ], columns=["Composante", "Montant (€)"])
        

        #self.df_taxes_contributions = pd.DataFrame(columns=["Composante", "Montant (€)"])
        #mois
        self.df_taxes_contributions=pd.DataFrame([
                ("Taxes et contributions (€)", self.taxes_contributions),
                ("- CTA (€)", self.euro_CTA),
                ("- TICGN (€)", self.euro_TICGN),
            ], columns=["Composante", "Montant (€)"])
        
        #self.df_molecule = pd.DataFrame(columns=["Composante", "Montant (€)"])
        #mois
        self.df_molecule=pd.DataFrame([
                ("Prix de la molécule de gaz (€)", self.euro_molecule_gaz),
            ], columns=["Composante", "Montant (€)"])
        #self.df_annuel = pd.DataFrame(columns=["Composante", "Montant (€)"])
        #annuel
        self.df_annuel=pd.DataFrame([
             ("self.euro_an_total_ATRT (€/an)", self.euro_an_total_ATRT),
            ("ATRT - Compensation stockage (€/an)", self.euro_an_compensation_stockage),
            ("total_ATRT_hors_compensation (€/an)", self.euro_an_total_ATRT_hors_compensation),
            ('ATRD_fixe_hors_capacite hors capacite" (€/an)', self.euro_an_ATRD_fixe_hors_capacite),

                ("ATRD total (€/an)", self.euro_an_ATRD_total),
                ("ARTD stockage annuel (€/an)", self.euro_an_compensation_stockage),
                ("ATRD fixe (€/an)", self.euro_an_ATRD_fixe_total),
                ("ATRD variable (€/an)", self.euro_an_ATRD_variable),
                ("CTA annuel (€)", self.euro_an_CTA),
                ("TICGN annuel (€)", self.euro_TICGN),
                ("Total HTVA (€)", self.euro_total_HTVA),
                ("TVA 5,5% (€)", self.euro_TVA_5_5),
                ("TVA 20% (€)", self.euro_TVA_20),
                ("Total TVA (€)", self.euro_TVA),
                ("Total TTC (€)", self.euro_total_TTC),
            ], columns=["Composantes annuelles", "Montant (€)"])
      
     
    def plot(self, title="Facture Gaz : les composantes principales", figsize=(8, 6)):
        """Affiche un donut plot de la répartition ATRD/ATRT/Taxes."""
        labels = ['Acheminement (Distribution et Transport)', 'Consommation de gaz (Fournisseur)','Taxes et Contributions']
        values = [self.euro_ATRD_total+self.euro_total_ATRT, self.euro_molecule_gaz,self.taxes_contributions ]
        colors = ['#4CAF50', '#FFC107', '#FF5722']

        total = sum(values)
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
        ax.text(0, 0, f"{total:,.2f} €", ha='center', va='center', fontsize=14, fontweight='bold')

        # Légende
        y_start = -0.05
        y_step = 0.07
        x_rect = -0.12
        x_text = -0.05
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


    def plot_detail(self, title="Détail des Composantes de la Facture Gaz (ATRD/ATRT/Taxes et Contributions)", figsize=(16, 6)):
        # Vérification des données nécessaires
        necessary_attrs = [
            'euro_ATRD_fixe_hors_capacite', 'euro_ATRD_souscript_capa_CJA', 'euro_ATRD_variable',
            'euro_ATRT_TCS', 'euro_ATRT_TCR', 'euro_ATRT_TCL', 'euro_ATRT_compensation_stockage',
            'euro_CTA', 'euro_TICGN'
        ]
        for attr in necessary_attrs:
            if getattr(self, attr, None) is None:
                print(f"Attribut {attr} non défini.")
                return

        # === Distribution (ATRD) ===
        atrd_labels = ['Fixe (hors capacité)', 'Souscription capacité', 'Variable']
        atrd_values = [
            self.euro_ATRD_fixe_hors_capacite,
            self.euro_ATRD_souscript_capa_CJA,
            self.euro_ATRD_variable
        ]

        # === Transport (ATRT) ===
        atrt_labels = ['Réseau principal TCS', 'Régional TCR', 'Capacité livraison TCL', 'Compensation stockage TS']
        atrt_values = [
            self.euro_ATRT_TCS,
            self.euro_ATRT_TCR,
            self.euro_ATRT_TCL,
            self.euro_ATRT_compensation_stockage
        ]

        # === Taxes et Contributions ===
        taxes_labels = ['CTA', 'TICGN']
        taxes_values = [
            self.euro_CTA,
            self.euro_TICGN
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
        plot_waterfall(axs[0], atrd_labels, atrd_values, "Distribution (ATRD)")
        plot_waterfall(axs[1], atrt_labels, atrt_values, "Transport (ATRT)")
        plot_waterfall(axs[2], taxes_labels, taxes_values, "Taxes et Contributions")

        plt.suptitle(title, fontsize=16, y=0.97)
        plt.tight_layout(rect=[0, 0, 1, 0.93])
        plt.show()

    def plot_euro_MWh(self, title="Décomposition du coût en €/MWh (HTVA)", figsize=(8, 6)):
        labels = [
            "Variable ATRD (€/MWh)",
            "TICGN (€/MWh)",
            "Molécule gaz (€/MWh)",
            "Total HTVA (€/MWh)"
        ]
        # Accumulation pour les 3 premières composantes
        values = [
            self.cout_variable_ATRD_euro_par_MWh,
            self.cout_TICGN_euro_par_MWh,
            self.cout_molecule_gaz_euro_par_MWh
        ]
        cum_values = [0]
        for v in values:
            cum_values.append(cum_values[-1] + v)
        # La 4e barre (total HTVA) n'est pas accumulée
        total_htva = self.cout_euro_HTVA_par_MWh

        colors = ['#4CAF50', '#FFC107', '#2196F3', '#9E9E9E']
        fig, ax = plt.subplots(figsize=figsize)

        # Barres en cascade (accumulation)
        for i, (label, val, color) in enumerate(zip(labels[:3], values, colors)):
            ax.bar(i, val, bottom=cum_values[i], color=color, edgecolor='black')
            y_text = cum_values[i] + val / 2
            ax.text(i, y_text, f"{val:.2f} €/MWh", ha='center', va='center', fontsize=10, color='black')

        # Barre du total HTVA (non accumulée)
        ax.bar(3, total_htva, color=colors[3], edgecolor='black')
        ax.text(3, total_htva / 2, f"{total_htva:.2f} €/MWh", ha='center', va='center', fontsize=10, color='black')

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha='right')
        ax.axhline(0, color='black', linewidth=0.8)
        ax.set_title(f"{title}\nTotal HTVA : {self.cout_euro_HTVA_par_MWh:.2f} €/MWh", fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()