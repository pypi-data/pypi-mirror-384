from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 
from datetime import datetime

import math

class Object:
    def __init__(self):
        self.Timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   
        self.Inlet1 = FluidPort()
        self.Outlet1 = FluidPort()
        self.Inlet2 = FluidPort()
        self.Outlet2 = FluidPort()

        self.T1o=None
        self.T2o=None
        self.C1=None
        self.C2=None
        self.R=None # Le rapport des débits de capacités des deux fluides est 
        self.Eff=None # efficacité
        self.UA=None
        self.NUT=None
        self.Cmin=None

        self.P_drop=0
   
     
        self.df = pd.DataFrame()


        
    def calculate (self):
    
        self.Outlet1.P=self.Inlet1.P-self.P_drop
        self.Outlet1.F=self.Inlet1.F
        self.Outlet2.F=self.Inlet2.F
        self.Outlet1.fluid=self.Inlet1.fluid
        self.Outlet2.fluid=self.Inlet2.fluid

        #self.Outlet1.calculate_properties()

   


    

        self.C1=self.Inlet1.F*self.Inlet1.cp
        self.C2=self.Inlet2.F*self.Inlet2.cp
        self.Cmin=min(self.C1,self.C2)
        self.Cmax=max(self.C1,self.C2)

        self.R=self.Cmin/self.Cmax


        self.NUT=self.UA/self.Cmin
        #print('self.NUT================',self.NUT)
        self.Eff=(1-math.exp(-self.NUT*(1-self.R)))/(1-self.R*math.exp(-self.NUT*(1-self.R)))
        #print('self.Eff================',self.Eff)
        self.Qth=self.Eff*self.Cmin*(self.Inlet1.T-self.Inlet2.T)
        #print('self.Qth================',self.Qth)

        self.Inlet1.calculate_properties()
        self.Outlet1.h=-(self.Qth/self.Inlet1.F)+self.Inlet1.h
        self.Inlet2.calculate_properties()
        self.Outlet2.h=(self.Qth/self.Inlet2.F)+self.Inlet2.h
        
        

        self.Outlet1.calculate_properties()
        #print('self.Outlet1.T °C================',self.Outlet1.T-273.15)
        self.Outlet2.calculate_properties()
        #print('self.Outlet2.T °C================',self.Outlet2.T-273.15)

        self.df = pd.DataFrame({'DTLM_HEX': [self.Timestamp,self.Qth], },
                      index = ['Timestamp',self.Qth])     


# from ThermodynamicCycles.Source import Source
# from ThermodynamicCycles.Connect import Fluid_connect

# SOURCE1=Source.Object()
# SOURCE1.F_m3h=15
# SOURCE1.Pi_bar=1
# SOURCE1.fluid='Dodecane'
# SOURCE1.Ti_degC=120
# SOURCE1.calculate()

# SOURCE2=Source.Object()
# SOURCE2.F_m3h=14*3.6
# SOURCE2.Pi_bar=1
# SOURCE2.fluid='water'
# SOURCE2.Ti_degC=20
# SOURCE2.calculate()

# HEX=Object()
# HEX.UA=6698.371240548343

# Fluid_connect(HEX.Inlet1,SOURCE1.Outlet)
# Fluid_connect(HEX.Inlet2,SOURCE2.Outlet)
# HEX.calculate()
# print("-------------------------------",HEX.df)

# print(HEX.Outlet1.df)
# print(HEX.Outlet2.df)

# print(HEX.R)
# print(HEX.Eff)
