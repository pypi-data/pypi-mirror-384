from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 
from datetime import datetime
from scipy.optimize import fsolve

import math

class Object:
    def __init__(self):
        self.Timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   
        self.Air_Inlet = FluidPort(fluid='air', F=15/3.6,P=101325)
        self.Air_Outlet = FluidPort(fluid='air',F=15/3.6,P=101325)
        self.Fluid_Inlet = FluidPort(fluid='water',P=101325)
        self.Fluid_Outlet = FluidPort(fluid='water',P=101325)

#########paramètre de design
        self.fluid="water" # "hydrocarbure léger" , "water" 
        self.Ti_fluid=165 #	Température d'entrée du fluide de procédé
        self.To_fluid=None	#Température de sortie Fluide de Procédé
        self.Cp_fluid=None	#Capacité thermique massique J/ Kg K
        self.F_fluid=None	#débit du fluide procédé     
        self.Ti_air=25	#température d'entrée de l'air ambiant
        self.rho_air=None #1.201	
        self.Cp_air=None
        self.TminAmb=5 #	température minimale ambiante
        
        self.largeur_baie=6 # Largeur (m)	3,5
        self.L_tube=10
        self.L_tube_max=18 # Tube	Longueur max (m)	18

        self.U=None
        self.DTLM=None
        self.UA=None

