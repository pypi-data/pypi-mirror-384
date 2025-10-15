from ThermodynamicCycles.FluidPort.FluidPort import FluidPort


from CoolProp.CoolProp import PropsSI

class Object:
    def __init__(self):
        
        ####parameter
        self.eta_is=0.7
        self.MecEff = 1 #"rendement mecanique" 
        self.VolEff = 0.99 # "rendement volumetrique";
        self.cyl= 0.02 #cylindrée en m3
        self.f=50 #SIunits.Frequency rotation
        self.p = 1 #"Nb pole/2" 
        #rendement volumetrique
        self.a0=0.95 #piston, à vis= 0.9
        self.a1=0.038 #piston, à vis= 0.008
        #rendement isentropique
        self.K1=0.8
        self.K2=0.0037
        self.K3=-0.16
        self.R1=7
        self.R2=1.2
        
        
        self.Inlet=FluidPort() 
        self.F=0.1
       # self.Inlet.F=self.F
        self.Outlet=FluidPort()
        self.So_is=0
        self.To_is=0
        self.Ho_is=0
        self.HP=15*100000
        self.Ho_ref=0
        self.To_ref=0
        self.So_ref=0
        self.Tdischarge_target=80
        self.To=0
        
        
        self.Pu = 50000 # "Puissance utile";
        self.Q_losses=0
        
        #######################################################Dymola
        self.Pel=1000 #Puissance electrique W
        self.Pth= 50000 ## Puissance mécanique theorique isentropique
        self.VitesseDeRotation=0 # "tr/min";
        
        self.Inlet_rho=0 #masse volumique à l'aspiration kg/m3
        self.Vol_Bal=0 #m3/s
        self.Vol_asp=0 #m3/s
        self.Taux=1 #taux de compression
        
        
        
    def calculate (self):
        
        self.Taux=self.HP/self.Inlet.P
        self.eta_is=self.K1+self.K2*(self.Taux-self.R1)**2+self.K3/(self.Taux-self.R2)
        print("self.eta_is=",self.eta_is)
        self.VolEff =self.a0-self.a1*self.Taux
        print("self.VolEff=",self.VolEff)
        self.Inlet_rho = PropsSI('D','P',self.Inlet.P,'H',self.Inlet.h,self.Inlet.fluid)
        print("self.Inlet_rho=",self.Inlet_rho)
        
        self.VitesseDeRotation=(self.f/self.p)*60
        print("self.VitesseDeRotation=",self.VitesseDeRotation)
        
        self.Vol_Bal = self.cyl * (self.VitesseDeRotation / 60)
        print("self.Vol_Bal=",self.Vol_Bal)
        self.F = self.VolEff * self.Vol_Bal * self.Inlet_rho
        print("self.F=",self.F)
        
        self.Vol_asp = self.F / self.Inlet_rho
        print("self.Vol_asp=",self.Vol_asp)
      
      
        #self.F=self.Inlet.F #débit imposé par le compresseur
        self.So_is = PropsSI('S','P',self.Inlet.P,'H',self.Inlet.h,self.Inlet.fluid)
        self.To_is=PropsSI('T','P',self.HP,'S',self.So_is,self.Inlet.fluid)
        self.Ho_is = PropsSI('H','P',self.HP,'S',self.So_is,self.Inlet.fluid)
        
        self.Ho_ref = (self.Ho_is-self.Inlet.h)/self.eta_is+self.Inlet.h
        self.To_ref=PropsSI('T','P',self.HP,'H',self.Ho_ref,self.Inlet.fluid)
        self.So_ref=PropsSI('S','P',self.HP,'H',self.Ho_ref,self.Inlet.fluid)
        
        self.To=self.Tdischarge_target+273.15
        self.Ho=PropsSI('H','P',self.HP,'T',self.To,self.Inlet.fluid)
        self.So=PropsSI('S','P',self.HP,'T',self.To,self.Inlet.fluid)
        
        self.Outlet.fluid=self.Inlet.fluid
        self.Outlet.h=self.Ho
        self.Outlet.F=self.F
        self.Outlet.P=self.HP
        
        self.Pu=self.F*(self.Ho_ref-self.Inlet.h)
        print("self.Pu=",self.Pu)
        
        self.Q_losses=self.F*(self.Ho_ref-self.Ho)
        print("self.Q_losses=",self.Q_losses)
       # print("To_is=",self.To_is-273.15,"H3is=",self.Ho_is,"T3ref=",self.To_ref-273.15,"H3ref=",self.Ho_ref,"To=",self.To-273.15,"Ho=",self.Ho)
       # print("Q_comp=",self.Pu)
       # print("Q_losses=",self.Q_losses)
       # print("self.Inlet.F=",self.Inlet.F)
       
        self.Pth = self.F * (self.Ho_is-self.Inlet.h)
        self.Pel = self.Pth / (self.eta_is * self.MecEff)
        print("self.Pth=",self.Pth)
        print("self.Pel=",self.Pel)
        
        
  
     

     
    

      
     
     

     

     
      
     
      
        
        
    
     
        