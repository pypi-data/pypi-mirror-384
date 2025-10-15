from datetime import datetime
from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 
import math

#http://cregen.free.fr/A%E9raulique/Guide%20de%20l%27a%E9raulique.pdf
#https://www.thermexcel.com/french/ressourc/calcul_perte_de_charge_lineaire.htm

class Object:
    def __init__(self):
        self.Timestamp = None
        self.Inlet = FluidPort() 
        self.Outlet = FluidPort()
        self.df = []

        self.delta_P=None #Perte de charge
        self.d_hyd=None #Diamètre hydraulique
        self.a=None #largeur de la conduite réctangulaire
        self.b=None #hauteur de la conduite réctangulaire
        self.S=None #Section de la conduite droite

        self.L=None #Longueur de la conduite droite
        self.lambda_=None #Coefficient pertes de charge
        self.rho=None #Masse volumique du fluide (kg/m3)
        self.epsilon_r=None #Rugosité réduite de la conduite
        self.epsilon=0.0002 #Rugosité absolue de la conduite en m
        self.u=None #Vitesse moyenne du fluide dans la conduite
        self.mu=None #Viscosité dynamique du fluide (Pa.s)

        self.Re=None #Nombre de Reynolds


    def calculate(self):
        # Vérifier si Timestamp est None, sinon utiliser le temps actuel
        if self.Timestamp is None:
            self.Timestamp = datetime.now()
        
        if self.a is not None and self.b is not None:
            self.d_hyd = 1.3*(self.a*self.b)**0.625/(self.a+self.b)**0.25 #Calcul du diamètre equivalent selon l'ashrae
            self.d_hyd = 4*self.a*self.b/(2*self.a+2*self.b) #Calcul du diamètre hydraulique 
            self.S = self.a*self.b #Calcul de la section de la conduite droite
        else:
            self.S = math.pi*(self.d_hyd/2)**2 #Calcul de la section de la conduite droite

        self.epsilon_r=self.epsilon/self.d_hyd #Calcul de la rugosité réduite
        
        self.mu=self.eta = PropsSI('V', 'P', self.Inlet.P, 'H', self.Inlet.h, self.Inlet.fluid) #Calcul de la viscosité dynamique du fluide
        self.rho = PropsSI('D', 'P', self.Inlet.P, 'H', self.Inlet.h, self.Inlet.fluid)
        self.u=(self.Inlet.F/self.rho)/(self.S) #Calcul de la vitesse moyenne du fluide dans la conduite
        self.Re=self.calculate_reynolds_number(self.rho,self.u,self.d_hyd,self.mu)
       
        if self.Re<2000:
            self.lambda_=64/self.Re
        else:
            #Blasius : pour les tubes lisses
            #lambda_=0.316/(self.Re**0.25) #if self.Re>=2000 and self.Re<=100000
            #utiliser Colbrook equation qui correspond sensiblement aux données de l’abaques de Moody 
     
            f=0.316/(self.Re**0.25)
            print(f"Initial f: {f}")
            f_old = 0  
            while abs(f-f_old)>0.0000001:
                f_old=f
                f=1/(-2*math.log10(2.51/(self.Re*math.sqrt(f))+self.epsilon_r/3.71))**2
            self.lambda_=f
      
        self.delta_P=(self.lambda_/self.d_hyd)*(self.rho*self.u**2)/2*self.L #Calcul de la perte de charge
        
        self.Outlet.F=self.Inlet.F
        self.Outlet.P=self.Inlet.P-self.delta_P
        self.Outlet.fluid=self.Inlet.fluid
       
        # Créer un DataFrame avec la Timestamp
        self.df = pd.DataFrame({'StraightPipe': [self.Timestamp,self.d_hyd,self.mu,self.rho,self.S,self.u,self.Re,self.epsilon_r,self.lambda_,self.delta_P]},
                               index=['Timestamp','d_hyd','viscosité dynamique (Pa.s)','masse volumique (kg/m3)','section (m2)','vitesse moyenne (m/s)','Reynolds','rugosité réduite','coefficient de perte de charge','perte de charge (Pa)'])

    def calculate_reynolds_number(self,rho, u,d_hyd, mu):
        # Nombre de Reynolds
        Re = (rho*u*d_hyd)/mu
        return Re
