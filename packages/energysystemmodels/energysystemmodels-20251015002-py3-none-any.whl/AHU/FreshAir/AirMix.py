from AHU.air_humide import air_humide
from AHU.AirPort.AirPort import AirPort
import pandas as pd


class Object:
    def __init__(self):
        
        self.Inlet1=AirPort() 
        self.Inlet2=AirPort() 
        self.Outlet=AirPort()
        self.id=1
        
        self.F_dry=None
        self.F_dry1=None
        self.F_dry2=None
        self.df = None  # DataFrame pour afficher les résultats
        
        
    def calculate(self):
        
        if (self.Inlet1.F is not None and self.Inlet1.w is not None):
            self.F_dry1=self.Inlet1.F/(1+self.Inlet1.w/1000)
        
        if (self.Inlet2.F is not None and self.Inlet2.w is not None):
            self.F_dry2=self.Inlet2.F/(1+self.Inlet2.w/1000)

        #connecteur   
      
    
        #Calcul le poid d'eau du mélange si les deux flux sont connus
        if (self.F_dry1 is not None and self.F_dry2 is not None):
            self.Outlet.w=(self.Inlet1.w*self.F_dry1+self.Inlet2.w*self.F_dry2)/(self.F_dry1+self.F_dry2)
            self.Outlet.h=(self.Inlet1.h*self.F_dry1+self.Inlet2.h*self.F_dry2)/(self.F_dry1+self.F_dry2)
            self.Outlet.F=self.Inlet1.F+self.Inlet2.F 

        if (self.F_dry1 is None and self.F_dry2 is not None):
            self.Outlet.w=(self.Inlet2.w*self.F_dry2)/(self.F_dry2)
            self.Outlet.h=(self.Inlet2.h*self.F_dry2)/(self.F_dry2)
            self.Outlet.F=self.Inlet2.F 
        
        if (self.F_dry1 is not None and self.F_dry2 is None):
            self.Outlet.w=(self.Inlet1.w*self.F_dry1)/(self.F_dry1)
            self.Outlet.h=(self.Inlet1.h*self.F_dry1)/(self.F_dry1)
            self.Outlet.F=self.Inlet1.F

        
        
        self.Outlet.P=min(self.Inlet1.P,self.Inlet2.P)
        
        
        #self.T_outlet=air_humide_NB.Air3_Tdb(self.Outlet.w/1000,self.Outlet.P,self.Outlet.h)
        
        self.F_dry=(self.Outlet.F)/(1+self.Outlet.w/1000)
        self.Outlet.F_dry=self.F_dry
    
        data = {
            'ID': [self.id],  # Identifiant de l'objet
            'self.Outlet.T (C)': [self.Outlet.T],  # Température de l'air
            'self.Outlet.RH (%)': [self.Outlet.RH],  # Humidité relative
            'self.Outlet.F (kg/s)': [self.Outlet.F],  # Débit d'air en kg/s
            'self.Outlet.F_dry (kg/s)': [self.Outlet.F_dry],  # Débit d'air sec en kg/s
            'self.Outlet.P (Pa)': [self.Outlet.P],  # Pression de l'air
            'self.Outlet.h (kJ/kg)': [self.Outlet.h],  # Enthalpie spécifique
            'self.Outlet.w (g/kgdry)': [self.Outlet.w],  # Humidité absolue
            'self.Outlet.Pv_sat (Pa)': [self.Outlet.Pv_sat],  # Pression de vapeur saturante
        }

        # Convertir les données en DataFrame et transposer pour avoir les paramètres en lignes
        self.df = pd.DataFrame(data).T



