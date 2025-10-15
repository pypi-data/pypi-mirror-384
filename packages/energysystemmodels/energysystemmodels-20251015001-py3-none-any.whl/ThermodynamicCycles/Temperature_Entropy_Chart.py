import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
import numpy as np

class Object:
    def __init__(self, fluid):
        self.fluid = fluid
        self.T_min = CP.PropsSI(fluid, 'Ttriple') - 273.15  # Triple point temperature in Celsius
        self.T_crit = CP.PropsSI(fluid, 'Tcrit') - 273.15   # Critical temperature in Celsius
        self.T_max = 2.5 * self.T_crit                      # 2.5 times critical temperature
        self.S_min = None
        self.S_max = None
        self.custom_points = []  # List to store custom points

    def set_temperature_range(self, T_min=None, T_max=None):
        if T_min is not None:
            self.T_min = T_min
        if T_max is not None:
            self.T_max = T_max

    def set_entropy_range(self, S_min=None, S_max=None):
        self.S_min = S_min
        self.S_max = S_max

    def add_points(self, points):
        for point in points:
            self.custom_points.append({'T': point['T'], 'S': point['S']})  # Temperature in Celsius

    def show(self, draw_arrows=False,figsize=(10, 6)):
        T_range = np.linspace(self.T_min, self.T_max, int(self.T_max-self.T_min)*5)
        plt.figure(figsize=figsize)

        # Plot saturation curves
        S_liquid = [CP.PropsSI('S', 'T', T + 273.15, 'Q', 0, self.fluid) for T in T_range if T <= self.T_crit]
        S_vapor = [CP.PropsSI('S', 'T', T + 273.15, 'Q', 1, self.fluid) for T in T_range if T <= self.T_crit]
        plt.plot(S_liquid, T_range[:len(S_liquid)], 'b')  # T in °C
        plt.plot(S_vapor, T_range[:len(S_vapor)], 'r')  # T in °C

        # Adjust S range if specified
        if self.S_min is not None or self.S_max is not None:
            plt.xlim(self.S_min, self.S_max)

        # Define pressures for isobar lines
        p_crit = CP.PropsSI(self.fluid, 'pcrit')
        pressures = [0.1 * 100000]+[0.5 * 100000] + list(np.arange(1 * 100000, 10 * 100000, 1 * 100000)) + \
                    list(np.arange(10 * 100000, 2 * p_crit + 1, 10 * 100000))

# Plot lines of constant pressure with spaced labels
# Plot lines of constant pressure with spaced labels
        n_pressures = len(pressures)
        for i, p in enumerate(pressures):
            S = []
            for T in T_range:
                try:
                    T_K = T + 273.15  # Convert to Kelvin
                    entropy = CP.PropsSI('S', 'P', p, 'T', T_K, self.fluid)
                    S.append(entropy)
                except ValueError:
                    continue
            if S:
                is_ten_bar_multiple = int(p / 100000) % 10 == 0 or p == 0.1 * 100000
                line_color = 'black' if is_ten_bar_multiple else 'blue'
                plt.plot(S, T_range[:len(S)], '--', linewidth=0.5, color=line_color)
                if is_ten_bar_multiple:
                    # Place label at a unique vertical position for each pressure line
                    label_pos = len(S) * i // n_pressures
                    plt.annotate(f'{p/100000:.1f} bar',  # Convert to bar
                                xy=(S[label_pos], T_range[label_pos]), 
                                xytext=(5, -15), textcoords='offset points', 
                                color=line_color, ha='right', fontsize=6)



        # Plot custom points and optionally arrows
        for i in range(len(self.custom_points) - 1):
            point = self.custom_points[i]
            next_point = self.custom_points[i + 1]
            plt.scatter(point['S'], point['T'], color='red')
            if draw_arrows:
                plt.arrow(point['S'], point['T'], next_point['S'] - point['S'], next_point['T'] - point['T'],
                          head_width=0.05, head_length=0.1, fc='black', ec='black', linewidth=0.5)

        if self.custom_points:
            last_point = self.custom_points[-1]
            plt.scatter(last_point['S'], last_point['T'], color='red')

        # Label the axes, title, and grid
        plt.xlabel('Entropy (J/kg-K)')
        plt.ylabel('Temperature (°C)')
        plt.title('Temperature-Entropy Diagram for ' + self.fluid)
        plt.grid(True)

        # Show the plot
        plt.show()

# Example usage
# Chart = Object('R407C')
# Chart.add_points([{'S': 1000, 'T': 12}, {'S': 666, 'T': 12}, {'S': 2000, 'T': 15}])
# Chart.show(draw_arrows=True)
