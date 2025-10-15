from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 
from datetime import datetime

class Object:
    def __init__(self):
        self.Timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.Inlet=FluidPort() 
        self.Outlet=FluidPort()

        self.To=None
        self.P_drop=0
        self.Qth=None
     
        self.df = pd.DataFrame()
        
    def calculate (self):
    
        self.Outlet.P=self.Inlet.P-self.P_drop
        self.Outlet.F=self.Inlet.F
        self.Outlet.fluid=self.Inlet.fluid

        if self.Outlet.F is not None and self.To is not None and self.Qth is None:
            print("Calcul de la puissance thermique ou frigorifique:")
            self.Outlet.T=self.To+273.15
            self.Outlet.h = PropsSI('H','P',self.Outlet.P,'T',self.Outlet.T,self.Outlet.fluid)
            #calcul de la puissance thermique de l'échangeur
            self.Qth=self.Inlet.F*(self.Outlet.h-self.Inlet.h)
        
        if self.Qth is not None and self.To is not None:
            print("calcul du débit!")
            self.Outlet.T=self.To+273.15
            self.Outlet.h = PropsSI('H','P',self.Outlet.P,'T',self.Outlet.T,self.Outlet.fluid)
            print('self.Qth;',self.Qth)
            if (self.Outlet.h-self.Inlet.h)!=0:
                self.Inlet.F=self.Qth/(self.Outlet.h-self.Inlet.h)
            else:
               self.Inlet.F=0.0
            self.Outlet.F=self.Inlet.F
            print("self.Inlet.F:",self.Inlet.F)

        if self.Outlet.F is not None and self.Qth is not None and self.To is None:
            print("calcul de la température de sortie")
            self.Outlet.h=(self.Qth+self.Inlet.F*self.Inlet.h)/self.Inlet.F
            self.To = PropsSI('T','P',self.Outlet.P,'H',self.Outlet.h,self.Outlet.fluid)-273.15



        self.Outlet.S = PropsSI('S','P',self.Outlet.P,'H',self.Outlet.h,self.Inlet.fluid)
        self.Outlet.calculate_properties()

        self.df = pd.DataFrame({'Simple_HEX': [self.Timestamp,self.To,self.Qth/1000,], },
                      index = ['Timestamp','Simple_HEX(°C)','hex_Qhex(kW)'])     