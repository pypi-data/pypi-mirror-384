#pip install thermochem
#http://garfield.chem.elte.hu/Burcat/BURCAT.TRH

from thermochem import burcat, combustion
from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 

# from scipy import *
# from pylab import *
# #from scipy.optimize import bisect   
# from scipy.optimize import fsolve  

# import numpy as np

class Object:
    def __init__(self):

        self.T_fumee_degC=110 #température des fumée
        self.Q_loss=None #pertes fumée.
        self.eta_HHV=None #rendement PCS
        self.eta_LHV=None #rendement PCI

        self.air_Inlet=FluidPort() 
        self.air_Inlet.fluid="air"
        self.Inlet=FluidPort()
        self.Inlet.fluid="water"
        self.Outlet=FluidPort()
        self.Outlet.fluid="water"

        self.fuel=None
        self.burca_name=None
        self.phi=None
        self.AIR_EXCESS=None
        self.products_O2_molRatio=None
        self.fuel_Sdensity=None #in kg/m3 at 101325 Pa, 273.15+15 °C
        
        #Fuel Flow rate
        self.F_fuel_Sm3h=None
        self.F_fuel_m3h=None
        self.F_fuel_kgh=None
        self.F_fuel_kgs=None
        self.Nominal_Power_kW=None

        #Heating value
        self.LHV_kJmol=None
        self.LHV_kJkg=None
        self.LHV_kWhJkg=None
        self.LHV_kWhSm3=None

        self.HHV_kJmol=None
        self.HHV_kJkg=None
        self.HHV_kWhkg=None
        self.HHV_kWhSm3=None

        self.Ti_air=None #température d'entrée d'air
        self.Tflame=None
        self.Tflame_degC=None
        self.air_mm=None

        #output data
        self.df=[]

    def calculate (self):
        #calcul de la température d'air
        self.Ti_air=PropsSI('T','P',self.air_Inlet.P,'H',self.air_Inlet.h,self.air_Inlet.fluid) # K
        print("self.Ti_air",self.Ti_air)
        #print("self.Ti_air=",self.Ti_air)

        db = burcat.Elementdb()

        if self.fuel=="methane" or self.fuel=="CH4" or self.fuel=="NG" or self.fuel=="GN" or self.fuel=="Gaz Naturel":
            self.burca_name="CH4   RRHO"
        self.fuel= db.getelementdata(self.burca_name)

        #print(self.fuel.elements)
        #print(self.fuel.cp,"J/kg K at 298 K")
        #print(self.fuel.cp_(273.15+1100),"J/kg K at T in K")
        self.fuel_Sdensity=self.fuel.density(101325, 273.15+15)

        #*****************************calcul de l'excés d'air********************************************
        if self.products_O2_molRatio is not None:
            #balance  at phi=1
            bal0=combustion.balance(self.fuel, 1, 1)
            #print("bal0[0]['O2']",bal0[0]['O2'])
            self.phi=(1-self.products_O2_molRatio*(1+3.76))/(1+(self.products_O2_molRatio/bal0[0]['O2']))
            #print("self.phi = ",self.phi)
           
        if self.AIR_EXCESS is not None:
            self.phi=1/((self.AIR_EXCESS)+1)
            #print("self.phi=",self.phi)
        if self.phi is not None:
            self.AIR_EXCESS=((1/self.phi)-1)
            #print("AIR_EXCESS= ",self.AIR_EXCESS)

        #***************************Calcul du pouvoir calorifique et les propriétés de la réaction********************************************
        combustor = combustion.SimpleCombustor(self.fuel,self.phi,db)
        #print("cp product",round(combustor.products.cp, 6),'J/kg-K')
        #print("heat of combustion",round(combustor.heat_of_comb(self.Ti_air), 2),'J/kg of fuel at Ti air')
        print('combustor.lower_heating_value',combustor.lower_heating_value)
        print('combustor.hight_heating_value',combustor.heat_of_comb(self.Ti_air))
        print('PCS/PCI',combustor.heat_of_comb(self.Ti_air)/combustor.lower_heating_value)

        self.LHV_kWhkg=round(combustor.heat_of_comb(self.Ti_air)/3600000, 2)
        self.LHV_kJmol=round(combustor.heat_of_comb(self.Ti_air)/1000*self.fuel.mm, 2)
        self.LHV_kJkg=round(combustor.heat_of_comb(self.Ti_air)/1000, 2)
        self.LHV_kWhSm3=self.LHV_kWhkg*self.fuel_Sdensity
        if self.burca_name=="CH4   RRHO":
            self.HHV_kWhkg=self.LHV_kWhkg*1.109
            self.HHV_kJmol=self.LHV_kJmol*1.109
            self.HHV_kJkg=self.LHV_kJkg*1.109
            self.HHV_kWhSm3=self.LHV_kWhSm3*1.109
        #print(combustor.reactants)
        #print(combustor.products)

        #Combustion balance
        am=1 #1 mol of fuel
        bal=combustion.balance(self.fuel, am, self.phi)
        print(bal)
        self.products_O2_molRatio=bal[1]['O2']/(bal[0]['fuel']+bal[0]['O2']+bal[0]['N2'])
        #print("products_O2_molRatio",self.products_O2_molRatio)
        self.AIR_EXCESS=((1/self.phi)-1)
        #print("self.phi=",self.phi)
        #print("AIR_EXCESS= ",self.AIR_EXCESS)

        #Calculate Heat Power and adiabatic temperature
        self.Tflame=round(combustor.adiabatic_flame_temp(self.Ti_air)[0], 1)
        self.Tflame_degC=round(combustor.adiabatic_flame_temp(self.Ti_air)[0]-273.15,1)
     
        
        #print(combustor.reactants.mm)
        #print(combustor.products.mm)
        #print(bal[0]['fuel'])
        #print(bal[0]['O2'])

        db2 = burcat.Elementdb()
        self.air = db2.getelementdata("AIR")
        self.air_mm=self.air.mm
        print(self.air_mm)

        if self.Nominal_Power_kW is None:
            self.F_air_mols=self.air_Inlet.F/self.air_mm/(1+3.76)
            #print(self.F_air_mols)
            self.F_fuel_mols=self.F_air_mols*bal[0]['fuel']/bal[0]['O2']
            #print(self.F_fuel_mols)
            self.F_fuel_kgs=self.F_fuel_mols*self.fuel.mm
            self.F_fuel_Sm3s=self.F_fuel_kgs/self.fuel_Sdensity
            self.F_fuel_Sm3h=self.F_fuel_Sm3s*3600

            #print(self.F_fuel_kgs)
            #bal2=combustion.balance(self.fuel, self.F_fuel_mols, self.phi)
            #print(bal2)
            
            
            self.Q_comb_HHV=self.HHV_kJkg*self.F_fuel_kgs*1000
            #print(self.Q_comb_LHV,"W")
            #print("self.HHV_kJkg",self.LHV_kJkg)

        
        #*********************************************recalcul du débit de combustible pour une puissance données*****************************
        if self.Nominal_Power_kW is not None:
            self.Q_comb_HHV=self.Nominal_Power_kW*1000
            self.F_fuel_kgs=self.Q_comb_HHV/1000/self.HHV_kJkg
            self.F_fuel_mols=self.F_fuel_kgs/self.fuel.mm
            #recalcul du nb mol air
            self.F_air_mols=self.F_fuel_mols/(bal[0]['fuel']/bal[0]['O2'])
            #recalcul du débit d'air
            self.air_Inlet.F=self.F_air_mols*(self.air_mm*(1+3.76))

        self.F_fuel_Sm3s=self.F_fuel_kgs/self.fuel_Sdensity
        self.F_fuel_Sm3h=self.F_fuel_Sm3s*3600
        self.Q_comb_LHV=self.LHV_kJkg*self.F_fuel_kgs*1000

        self.F_products_kgs=self.F_fuel_kgs+self.air_Inlet.F
        
        # Calculez la chaleur sensible perdue due à la différence de température
        delta_T_degC =  self.T_fumee_degC-(self.Ti_air -273.15)  # Différence de température
        Q_sensible_loss = self.F_products_kgs * delta_T_degC * combustor.products.cp

        # Calculez la chaleur latente perdue due à la condensation de la vapeur d'eau
        H2O_molar_mass = 18.01528  # Masse molaire de H2O en g/mol
        H2O_molar_fraction = bal[1]['H2O'] / (bal[0]['fuel'] + bal[0]['O2'] + bal[0]['N2'])
        H2O_mass_fraction = H2O_molar_fraction * H2O_molar_mass / 1000  # Convertir en kg/kg de produits
        latent_heat_of_condensation = 2500  # Chaleur latente de condensation de la vapeur d'eau en kJ/kg

        Q_latent_loss = self.F_products_kgs * H2O_mass_fraction * latent_heat_of_condensation*1000
        print("Q_latent_loss============",Q_latent_loss)

        # Calculez la perte totale
        self.Q_loss = Q_sensible_loss + Q_latent_loss

        # Recalcul du rendement
        self.Q_util = self.Q_comb_HHV - self.Q_loss
        self.eta_HHV = self.Q_util / self.Q_comb_HHV
        self.eta_LHV = self.Q_util / self.Q_comb_LHV
        

        self.df = pd.DataFrame({'Boiler': [self.fuel,self.F_fuel_Sm3h,self.F_fuel_kgs,self.fuel.mm,self.fuel_Sdensity,self.HHV_kWhSm3,self.products_O2_molRatio,self.phi,self.AIR_EXCESS,self.Q_comb_LHV,self.Q_comb_HHV,self.Tflame_degC,self.air_Inlet.F,self.F_products_kgs,self.Q_loss,self.Q_util,self.eta_HHV,self.eta_LHV], },
                      index = ['fuel','F_fuel_Sm3h','F_fuel_kgs','molar mass (kg/mol)',"fuel_Sdensity (Kg/Sm3)",'HHV_kWhSm3','products_O2_molRatio','phi','AIR_EXCESS','Q_comb_LHV(W)','Q_comb_HHV(W)','Tflame_degC','air_Inlet.F','F_products_kgs','self.Q_loss','self.Q_util','self.eta_HHV','self.eta_LHV'])
       

        #N2 : 28,0134 g/mol
       # O2 : 32 g/mol
      # CH4 : 16,04 g/mol


        

            
            
            
            


