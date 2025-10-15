# =============================================================================
# Chiller Model (Evaporator + Compressor + Desuperheater + Condenser + Expansion_Valve)
# =============================================================================

import CoolProp.CoolProp as CP
import pandas as pd
from ThermodynamicCycles.Evaporator import Evaporator
from ThermodynamicCycles.Compressor import Compressor
from ThermodynamicCycles.Desuperheater import Desuperheater
from ThermodynamicCycles.Expansion_Valve import Expansion_Valve
from ThermodynamicCycles.Condenser import Condenser
from ThermodynamicCycles.Connect import Fluid_connect

from ThermodynamicCycles import Temperature_Entropy_Chart

class Object:
    def __init__(self, fluid='R134a', evap_params=None, comp_params=None, cond_params=None):
        # Initialize chiller components
        self.EVAP = Evaporator.Object()
        self.COMP = Compressor.Object()
        self.DESURCH = Desuperheater.Object()
        self.COND = Condenser.Object()
        self.DET = Expansion_Valve.Object()

        # Set fluid for all components
        self.fluid = fluid
        self.EVAP.fluid = self.fluid
        self.COMP.fluid = self.fluid
        self.DESURCH.fluid = self.fluid
        self.COND.fluid = self.fluid
        self.DET.fluid = self.fluid

        # Set parameters for each component
        self.set_evaporator_parameters(evap_params)
        self.set_compressor_parameters(comp_params)
        self.set_condenser_parameters(cond_params)

        self.points=[]

    def set_evaporator_parameters(self, params):
        if params:
            self.EVAP.Ti_degC= params.get('Ti_degC', 5)
            self.EVAP.surchauff = params.get('surchauff', 2)
            self.EVAP.Inlet.F = params.get('F', 1)
            

    def set_compressor_parameters(self, params):
        if params:
            self.COMP.Tcond_degC = params.get('Tcond_degC', 40)
            self.COMP.eta_is = params.get('eta_is', 0.8)
            self.COMP.Tdischarge_target = params.get('Tdischarge_target', 80)
            if 'Q_comp' in params:
                self.COMP.Q_comp = params['Q_comp']

    def set_condenser_parameters(self, params):
        if params:
            self.COND.subcooling = params.get('subcooling', 2)

    def calculate_cycle(self):
        # Calculation algorithm
        self.EVAP.Inlet.h = CP.PropsSI('H', 'P', 1 * 1e5, 'T', 40 + 273.15, self.fluid)
        self.EVAP.calculate() 
        Fluid_connect(self.COMP.Inlet, self.EVAP.Outlet)
        self.COMP.calculate()
        Fluid_connect(self.DESURCH.Inlet, self.COMP.Outlet)
        self.DESURCH.calculate()
        Fluid_connect(self.COND.Inlet, self.DESURCH.Outlet)
        self.COND.calculate()
        Fluid_connect(self.DET.Inlet, self.COND.Outlet)
        Fluid_connect(self.DET.Outlet, self.EVAP.Inlet)
        self.DET.calculate()
        Fluid_connect(self.EVAP.Inlet, self.DET.Outlet)
        self.EVAP.calculate() # Recalculate evaporator

        self.EER = self.EVAP.Q_evap / self.COMP.Q_comp
        self.Q_condTot = self.COND.Q_cond + self.DESURCH.Qdesurch
        self.COP = self.Q_condTot / self.COMP.Q_comp

        self.df = pd.DataFrame({
            
            'Chiller': [self.EER,self.COP,self.COMP.Q_comp/1000,self.COMP.Q_losses/1000,self.EVAP.Q_evap/1000,self.Q_condTot/1000]
        }, index=[ 'EER', 'COP','Q_comp (kW)','COMP.Q_losses (kW)','Q_evap (kW)', 'Q_condTot(kW)'])


        self.points = [
            {"T": self.EVAP.Tsv - 273.15, "S": self.EVAP.Ssv},
            {"T": self.EVAP.Outlet.T - 273.15, "S": self.EVAP.Outlet.S},
            {"T": self.COMP.Outlet.T - 273.15, "S": self.COMP.Outlet.S},
            {"T": self.DESURCH.Outlet.T - 273.15, "S": self.DESURCH.Outlet.S},
            {"T": self.COND.Tl_sat- 273.15, "S": self.COND.Sl_sat},
            {"T": self.COND.Outlet.T - 273.15, "S": self.COND.Outlet.S},
            {"T": self.DET.Outlet.T- 273.15, "S": self.DET.Outlet.S},
            {"T": self.EVAP.Tsv - 273.15, "S": self.EVAP.Ssv}
        ]
      



    def print_results(self):
        print(self.df)
        # Print Results
        print("COMPONENT DATAFRAMES:\n")
        print("Compressor:")
        print(self.COMP.df)
        print("\nEvaporator:")
        print(self.EVAP.df)
        print("\nDesuperheater:")
        print(self.DESURCH.df)
        print("\nCondenser:")
        print(self.COND.df)
        print("\nExpansion Valve:")
        print(self.DET.df)



    def plot_TS_diagram(self,figsize=(10, 6)):
        # Create a Temperature-Entropy chart object
        chart = Temperature_Entropy_Chart.Object(self.fluid)


        # Add points to the chart
        chart.add_points(self.points)

        # Display the chart
        chart.show(draw_arrows=True,figsize=figsize)


