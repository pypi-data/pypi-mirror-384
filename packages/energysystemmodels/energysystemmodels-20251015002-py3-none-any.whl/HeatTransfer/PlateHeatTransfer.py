class Object:
    def __init__(self, orientation, Tp, Ta, W=None, L=None, H=None, Cp=1007, beta=0.0034, k=0.0261, mu=0.0000185, rhoref=1.201, e=0.85):
        self.orientation = orientation
        self.Tp = Tp
        self.Ta = Ta
        self.W = W
        self.L = L
        self.H = H
        self.Cp = Cp
        self.beta = beta
        self.k = k
        self.mu = mu
        self.rhoref = rhoref
        self.e = e
        self.g = 9.81  # Acceleration due to gravity (m/s^2)
        self.sigma = 5.67e-8  # Stefan-Boltzmann constant (W/m^2-K^4)

    def calculate(self):
        if self.orientation == 'horizontal_down':
            return self._horizontal_plate_facing_down_heat_transfer()
        elif self.orientation == 'horizontal_up':
            return self._horizontal_plate_facing_up_heat_transfer()
        elif self.orientation == 'vertical':
            return self._vertical_plate_heat_transfer()
        else:
            raise ValueError("Invalid orientation. Choose from 'horizontal_down', 'horizontal_up', or 'vertical'.")

    def _horizontal_plate_facing_down_heat_transfer(self):
        # Calculated Parameters
        Tf = (self.Tp + self.Ta) / 2  # Film temperature (°C)
        v = self.mu / self.rhoref  # Kinematic viscosity (m^2/s) at reference density
        rho = self.rhoref * (1 - self.beta * (Tf - 20))  # Density at film temperature (kg/m^3)
        a = self.k / (rho * self.Cp)  # Thermal diffusivity (m^2/s)

        # Dimensionless Numbers
        Pr = v / a  # Prandtl number
        Gr = self.g * self.beta * (self.Tp - self.Ta) * ((self.W * self.L) / (2 * self.W + 2 * self.L))**3 / v**2  # Grashof number
        Ra = Gr * Pr  # Rayleigh number

        # Nusselt Number for horizontal plate facing down
        Nu = 0.27 * Ra**0.25 if Ra > 1e4 and Ra < 1e7 else (0.54 * Ra**0.25 if Ra >= 1e7 else 1)

        # Heat Transfer Coefficient
        h = Nu * self.k / ((self.W * self.L) / (2 * self.W + 2 * self.L))

        # Convective Heat Transfer
        q_conv = h * self.W * self.L * (self.Tp - self.Ta)

        # Radiative Heat Transfer
        q_rad = self.sigma * self.W * self.L * self.e * ((self.Tp + 273.15)**4 - (self.Ta + 273.15)**4)

        # Total Heat Transfer
        q_total = q_conv + q_rad

        return q_total

    def _horizontal_plate_facing_up_heat_transfer(self):
        # Film temperature
        Tf = (self.Tp + self.Ta) / 2.0

        # Fluid properties at film temperature
        Pr = self.mu / (self.k / (self.Cp * self.rhoref))  # Prandtl number
        rho = self.rhoref * (1 - self.beta * (Tf - 20))  # Density at Tf

        # Grashof number calculation
        Gr = self.g * self.beta * (self.Tp - self.Ta) * ((self.W * self.L) / (2 * self.W + 2 * self.L))**3 / self.mu**2

        # Rayleigh number
        Ra = Gr * Pr

        # Nusselt number calculation based on Ra
        Nu = 0.15 * (Ra**0.33)

        # Average heat transfer coefficient
        h = Nu * self.k / ((self.W * self.L) / (2 * self.W + 2 * self.L))

        # Convective heat transfer
        q_conv = h * self.W * self.L * (self.Tp - self.Ta)

        # Radiative heat transfer
        q_rad = self.sigma * self.W * self.L * self.e * ((self.Tp + 273.15)**4 - (self.Ta + 273.15)**4)

        # Total heat transfer
        q_total = q_conv + q_rad

        return q_total

    def _vertical_plate_heat_transfer(self):
        if self.H is None:
            raise ValueError("Height (H) must be provided for vertical plate heat transfer calculation.")

        # Film temperature
        Tf = (self.Tp + self.Ta) / 2
        # Fluid properties at film temperature
        v = self.mu / self.rhoref  # Kinematic viscosity
        alpha = self.k / (self.rhoref * self.Cp)  # Thermal diffusivity
        Pr = v / alpha  # Prandtl number

        # Density at film temperature
        rho = self.rhoref * (1 - self.beta * (Tf - 20))

        # Grashof number calculation
        Gr = self.g * self.beta * (self.Tp - self.Ta) * self.H**3 / v**2

        # Rayleigh number
        Ra = Gr * Pr

        # Nusselt number calculation
        if Ra < 1e9:
            Nu = (0.68 + (0.67 * Ra ** (1 / 4)) / (1 + (0.492 / Pr) ** (9 / 16)) ** (4 / 9)) ** 2
        else:
            Nu = (0.825 + (0.387 * Ra ** (1 / 6)) / ((1 + (0.492 / Pr) ** (9 / 16)) ** (8 / 27))) ** 2

        # Average heat transfer coefficient
        h = Nu * self.k / self.H

        # Convective heat transfer
        q_conv = h * self.W * self.H * (self.Tp - self.Ta)

        # Radiative heat transfer
        q_rad = self.sigma * self.W * self.H * self.e * ((self.Tp + 273.15)**4 - (self.Ta + 273.15)**4)

        # Total heat transfer
        q_total = q_conv + q_rad

        return q_total