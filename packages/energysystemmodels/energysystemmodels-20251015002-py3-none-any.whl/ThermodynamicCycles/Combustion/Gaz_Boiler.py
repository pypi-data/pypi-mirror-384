from thermochem import burcat, combustion
from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 

class Object:
    def __init__(self):
        self.air_Inlet=FluidPort() 
        self.air_Inlet.fluid="air"
        self.Inlet=FluidPort()
        self.Inlet.fluid="water"
        self.Outlet=FluidPort()
        self.Outlet.fluid="water"

    def calculate (self):
        #calcul de la température d'air
        self.Ti_air=PropsSI('T','P',self.air_Inlet.P,'H',self.air_Inlet.h,self.air_Inlet.fluid) # K
        print("self.Ti_air",self.Ti_air)
        #print("self.Ti_air=",self.Ti_air)