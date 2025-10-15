from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 

class Object :
    def __init__(self):
        self.Inlet=FluidPort() 
        self.Outlet=FluidPort()
       
  
        self.Q_exp=0

         #Output Data
        self.df=[]

    def calculate(self):
        self.Outlet.fluid=self.Inlet.fluid
        #print(self.Inlet.h)
        self.Outlet.h = self.Inlet.h
        #print("Ho=",self.Outlet.h)
        self.Outlet.T=PropsSI('T','P',self.Outlet.P,'H',self.Outlet.h,self.Inlet.fluid)
     
        #print("self.Outlet.T °C=",self.Outlet.T-273.15)
        #print("valv self.Outlet.P=",self.Outlet.P)
        self.Outlet.S =PropsSI('S','P',self.Outlet.P,'H',self.Outlet.h,self.Inlet.fluid)
        
        
        self.Outlet.F=self.Inlet.F
        #self.Outlet.P=self.LP
        #pour calculate une detente avec travail exterieur :(=0)
        self.Q_exp=self.Inlet.F*(self.Outlet.h-self.Inlet.h)

        self.Outlet.calculate_properties()
        
        self.df = pd.DataFrame({'Expansion_Valve': [self.Inlet.fluid,self.Outlet.F,self.Outlet.T-273.15, self.Outlet.h/1000, self.Outlet.S/1000,], },
                      index = ['fluid','Outlet.F', "To(°C)", "Ho (kJ/kg)", "So(kJ/kg-K)", ])


       