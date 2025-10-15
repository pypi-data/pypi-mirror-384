from AHU.air_humide import air_humide
from AHU.air_humide import air_humide_NB
#from modules.FreshAir import FreshAir
from AHU.AirPort.AirPort import AirPort
import pandas as pd

from scipy import *
from pylab import *
from scipy.optimize import bisect   
from scipy.optimize import fsolve   
  
class Object:
    def __init__(self):
        self.Inlet=AirPort() 
        self.Outlet=AirPort()
        
        self.P_drop=0 #perte de charge
        
    
        #parameter
        #type d'humidification
        self.HumidType="adiabatique"
        #consigne Humidité relative
        self.RH_out_target=60
        
        self.wo_target=10
        
        # données air amont
        self.T_in=18
        self.RH=20
        self.hi=24.522
        self.wi=10
        self.F=20000
        self.Llv=2500.8 #kJ/kg
        self.T_vap=100
        self.Cpv=1.8262 #KJ/kg-K
        self.h_vap=self.Cpv*self.T_vap+self.Llv #2676 kJ/kg à 100 °C
       # print("self.h_vap",self.h_vap)
        
        
        # calcul Outlet Coil
        self.Pv_sat_out=0
        self.RH_out=0
        
        self.T_out=0
        self.F_water=0
        self.ho=0
        self.Q_th=0
        
        self.P=0
        self.id=None #ID
        self.df = None  # DataFrame pour afficher les résultats
        
        
    def calculate(self):
        
        self.wi=self.Inlet.w
        self.P=self.Inlet.P
        self.hi=self.Inlet.h
        self.F=self.Inlet.F
        
        if self.wo_target>self.wi:
            # print("self.wo_target>self.wi",self.wo_target,self.wi)
               
            if self.HumidType=="adiabatique" :
                # print("calcul Humidifier adiabatique réussi")
                #Bilan de masse
                self.ho=self.hi
                def syst(var): # définition du système
                    self.Pv_sat_out,self.T_out, self.RH_out, = var[0], var[1], var[2] # définition des variables
                    eq1 =self.Pv_sat_out-air_humide.Air_Pv_sat(self.T_out)
                    eq2 =self.wo_target-air_humide.Air_w(Pv_sat=self.Pv_sat_out,RH=self.RH_out,P=101325)
                    eq3 =self.hi-air_humide.Air_h(T_db=self.T_out, w=self.wo_target)
                    res = [eq1, eq2, eq3]
                    return res
                #self.ho=self.hi
                x0, y0, z0 = 0, 0, 0 # Initialisation de la recherche des solutions numériques
                sol_ini = [x0, y0, z0]
    
                x=fsolve(syst, sol_ini)
               # print(x)
                self.F_dry=(self.Inlet.F)/(1+(self.Inlet.w/1000))
                #self.F_dry=(self.Inlet.F)/air_humide_NB.Air3_Vs(self.Inlet.w/1000,self.Inlet.P,self.Inlet.h) #[m3/s] / [m3/kg air sec]  = [kg air sec/s]
                self.F_water=self.F_dry*(self.wo_target-self.wi)/1000 #débit d'eau en kgH2O/s
               # print("self.F",self.F,"\n","self.F_water",self.F_water,"\n","self.T_out",self.T_out,"\n","self.wo_target",self.wo_target,"\n","self.RH_out",self.RH_out,"\n")
            
            if self.HumidType=="vapeur" :
              #  print("hvap=",self.h_vap)
                def syst(var): # définition du système
                    self.Pv_sat_out,self.T_out, self.RH_out,self.ho = var[0], var[1], var[2], var[3] # définition des variables
                    eq1 =self.Pv_sat_out-air_humide.Air_Pv_sat(self.T_out)
                    eq2 =self.wo_target-air_humide.Air_w(Pv_sat=self.Pv_sat_out,RH=self.RH_out,P=101325)
                    eq3 =self.ho-air_humide.Air_h(T_db=self.T_out, w=self.wo_target)
                    eq4 =self.ho-self.hi-(self.wo_target-self.wi)/1000*self.h_vap
                    res = [eq1, eq2, eq3, eq4]
                    return res
                #self.ho=self.hi
                x0, y0, z0, t0 = 0, 0, 0, 0 # Initialisation de la recherche des solutions numériques
                sol_ini = [x0, y0, z0, t0]
    
                x=fsolve(syst, sol_ini)
               # print(x)
                self.F_dry=(self.Inlet.F)/(1+(self.Inlet.w/1000))
                #self.F_dry=(self.Inlet.F)/air_humide_NB.Air3_Vs(self.Inlet.w/1000,self.Inlet.P,self.Inlet.h) #[m3/s] / [m3/kg_air_sec]  = [kg_air_sec/s]
                self.F_water=self.F_dry*(self.wo_target-self.wi)/1000 #débit d'eau en kgH2O/s = [kg_air_sec/s] * kg_H20 /kg_air_sec
                # print("self.F_water=",self.F_water)
                
              #  print("self.F",self.F,"\n","self.F_water",self.F_water,"\n","self.T_out",self.T_out,"\n","self.wo_target",self.wo_target,"\n","self.RH_out",self.RH_out,"\n")
            
                 #connecteur   
             
             #modele perte de charge
             #self.P_drop=f(self.F)
              
            self.Outlet.w=self.wo_target
            self.Outlet.P=self.Inlet.P-self.P_drop
            self.Outlet.h=self.ho
            self.F_dry=(self.Inlet.F)/(1+(self.Inlet.w/1000))
            #self.F_dry=(self.Inlet.F)/air_humide_NB.Air3_Vs(self.Inlet.w/1000,self.Inlet.P,self.Inlet.h) #[m3/s] / [m3/kg_air_sec]  = [kg_air_sec/s]
            self.Outlet.F=self.F_dry*(1+(self.Outlet.w/1000))
            self.Outlet.F_dry=self.F_dry
            #self.Outlet.F=self.F_dry*air_humide_NB.Air3_Vs(self.Outlet.w/1000,self.Outlet.P,self.Outlet.h) #[kg air sec/s] * [m3/kg air sec] =[m3/s]
           # self.F_water=self.F_dry*(self.wo_target-self.wi)/1000
            self.Q_th=(self.Outlet.h-self.Inlet.h)*self.F_dry
        else:
            self.Outlet.w=self.Inlet.w
            self.Outlet.P=self.Inlet.P-self.P_drop
            self.Outlet.h=self.Inlet.h
            self.F_dry=(self.Inlet.F)/(1+(self.Inlet.w/1000))
            self.Outlet.F=self.F_dry*(1+(self.Outlet.w/1000))
            self.Outlet.F_dry=self.F_dry
            #self.F_dry=(self.Inlet.F)/air_humide_NB.Air3_Vs(self.Inlet.w/1000,self.Inlet.P,self.Inlet.h) #[m3/s] / [m3/kg_air_sec]  = [kg_air_sec/s]
            #self.Outlet.F=self.F_dry*air_humide_NB.Air3_Vs(self.Outlet.w/1000,self.Outlet.P,self.Outlet.h) #[kg air sec/s] * [m3/kg air sec] =[m3/s]
            self.F_water=0
            self.Q_th=0
            # print("pas d'humidification")
            
        self.Outlet.update_properties()
        # Préparation des données pour créer un DataFrame et afficher les résultats
   
        self.df = pd.DataFrame({'Humidifier': [ self.id, round(self.Outlet.T, 1), round(self.Outlet.RH, 1), 
                round(self.Outlet.F, 3), round(self.Outlet.F_dry, 3), 
                round(self.Outlet.P, 1), round(self.Outlet.P / 100000, 1), 
                round(self.Outlet.h, 1), round(self.Outlet.w, 3), 
                round(self.Outlet.Pv_sat, 1),self.HumidType,round(self.F_water, 6),round(self.Q_th/1000, 3)], },
                      index = ['ID', 'Outlet.T (C)', 'Outlet.RH (%)', 'Outlet.F (kg/s)', 
                'Outlet.F_dry (kg/s)', 'Outlet.P (Pa)', 'Outlet.P/10^5 (bar)', 
                'Outlet.h (kJ/kg)', 'Outlet.w (g/kgdry)', 'Outlet.Pv_sat (Pa)','HumidType','F_water (kg/s)','Q_th (kW)'])