###################géométrie de référence
        self.L_tube=3 
        self.diametre_ext_tube=25.4 # Diamètre extérieur (mm)	25,4
        self.rapport_ailetage=20.5 # Rapport d'ailetage (m2 aileté/m2 nu)	20,5
        self.pas_triangulaire=63.5#     Baie	pas triangulaire (mm)	63,5
 
        self.nb_faisceaux=2# Nombre de faisceau	2

        self.rendement_statique_ventilateur=0.6# Rendement statique	0,6
        self.Pression_statique_ventilateur=150# Pression statique	150
        self.rendement_transmission_ventilateur=0.95# Rendement de trasmission	0,95

        

        #résult
        self.Qth_fluid=None
        self.nb_rangs=None
        self.Ntr=None #nombre de tube par rang
        self.Ntf=None # nombre de tube par faisceau
        self.Sf=None #Surface faciale Sf m2
        self.Stn=None #Surface de tube Nus
        self.surface_ailetee=None # Surface Ailetée
        self.V_air=None #m/s
        self.Qth_air=None

        self.nb_baie_design=None
        self.S_sol_design=None
        self.Stn_design=None
        self.surface_ailetee_design=None
        self.dmin_vent=None
        self.d_vent=None

        #Nombres Adim
        self.R1=None
        self.R2=None
        self.R3=None

        #Détermination de la ventilation
        self.nb_vent_baie=2
        self.S_vent=None

        self.F_vent_m3h=None
        self.F_air_m3h=None


                # Détermination du nombre de rangs 

        if (self.Ti_fluid-self.Ti_air)<=10:
           self.nb_rangs=3
        if (self.Ti_fluid-self.Ti_air)<=50 and (self.Ti_fluid-self.Ti_air)>10:
            self.nb_rangs=4
        if (self.Ti_fluid-self.Ti_air)<=90 and (self.Ti_fluid-self.Ti_air)>50:
            self.nb_rangs=6
        if (self.Ti_fluid-self.Ti_air)<=140 and (self.Ti_fluid-self.Ti_air)>90:
            self.nb_rangs=7
        else:
            self.nb_rangs=3

        self.df = pd.DataFrame()
        
    def calculate(self):

        self.Ti_fluid=self.Fluid_Inlet.T-273.15
        self.Cp_fluid=self.Fluid_Inlet.cp
        self.F_fluid=self.Fluid_Inlet.F
        self.fluid=self.Fluid_Inlet.fluid

        self.Ti_air=self.Air_Inlet.T-273.15
        self.Cp_air=self.Air_Inlet.cp
        self.rho_air=self.Air_Inlet.rho
 

        #Détermination de la quantité de chaleur à évacuer :
        self.Qth_fluid=self.F_fluid*self.Cp_fluid*(self.Ti_fluid-self.To_fluid)

        #Détermination du coefficient de transmission thermique globale
        if self.U is None:
            if self.fluid=="water":
                self.U=850
            if self.fluid=="hydrocarbure léger":
                self.U=540
            if self.fluid=="Gasoil léger":
                self.U=400


  

        # Détermination de la géométrie de la baie

        # le nombre de tubes par rang
        self.Ntr=int((self.largeur_baie)/2/(self.pas_triangulaire*10**(-3)))

        self.Ntf=self.nb_rangs*self.Ntr

        if self.L_tube>=self.L_tube_max:
            self.L_tube=self.L_tube_max

        self.Sf=self.largeur_baie*self.L_tube

        self.Stn=round(self.Ntf*math.pi*self.diametre_ext_tube*10**(-3)*self.L_tube*self.nb_faisceaux,2)
        self.surface_ailetee=self.Stn*self.rapport_ailetage

        if self.nb_rangs==4:
            self.V_air=3.55
        if self.nb_rangs==5:
            self.V_air=3.1
        if self.nb_rangs==6:
            self.V_air=2.75
        if self.nb_rangs==7:
            self.V_air=2.5

        self.R3=(self.Ti_fluid-self.To_fluid)/(self.Ti_fluid-self.Ti_air)
        self.R1=(self.U*self.Stn)/(self.V_air*self.Sf*self.rho_air*self.Cp_air)
        # Utilisation de fsolve pour trouver R2
        equation = lambda R2: self.R1 - math.log((1 - R2) / (1 - self.R3)) / ((self.R3 / R2) - 1)
        R2 = fsolve(equation, x0=0.1)[0]  # x0 est la valeur initiale, ajustez selon vos besoins
        self.R2 = R2  # Mettez à jour self.R2 avec la valeur calculée

        #calcul de self.To_air
        self.To_air=round(self.Ti_air+self.R2*(self.Ti_fluid-self.Ti_air),1)
        self.DTLM=((self.Ti_fluid-self.To_air)-(self.To_fluid-self.Ti_air))/math.log((self.Ti_fluid-self.To_air)/(self.To_fluid-self.Ti_air))
        


        self.Qth_air=self.V_air*self.Sf*self.rho_air*self.Cp_air*(self.To_air-self.Ti_air)

        self.nb_baie=self.Qth_fluid/self.Qth_air
        self.nb_baie_design=round(self.Qth_fluid/self.Qth_air,0)
        self.S_sol_design=self.nb_baie_design*self.largeur_baie*self.L_tube
        self.Stn_design=self.nb_baie_design*self.Stn
        self.surface_ailetee_design=self.nb_baie_design*self.surface_ailetee
        self.UA=self.Qth_fluid/self.DTLM
        self.Qth=self.UA*self.DTLM
 




        #design 
        
        self.dmin_vent=(4*0.4*self.Sf/math.pi/self.nb_vent_baie)**(0.5)
        if self.d_vent<=self.dmin_vent:
            self.d_vent=self.dmin_vent

  
        self.F_vent_m3s=round(self.V_air*self.Sf*(273.15+self.Ti_air)/((273.15+self.TminAmb)*self.nb_vent_baie),1)
        self.F_vent_m3h=self.F_vent_m3s*3600


        self.P_vent=self.F_vent_m3h/3600*self.Pression_statique_ventilateur/(self.rendement_statique_ventilateur*self.rendement_transmission_ventilateur)*(273.15+self.Ti_air)/(273.15+self.TminAmb)
        self.P_vent = math.ceil(self.P_vent / 5000) * 5000 #arrondir la puissance du ventillateur à installer

        self.nb_vent=self.nb_vent_baie*self.nb_baie_design
        self.F_air_m3h=self.nb_vent*self.F_vent_m3h
        self.nb_tube=self.Ntf*self.nb_vent
        self.P_elec=self.P_vent*self.nb_vent
                                  

        self.Fluid_Outlet.T=self.To_fluid+273.15
        self.Fluid_Outlet.F=self.Fluid_Inlet.F
        self.Fluid_Outlet.P=self.Fluid_Inlet.P
        self.Fluid_Outlet.calculate_properties()

        self.Air_Outlet.T=self.To_air+273.15
        self.Air_Outlet.F=self.Air_Inlet.F
        self.Air_Outlet.P=self.Air_Inlet.P-self.Pression_statique_ventilateur
        self.Air_Outlet.calculate_properties()

        self.df = pd.DataFrame({'DTLM_HEX': [self.Timestamp,self.Qth_fluid/1000,self.U,self.nb_rangs,self.Ntr,self.Ntf,self.Sf,
                                             self.Stn,self.surface_ailetee,self.V_air,self.To_air,self.Qth_air/1000,self.nb_baie,self.nb_baie_design,self.S_sol_design,self.Stn_design,self.surface_ailetee_design,self.dmin_vent,self.d_vent,self.F_vent_m3h,self.F_vent_m3s,
                                             self.P_vent/1000,self.F_air_m3h,self.nb_tube,self.P_elec/1000,self.nb_vent
                                             ], },
                      index = ['Timestamp','quantité de chaleur à évacuer : Qth_fluid (kW)','coefficient de transmission thermique globale :U ((W/m2-K))','self.nb_rangs','nb tubes par rangée','nb tubes par faisceaux','Surface faciale Sf',
                               'Surface des tubes nus Stn','self.surface_ailetee','self.V_air','self.To_air','Qth_air(kW)','self.nb_baie','self.nb_baie_design',"Surface au sol de l'équipement","Surface d'échange nue (m2)","Surface Aileté totale","diamètre min d'un ventilateur","diamètre d'un ventilateur retenu","self.F_vent_m3h","self.F_vent_m3s","P_vent (kW)","self.F_air_m3h","self.nb_tube",'P_elec (kW)','self.nb_vent'])     


