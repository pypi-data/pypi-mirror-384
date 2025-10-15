import pandas as pd

class Object:
    MATERIALS = {
        'Laine de verre': 0.034,
        'Liège expansé aggloméré au brai': 0.048,
        'Liège expansé pur': 0.043,
        'Parpaings creux': 1.4,
        'Pierre calcaire dure (marbre)': 2.9,
        'Pierre calcaire tendre': 0.95,
        'Pierre granit': 3.5,
        'Polystyrène expansé': 0.047,
        'Polystyrène': 0.03,
        'Polystyrène extrudé': 0.035,
        'Mousse de polyuréthane': 0.03,
        'Plâtre': 0.5,
        'Verre': 1.0,
        'Glass wool': 0.034,
        'Expanded cork agglomerated with pitch': 0.048,
        'Pure expanded cork': 0.043,
        'Hollow concrete blocks': 1.4,
        'Hard limestone (marble)': 2.9,
        'Soft limestone': 0.95,
        'Granite': 3.5,
        'Expanded polystyrene': 0.047,
        'Extruded polystyrene': 0.035,
        'polystyrene': 0.03,
        'Polyurethane foam': 0.03,
        'Plaster': 0.5,
        'Glass': 1.0,
        'Air': None  # Special case for air gap
    }

    def __init__(self, he=23, hi=8, Ti=20, Te=-10, A=10):
        self.he = he  # External convection coefficient (W/m².°C)
        self.hi = hi  # Internal convection coefficient (W/m².°C)
        self.Ti = Ti  # Internal temperature (°C)
        self.Te = Te  # External temperature (°C)
        self.A = A  # Area of the wall (m²)
        self.Q=None
        self.R_total=None
        self.layers = []
        self.df = pd.DataFrame()

    # def add_layer(self, thickness, conductivity=None, material=None):
    #     """
    #     Add a layer to the composite wall.
    #     :param thickness: Thickness of the layer (m)
    #     :param conductivity: Thermal conductivity of the layer (W/m.°C)
    #     :param material: Name of the material
    #     """
    #     if material == 'Air':
    #         if 0.005 <= thickness <= 0.007:
    #             resistance = 0.11
    #         elif 0.007 < thickness <= 0.009:
    #             resistance = 0.13
    #         elif 0.009 < thickness <= 0.011:
    #             resistance = 0.14
    #         elif thickness > 0.011:
    #             resistance = 0.16
    #         else:
    #             raise ValueError("Invalid thickness for air gap.")
    #         self.layers.append({'resistance': resistance})
    #     else:
    #         if material:
    #             conductivity = self.MATERIALS.get(material)
    #             if conductivity is None:
    #                 raise ValueError(f"Material '{material}' not found in the database.")
    #         if conductivity is None:
    #             raise ValueError("Either conductivity or material must be provided.")
    #         resistance = thickness / conductivity
    #         self.layers.append({'thickness': thickness, 'conductivity': conductivity, 'resistance': resistance})

    def add_layer(self, thickness, conductivity=None, material=None):
        """
        Add a layer to the composite wall.
        :param thickness: Thickness of the layer (m)
        :param conductivity: Thermal conductivity of the layer (W/m.°C)
        :param material: Name of the material
        """
        if material == 'Air':
            if 0.005 <= thickness <= 0.007:
                resistance = 0.11
            elif 0.007 < thickness <= 0.009:
                resistance = 0.13
            elif 0.009 < thickness <= 0.011:
                resistance = 0.14
            elif thickness > 0.011:
                resistance = 0.16
            else:
                raise ValueError("Invalid thickness for air gap.")
            self.layers.append({'material': 'Air', 'resistance': resistance})
        else:
            if material:
                conductivity = self.MATERIALS.get(material)
                if conductivity is None:
                    raise ValueError(f"Material '{material}' not found in the database.")
            if conductivity is None:
                raise ValueError("Either conductivity or material must be provided.")
            resistance = thickness / conductivity
            self.layers.append({'material': material, 'thickness': thickness, 'conductivity': conductivity, 'resistance': resistance})


    def calculate(self):
        """
        Calculate the heat transfer through the composite wall and the temperature at each layer interface.
        :return: Heat transfer (W) and list of temperatures at each layer interface
        """
        # Résistances de convection
        R_e = 1 / self.he
        R_i = 1 / self.hi

        # Calcul des résistances des couches
        R_layers = [layer['resistance'] for layer in self.layers]

        # Résistance totale
        self.R_total = R_e + R_i + sum(R_layers)


        # Coefficient de transmission thermique
        U = 1 / self.R_total

        # Flux thermiself.Que total
        self.Q = U * self.A * (self.Ti - self.Te)

        # Calcul des températures aux interfaces des couches
        temperatures = [self.Te]
        current_temperature = self.Te

 # Température de la paroi exterieure après résistance convective
        T_paroi_externe = self.Te + (self.Q * R_e / self.A)
        temperatures.append(T_paroi_externe)

        # Températures aux interfaces des couches
        current_temperature = T_paroi_externe
        for R_layer in R_layers:
            delta_T = self.Q * R_layer / self.A
            current_temperature += delta_T
            temperatures.append(current_temperature)

        # Ajout de la température extérieure
        temperatures.append(self.Ti)

                # Création du DataFrame des résultats
        self.df = pd.DataFrame({
            'Épaisseur (m)': [None] + [layer.get('thickness', None) for layer in self.layers] + [None],
            'Matériau': ['Air extérieur'] + [layer.get('material', 'Air') for layer in self.layers] + ['Air intérieur'],
            'Conductivité (W/m.°C)': [None] + [layer.get('conductivity', None) for layer in self.layers] + [None],
            'Résistance (m².°C/W)': [R_e] + [layer['resistance'] for layer in self.layers] + [R_i],
            'Température entrée (°C)': temperatures[:-1],  # Température avant la couche
    'Température sortie (°C)': temperatures[1:] ,  # Température après la couche
     'Q (W)': [self.Q] * (len(self.layers) + 2),    # Répéter la valeur de Q pour toutes les lignes
    'A (m²)': [self.A] * (len(self.layers) + 2)    # Répéter la valeur de A pour toutes les lignes
        })


        return self.df
