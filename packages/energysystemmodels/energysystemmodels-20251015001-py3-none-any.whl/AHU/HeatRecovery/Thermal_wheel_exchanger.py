# Modèle de l'échangeur
from AHU.AirPort.AirPort import AirPort
from AHU.air_humide import air_humide
import pandas as pd

class Object:
    def __init__(self):
        # Initialisation des ports d'entrée et de sortie
        self.id=2 #identifiant de l'objet
        self.Inlet1 = AirPort()  # Air frais entrant
        self.Outlet1 = AirPort()  # Air frais sortant
        self.Inlet2 = AirPort()  # Air extrait entrant
        self.Outlet2 = AirPort()  # Air extrait sortant

        # Paramètres de l'échangeur
        self.h_efficiency = None  # Efficacité enthalpique (calculée)
        self.T_efficiency = 80    # Efficacité en température (%)
        self.T_efficiency_target=None
        self.T_target=16

        self.heat_transfer1 = None  # Transfert de chaleur du flux 1 (kW)
        self.heat_transfer2 = None  # Transfert de chaleur du flux 2 (kW)
        self.sensible_heat_transfer1=None
        self.sensible_heat_transfer2=None
        self.T1o = None  # Température de sortie de l'air frais (°C)
        self.T2o = None  # Température de sortie de l'air frais (°C)
        self.df=None
        self.F_dry_min=None

        self.delta_mw1=None #quantité d'eau gagné ou perdu par le flux 1 en g/s
        self.delta_mw2=None #quantité d'eau gagné ou perdu par le flux 2 en g/s



    def calculate(self):
        # Détermination du débit massique minimum
        self.F_dry_min = min(self.Inlet1.F_dry, self.Inlet2.F_dry)
      
        
        # Cas hivernal : l'air extrait est plus chaud que l'air extérieur
        if (self.Inlet2.T >= self.Inlet1.T and self.Inlet1.T<=self.T_target):

            self.T_efficiency_target=100*self.Inlet1.F_dry*(self.T_target-self.Inlet1.T)/(self.F_dry_min*(self.Inlet2.T - self.Inlet1.T))
            if self.T_efficiency>self.T_efficiency_target:
                self.T_efficiency=max(self.T_efficiency_target,0)

            # Calcul de la température de sortie de l'air frais
            self.T1o = self.Inlet1.T + (self.F_dry_min*(self.T_efficiency / 100) * (self.Inlet2.T - self.Inlet1.T))/self.Inlet1.F_dry
            # Calcul de l'enthalpie de sortie de l'air 
            

            self.Outlet1.h = self.Inlet1.h + (self.F_dry_min*(self.T_efficiency / 100) * (self.Inlet2.h - self.Inlet1.h))/self.Inlet1.F_dry

            #déduction de l'humidité absolue à la sortie de l'air frai préchauffé
            self.Outlet1.w = air_humide.Air_w(h=self.Outlet1.h,T_db=self.T1o)

            # Calcul du transfert de chaleur de l'air frais
            self.heat_transfer1 = (self.Outlet1.h - self.Inlet1.h) * self.Inlet1.F_dry
            self.sensible_heat_transfer1=(air_humide.Air_h(w=self.Inlet1.w,T_db=self.T1o)-self.Inlet1.h)*self.Inlet1.F_dry


          
            self.heat_transfer2=-self.heat_transfer1
            # Calcul des propriétés de sortie de l'air extrait
            self.Outlet2.h = (self.heat_transfer2 / self.Inlet2.F_dry) + self.Inlet2.h
            
            self.delta_mw1=self.Inlet1.F_dry*(self.Outlet1.w-self.Inlet1.w) #quantité d'eau gagné ou perdu par le flux 1 en g/s
            self.delta_mw2=-self.delta_mw1
            self.Outlet2.w=self.delta_mw2/self.Inlet2.F_dry+self.Inlet2.w #quantité d'eau gagné ou perdu par le flux 2 en g/s
            self.T2o=air_humide.Air_T_db(w=self.Outlet2.w,h=self.Outlet2.h)

            self.sensible_heat_transfer2=(air_humide.Air_h(w=self.Inlet2.w,T_db=self.T2o)-self.Inlet2.h)*self.Inlet2.F_dry
           
            # Calcul de l'efficacité enthalpique
            self.h_efficiency = 100 * self.Inlet1.F_dry * (self.Outlet1.h - self.Inlet1.h) / (self.F_dry_min * (self.Inlet2.h - self.Inlet1.h))

        elif (self.Inlet2.T >= self.Inlet1.T and self.Inlet1.T>self.T_target):
            self.Outlet1.h = self.Inlet1.h # ne rien échanger
            self.Outlet1.w = self.Inlet1.w  
           
        # Cas estival : l'air extérieur est plus chaud que l'air extrait
        elif (self.Inlet2.T < self.Inlet1.T):
            print("été")
            self.T1o = self.Inlet1.T - (self.F_dry_min*(self.T_efficiency / 100) * (self.Inlet1.T-self.Inlet2.T))/self.Inlet1.F_dry
            self.Outlet1.h = self.Inlet1.h - (self.F_dry_min*(self.T_efficiency / 100) * (self.Inlet1.h-self.Inlet2.h))/self.Inlet1.F_dry
            #déduction de l'humidité absolue à la sortie de l'air frai préchauffé
            self.Outlet1.w = air_humide.Air_w(h=self.Outlet1.h,T_db=self.T1o)

            # Calcul du transfert de chaleur de l'air frais
            self.heat_transfer1 = (self.Outlet1.h - self.Inlet1.h) * self.Inlet1.F_dry
            self.sensible_heat_transfer1=(air_humide.Air_h(w=self.Inlet1.w,T_db=self.T1o)-self.Inlet1.h)*self.Inlet1.F_dry


          
            self.heat_transfer2=-self.heat_transfer1
            # Calcul des propriétés de sortie de l'air extrait
            self.Outlet2.h = (self.heat_transfer2 / self.Inlet2.F_dry) + self.Inlet2.h
            
            self.delta_mw1=self.Inlet1.F_dry*(self.Outlet1.w-self.Inlet1.w) #quantité d'eau gagné ou perdu par le flux 1 en g/s
            self.delta_mw2=-self.delta_mw1
            self.Outlet2.w=self.delta_mw2/self.Inlet2.F_dry+self.Inlet2.w #quantité d'eau gagné ou perdu par le flux 2 en g/s
            self.T2o=air_humide.Air_T_db(w=self.Outlet2.w,h=self.Outlet2.h)

            self.sensible_heat_transfer2=(air_humide.Air_h(w=self.Inlet2.w,T_db=self.T2o)-self.Inlet2.h)*self.Inlet2.F_dry
           
            # Calcul de l'efficacité enthalpique
            self.h_efficiency = 100 * self.Inlet1.F_dry * (self.Outlet1.h - self.Inlet1.h) / (self.F_dry_min * (self.Inlet2.h - self.Inlet1.h))


        else:
            # Calcul de l'enthalpie de sortie de l'air frais
            pass
   
        # Conservation du débit massique et de l'humidité absolue
        self.Outlet1.F_dry = self.Inlet1.F_dry
        self.Outlet2.F_dry = self.Inlet2.F_dry
        
        self.Outlet1.update_properties()
        self.Outlet2.update_properties()

        data = {
            'ID': [self.id],  # Identifiant de l'objet

            'Heat recovery (kW)': [self.heat_transfer1],
             'sensible_heat_transfer1 (kW)': [self.sensible_heat_transfer1],
             'sensible_heat_transfer2 (kW)': [self.sensible_heat_transfer2],      
             'self.delta_mw1 (gH20/s)':self.delta_mw1,
             'self.delta_mw2 (gH2O/s)':self.delta_mw2,
            'sefficacité échangeur T_efficiency (%)': [self.T_efficiency],
            'rendement thermique (rapport des enthalpies) h_efficiency (%)': [self.h_efficiency],
           

            'self.Inlet1.T (C)': [self.Inlet1.T],  # Température de l'air
            'self.Outlet1.T (C)': [self.Outlet1.T],  # Température de l'air
            'self.Inlet2.T (C)': [self.Inlet2.T],  # Température de l'air
            'self.Outlet2.T (C)': [self.Outlet2.T],  # Température de l'air

            'self.Inlet1.RH (%)': [self.Inlet1.RH],  # Humidité relative
            'self.Outlet1.RH (%)': [self.Outlet1.RH],  # Humidité relative
            'self.Inlet2.RH (%)': [self.Inlet2.RH],  # Humidité relative
            'self.Outlet2.RH (%)': [self.Outlet2.RH],  # Humidité relative


            'self.Inlet1.F (kg/s)': [self.Inlet1.F],  # Débit d'air en kg/s
            'self.Inlet1.F_dry (kg/s)': [self.Inlet1.F_dry],  # Débit d'air sec en kg/s
            'self.Outlet1.F (kg/s)': [self.Outlet1.F],  # Débit d'air en kg/s
            'self.Outlet1.F_dry (kg/s)': [self.Outlet1.F_dry],  # Débit d'air sec en kg/s
            'self.Inlet2.F (kg/s)': [self.Inlet2.F],  # Débit d'air en kg/s
            'self.Inlet2.F_dry (kg/s)': [self.Inlet2.F_dry],  # Débit d'air sec en kg/s
            'self.Outlet2.F (kg/s)': [self.Outlet2.F],  # Débit d'air en kg/s
            'self.Outlet2.F_dry (kg/s)': [self.Outlet2.F_dry],  # Débit d'air sec en kg/s

            'self.Inlet1.P (Pa)': [self.Inlet1.P],  # Pression de l'air
            'self.Outlet1.P (Pa)': [self.Outlet1.P],  # Pression de l'air
            'self.Inlet2.P (Pa)': [self.Inlet2.P],  # Pression de l'air
            'self.Outlet2.P (Pa)': [self.Outlet2.P],  # Pression de l'air

            'self.Inlet1.h (kJ/kg)': [self.Inlet1.h],  # Enthalpie spécifique
            'self.Outlet1.h (kJ/kg)': [self.Outlet1.h],  # Enthalpie spécifique
            'self.Inlet2.h (kJ/kg)': [self.Inlet2.h],  # Enthalpie spécifique
            'self.Outlet2.h (kJ/kg)': [self.Outlet2.h],  # Enthalpie spécifique

            'self.Inlet1.w (gH2O/kgdry)': [self.Inlet1.w],  # Humidité absolue
            'self.Outlet1.w (gH2O/kgdry)': [self.Outlet1.w],  # Humidité absolue
            'self.Inlet2.w (gH2O/kgdry)': [self.Inlet2.w],  # Humidité absolue
           'self.Outlet2.w (gH2O/kgdry)': [self.Outlet2.w],  # Humidité absolue


            'self.Inlet1.Pv_sat (Pa)': [self.Inlet1.Pv_sat],  # Pression de vapeur saturante
            'self.Outlet1.Pv_sat (Pa)': [self.Outlet1.Pv_sat],  # Pression de vapeur saturante
            'self.Inlet2.Pv_sat (Pa)': [self.Inlet2.Pv_sat],  # Pression de vapeur saturante
            'self.Outlet2.Pv_sat (Pa)': [self.Outlet2.Pv_sat],  # Pression de vapeur saturante
        }

        # Convertir les données en DataFrame et transposer pour avoir les paramètres en lignes
        self.df = pd.DataFrame(data).T
       

