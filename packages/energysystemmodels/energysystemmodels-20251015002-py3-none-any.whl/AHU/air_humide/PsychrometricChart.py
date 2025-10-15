import matplotlib.pyplot as plt
import numpy as np
from AHU.air_humide import air_humide

class Object:
    def __init__(self, figsize=(10, 6)):

        self.points_to_plot = []
        self.T_db_min = -10
        self.T_db_max = 40
        self.w_min = float('inf')
        self.w_max = air_humide.Air_w(T_db=self.T_db_max, RH=100)

   
        self.title = 'Diagramme Psychrométrique'
        self.T_db_range = np.linspace(self.T_db_min, self.T_db_max, self.T_db_max - self.T_db_min)
     
        self.RH_values_dizaines = list(range(10, 101, 10))
        self.RH_values_intermediaires = list(range(5, 96, 10))
        self.enthalpy_values = list(range(0, 111, 10))
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.points_to_plot = []


    def set_title(self, new_title):
        self.title = new_title


    def add_points(self, points):
        for point in points:
            T_db, w = None, None
            if 'T_db' in point and 'RH' in point:
                T_db, w = point['T_db'], air_humide.Air_w(RH=point['RH'], T_db=point['T_db'])
            elif 'h' in point and 'T_db' in point:
                T_db, w = point['T_db'], air_humide.Air_w(h=point['h'], T_db=point['T_db'])
            elif 'w' in point and 'T_db' in point:
                T_db, w = point['T_db'], point['w']
            elif 'RH' in point and 'w' in point:
                T_db, w = air_humide.Air_T_db(RH=point['RH'], w=point['w']), point['w']
            elif 'h' in point and 'w' in point:
                T_db, w = air_humide.Air_T_db(h=point['h'], w=point['w']), point['w']
            elif 'Pv_sat' in point and 'RH' in point:
                T_db= air_humide.Air_T_db(Pv_sat=point['Pv_sat'])
                w=air_humide.Air_w(RH=point['RH'], T_db=T_db)
            elif 'Pv_sat' in point and 'w' in point:
                T_db, w = air_humide.Air_T_db(Pv_sat=point['Pv_sat']), point['w']
            
            self.points_to_plot.append((T_db, w))
         
            for T_db, w in self.points_to_plot:
                self.T_db_min = int(min(self.T_db_min, T_db))
                self.T_db_max = int(max(self.T_db_max, T_db))
                self.w_min = int(min(self.w_min, w))
                self.w_max = int(max(self.w_max, w))

        #print("self.w_max=================",self.w_max)
        self.enthalpy_values_max=round(int(air_humide.Air_h(T_db=self.T_db_min,w=self.w_max))/ 10) * 10
        self.enthalpy_values_min=round(int(air_humide.Air_h(T_db=self.T_db_min,w=0)) / 10) * 10

        num_values = 10
        step = int((self.enthalpy_values_max - self.enthalpy_values_min) / (num_values - 1))

        self.enthalpy_values = list(range(self.enthalpy_values_min, self.enthalpy_values_max+1, step))
       


        # Mettre à jour les valeurs d'enthalpie
        self.T_db_range = np.linspace(self.T_db_min, self.T_db_max, self.T_db_max - self.T_db_min)
        self.draw_enthalpy_lines()




        
     



    def draw_enthalpy_lines(self):
     
        for h_value in self.enthalpy_values:
            w_values = [air_humide.Air_w(h=h_value, T_db=T_db) for T_db in self.T_db_range]
            self.ax.plot(self.T_db_range, w_values, 'k-', linewidth=0.5)
            x_pos = self.T_db_range[0] - 1
            y_pos = w_values[0]
            self.ax.text(x_pos, y_pos, f'{h_value} kJ/kg', va='center', ha='left', color='black', fontsize=8)





    def _plot_base_chart(self):
        self.ax.clear()  # Effacer le graphique existant
        
        # Tracer les lignes d'iso-RH
        for RH in self.RH_values_dizaines + self.RH_values_intermediaires:
            w_values = [air_humide.Air_w(RH=RH, T_db=T_db) for T_db in self.T_db_range]
            line_style = 'k-' if RH % 10 == 0 else 'k--'
            self.ax.plot(self.T_db_range, w_values, line_style, linewidth=0.5)

        self.draw_enthalpy_lines()


        # Définir les limites des axes et autres paramètres
        self.ax.set_ylim(0, self.w_max)
        self.ax.set_title(self.title)
        self.ax.set_xlabel('Température de bulbe sec (°C)')
        self.ax.set_ylabel('Humidité spécifique (g/kg air sec)')
        self.ax.yaxis.set_label_position("right")
        self.ax.yaxis.tick_right()
        self.ax.grid(True)


    def _draw_arrows(self):
        for i in range(len(self.points_to_plot) - 1):
            start_point = self.points_to_plot[i]
            end_point = self.points_to_plot[i + 1]
            self.ax.annotate(
                '',
                xy=end_point,
                xytext=start_point,
                arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5)
            )

    def show(self,draw_arrows=True):
        self._plot_base_chart()
        for T_db, w in self.points_to_plot:
            self.ax.plot(T_db, w, 'ro')
        if draw_arrows==True:
            self._draw_arrows()  # Dessiner les flèches entre les points

        plt.show()




