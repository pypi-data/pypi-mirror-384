import pvlib
import pandas as pd
import matplotlib.pyplot as plt

class SolarSystem:
    def __init__(self, latitude, longitude, name, altitude, timezone, azimut, inclinaison):
        self.latitude = latitude
        self.longitude = longitude
        self.name = name
        self.altitude = altitude
        self.timezone = timezone
        self.azimut = azimut
        self.inclinaison = inclinaison
        self.weather = None
        self.module = None
        self.inverter = None
        self.temperature_model_parameters = None
        self.system = None
        self.solpos = None
        self.dni_extra = None
        self.airmass = None
        self.pressure = None
        self.am_abs = None
        self.aoi = None
        self.total_irradiance = None
        self.cell_temperature = None
        self.effective_irradiance = None
        self.dc = None
        self.ac = None
        self.annual_energy = None

    def retrieve_module_inverter_data(self):
        # Récupération de la base de données des modules Sandia
        sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
        #print("Modules PV Sandia", sandia_modules)
        # Récupération de la base de données des onduleurs SAPM
        sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
        #print("Onduleurs", sapm_inverters)
        # Sélection d'un module spécifique à partir de la base de données des modules Sandia
        self.module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
        # Sélection d'un onduleur spécifique à partir de la base de données des onduleurs SAPM
        self.inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
        # Récupération des paramètres du modèle de température pour le modèle SAPM et le module open rack glass-glass
        self.temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
        #print("Modèle de température", self.temperature_model_parameters)

    def retrieve_weather_data(self):
        # Récupération des données météorologiques TMY à partir de PVGIS pour l'emplacement spécifié
        weather = pvlib.iotools.get_pvgis_tmy(self.latitude, self.longitude, map_variables=True)[0]
        weather.index.name = "utc_time"  # Définition du nom de l'index des données météorologiques
        self.weather = weather
        #print("Données météorologiques typiques :", self.weather)

    def calculate_solar_parameters(self):
        # Configuration du système solaire avec le module, l'onduleur et l'azimut de surface fixé à 180 degrés
        print("azimut:",self.azimut)
        self.system = {'module': self.module, 'inverter': self.inverter, 'surface_azimuth': self.azimut}
        # Définition de l'inclinaison de la surface du système solaire à la latitude de l'emplacement
        self.system['surface_tilt'] = self.inclinaison
        print("inclinaison", self.system['surface_tilt'])
        # Calcul de la position solaire
        self.solpos = pvlib.solarposition.get_solarposition(
            time=self.weather.index,
            latitude=self.latitude,
            longitude=self.longitude,
            altitude=self.altitude,
            temperature=self.weather["temp_air"],
            pressure=pvlib.atmosphere.alt2pres(self.altitude),
        )
        #print("position du soleil===", self.solpos)
        # Calcul du rayonnement solaire supplémentaire
        self.dni_extra = pvlib.irradiance.get_extra_radiation(self.weather.index)
        #print("rayonnement solaire suplémentaire", self.dni_extra)
        # Calcul de la masse d'air relative
        self.airmass = pvlib.atmosphere.get_relative_airmass(self.solpos['apparent_zenith'])
        #print("masse d'air relative", self.airmass)
        # Calcul de la pression atmosphérique
        self.pressure = pvlib.atmosphere.alt2pres(self.altitude)
        #print("pression atm", self.pressure)
        # Calcul de la masse d'air absolue
        self.am_abs = pvlib.atmosphere.get_absolute_airmass(self.airmass, self.pressure)
        #print("masse d'air absolue", self.am_abs)
        # Calcul de l'angle d'incidence
        self.aoi = pvlib.irradiance.aoi(
            self.system['surface_tilt'],
            self.system['surface_azimuth'],
            self.solpos["apparent_zenith"],
            self.solpos["azimuth"],
        )
        #print("angle d'incidence", self.aoi)
        # Calcul du rayonnement solaire total
        self.total_irradiance = pvlib.irradiance.get_total_irradiance(
            self.system['surface_tilt'],
            self.system['surface_azimuth'],
            self.solpos['apparent_zenith'],
            self.solpos['azimuth'],
            self.weather['dni'],
            self.weather['ghi'],
            self.weather['dhi'],
            dni_extra=self.dni_extra,
            model='haydavies',
        )
        #print("rayonnement solaire total", self.total_irradiance)
        # Calcul de la température des cellules solaires
        self.cell_temperature = pvlib.temperature.sapm_cell(
            self.total_irradiance['poa_global'],
            self.weather["temp_air"],
            self.weather["wind_speed"],
            **self.temperature_model_parameters,
        )
        #print("température des cellules solaires", self.cell_temperature)
        # Calcul du rayonnement solaire effectif
        self.effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(
            self.total_irradiance['poa_direct'],
            self.total_irradiance['poa_diffuse'],
            self.am_abs,
            self.aoi,
            self.module,
        )
        #print("rayonnement solaire effectif", self.effective_irradiance)
        # Calcul de la puissance CC (courant continu)
        self.dc = pvlib.pvsystem.sapm(self.effective_irradiance, self.cell_temperature, self.module)
        #print("puissance CC", self.dc)
        # Calcul de la puissance CA (courant alternatif)
        self.ac = pvlib.inverter.sandia(self.dc['v_mp'], self.dc['p_mp'], self.inverter)
        #print("puissance CA (courant alternatif)", self.ac)
        # Calcul de l'énergie annuelle
        self.annual_energy = -self.ac.sum()
        print("énergie annuelle:")
        print(self.annual_energy)
        

    def plot_annual_energy(self):
        # Stockage de l'énergie annuelle dans un dictionnaire avec le nom de l'emplacement comme clé
        energies = {self.name: self.annual_energy}
        print("energies résult", energies)
        # Conversion du dictionnaire en une série pandas
        energies = pd.Series(energies)
        # Affichage de la série d'énergies
        print("Rendement énergétique annuel (KWh)", energies / 1000)
        # Affichage du graphique en barres des rendements énergétiques annuels
        energies.plot(kind='bar', rot=0)
        # Configuration de l'axe des ordonnées
        plt.ylabel('Rendement énergétique annuel (Wh)')