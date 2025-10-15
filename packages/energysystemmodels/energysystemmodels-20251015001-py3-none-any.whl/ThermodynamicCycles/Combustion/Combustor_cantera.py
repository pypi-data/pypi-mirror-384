# Importation de la bibliothèque Cantera pour les simulations thermodynamiques
import cantera as ct
# Importation de CoolProp pour les propriétés des fluides
from CoolProp.CoolProp import PropsSI
# Importation de pandas pour la manipulation de données
import pandas as pd
# Importation de datetime pour enregistrer les horodatages
from datetime import datetime
# Importation de la classe FluidPort pour gérer les entrées et sorties de fluides
from ThermodynamicCycles.FluidPort.FluidPort import FluidPort

# Définition de la classe 'Object'
class Object:
    def __init__(self):
        # Initialisation des ports pour le carburant et l'oxydant
        self.fuel_Inlet = FluidPort()
        self.oxidizer_Inlet = FluidPort()

        # Enregistrement de l'horodatage actuel
        self.Timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Initialisation de l'objet gaz Cantera avec le mécanisme de réaction 'gri30.yaml'
        self.gas = ct.Solution("gri30.yaml")
        # Définition des noms par défaut du carburant et de l'oxydant
        self.fuel_name = "H2"
        self.oxidizer_name = "O2:1.0"

        # Définition du débit de carburant par défaut en kg/s
        #self.fuel_F_kgs = 0.001
        # Variable pour la quantité de chaleur de combustion (sera calculée)
        self.Q_comb = None

        # Ratio du mélange carburant/oxydant (phi) et excès d'air (à calculer)
        self.phi = None
        self.AIR_EXCESS = None
        self.products_O2_molRatio = None

        # Débit d'oxydant par défaut en kg/s
        self.oxidizer_F_kgs = 1.0

        # Initialisation d'un DataFrame pandas pour stocker les données de Outlet
        self.df = pd.DataFrame()

    # Définition de la méthode 'calculate' pour effectuer les calculs thermodynamiques
    def calculate(self):
        # Mise à jour des débits si des valeurs ont été fournies via les ports
        if self.fuel_Inlet.F is not None:
            print('----------------------------------------',self.fuel_Inlet.F)
            self.fuel_F_kgs = self.fuel_Inlet.F

        if self.oxidizer_Inlet.F is not None:
            self.oxidizer_F_kgs = self.oxidizer_Inlet.F

        # Mise à jour du nom du carburant en fonction du fluide entrant
        if self.fuel_Inlet.fluid == "methane":
            self.fuel_name = "CH4"
            M_CH4 = PropsSI('M', 'methane')
            print('-------------------------------------------',self.fuel_F_kgs,M_CH4)
            self.CH4_mols=self.fuel_F_kgs/M_CH4

        # Conversion des noms de carburants en noms reconnus par Cantera
        if self.fuel_name == "C2H6":
            self.fuel_name = "ethane"
        if self.fuel_name == "CH3OH":
            self.fuel_name = "methanol"

        # Mise à jour du nom de l'oxydant en fonction du fluide entrant et calcul des propriétés
        if self.oxidizer_Inlet.fluid == "air":
            self.oxidizer_name = f"O2:2,N2:7.52"
            M_N2 = PropsSI('M', 'Nitrogen')
            M_O2 = PropsSI('M', 'Oxygen')
            fraction_molaire_N2 = 0.79
            fraction_molaire_O2 = 0.21
            # Masse molaire moyenne de l'air sec (N2 et O2 uniquement)
            M_air = fraction_molaire_N2 * M_N2 + fraction_molaire_O2 * M_O2
            print('M_air===================',M_air)
            # Convertir le débit massique total en débit molaire total (en mol/s)
            oxidizer_mols = self.oxidizer_F_kgs / M_air
            print('oxidizer_mols==============' ,oxidizer_mols )
            self.N2_mols = oxidizer_mols *fraction_molaire_N2
            self.O2_mols = oxidizer_mols *fraction_molaire_O2

            # Calcul des débits massiques partiels pour N2 et O2
            N2_F_kgs = self.N2_mols * M_N2
            O2_F_kgs = self.O2_mols * M_O2

        if self.oxidizer_Inlet.fluid == "oxygen":
            self.oxidizer_name = f"O2:1"
            M_O2 = PropsSI('M', 'Oxygen')
            oxidizer_mols = self.oxidizer_F_kgs / M_O2
            self.O2_mols = self.oxidizer_F_kgs/M_O2
            O2_F_kgs = self.oxidizer_F_kgs




        # Calcul de phi en fonction du rapport molaire O2 dans les produits
        if self.products_O2_molRatio is not None:
            # Équilibre à phi=1
            if self.oxidizer_Inlet.fluid == "air": 
                self.phi = 1.0 / (1.0 + 3.76 / self.products_O2_molRatio)
            if self.oxidizer_Inlet.fluid == "oxygen":
                self.phi = 1.0 / (1.0 + 1.0 / self.products_O2_molRatio)

        # Calcul de l'excès d'air en fonction de phi
        if self.AIR_EXCESS is not None:
            self.phi = 1 / ((self.AIR_EXCESS) + 1)
        if self.phi is not None:
            self.AIR_EXCESS = ((1 / self.phi) - 1)
        
        # Affichage de l'excès d'air, de phi et du rapport molaire O2
        print('self.AIR_EXCESS,self.phi,self.products_O2_molRatio',self.AIR_EXCESS,self.phi,self.products_O2_molRatio)


        
        # Appel de la méthode 'Heating_value' pour calculer les valeurs calorifiques
        self.Heating_value()
        # Mise à jour du DataFrame avec les résultats
        self.df = pd.DataFrame({
            'Source': [
                self.Timestamp, self.fuel_name, self.oxidizer_name, self.LHV, self.HHV,
                self.Total_Latent_heat_MJ_kgFuel, self.LHV_kWh_Nm3, self.HHV_kWh_Nm3,
                self.LHV_kWh_Sm3, self.HHV_kWh_Sm3, self.Q_comb_LHV, self.Q_comb_HHV,
                oxidizer_mols,
                self.N2_mols if self.oxidizer_Inlet.fluid == "air" else 0,  # mol/s
                self.O2_mols,  # mol/s
                self.oxidizer_F_kgs,
                N2_F_kgs if self.oxidizer_Inlet.fluid == "air" else 0,  # kg/s
                O2_F_kgs,  # kg/s
            ]
        }, index=[
            'Timestamp', 'fuel_name', 'oxidizer_name', 'comb_LHV (MJ/kg)', 'comb_HHV (MJ/kg)',
            'Total_Latent_heat_MJ_kgFuel', 'LHV_kWh_Nm3', 'HHV_kWh_Nm3',
            'LHV_kWh_Sm3', 'HHV_kWh_Sm3', 'Q_comb_LHV (kW)', 'Q_comb_HHV (kW)','oxidizer (mol/s)',
            'N2_mols (mol/s)', 'O2_mols (mol/s)','oxidizer (kg/s)', 'N2_F_kgs (kg/s)', 'O2_F_kgs (kg/s)'
        ])
        
        self.heat_losses()

    # Définition de la méthode 'Heating_value' pour calculer les valeurs calorifiques
    def Heating_value(self):
        # Création d'un objet eau pour les calculs de propriétés
        water = ct.Water()
        # Réglage de la température et de la qualité de l'eau à 298 K et phase liquide
        water.TQ = 298, 0
        h_liquid = water.h
        # Réglage de la qualité de l'eau à phase gazeuse
        water.TQ = 298, 1
        h_gas = water.h

        # Réglage des conditions initiales du gaz avant combustion
        self.gas.TP = 298, ct.one_atm
        self.gas.set_equivalence_ratio(phi=1, fuel=self.fuel_name, oxidizer=self.oxidizer_name)

        h1 = self.gas.enthalpy_mass
        print('h1================================================',h1)
        Y_fuel = self.gas[self.fuel_name].Y[0]

        # Simulation de la combustion
        X_products = {
            "CO2": self.gas.elemental_mole_fraction("C"),
            "H2O": 0.5 * self.gas.elemental_mole_fraction("H"),
            "N2": 0.5 * self.gas.elemental_mole_fraction("N"),
        }

        self.gas.TPX = None, None, X_products
        Y_H2O = self.gas["H2O"].Y[0]
        h2 = self.gas.enthalpy_mass

        # Calcul de la valeur calorifique inférieure (LHV) et supérieure (HHV)
        self.LHV = -(h2 - h1) / Y_fuel / 1e6  # LHV en MJ/kg
        self.HHV = -(h2 - h1 + (h_liquid - h_gas) * Y_H2O) / Y_fuel / 1e6  # HHV en MJ/kg
        self.Total_Latent_heat_MJ_kgFuel = self.HHV - self.LHV

        # Calcul de la densité à des températures normales et standard
        rho_N = PropsSI("D", "T", 0 + 273.15, "P", 101325, self.fuel_name)  # Densité à 0°C en kg/m^3
        rho_S = PropsSI("D", "T", 20 + 273.15, "P", 101325, self.fuel_name)  # Densité à 20°C en kg/m^3

        # Conversion des valeurs calorifiques en kWh/m^3
        self.LHV_kWh_Nm3 = self.LHV * rho_N / 3.6
        self.HHV_kWh_Nm3 = self.HHV * rho_N / 3.6
        self.LHV_kWh_Sm3 = self.LHV * rho_S / 3.6
        self.HHV_kWh_Sm3 = self.HHV * rho_S / 3.6

        # Calcul de la quantité de chaleur libérée par la combustion
        self.Q_comb_HHV = self.HHV * self.fuel_F_kgs * 1e3  # HHV en kW
        self.Q_comb_LHV = self.LHV * self.fuel_F_kgs * 1e3  # LHV en kW

    def heat_losses(self):
        # Ici, nous définissons la nouvelle composition de carburant et d'oxydant
        fuel_composition = f"CH4:{round(self.CH4_mols,2)}"
        if self.oxidizer_Inlet.fluid == "air":
            oxidizer_composition = f"O2:{round(self.O2_mols,2)},N2:{round(self.N2_mols,2)}"
        else:
            oxidizer_composition = f"O2:{round(self.O2_mols,2)}"
        
        print(f"Fuel composition: {fuel_composition}")
        print(f"Oxidizer composition: {oxidizer_composition}")
        
        # Créer une instance de Solution
        gas = ct.Solution('gri30.yaml')
        # Définir les fractions molaires directement pour créer le mélange de gaz
        gas.X = f"{fuel_composition},{oxidizer_composition}"
   
        # Équilibre le gaz à une température et une pression données
        gas.TP = 300.0, ct.one_atm
        gas.equilibrate('HP')
        # Enregistrez l'enthalpie à l'état équilibré
        h_initial = gas.enthalpy_mass

        # Calculer phi après équilibrage en utilisant les nouvelles fractions molaires
        self.phi = gas.equivalence_ratio()
        
        print(f"State after equilibration: T = {gas.T:.2f} K, P = {gas.P:.2f} Pa, rho = {gas.density:.2f} kg/m³")
        print(f"Phi recalculé après équilibrage = {self.phi:.3f}")
        print(gas())

         # État final à 110°C (383 K)
        gas.TP = 25+273.15, ct.one_atm
        # Pas besoin d'équilibrer de nouveau, nous voulons juste l'enthalpie à cette température
        h_final = gas.enthalpy_mass

        self.mass_flow_rate=self.fuel_F_kgs+self.oxidizer_F_kgs
        # La chaleur perdue sera la différence d'enthalpie par unité de masse multipliée par la masse totale du gaz
        heat_lost = (h_initial - h_final) * self.mass_flow_rate  # masse_flow_rate doit être définie ailleurs dans la classe

        print(f"Chaleur perdue (jusqu'à 210°C): {heat_lost/1000:.2f} kW")


