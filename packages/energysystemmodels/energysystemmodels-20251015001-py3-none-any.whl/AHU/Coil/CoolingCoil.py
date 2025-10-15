from AHU.air_humide import air_humide
from AHU.air_humide import air_humide_NB
from AHU.AirPort.AirPort import AirPort


class Object:
    def __init__(self):
        self.Inlet=AirPort() 
        self.Outlet=AirPort()
        
        #parameter :
        self.P_drop=0
        
        '''Point de consignes'''
        self.w_target=8 
        self.T_target=0
        
        '''Température point de rosée de l air au contact de la Coil froide '''
        self.T_sat=7  
        '''Températures inlet et outlet'''
        self.T_inlet=0
        self.T_Outlet=0
        
        '''Déshumidification Type'''
        self.Déshutype="Droite_sat"
                
        """facteur de bypass"""
        self.FB=0.2
        self.w_sat=0
        self.h_sat=0
        # calcul Outlet Coil
       
        self.Q_th=12      
        self.Eff=0.8 #efficacité de la Coil froide
        
        self.F=0
        self.F_m3h=0
        self.F_dry=0 #Débit d'air sec
        
    def calculate(self):
        #print("self.Inlet.P=",self.Inlet.P,"air_humide.Air_Pv_sat(self.T_sat)=",air_humide.Air_Pv_sat(self.T_sat),"self.T_sat=",self.T_sat)
        self.w_sat=air_humide.Air_w(T_db=self.T_sat, RH=100, P=self.Inlet.P)
        self.h_sat=air_humide.Air_h(T_db=self.T_sat,w=self.w_sat)
        self.Outlet.w=self.w_target
        self.T_inlet=air_humide_NB.Air3_Tdb(self.Inlet.w/1000, self.Inlet.P, self.Inlet.h)
        self.F=self.Inlet.F
        #print("self.w_sat=",self.w_sat,"self.w_target=",self.w_target)
        
        '''Test que la consigne de déshu est située entre w de l'air humide et HA_sat à la surface de la Coil froide'''
        # if self.Déshutype="Droite_sat":
        if self.Inlet.w>=self.w_target and self.w_target>=self.w_sat:
          
            self.Eff=(self.Inlet.w-self.Outlet.w)/(self.Inlet.w-self.w_sat)
            self.FB=1-self.Eff
            self.Outlet.h=self.Inlet.h-self.Eff*(self.Inlet.h-self.h_sat)
            self.T_Outlet=air_humide_NB.Air3_Tdb(self.w_target/1000, self.Inlet.P, self.Outlet.h)
            # print('CAS 1')
            
            #'''cas où après la transormation, la température de l'air traité est supérieure à la température de consigne'''
           
            # if self.T_Outlet>=self.T_target:
            #     self.Inlet.h=self.Outlet.h
            #     self.T_inlet=self.T_Outlet
            #     self.Eff=(self.T_target-self.T_sat)/(self.T_inlet-self.T_sat)
            #     self.FB=1-self.Eff
            #     self.Outlet.h=self.h_sat+self.Eff*(self.Inlet.h-self.h_sat)
            #     self.Outlet.w=self.w_sat+self.Eff*(self.w_target-self.w_sat)
              
                # print('CAS 2')
                
                
             #Air exterieur compris entre HA_sat et HA_Target et T_air extérieur > T_target   
       
        elif self.Inlet.w>self.w_sat and self.Inlet.w<=self.w_target and self.T_inlet>=self.T_target:
            self.Eff=(self.T_target-self.T_sat)/(self.T_inlet-self.T_sat)
            self.FB=1-self.Eff
            self.Outlet.h=self.h_sat+self.Eff*(self.Inlet.h-self.h_sat)
            self.Outlet.w=self.w_sat+self.Eff*(self.w_target-self.w_sat)
            #self.Outlet.h=air_humide_NB.Air4_Hs(self.T_target, self.Inlet.P, self.Inlet.w/1000)
            #self.Outlet.w=self.Inlet.w
            # print('CAS 3')
            
        # '''Cas où l'w de l'air à traiter est inférieure à l'HA_sat à la surface de la Coil'''
        #         ''' Avec refroidissement sensible sans déshu '''
        elif self.Inlet.w<=self.w_sat and self.T_inlet>=self.T_target:
            self.Eff=(self.T_sat-self.T_target)/(self.T_inlet-self.T_sat)
            self.FB=1-self.Eff
            self.Outlet.h=air_humide_NB.Air4_Hs(self.T_target, self.Inlet.P, self.Inlet.w/1000)
            self.Outlet.w=self.Inlet.w
            #print('CAS 4')
            
            ''' sans aucune action de la Coil froide (Pas de traitement à faire) '''
        else:
            self.Outlet.h=self.Inlet.h
            self.Outlet.w=self.Inlet.w
            self.Eff=0
            self.FB=1-self.Eff
            # print('CAS 5') 
        
        
        
        
        self.Outlet.P=self.Inlet.P-self.P_drop
        #self.F_dry=(self.Inlet.F)/air_humide_NB.Air3_Vs(self.Inlet.w/1000,self.Inlet.P,self.Inlet.h) #[m3/s] / [m3/kg air sec]  = [kg air sec/s]
        self.F_dry=(self.Inlet.F)/(1+(self.Inlet.w/1000))
        #print("self.F_dry=",self.F_dry)
        self.Q_th=(self.Outlet.h-self.Inlet.h)*self.F_dry       
        #self.Outlet.F=self.F_dry*air_humide_NB.Air3_Vs(self.Outlet.w/1000,self.Outlet.P,self.Outlet.h) #[kg air sec/s] * [m3/kg air sec] =[m3/s]
        self.Outlet.F=self.F_dry*(1+(self.Outlet.w/1000))
        #print("self.Inlet.F=",self.Inlet.F)
        #print("self.Outlet.F=",self.Outlet.F)
        self.Outlet.F_dry=self.F_dry
        
        
 
           
            
            


