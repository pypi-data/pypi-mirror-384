from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 

class Object:
    def __init__(self):
        self.Timestamp=None

        #Input and Output Connector
        self.Inlet=FluidPort() 
        self.Outlet=FluidPort()

        #Input Data
        self.eta_is=0.75
        self.HP_bar=None
        self.Tcond_degC=None
        self.HP=None #self.HP_bar*100000
        self.Tdischarge_target=None #°C
        

        #Initial Values
        self.Inlet.fluid="air"
        self.Inlet.P=None
        self.F=0.1
        self.Inlet.F=self.F

        self.F_Sm3s=None
        self.F_Sm3h=None
        
        #Output Data
        self.df=[]
        self.HeatLossesRatio=0
        self.So_is=0
        self.To_is=0
        self.Ho_is=0
        self.Ho_ref=0
        self.To_ref=0
        self.So_ref=0
        self.To=0
        self.Q_comp=None
        self.Q_losses=0
        self.Ti_degC=0
        
    def calculate (self):


        if self.Tcond_degC is not None:
            self.HP = PropsSI('P','T',self.Tcond_degC+273.15,'Q',1,self.Inlet.fluid)
            print("test HP calculation",self.HP)

        if self.HP_bar is not None:
            self.HP=self.HP_bar*100000
        if self.HP is not None:
            self.HP_bar=self.HP/100000
        
        #Inlet temperature calculation
        self.Ti_degC=PropsSI('T','P',self.Inlet.P,'H',self.Inlet.h,self.Inlet.fluid)-273.15
        
        self.So_is = PropsSI('S','P',self.Inlet.P,'H',self.Inlet.h,self.Inlet.fluid)
        self.To_is=PropsSI('T','P',self.HP,'S',self.So_is,self.Inlet.fluid)
        self.Ho_is = PropsSI('H','P',self.HP,'S',self.So_is,self.Inlet.fluid)
        
        self.Ho_ref = (self.Ho_is-self.Inlet.h)/self.eta_is+self.Inlet.h
        self.To_ref=PropsSI('T','P',self.HP,'H',self.Ho_ref,self.Inlet.fluid)
        self.So_ref=PropsSI('S','P',self.HP,'H',self.Ho_ref,self.Inlet.fluid)
        
               
        if self.Tdischarge_target<=(self.To_ref-273.15):
            self.To=self.Tdischarge_target+273.15
            print("Le compresseur est refroidi")

        if self.Tdischarge_target>(self.To_ref-273.15):  
            self.Tdischarge_target=self.To_ref-273.15    # Passer un compresseur adiabatique
            self.To=self.To_ref
            print("Le compresseur n'est pas refroidi")
        
        self.Ho=PropsSI('H','P',self.HP,'T',self.To,self.Inlet.fluid)
        self.So=PropsSI('S','P',self.HP,'T',self.To,self.Inlet.fluid)
        
        #mass flow rate or Energy Power Calculation

        if self.Q_comp is not None:
            self.F=self.Q_comp/(self.Ho_ref-self.Inlet.h)
        else: # self.Inlet.F is not None:
            self.F=self.Inlet.F
            self.Q_comp=self.F*(self.Ho_ref-self.Inlet.h)
        
        

        self.Q_losses=self.F*(self.Ho_ref-self.Ho)

        self.HeatLossesRatio=self.Q_losses/self.Q_comp

        self.F_Sm3s=self.F/PropsSI("D", "P", 100000*1.01325, "T", (15+273.15), self.Inlet.fluid)
        self.F_Sm3h=self.F_Sm3s*3600

        self.eta_WhSm3=self.Q_comp/self.F_Sm3h
        
        # outlet connector calculation
        self.Outlet.fluid=self.Inlet.fluid
        self.Outlet.h=self.Ho
        self.Outlet.F=self.F
        self.Outlet.P=self.HP

        # Results
        self.df = pd.DataFrame({'Compressor': [self.Timestamp,self.Inlet.fluid,self.F,self.Q_comp/1000, self.Q_losses/1000, self.HeatLossesRatio,self.To_is-273.15,self.eta_WhSm3,self.To_is-273.15,self.Ho_is/1000,self.So_is/1000,self.To_ref-273.15,self.Ho_ref/1000,self.So_ref/1000,self.To-273.15,self.Ho/1000,self.So/1000,self.Outlet.P/100000,], },
                      index = ['Timestamp','comp_fluid','comp_F_kgs','Q_comp(KW)', 'Q_losses(KW)', 'HeatLossesRatio','Tis(°C)','eta_WhSm3',"To_is(°C)","H3is(kJ/kg)","S3is (J/kg-K)","T3ref(°C)","H3ref(kJ/kg)", "S3ref(J/kg-K)",
        "To(°C)", "Ho(kJ/kg)", "So(J/kg-K)","self.Outlet.P (bar)"])

      
       
        
        