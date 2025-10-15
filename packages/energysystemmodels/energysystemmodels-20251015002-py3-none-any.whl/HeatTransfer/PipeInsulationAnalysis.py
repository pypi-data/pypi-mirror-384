import CoolProp.CoolProp as CP
import math
import pandas as pd
from AHU.air_humide import air_humide
from scipy.optimize import fsolve  # Add import for solver

class Object:
    DN_TABLE = {
        6: {'di': 0.0078, 'de': 0.0102, 'thickness': 0.0016},
        8: {'di': 0.0109, 'de': 0.0135, 'thickness': 0.0023},
        10: {'di': 0.0136, 'de': 0.0172, 'thickness': 0.0028},
        15: {'di': 0.0169, 'de': 0.0213, 'thickness': 0.0027},
        20: {'di': 0.0217, 'de': 0.0269, 'thickness': 0.0032},
        25: {'di': 0.0273, 'de': 0.0337, 'thickness': 0.0032},
        32: {'di': 0.0358, 'de': 0.0424, 'thickness': 0.0033},
        40: {'di': 0.0411, 'de': 0.0483, 'thickness': 0.0036},
        50: {'di': 0.0525, 'de': 0.0603, 'thickness': 0.0039},
        65: {'di': 0.0683, 'de': 0.0761, 'thickness': 0.0039},
        80: {'di': 0.0809, 'de': 0.0889, 'thickness': 0.0040},
        100: {'di': 0.1061, 'de': 0.1143, 'thickness': 0.0041},
        125: {'di': 0.1311, 'de': 0.1397, 'thickness': 0.0043},
        150: {'di': 0.1593, 'de': 0.1683, 'thickness': 0.0045},
        200: {'di': 0.2091, 'de': 0.2191, 'thickness': 0.0050},
        250: {'di': 0.2618, 'de': 0.2730, 'thickness': 0.0056},
        300: {'di': 0.3123, 'de': 0.3239, 'thickness': 0.0058},
        350: {'di': 0.3434, 'de': 0.3556, 'thickness': 0.0061},
        400: {'di': 0.3934, 'de': 0.4064, 'thickness': 0.0065},
        450: {'di': 0.4432, 'de': 0.4572, 'thickness': 0.0070},
        500: {'di': 0.4930, 'de': 0.5080, 'thickness': 0.0075},
        550: {'di': 0.5428, 'de': 0.5588, 'thickness': 0.0080},
        600: {'di': 0.5926, 'de': 0.6096, 'thickness': 0.0085},
        650: {'di': 0.6424, 'de': 0.6604, 'thickness': 0.0090},
        700: {'di': 0.6922, 'de': 0.7112, 'thickness': 0.0095},
        750: {'di': 0.7420, 'de': 0.7620, 'thickness': 0.0100},
        800: {'di': 0.7918, 'de': 0.8128, 'thickness': 0.0105},
        850: {'di': 0.8416, 'de': 0.8636, 'thickness': 0.0110},
        900: {'di': 0.8914, 'de': 0.9144, 'thickness': 0.0115},
        950: {'di': 0.9412, 'de': 0.9652, 'thickness': 0.0120},
        1000: {'di': 0.9910, 'de': 1.0160, 'thickness': 0.0125},
        1050: {'di': 1.0408, 'de': 1.0668, 'thickness': 0.0130}
    }

    MATERIALS = {
        'Cuivre': 380,
        'Plomb': 35,
        'Acier': 50,
        'Aluminium 99%': 160,
        'Fonte': 50,
        'Zinc': 110
    }

    INSULATION_MATERIALS = {
        'aucun isolant': 0,
        'laine minérale': 0.04,
        'polyuréthanne PUR': 0.03,
        'polystyrène': 0.036,
        'polyéthylène': 0.038,
        'Liège (ICB)': 0.05,
        'Laine minérale (MW)': 0.045,
        'Polystyrène expansé (EPS)': 0.045,
        'Polyéthylène extrudé (PEF)': 0.045,
        'Mousse phénolique – revêtu (PF)': 0.045,
        'Polyuréthane – revêtu (PUR/PIR)': 0.035,
        'Polystyrène extrudé (XPS)': 0.04,
        'Verre cellulaire (CG)': 0.055,
        'Perlite (EPB)': 0.06,
        'Vermiculite': 0.065,
        'Vermiculite expansée (panneaux)': 0.09
    }

    FLUID_PROPERTIES = {
        'Huile thermique': {
            'Cp': 2632.1544,  # J/kg.K
            'mu': 0.1,  # Pa.s
            'k': 0.21,  # W/m.K
            'rho': 900  # kg/m3
        }
    }

    def __init__(self, fluid, T_fluid, F_m3h, DN, material='Acier', insulation='laine minérale', insulation_thickness=0.04, emissivity=0.01, Tamb=20, humidity=40,L_tube=1):
        self.fluid = fluid
        self.Tfluid = T_fluid
        self.F_m3h = F_m3h
        self.Tamb = Tamb
        self.RH = humidity
        self.Tamb = Tamb  # Assuming T1 is the ambient temperature


        # Convert temperatures to Kelvin for calculations
        self.Tamb_K = self.Tamb + 273.15
        self.Tamb_K = self.Tamb + 273.15
        self.Tfluid_K = self.Tfluid + 273.15

        # Pipe properties
        self.dn = DN / 1000  # Convert DN from mm to meters
        self.material = material  # Pipe material
        if DN in self.DN_TABLE:
            self.di = self.DN_TABLE[DN]['di']
            self.de = self.DN_TABLE[DN]['de']
        else:
            raise ValueError(f"DN {DN} not found in the DN_TABLE.")
        self.L_tube = L_tube  # L_tube in meters
        if material in self.MATERIALS:
            self.k_pipe = self.MATERIALS[material]  # Thermal conductivity of the pipe in W/m-°C
        else:
            raise ValueError(f"Material '{material}' not found in the MATERIALS table.")

        # Insulation properties
        self.insulation = insulation
        self.insulation_thickness = insulation_thickness
        self.emissivity = emissivity
        if insulation in self.INSULATION_MATERIALS:
            self.k_insulation = self.INSULATION_MATERIALS[insulation]  # Thermal conductivity of the insulation in W/m-°C
        else:
            raise ValueError(f"Insulation '{insulation}' not found in the INSULATION_MATERIALS table.")

        # Calculate outer diameter with insulation
        self.de_with_insulation = self.de + 2 * self.insulation_thickness

        # Fluid properties
        if fluid in self.FLUID_PROPERTIES:
            self.Cp = self.FLUID_PROPERTIES[fluid]['Cp']
            self.mu = self.FLUID_PROPERTIES[fluid]['mu']
            self.k = self.FLUID_PROPERTIES[fluid]['k']
            self.rho = self.FLUID_PROPERTIES[fluid]['rho']
        else:
            # Using CoolProp to get properties of fluid
            self.Cp = CP.PropsSI('C', 'T', self.Tfluid_K, 'P', 101325, fluid)
            self.mu = CP.PropsSI('V', 'T', self.Tfluid_K, 'P', 101325, fluid)
            self.k = CP.PropsSI('L', 'T', self.Tfluid_K, 'P', 101325, fluid)
            self.rho = CP.PropsSI('D', 'T', self.Tfluid_K, 'P', 101325, fluid)

        # Properties of ambient air
        self.B = 0.0034  # 1/K

        # Using CoolProp to get properties of air
   
        self.mu_air = CP.PropsSI('V', 'T', self.Tamb_K, 'P', 101325, 'Air')
        self.k_air = CP.PropsSI('L', 'T', self.Tamb_K, 'P', 101325, 'Air')
        self.Cp_air = CP.PropsSI('C', 'T', self.Tamb_K, 'P', 101325, 'Air')

        # Calculate Prandtl Number for ambient air
        self.Pr_air = self.Cp_air * self.mu_air / self.k_air
        self.Pr_fluid = self.Cp * self.mu / self.k
   

        # Calculate external surface area of the insulated pipe
        self.A_e_insulated = 3.14159 * self.de_with_insulation * self.L_tube
        self.A_i= 3.14159 * self.di * self.L_tube

        # Initialize DataFrame
        self.df = pd.DataFrame()

        # Initialize Tc and Tf
        self.Tc = self.Tamb + 10.4  # Initial guess for Tc, less than Ta
        self.Tf = (self.Tc + self.Tamb) / 2  # Initial film temperature
        self.rho_air = air_humide.Air_rho_hum(T_db=self.Tf, RH=self.RH, P=101325)

    def calculate_ambient_air_properties(self):
        # Calculate Rayleigh Number
        g = 9.81  # m/s², acceleration due to gravity
        Ra_air = (g * self.B * self.rho_air ** 2 * self.Cp_air * (self.Tc - self.Tamb) * self.de_with_insulation ** 3) / (self.k_air * self.mu_air)
      
        # Calculate Nusselt Number
        Nu = (0.60 + (0.387 * Ra_air ** (1/6)) / (1 + (0.559 / self.Pr_air) ** (9/16)) ** (8/27)) ** 2
      
        
        # Calculate average heat transfer coefficient
        self.h_air = Nu * self.k_air / self.de_with_insulation
        

        return Ra_air, Nu, self.h_air

    def calculate_heat_transfer(self):
        # Convective heat transfer
        q_conv = self.h_air * self.A_e_insulated * (self.Tc - self.Tamb)
        R_conv = (self.Tc - self.Tamb) / q_conv  # Convective resistance

        # Radiative heat transfer
        sigma = 5.670373e-8  # Stefan-Boltzmann constant in W/m²K⁴
        q_rad = self.A_e_insulated * self.emissivity * sigma * ((self.Tc+273.15)**4 - self.Tamb_K**4)
        R_rad = (self.Tc - self.Tamb) / q_rad  # Radiative resistance

        # Calculate internal convective resistance
        R_conv_i = 1 / (self.h_fluid * self.A_i)


        # Calculate conductive resistance of the bare tube : =LN('données d''entrée'!B17/('données d''entrée'!B16))/(2*PI()*'données d''entrée'!B19*'Calculs & résultats'!C7)
        R_cond_tube = math.log(self.de / self.di) / (2 * 3.14159 * self.k_pipe * self.L_tube)
   

        #calcul de la resistance de l'isolant
        R_cond_insulation = math.log(self.de_with_insulation / self.de) / (2 * 3.14159 * self.k_insulation * self.L_tube)

        q_total = q_conv + q_rad
        if R_rad != 0 or R_rad is not None:
            R_total = 1/(1/R_conv + 1/R_rad)
        else:
            R_total = R_conv
        
        # Calculate internal wall temperature
        T_wall_i = self.Tfluid - (q_total * R_conv_i)
        T_wall_e=T_wall_i - (q_total * R_cond_tube)
        Tc=T_wall_e - (q_total * R_cond_insulation)
    

        return q_conv, q_rad, q_total, R_conv, R_rad, R_total, R_conv_i, T_wall_i, T_wall_e, Tc, R_cond_tube

    def calculate_reynolds_number(self):
        # Calculate Reynolds number for the fluid side
        self.v = (self.F_m3h / 3600)*4 / (3.14159 * self.di ** 2)
        Re_fluid = (self.rho * self.v * self.di) / self.mu

        return Re_fluid

    def heat_balance(self, Tc):
        self.Tc = Tc
        self.Tf = (self.Tc + self.Tamb) / 2
        self.rho_air = air_humide.Air_rho_hum(T_db=self.Tf, RH=self.RH, P=101325)
        self.Ra_air, self.Nu, self.h_air = self.calculate_ambient_air_properties()
        self.q_conv, self.q_rad, self.q_total, self.R_conv_e, self.R_rad, self.R_total, self.R_conv_i, self.T_wall_i, self.T_wall_e, T_insulation, self.R_cond_tube = self.calculate_heat_transfer()
        return T_insulation - Tc  # Return the difference for the solver

    def calculate(self):
        Re_fluid = self.calculate_reynolds_number()  # Calculate Reynolds number
        if Re_fluid >= 2300:
            self.regime = 'turbulent'
            self.Nu_fluid = 0.023 * Re_fluid**0.8 * self.Pr_fluid**0.4
        else:
            self.regime = 'laminar'
            self.Nu_fluid = 3.66

        self.h_fluid = self.Nu_fluid * self.k / self.di

        # Use fsolve to find the final value of Tc
        self.Tc = fsolve(self.heat_balance, self.Tc)[0]

        # Recalculate film temperature
        self.Tf = (self.Tc + self.Tamb) / 2
        self.rho_air = air_humide.Air_rho_hum(T_db=self.Tf, RH=self.RH, P=101325)
        self.Ra_air, self.Nu, self.h_air = self.calculate_ambient_air_properties()
        self.q_conv, self.q_rad, self.q_total, self.R_conv_e, self.R_rad, self.R_total, self.R_conv_i, self.T_wall_i, self.T_wall_e, self.Tc, self.R_cond_tube = self.calculate_heat_transfer()

        data = {
            'Fluid': [self.fluid],
            'Regime': [self.regime],
            'T_fluid (°C)': [self.Tfluid],
            'v (m/s)': [self.v],
            'F_m3h (m3/h)': [self.F_m3h],
            'DN': [self.dn * 1000],  # Convert back to mm for display
            'di (m)': [self.di],
            'de (m)': [self.de],
            'L_tube (m)': [self.L_tube],
            'Material': [self.material],
            'Insulation': [self.insulation],
            'Insulation Thickness (m)': [self.insulation_thickness],
            'Emissivity': [self.emissivity],
            'Tamb (°C)': [self.Tamb],
            'Humidity (%)': [self.RH],
            'Tamb (°C)': [self.Tamb],
      
        
            'Flow Regime': [self.regime],
            'Tc (°C)': [self.Tc],
            'Tf (°C)': [self.Tf],
            'Outer Diameter with Insulation (m)': [self.de_with_insulation],
            'Prandtl Number (Pr)': self.Pr_air,
            'External Surface Area (m²)': self.A_e_insulated,
            'Rayleigh Number': self.Ra_air,
            'Nusselt Number': self.Nu,
            'Average Heat Transfer Coefficient (W/m².K)': self.h_air,
            'Convective Heat Transfer (W)': self.q_conv,
            'Radiative Heat Transfer (W)': self.q_rad,
            'Total Heat Transfer (W)': self.q_total,
            'Convective Resistance (K/W)': self.R_conv_e,
            'Radiative Resistance (K/W)': self.R_rad,
            'Equivalent Resistance (K/W)': self.R_total,
            'Internal Surface Area (m²)': [self.A_i],
            'Reynolds Number (Re_fluid)': Re_fluid,  
            'velocity (m/s)': self.v,
            'Prandtl Number (Pr)': self.Pr_fluid,  # Add Prandtl number of the fluid to the data
            'Nusselt Number (self.Nu_fluid)': self.Nu_fluid,  # Add Nusselt number of the fluid to the data
            'Heat Transfer Coefficient (self.h_fluid)': self.h_fluid,  # Add heat transfer coefficient of the fluid to the data
            'Internal Convective Resistance (K/W)': self.R_conv_i,
            'Internal Wall Temperature (°C)': self.T_wall_i,
            'External Wall Temperature (°C)': self.T_wall_e,
            'Insulation Temperature (°C)':  self.Tc,
            'Conductive Resistance of Bare Tube (K/W)': self.R_cond_tube,
        }

        self.df = pd.DataFrame(data).T

# Example usage

