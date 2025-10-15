from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 

class Object :
    def __init__(self):
        self.Inlet=FluidPort() 
        self.Outlet=FluidPort()
        self.Tl_sat=0
        self.Hl_sat = 0
        self.Sl_sat = 0
        self.subcooling=2
        self.Q_cond=0
        #Output Data
        self.df=[]
        
    def calculate (self):
        self.Tl_sat=PropsSI('T','P',self.Inlet.P,'Q',0,self.Inlet.fluid)
       
        self.Hl_sat =PropsSI('H','P',self.Inlet.P,'Q',0,self.Inlet.fluid)
        #print("H5=",self.Hl_sat )
        #print("self.Inlet.P=",self.Inlet.P )
        #print("self.Inlet.fluid=",self.Inlet.fluid )
        
        self.Sl_sat =PropsSI('S','P',self.Inlet.P,'Q',0,self.Inlet.fluid)
        
        self.To=self.Tl_sat-self.subcooling
        self.Ho = PropsSI('H','P',self.Inlet.P,'T',self.To,self.Inlet.fluid)
        self.So = PropsSI('S','P',self.Inlet.P,'T',self.To,self.Inlet.fluid)
        self.Outlet.fluid=self.Inlet.fluid
        self.Outlet.h=self.Ho
        self.Outlet.F=self.Inlet.F
        self.Outlet.P=self.Inlet.P
        
        self.Q_cond=self.Inlet.F*(self.Inlet.h-self.Outlet.h)

        #self.Outlet.calculate_properties()
        self.df = pd.DataFrame({'Condenser': [self.Inlet.fluid,self.Outlet.F,self.Tl_sat-273.15,self.Hl_sat/1000,self.Sl_sat/1000,self.To-273.15,self.Ho/1000,self.So/1000,self.Q_cond/1000,], },
                      index = ['fluid','Outlet.F',"Tl_sat(°C)",    "Hl_sat(kJ/kg)",      "Sl_sat(kJ/kg-K)",       "To(°C)",      "Ho(kJ/kg)",       "So(kJ/kg-K)",     "Q_cond(kW)", ])

      