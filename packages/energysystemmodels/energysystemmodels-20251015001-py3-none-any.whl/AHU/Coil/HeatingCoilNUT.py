from AHU.air_humide import air_humide
import pandas as pd
from AHU.AirPort.AirPort import AirPort
from ThermodynamicCycles.FluidPort.FluidPort import FluidPort  # Correction de l'import
import CoolProp.CoolProp as CP
import math

class HeatingCoilNUT:
    def __init__(self):
        # Ports air
        self.Inlet = AirPort()
        self.Outlet = AirPort()
        
        # Ajout du port eau
        self.Water_Inlet = FluidPort(fluid='Water')
        self.Water_Outlet = FluidPort(fluid='Water')
        
        # Paramètres généraux
        self.id = 2
        self.P_drop = 0  # Perte de charge air [Pa]
        
        # Paramètres côté air
        self.T_in = 0    # Température entrée air [°C]
        self.hi = 0      # Enthalpie entrée air [kJ/kg]
        self.wi = 12     # Humidité spécifique entrée [g/kg]
        self.F = 0       # Débit massique air humide [kg/s]
        self.F_dry = 0   # Débit massique air sec [kg/s]
        
        # Paramètres côté eau
        self.T_water_in = 80    # Température entrée eau [°C]
        self.T_water_out = 60   # Température sortie eau [°C]
        self.P_water = 3e5      # Pression eau [Pa]
        self.m_water = 0        # Débit massique eau [kg/s]
        
        # Paramètres échangeur
        self.S = 10             # Surface d'échange [m²]
        self.U = 50            # Coefficient d'échange global [W/m².K]
        self.NUT = 0           # Number of Transfer Units [-]
        self.effectiveness = 0  # Efficacité de l'échangeur [-]
        
        # Résultats
        self.Q_th = 0          # Puissance échangée [kW]
        self.To_target = 20    # Température de consigne sortie air [°C]
        self.ho = 0            # Enthalpie sortie air [kJ/kg]
        self.RH_out = 0        # Humidité relative sortie [%]
        
        self.df = None         # DataFrame résultats

    def calculate(self):
        # Connecteur air
        self.Outlet.P = self.Inlet.P - self.P_drop
        
        # Récupération conditions entrée air
        self.wi = self.Inlet.w
        self.hi = self.Inlet.h
        self.F = self.Inlet.F
        self.T_in = air_humide.Air_T_db(w=self.wi, h=self.hi, P=self.Inlet.P)
        self.F_dry = self.F/(1+self.wi/1000)  # [kg air sec/s]
        
        # Utilisation des propriétés du port d'eau
        self.T_water_in = self.Water_Inlet.T - 273.15  # Conversion K -> °C
        self.P_water = self.Water_Inlet.P
        self.m_water = self.Water_Inlet.F
        
        # Calcul propriétés eau
        cp_water = CP.PropsSI('CP0MASS', 'T', self.T_water_in + 273.15, 'P', self.P_water, 'Water')
        rho_water = CP.PropsSI('D', 'T', self.T_water_in + 273.15, 'P', self.P_water, 'Water')
        
        # Calcul des débits calorifiques
        C_water = self.m_water * cp_water    # [W/K]
        C_air = self.F_dry * 1006           # [W/K] (cp air ≈ 1006 J/kg.K)
        
        C_min = min(C_water, C_air)
        C_max = max(C_water, C_air)
        
        # Calcul NUT et efficacité
        self.NUT = self.U * self.S / C_min
        Cr = C_min/C_max
        
        # Efficacité pour échangeur à courants croisés non brassés
        #expenotiel en python
        
        self.effectiveness = 1 - math.exp(-self.NUT * (1 - math.exp(-Cr * self.NUT))/Cr)
        
        # Puissance maximale possible
        Q_max = C_min * (self.T_water_in - self.T_in)
        
        # Puissance réelle échangée
        self.Q_th = self.effectiveness * Q_max / 1000  # [kW]
        
        if self.To_target > self.T_in:
            # Calcul température sortie air
            delta_T = self.Q_th * 1000 / (self.F_dry * 1006)
            T_out = self.T_in + delta_T
            
            # Calcul propriétés air sortie
            self.ho = air_humide.Air_h(T_db=T_out, w=self.wi)
            self.RH_out = air_humide.Air_RH(
                Pv_sat=air_humide.Air_Pv_sat(T_out),
                w=self.wi,
                P=self.Outlet.P
            )
        else:
            self.ho = self.hi
            self.Q_th = 0
            
        # Connecteur sortie air
        self.Outlet.w = self.Inlet.w
        self.Outlet.h = self.ho
        self.Outlet.F = self.F_dry * (1 + self.Outlet.w/1000)
        self.Outlet.F_dry = self.F_dry
        
        # Mise à jour du port de sortie eau
        self.Water_Outlet.P = self.Water_Inlet.P  # Néglige les pertes de charge eau
        delta_h = self.Q_th * 1000 / self.m_water  # Variation d'enthalpie eau [J/kg]
        self.Water_Outlet.h = self.Water_Inlet.h - delta_h
        self.Water_Outlet.F = self.Water_Inlet.F

        # Mise à jour des propriétés du port eau
        self.Water_Outlet.calculate_properties()
        
        # Calcul T_water_out
        self.T_water_out = self.Water_Outlet.T - 273.15  # Conversion K -> °C
        
        # Mise à jour DataFrame résultats
        self.df = pd.DataFrame(
            data={
                'HeatingCoilNUT': [
                    self.id,
                    round(self.Outlet.T, 1),
                    round(self.Outlet.RH, 1),
                    round(self.Outlet.F, 3),
                    round(self.Outlet.F_dry, 3),
                    round(self.Outlet.P, 1),
                    round(self.Outlet.P / 100000, 1),
                    round(self.Outlet.h, 1),
                    round(self.Outlet.w, 3),
                    round(self.Outlet.Pv_sat, 1),
                    round(self.Q_th, 1),
                    round(self.NUT, 2),
                    round(self.effectiveness, 2),
                    round(self.T_water_out, 1)
                ]
            },
            index=[
                'ID', 'Outlet.T (C)', 'Outlet.RH (%)',
                'Outlet.F (kg/s)', 'Outlet.F_dry (kg/s)',
                'Outlet.P (Pa)', 'Outlet.P/10^5 (bar)',
                'Outlet.h (kJ/kg)', 'Outlet.w (g/kgdry)',
                'Outlet.Pv_sat (Pa)', 'Q_th (kW)',
                'NUT (-)', 'Effectiveness (-)',
                'T_water_out (C)'
            ]
        )