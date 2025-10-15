from AHU.air_humide import air_humide



class AirPort:
    def __init__(self):
        self.F=None # air humide en kg/s
        self.F_dry=None # air sec en kg/s
        self.P = 101325 # pression
        self.h = None # enthalpie spéc
        self.w = None # Humidité absolue
        
    # def propriete(self):
    #     self.result="RH,Pv_sat,T="
    #     self.T=air_humide.Air_T_db(h=self.h, w=self.w)
    #     self.Pv_sat=air_humide.Air_Pv_sat(self.T)
    #     self.RH=air_humide.Air_RH(Pv_sat=self.Pv_sat, w=self.w, P=self.P)
    #     return self.result,self.RH,self.Pv_sat,self.T

        # Propriétés calculées
        self._T = None       # Température de l'air en °C (calculée si nécessaire)
        self._RH = None      # Humidité relative de l'air en % (calculée si nécessaire)
        self._Pv_sat = None  # Pression de vapeur saturante (Pa) (calculée si nécessaire)

    @property
    def T(self):
        """
        Calcul automatique de la température de l'air en fonction de l'enthalpie et de l'humidité absolue.
        """
        if self._T is None and self.h is not None and self.w is not None:
            self._T = air_humide.Air_T_db(h=self.h, w=self.w)  # Calcul de la température en 
        return self._T

    @property
    def RH(self):
        """
        Calcul automatique de l'humidité relative en fonction de la température, de l'humidité absolue et de la pression.
        """
        if self._RH is None and self.w is not None and self.P is not None:
            # Calcul de la pression de vapeur saturante et de l'humidité relative
            self._Pv_sat = air_humide.Air_Pv_sat(self.T)  # Calcul de la pression de vapeur saturante
            self._RH = air_humide.Air_RH(Pv_sat=self._Pv_sat, w=self.w, P=self.P)  # Calcul de RH
        return self._RH

    @property
    def Pv_sat(self):
        """
        Calcul automatique de la pression de vapeur saturante en fonction de la température.
        """
        if self._Pv_sat is None and self.T is not None:
            self._Pv_sat = air_humide.Air_Pv_sat(self.T)  # Calcul de la pression de vapeur saturante
        return self._Pv_sat

  
    def update_properties(self):
        """
        Méthode qui permet de forcer le recalcul des propriétés (T, RH, Pv_sat) si nécessaire.
        Cela permet de mettre à jour les propriétés automatiquement si les valeurs de base changent.
        """
        self._T = None
        self._RH = None
        self._Pv_sat = None
        # Recalcule les propriétés dès qu'elles sont nécessaires
        _ = self.T
        _ = self.RH
        _ = self.Pv_sat  

