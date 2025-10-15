from CoolProp.CoolProp import PropsSI
import pandas as pd

class FluidPort:
    def __init__(self, fluid='ammonia', P=101325, h=None, F=None, T=None, S=None):
        self.F = F
        self._P = P
        self.h = h
        self.fluid = fluid
        self.T = T
        self.S = S
        self.rho = None
        self.cp = None
        self.lamda = None
        self.mu = None
        self.callback = None  
        self.calculate_properties()

    @property
    def P(self):
        """Getter pour la pression."""
        return self._P

    @P.setter
    def P(self, value):
        """Setter pour la pression avec détection de changement."""
        if self._P != value:  # Vérifie si la valeur a changé
            self._P = value
            print(f"FluidPort.P a changé : {value}")
            self.calculate_properties()  # Recalcule les propriétés du fluide
            if self.callback:  # Si un callback est défini, l'appeler
                self.callback()

    def propriete(self, Pro, I1, ValI1, I2, ValI2):
        result = PropsSI(Pro, I1, ValI1, I2, ValI2, self.fluid)
        return result

    def calculate_properties(self):
        # Ensure all needed properties are set

        if self.P is not None and self.T is not None and self.h is None:
            self.h = PropsSI('H', 'T', self.T, 'P', self.P, self.fluid)
            #print("self.h",self.h)
        
        if self.P is not None and self.h is not None:
            #print("self.....P",self.P)
            self.T = PropsSI('T', 'P', self.P, 'H', self.h, self.fluid)
            self.S = PropsSI('S', 'P', self.P, 'H', self.h, self.fluid)
            self.rho = PropsSI('D', 'P', self.P, 'H', self.h, self.fluid)
            self.cp = PropsSI('C', 'P', self.P, 'H', self.h, self.fluid)
            self.lamda = PropsSI('L', 'P', self.P, 'H', self.h, self.fluid)
            self.mu = PropsSI('V', 'P', self.P, 'H', self.h, self.fluid)

     
    
        self.df = pd.DataFrame({
            'FluidPort': [self.fluid, self.F, self.T, self.P, self.h, self.S, self.rho, self.cp, self.lamda, self.mu],
            },
            index=['Fluide', 'Débit(kg/s)', 'Température(k)', 'Pression (Pa)', 'Enthalpie (J/kg)', 'Entropie (J/kg-K)',
                   'Densité (kg/m^3)', 'Chaleur spécifique (J/kg-K)', 'Conductivité thermique (W/m-K)', 'Viscosité dynamique (Pa-s)'])
