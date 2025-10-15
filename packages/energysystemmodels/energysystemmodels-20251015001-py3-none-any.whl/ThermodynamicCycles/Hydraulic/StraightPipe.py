from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 
import math

class Object :
    def __init__(self):

        self.Timestamp=None

        self.Inlet=FluidPort() 
        self.Outlet=FluidPort()
        self.Outlet.callback = self.on_pressure_change  # Associer la fonction de rappel à Outlet.P
        self.df = []
       

        #Paramètres 
        self.Ti = None  # Modelica.Units.SI.Temperature Ti
        self.To = None  # Modelica.Units.SI.Temperature To
        #self.Inlet.fluid = None  # replaceable package fluidEau = Package_thermal.Toolbox.Media.MyThBlD.H2O
        self.roughness = True # Choice of considering surface roughness
        #   //Valeurs usuelles indices de rugosite (K) en mm
        #   //Nature de la surface interieure , Indice rugosite k
        #   //cuivre, plomb, laiton, inox  0,001 a 0,002
        #   //Tube PVC                     0,0015
        #   //Acier inox                   0,015
        #   //tube acier du commerce       0,045 a 0,09
        #   //Acier etire                  0,015
        #   //Acier soude                  0,045
        #   //acier galvanise              0,15
        #   //Acier rouille                0,1 a 1
        #   //fonte neuve                  0,25 a 0,8
        #   //fonte usagee                 0,8 a 1,5
        #   //fonte incrustee              1,5 a 2,5
        #   //tôle ou fonte asphaltee      0,01 a 0,015
        #   //ciment bien lisse            0,3
        #   //Beton ordinaire              1
        #   //beton grossier               5
        #   //bois bien rabote             5
        #   //bois ordinaire               1

        self.d_hyd = 0.04  # Modelica.Units.SI.Diameter d_hyd=0.04 Hydraulic diameter
        self.L = 1  # Modelica.Units.SI.Length L=1 Length
        self.K = 0.0015 * 10**(-3)  # Modelica.Units.SI.Length K=0.0015*10^(-3) Roughness (average height of surface asperities)
        self.alpha = math.pi / 2  # Modelica.Units.SI.Angle alpha=pi/2 inclinaison du tube par rapport a l horizontale
        self.delta_Z = None  # Modelica.Units.SI.Height delta_Z hauteur du tuyau
        self.delta_H = None  # Modelica.Units.SI.Height delta_H perte de pression en m
        self.eta = None  # Modelica.Units.SI.DynamicViscosity eta Dynamic viscosity of fluid
        self.rho = 998.2  # Modelica.Units.SI.Density rho(start=998.2) Density of fluid
        self.delta_P = 80  # Modelica.Units.SI.Pressure delta_P(start=80) perte de pression du aux frottements
        self.diff_P = None  # Modelica.Units.SI.Pressure diff_P dif de pression entre Inlet et Outlet
        self.IN_con = None  # Package_thermal.PressureLoss.StraightPipe.dp_overall_IN_con IN_con
        self.IN_var = None # Modelica.Fluid.Dissipation.PressureLoss.StraightPipe.dp_overall_IN_var IN_var
        self.m_flow = 1  # Modelica.Units.SI.MassFlowRate m_flow(start=1)
        self.perimeter = None
        self.A = None  # Real A(unit="m2") section du tube
        self.V = None  # Real V(unit="m/s")
        self.Re = None  # Real Re
        self.h = 10000  # Real h( start=10000);
        
   

    def on_pressure_change(self):
        """Callback appelé lorsque self.Outlet.P change."""
        print("Détection d'un changement de Outlet.P. Recalcul en cours...")
        self.calculate()


    
    def calculate(self):
        self.m=self.Inlet.F
        self.Ti_degC=-273.15+PropsSI('T','P',self.Inlet.P,'H',self.Inlet.h,self.Inlet.fluid)
        
        # Potentiel (Inlet.h - Outlet.h = 0)  (pas traduit car cela semble être une équation d'énergie)
        self.h = self.Inlet.h
        # isenthalpic state transformation (no storage and no loss of energy)
        self.Outlet.h = self.Inlet.h

        self.rho = PropsSI('D', 'P', self.Inlet.P, 'H', self.Inlet.h, self.Inlet.fluid)
        #print( "self.rho", self.rho)
        self.eta = PropsSI('V', 'P', self.Inlet.P, 'H', self.Inlet.h, self.Inlet.fluid)
    
        #print("self.eta",self.eta)
        self.Ti = PropsSI('T', 'P', self.Inlet.P, 'H', self.Inlet.h, self.Inlet.fluid)
        #self.To = PropsSI('T', 'P', self.Outlet.P, 'H', self.Outlet.h, self.Inlet.fluid)


        self.delta_Z = self.L * math.sin(self.alpha)  # geom et autre

        self.A = (math.pi * self.d_hyd**2) / 4
        self.V = self.Inlet.F / (self.rho * self.A)

        self.Re = self.calculate_reynolds_number(self.rho,self.V,self.d_hyd, self.eta)

        self.delta_P=self.calculate_pressure_loss(self.L, self.d_hyd, self.rho, self.V, self.Re, self.roughness, self.K)



        self.Outlet.F=self.Inlet.F
        self.Inlet.P=self.delta_P+self.Outlet.P

        print("self.Outlet.P",self.Outlet.P)
        self.Outlet.fluid=self.Inlet.fluid
            ##################"fonctions"

        self.df = pd.DataFrame({'StraightPipe': [self.Timestamp,self.Inlet.fluid,round(self.Ti_degC,1),round(self.Inlet.F,3),round(self.Inlet.h,0),round(self.Outlet.h,0),round(self.A,3),round(self.V,3),round(self.Re,0),round(self.delta_P,1),round(self.Inlet.P,0),round(self.Outlet.P,0)], },
                      index = ['Timestamp','fluid','Ti_degC','Inlet.F (kg/s)','Inlet.h (j/kg)','Outlet.h (j/kg)','A (m2)','V (m/s)','Re','delta_P(Pa)'
                               ,'Inlet.P(Pa)','Outlet.P(Pa)'])
        
    def calculate_reynolds_number(self,rho, V,d_hyd, eta):
        # Nombre de Reynolds
        Re = (rho*V*d_hyd)/eta
        #print("Re = (rho*V*d_hyd)/eta =","(",rho,"*",V,"*",d_hyd,")/",eta)
        return Re
    
    def calculate_pressure_loss(self,L, d_hyd, rho, velocity, Reynolds_number, roughness, K):
        k = K/d_hyd
        #print("Reynolds_number:", Reynolds_number)

        Re_lam_min = 1e3  # Minimum Reynolds number for laminar regime
        Re_lam_max = 2090 * (1 / max(0.007, k)) ** 0.0635  # Maximum Reynolds number for laminar regime
        Re_turb_min = 4000
        Re_lam_leave = min(Re_lam_max, max(Re_lam_min, 754 * math.exp(0.0065 / 0.007 if k <= 0.007 else 0.0065 / k)))

        if roughness == "Neglected":
            lambda_FRI = 0.3164 * Reynolds_number ** (-0.25)
        else:
            lambda_FRI = 0.25 * (max(Reynolds_number, Re_lam_leave) / (math.log10(k/3.7 + 5.74 / max(Reynolds_number, Re_lam_leave) ** 0.9))) ** 2

        if Reynolds_number < Re_lam_leave:
            lambda_FRI_cal = 64 / Reynolds_number
        elif Reynolds_number > Re_turb_min:
            lambda_FRI_cal = lambda_FRI / (Reynolds_number ** 2)
        else:
            # You'll need to implement the cubic interpolation function here
            lambda_FRI_cal = self.cubic_interpolation_lambda(Reynolds_number, Re_lam_leave, Re_turb_min, k) / Reynolds_number ** 2

        #print("lambda_FRI:", lambda_FRI)

        # Calculate pressure loss using the formula
        dp = lambda_FRI_cal * (L / d_hyd) * (rho / 2) * velocity ** 2

        return dp

    import math

    def cubic_interpolation_lambda(self,Re, Re1, Re2, k):
        # Point x1=lg(Re1) with derivative yd1=1 at y1=lg(lambda2(Re1))
        x1 = math.log10(Re1)
        y1 = math.log10(64 * Re1)
        yd1 = 1

        # Point x2=lg(Re2) with derivative yd2 at y2=lg(lambda2(Re2))
        aux1 = (0.5 / math.log(10)) * 5.74 * 0.9
        aux2 = k / 3.7 + 5.74 / Re2**0.9
        aux3 = math.log10(aux2)
        L2 = 0.25 * (Re2 / aux3)**2
        aux4 = 2.51 / math.sqrt(L2) + 0.27 * k
        aux5 = -2 * math.sqrt(L2) * math.log10(aux4)
        x2 = math.log10(Re2)
        y2 = math.log10(L2)
        yd2 = 2 + 4 * aux1 / (aux2 * aux3 * (Re2)**0.9)

        # Constants: Cubic polynomial between x1=lg(Re1) and x2=lg(Re2)
        diff_x = x2 - x1
        m = (y2 - y1) / diff_x
        c2 = (3 * m - 2 * yd1 - yd2) / diff_x
        c3 = (yd1 + yd2 - 2 * m) / (diff_x * diff_x)
        dx = math.log10(Re / Re1)

        # Calculate lambda2 using the cubic Hermite spline interpolation formula
        lambda2 = 64 * Re1 * (Re / Re1)**(yd1 + dx * (c2 + dx * c3))
        
        return lambda2


