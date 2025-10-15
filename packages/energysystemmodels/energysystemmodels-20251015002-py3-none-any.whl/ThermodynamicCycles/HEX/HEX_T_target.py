from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 
from datetime import datetime

class Object:
    def __init__(self):
        self.Timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.Inlet=FluidPort() 
        self.Outlet=FluidPort()

        self.T_target=0
        self.P_drop=0
        self.Qth=0
     
        self.df = pd.DataFrame()
        
    def calculate (self):
    
        self.Outlet.P=self.Inlet.P-self.P_drop

        
        #conditions de Outlet
        self.Outlet.T=self.T_target+273.15
        self.Outlet.h = PropsSI('H','P',self.Outlet.P,'T',self.Outlet.T,self.Inlet.fluid)
        self.Outlet.S = PropsSI('S','P',self.Outlet.P,'H',self.Outlet.h,self.Inlet.fluid)
        self.Outlet.F=self.Inlet.F
        self.Outlet.fluid=self.Inlet.fluid
        self.Outlet.calculate_properties()
        
        #calcul de la puissance thermique de l'échangeur
        self.Qth=self.Inlet.F*(self.Outlet.h-self.Inlet.h)

        self.df = pd.DataFrame({'Simple_HEX': [self.Timestamp,self.T_target,self.Qth/1000,], },
                      index = ['Timestamp','Simple_HEX(°C)','hex_Qhex(kW)'])     