# utilisation du module
from ThermodynamicCycles.Combustion import Combustor_cantera
from ThermodynamicCycles.Source import Source
from ThermodynamicCycles.Connect import Fluid_connect

fioul_SOURCE = Source.Object()
oxidizer_SOURCE = Source.Object()
COMB = Combustor_cantera.Object()

fioul_SOURCE.F = 1
fioul_SOURCE.fluid = "methane"
fioul_SOURCE.Ti_degC = -5.0
fioul_SOURCE.Pi_bar = 1.01325 + 0.030  # 30 millibar

oxidizer_SOURCE.fluid = "air" #"oxygen"
oxidizer_SOURCE.F = 17.2
oxidizer_SOURCE.Ti_degC = 15.0
oxidizer_SOURCE.Pi_bar = 1.01325 + 0.2  # 30 millibar

#COMB.phi = 1.0
#COMB.AIR_EXCESS = 0.03*0

fioul_SOURCE.calculate()
oxidizer_SOURCE.calculate()

Fluid_connect(COMB.fuel_Inlet, fioul_SOURCE.Outlet)
Fluid_connect(COMB.oxidizer_Inlet, oxidizer_SOURCE.Outlet)
COMB.calculate()

print(fioul_SOURCE.df)
print(oxidizer_SOURCE.df)
print(COMB.df)
