from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI

class Object:
    def __init__(self):
        self.IsenEff=0.7
        self.Inlet=FluidPort() 
        self.F=0.1
        self.Inlet.F=self.F
        self.Outlet=FluidPort()
        self.So_is=0
        self.To_is=0
        self.Ho_is=0
        self.LP=1*100000
        self.Ho=0
        self.To=0
        self.So=0
   
        self.Q_turb=0
   
        
    def calculate (self):
        self.F=self.Inlet.F
        self.So_is = PropsSI('S','P',self.Inlet.P,'H',self.Inlet.h,self.Inlet.fluid)
        self.To_is=PropsSI('T','P',self.LP,'S',self.So_is,self.Inlet.fluid)
        self.Ho_is = PropsSI('H','P',self.LP,'S',self.So_is,self.Inlet.fluid)
        
        self.Ho = (self.Ho_is-self.Inlet.h)*self.IsenEff+self.Inlet.h
        self.To=PropsSI('T','P',self.LP,'H',self.Ho,self.Inlet.fluid)
        self.So=PropsSI('S','P',self.LP,'H',self.Ho,self.Inlet.fluid)      
        
        self.Outlet.fluid=self.Inlet.fluid
        self.Outlet.h=self.Ho
        self.Outlet.F=self.F
        self.Outlet.P=self.LP
        
        self.Q_turb=-self.Inlet.F*(self.Ho-self.Inlet.h)
        
        