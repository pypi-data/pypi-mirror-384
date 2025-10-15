from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 

import matplotlib.pyplot as plt
import numpy as np
import random
from scipy.optimize import minimize
from matplotlib.ticker import FuncFormatter

class Object:
    def __init__(self):
        self.Timestamp=None

        #Input and Output Connector
        self.Inlet=FluidPort() 
        self.Outlet=FluidPort()

        # #Input Data
        self.eta=None
        self.Pdischarge_bar=None
        # self.Tcond_degC=None
        self.Pdischarge=None #self.Pdischarge_bar*100000
        # self.Tdischarge_target=None #°C

        #points de fonctionnement de la pompe
        self.X_F = None #débit volumique m3/h X_F = [5,34,40,50]
      
        self.Y_hmt = None # Hauteur manométrique Y_hmt = [12,60,80,68]
        self.Y_eta = None # point de rendement Y_eta = [0.4,0.8,0.9,0.1]

        # Modèles et données pour la courbe
        self.model_hmt = None
        self.model_eta = None
        self.polynomial_features = None
        self.nb_degree = None
        self.x_new_min = None
        self.x_new_max = None
        self.Y_hmt_NEW = None
        self.Y_eta_NEW = None

        # #Initial Values
        #self.Inlet.fluid=None
        # self.Inlet.P=101325
        # self.F=0.1
        # self.Inlet.F=self.F

        # self.F_Sm3s=None
        # self.F_Sm3h=None
        self.F_Sm3s=None
        
        #Output Data
        self.df=[]

        self.Q_pump=0
    #     self.Q_losses=0
        self.Ti_degC=None
        
    def calculate (self):
        if self.Pdischarge_bar is not None:
            self.Pdischarge=self.Pdischarge_bar*100000

        self.Ti_degC=-273.15+PropsSI("T", "P", self.Inlet.P, "H", self.Inlet.h, self.Inlet.fluid)
        #print("Ti_degC",self.Ti_degC)
        if self.Inlet.F is not None:
            self.F_m3s =self.Inlet.F/PropsSI("D", "P", self.Inlet.P, "T", (self.Ti_degC+273.15), self.Inlet.fluid)
            self.F_m3h=self.F_m3s*3600
        #print("F_m3s",self.F_m3s)

        

        
    #     # outlet connector calculation
        self.Outlet.fluid=self.Inlet.fluid
        self.Outlet.h=self.Inlet.h
        self.Outlet.F=self.Inlet.F
        self.Outlet.P=self.Inlet.P


        #Corrélation de la courbe caractéristique de la pompe
        #pip install scikit-learn
        from sklearn.linear_model import LinearRegression  
        from sklearn.preprocessing import PolynomialFeatures 
        from sklearn.metrics import mean_squared_error, r2_score



        #----------------------------------------------------------------------------------------#
        # Step 1: training data
        if self.X_F is None:
            self.X_F = [7,50,100,150]
        if self.Y_hmt is None:
            self.Y_hmt = [12,60,80,68]
        if self.Y_eta is None:
            self.Y_eta = [0.5,0.7,0.5,0.4]
        
       
        #print(max(self.X_F))
        self.X_F = np.asarray(self.X_F)
        max_x=max(self.X_F)
        self.Y_hmt = np.asarray(self.Y_hmt)
        self.max_Y_hmt=max(self.Y_hmt)
        self.Y_eta = np.asarray(self.Y_eta)
        max_Y_eta=max(self.Y_eta)


        self.X_F = self.X_F[:,np.newaxis]
        self.Y_hmt = self.Y_hmt[:,np.newaxis]
        self.Y_eta = self.Y_eta[:,np.newaxis]


        #----------------------------------------------------------------------------------------#
        # Step 2: data preparation

        self.nb_degree = len(self.X_F)-1

        self.polynomial_features = PolynomialFeatures(degree = self.nb_degree)

        X_TRANSF = self.polynomial_features.fit_transform(self.X_F)
       

        #----------------------------------------------------------------------------------------#
        # Step 3: define and train a model

        self.model_hmt = LinearRegression()
        self.model_eta = LinearRegression()

        #self.model_hmt.fit(X_TRANSF, self.Y_hmt)
        self.model_hmt.fit(X_TRANSF, self.Y_hmt)
        self.model_eta.fit(X_TRANSF, self.Y_eta)

        #----------------------------------------------------------------------------------------#
        # Step 4: calculate bias and variance

        self.Y_hmt_NEW = self.model_hmt.predict(X_TRANSF)
        self.Y_eta_NEW = self.model_eta.predict(X_TRANSF)

        self.rmse_hmt = np.sqrt(mean_squared_error(self.Y_hmt,self.Y_hmt_NEW))
        self.r2_hmt = r2_score(self.Y_hmt,self.Y_hmt_NEW)
        #print('RMSE: ', self.rmse_hmt)
        #print('R2: ', self.r2_hmt)

        rmse_eta = np.sqrt(mean_squared_error(self.Y_eta,self.Y_eta_NEW))
        r2_eta = r2_score(self.Y_eta,self.Y_eta_NEW)
        #print('RMSE: ', rmse_eta)
        #print('R2: ', r2_eta)

        #----------------------------------------------------------------------------------------#
        # Step 5: prediction

        self.x_new_min = 0.0
        self.x_new_max = 1.05*max_x

        self.X_NEW = np.linspace(self.x_new_min, self.x_new_max, 100)
        self.X_NEW = self.X_NEW[:,np.newaxis]
        #print(self.X_NEW)

        X_NEW_TRANSF = self.polynomial_features.fit_transform(self.X_NEW)
   

        self.Y_hmt_NEW = self.model_hmt.predict(X_NEW_TRANSF)
        self.Y_eta_NEW = self.model_eta.predict(X_NEW_TRANSF)

        #calculer hmt et delta_p pour le point de fonctionnement self.m3/h
        if self.F_m3h is not None and self.Pdischarge is None:
            self.calculate_hmt()

        if self.Pdischarge is not None:
            self.calculate_flow_rate()
        
        if self.F_m3h is not None:
            self.calculate_eta()

        try:
            self.Q_pump=self.F_m3s*(self.Pdischarge-self.Inlet.P)/self.eta
        except:
            self.Q_pump=self.F_m3s*(self.delta_p)/self.eta

        #-----------------------------------------------------------------------------------------#
        # sortir les résultats sous forme de dataframe avec le débit volumique et la hauteur manométrique du point de fonctionnement

        self.df = pd.DataFrame({'Pump': [self.Timestamp,self.Inlet.fluid,self.Inlet.F,self.F_m3h,self.hmt,self.delta_p,self.Q_pump/1000,self.eta,], },
                      index = ['Timestamp','pump_fluid','pump_F_kgs','pump_F_m3h','hmt(m)','delta_p (Pa)','Qpump(KW)','self.eta' ])


    def calculate_eta(self):
        """
        Calcule le rendement (eta) de la pompe en fonction du débit volumique (F_m3h)
        en utilisant la corrélation.

        Returns:
            float: Rendement (eta) de la pompe.
        """
        if self.model_eta is None:
            raise ValueError("Le modèle de rendement (eta) doit être entraîné avant de l'utiliser.")

        if self.F_m3h is None:
            raise ValueError("Le débit volumique (F_m3h) doit être calculé avant de prédire le rendement.")

        # Transformer le débit volumique pour le modèle
        F_m3h_array = np.array([[self.F_m3h]])  # Assurez-vous que F_m3h est un tableau 2D
        F_transformed = self.polynomial_features.transform(F_m3h_array)

        # Prédire le rendement
        self.eta = self.model_eta.predict(F_transformed)[0][0]
        return self.eta

    def calculate_flow_rate(self):
        """
        Calcule le débit volumique (F_m3h) en fonction des pressions d'entrée et de sortie,
        et de la hauteur manométrique calculée à partir de la corrélation.

        Returns:
            float: Débit volumique (F_m3h) en m³/h.
        """
        if self.Inlet.P is None or self.Pdischarge is None:
            raise ValueError("Les pressions d'entrée et de sortie doivent être définies.")

        if self.model_hmt is None:
            raise ValueError("Le modèle de hauteur manométrique (Hmt) doit être entraîné avant de l'utiliser.")

        # Calculer la hauteur manométrique (Hmt) à partir des pressions
        rho = PropsSI("D", "P", self.Inlet.P, "T", self.Ti_degC + 273.15, self.Inlet.fluid)
        g = 9.81  # Accélération gravitationnelle en m/s²
        self.delta_p = self.Pdischarge - self.Inlet.P
        self.hmt = self.delta_p / (rho * g)
        # print("Hauteur manométrique calculée (self.hmt):", self.hmt)

        # Fonction d'erreur pour minimisation
        def error_function(F_m3h):
            """
            Fonction d'erreur pour la minimisation.
            Compare la hauteur manométrique prédite avec la hauteur calculée.
            """
            F_m3h_array = np.array(F_m3h).reshape(-1, 1)  # Convertir en tableau 2D
            F_transformed = self.polynomial_features.transform(F_m3h_array)
            hmt_predicted = self.model_hmt.predict(F_transformed)[0][0]
            return abs(hmt_predicted - self.hmt)

        # Estimation initiale et bornes
        initial_guess = self.F_m3h if self.F_m3h is not None else self.X_F[0][0]  # Utiliser une estimation existante ou le premier point
        bounds = [(0.1, 1.5 * max(self.X_F))]  # Débit volumique entre 0.1 et 1.5 fois le maximum des données

        # Recherche numérique pour minimiser l'erreur
        result = minimize(
            error_function,
            x0=initial_guess,
            bounds=bounds,
            method='L-BFGS-B',  # Méthode robuste pour les problèmes avec bornes
            options={'ftol': 1e-6, 'disp': False}  # Tolérance plus stricte pour une meilleure précision
        )

        if result.success:
            self.F_m3h = result.x[0]
            # print("Débit volumique calculé (self.F_m3h):", self.F_m3h)
        else:
            raise ValueError(f"La recherche numérique pour le débit volumique a échoué : {result.message}")


    def calculate_hmt(self):
        """
        Calcule la hauteur manométrique (Hmt) à partir de la corrélation pour X_F = self.F_m3h.

        Returns:
            float: Hauteur manométrique prédite (Hmt) en mètres.
        """
        if self.model_hmt is None:
            raise ValueError("Le modèle de hauteur manométrique (Hmt) doit être entraîné avant de l'utiliser.")

        if self.F_m3h is None:
            raise ValueError("Le débit volumique (F_m3h) doit être calculé avant de prédire Hmt.")

        # Transformer le débit volumique pour le modèle
        F_m3h_array = np.array([[self.F_m3h]])
        F_transformed = self.polynomial_features.transform(F_m3h_array)

        # Prédire la hauteur manométrique
        self.hmt = self.model_hmt.predict(F_transformed)[0][0]
        
            # Obtenir la densité du fluide à l'entrée
        rho = PropsSI("D", "P", self.Inlet.P, "T", self.Ti_degC + 273.15, self.Inlet.fluid)

        # Accélération gravitationnelle
        g = 9.81  # m/s²

        # Calcul de la différence de pression
        self.delta_p = rho * g * self.hmt

    

        #----------------------------------------------------------------------------------------#
        # Step 6: Plotting

        
    def plot_pump_curve(self,figsize=(10, 6)):
        """
        Trace la courbe caractéristique de la pompe avec deux axes :
        - Axe principal : Hauteur manométrique (Hmt)
        - Axe secondaire : Rendement (eta)
        Affiche également les points utilisés pour créer les corrélations et le point de fonctionnement.
        """

                # Calculer la densité du fluide pour convertir Hmt en bar
        rho = PropsSI("D", "P", self.Inlet.P, "T", self.Ti_degC + 273.15, self.Inlet.fluid)
        g = 9.81  # Accélération gravitationnelle en m/s²

        # Fonction pour ajouter "bar" après chaque valeur de l'axe Y
        def format_with_bar(value, tick_number):
            pressure_bar = round(value * rho * g / 100000, 1)  # Conversion de Hmt en bar
            return f"{value:.0f}m({pressure_bar}bar)"
    
        # Créer une figure et un axe principal
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Axe principal pour la hauteur manométrique (Hmt)
        ax1.set_xlabel('Débit volumique (m³/h)')
        ax1.set_ylabel('Hauteur manométrique (m)', color='coral')
        ax1.plot(self.X_NEW, self.Y_hmt_NEW, color='coral', linewidth=3, label='Hauteur manométrique (Hmt)')
       
        ax1.tick_params(axis='y', labelcolor='coral')
        ax1.yaxis.set_major_formatter(FuncFormatter(format_with_bar))  # Appliquer le format personnalisé
        ax1.grid()

        # Axe secondaire pour le rendement (eta)
        ax2 = ax1.twinx()
        ax2.set_ylabel('Rendement (%)', color='blue')
        ax2.plot(self.X_NEW, self.Y_eta_NEW * 100, color='blue', linewidth=3, label='Rendement (eta)')
       
        ax2.tick_params(axis='y', labelcolor='blue')

        # Tracer le point de fonctionnement
        if self.F_m3h is not None and self.hmt is not None and self.eta is not None:
            ax1.scatter([self.F_m3h], [self.hmt], color='red', label='Point de fonctionnement', zorder=10)
            ax2.scatter([self.F_m3h], [self.eta * 100], color='red', zorder=10)

            # Ajouter des lignes pointillées vers les axes
            ax1.axvline(self.F_m3h, color='red', linestyle='--', linewidth=1)
            ax1.axhline(self.hmt, color='red', linestyle='--', linewidth=1)
            ax2.axhline(self.eta * 100, color='red', linestyle='--', linewidth=1)

        # Titre et limites
        title = 'Degree = {}; RMSE = {}; R2 = {}'.format(self.nb_degree, round(self.rmse_hmt, 2), round(self.r2_hmt, 2))
        plt.title("Courbe caractéristique de la pompe\n" + title, fontsize=10)
        ax1.set_xlim(self.x_new_min, self.x_new_max)
        ax1.set_ylim(0, 1.05 * self.max_Y_hmt)
        ax2.set_ylim(0, 105)  # Rendement en pourcentage (0 à 100%)



        # Sauvegarde et affichage
        plt.show() 