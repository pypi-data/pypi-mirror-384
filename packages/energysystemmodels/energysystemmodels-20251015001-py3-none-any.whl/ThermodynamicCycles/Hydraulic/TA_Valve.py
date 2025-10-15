from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
from CoolProp.CoolProp import PropsSI
import pandas as pd 
import math

#No module named 'openpyxl'
#pip install openpyxl

class Object :
    def __init__(self):

        self.Timestamp=None
        self.Inlet=FluidPort() 
        self.Outlet=FluidPort()
        self.df=[]
        self.delta_P=None

        self.q=None
        self.nb_tours=None
        self.dn=None

        self.kv_values = {
            0.5: [None,0.127, 0.511, 0.60, 1.14, 1.75, 2.56, 1.8, 2, 2.5, 5.5, 6.5],
            0.6: [None,0.144,0.5602,0.686,1.292,2.06,2.888,2.12,2.4,3.2,6.5,7.6],
            0.7: [None,0.161,0.6094,0.772,1.444,2.37,3.216,2.44,2.8,3.9,7.5,8.7],
            0.8: [None,0.178,0.6586,0.858,1.596,2.68,3.544,2.76,3.2,4.6,8.5,9.8],
            0.9: [None,0.195,0.7078,0.944,1.748,2.99,3.872,3.08,3.6,5.3,9.5,10.9],
            1: [0.090, 0.212, 0.757, 1.03, 1.90, 3.30, 4.20, 3.4, 4, 6, 10.5, 12],
            1.1: [0.0994,0.2324,0.8436,1.244,2.14,3.56,4.8875,3.7,4.4,6.6,11.5,14],
            1.2: [0.1088,0.2528,0.9302,1.458,2.38,3.82,5.575,4,4.8,7.2,12.5,16],
            1.3: [0.1182,0.2732,1.0168,1.672,2.62,4.08,6.2625,4.3,5.2,7.8,13.5,18],
            1.4: [0.1276,0.2936,1.1034,1.886,2.86,4.34,6.95,4.6,5.6,8.4,14.5,20],
            1.5: [0.137, 0.314, 1.19, 2.10, 3.10, 4.60, 7.20, 4.9, 6, 9, 15.5, 22],
            1.6: [0.1616,0.3654,1.332,2.404,3.412,4.9,8.1,5.22,6.4,9.5,16.7,25.6],
            1.7: [0.1862,0.4168,1.474,2.708,3.724,5.2,9,5.54,6.8,10,17.9,29.2],
            1.8: [0.2108,0.4682,1.616,3.012,4.036,5.5,9.9,5.86,7.2,10.5,19.1,32.8],
            1.9: [0.2354,0.5196,1.758,3.316,4.348,5.8,10.8,6.18,7.6,11,20.3,36.4],
            2: [0.260, 0.571, 1.90, 3.62, 4.66, 6.10, 11.7, 6.5, 8, 11.5, 21.5, 40],
           2.1	:	[	0.304	,	0.6322	,	2.08	,	3.956	,	5.148	,	6.64	,	12.6	,	7.06	,	8.6	,	12.4	,	22.6	,	45	]	,
2.2	:	[	0.348	,	0.6934	,	2.26	,	4.292	,	5.636	,	7.18	,	13.5	,	7.62	,	9.2	,	13.3	,	23.7	,	50	]	,
2.3	:	[	0.392	,	0.7546	,	2.44	,	4.628	,	6.124	,	7.72	,	14.4	,	8.18	,	9.8	,	14.2	,	24.8	,	55	]	,
2.4	:	[	0.436	,	0.8158	,	2.62	,	4.964	,	6.612	,	8.26	,	15.3	,	8.74	,	10.4	,	15.1	,	25.9	,	60	]	,
            2.5: [0.480, 0.877, 2.80, 5.30, 7.10, 8.80, 16.2, 9.3, 11, 16, 27, 65],
2.6	:	[	0.5492	,	0.9776	,	3.014	,	5.62	,	7.58	,	9.56	,	17.26	,	10.7	,	11.6	,	18	,	28.8	,	72	]	,
2.7	:	[	0.6184	,	1.0782	,	3.228	,	5.94	,	8.06	,	10.32	,	18.32	,	12.1	,	12.2	,	20	,	30.6	,	79	]	,
2.8	:	[	0.6876	,	1.1788	,	3.442	,	6.26	,	8.54	,	11.08	,	19.38	,	13.5	,	12.8	,	22	,	32.4	,	86	]	,
2.9	:	[	0.7568	,	1.2794	,	3.656	,	6.58	,	9.02	,	11.84	,	20.44	,	14.9	,	13.4	,	24	,	34.2	,	93	]	,
            3: [0.826, 1.38, 3.87, 6.90, 9.50, 12.6, 21.5, 16.3, 14, 26, 36, 100],
           3.1	:	[	0.9128	,	1.5	,	4.046	,	7.12	,	9.96	,	13.28	,	22.5	,	18.16	,	15.1	,	29.6	,	39.8	,	107	]	,
3.2	:	[	0.9996	,	1.62	,	4.222	,	7.34	,	10.42	,	13.96	,	23.5	,	20.02	,	16.2	,	33.2	,	43.6	,	114	]	,
3.3	:	[	1.0864	,	1.74	,	4.398	,	7.56,10.88	,	14.64	,	24.5	,	21.88	,	17.3	,	36.8	,	47.4	,	121	]	,
        3.4	:[1.1732,1.86,4.574	,7.78,	11.34	,	15.32,25.5	,	23.74	,	18.4	,	40.4	,	51.2	,128	]	,
        3.5: [1.26, 1.98, 4.75, 8.00, 11.8, 16.0, 26.5, 25.6, 19.5, 44, 55, 135],
         3.6	:	[	1.302	,	2.088	,	4.94	,	8.14	,	12.28	,	16.64	,	27.8	,	27.54	,	21.4	,	47.8	,	60.6	,	141.8	]	,
3.7	:	[	1.344	,	2.196	,	5.13	,	8.28	,	12.76	,	17.28	,	29.1	,	29.48	,	23.3	,	51.6	,	66.2	,	148.6	]	,
3.8	:	[	1.386	,	2.304	,	5.32	,	8.42	,	13.24	,	17.92	,	30.4	,	31.42	,	25.2	,	55.4	,	71.8	,	155.4	]	,
3.9	:	[	1.428	,	2.412	,	5.51	,	8.56	,	13.72	,	18.56	,	31.7	,	33.36	,	27.1	,	59.2	,	77.4	,	162.2	]	,
            4: [1.47, 2.52, 5.70, 8.70, 14.2, 19.2, 33.0, 35.3, 29, 63, 83, 169],
         4.1	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	37.14	,	31.4	,	66.4	,	89.2	,	176.6	]	,
4.2	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	38.98	,	33.8	,	69.8	,	95.4	,	184.2	]	,
4.3	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	40.82	,	36.2	,	73.2	,	101.6	,	191.8	]	,
4.4	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	42.66	,	38.6	,	76.6	,	107.8	,	199.4	]	,
            4.5: [None,None,None,None,None,None,None,44.5, 41, 80, 114, 207],
         4.6	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	46	,	43.8	,	83.6	,	119.4	,	214	]	,
4.7	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	47.5	,	46.6	,	87.2	,	124.8	,	221	]	,
4.8	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	49	,	49.4	,	90.8	,	130.2	,	228	]	,
4.9	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	50.5	,	52.2	,	94.4	,	135.6	,	235	]	,
            5: [None,None,None,None,None,None,None,52, 55, 98, 141, 242],
 5.1	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	53.7	,	57.6	,	101.4	,	146.2	,	249.4	]	,
5.2	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	55.4	,	60.2	,	104.8	,	151.4	,	256.8	]	,
5.3	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	57.1	,	62.8	,	108.2	,	156.6	,	264.2	]	,
5.4	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	58.8	,	65.4	,	111.6	,	161.8	,	271.6	]	,          
           

            5.5: [None,None,None,None,None,None,None,60.5, 68, 115, 167, 279],
 5.6	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	62	,	70.4	,	118.4	,	173	,	285.6	]	,
5.7	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	63.5	,	72.8	,	121.8	,	179	,	292.2	]	,
5.8	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	65	,	75.2	,	125.2	,	185	,	298.8	]	,
5.9	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	66.5	,	77.6	,	128.6	,	191	,	305.4	]	,          
           


            6: [None,None,None,None,None,None,None,68, 80, 132, 197, 312],
  6.1	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	69	,	82.4	,	134.6	,	201.6	,	317.6	]	,
6.2	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	70	,	84.8	,	137.2	,	206.2	,	323.2	]	,
6.3	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	71	,	87.2	,	139.8	,	210.8	,	328.8	]	,
6.4	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	72	,	89.6	,	142.4	,	215.4	,	334.4	]	,          
            


            6.5: [None,None,None,None,None,None,None,73, 92, 145, 220, 340],
    6.6	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	73.8	,	94.2	,	147.8	,	225.8	,	345.4	]	,
6.7	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	74.6	,	96.4	,	150.6	,	231.6	,	350.8	]	,
6.8	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	75.4	,	98.6	,	153.4	,	237.4	,	356.2	]	,
6.9	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	76.2	,	100.8	,	156.2	,	243.2	,	361.6	]	,      
          

            7: [None,None,None,None,None,None,None,77, 103, 159, 249, 367],
        
  7.1	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	77.7	,	105	,	162.2	,	254.4	,	371.8	]	,
7.2	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	78.4	,	107	,	165.4	,	259.8	,	376.6	]	,
7.3	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	79.1	,	109	,	168.6	,	265.2	,	381.4	]	,
7.4	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	79.8	,	111	,	171.8	,	270.6	,	386.2	]	,      

            7.5: [None,None,None,None,None,None,None,80.5, 113, 175, 276, 391],
 7.6	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	81.4	,	114.4	,	178	,	280.8	,	396.8	]	,
7.7	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	82.3	,	115.8	,	181	,	285.6	,	402.6	]	,
7.8	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	83.2	,	117.2	,	184	,	290.4	,	408.4	]	,
7.9	:	[	None	,	None	,	None	,	None	,	None	,	None	,	None	,	84.1	,	118.6	,	187	,	295.2	,	414.2	]	,          
           

            8: [None,None,None,None,None,None,None,85, 120, 190, 300, 420],

        }

  

        self.diametres = [10, 15, 20, 25, 32, 40, 50, 65, 80, 100, 125, 150]
    
    def calculate(self):
        """
        Calcule la perte de charge en fonction du débit (q en m3/h),
        du nombre de tours et du diamètre nominal (DN).
        """
        self.rho = PropsSI('D', 'P', self.Inlet.P, 'H', self.Inlet.h, self.Inlet.fluid)
        #convertir le débit de kg/s à m3/h
        self.q=self.Inlet.F*3600/self.rho # Débit en m3/h

        if self.nb_tours not in self.kv_values:
            raise ValueError("Nombre de tours non valide")
        
        if self.dn not in self.diametres:
            raise ValueError("Diamètre nominal non valide")
        
        kv_index = self.diametres.index(self.dn)
        kv = self.kv_values[self.nb_tours][kv_index]
        
        self.delta_P = (self.q / kv) ** 2*10**5 # Formule : ΔP = (q / Kv)²  en Pa

        self.Inlet.calculate_properties()
        self.Outlet.P=self.Inlet.P-self.delta_P
        self.Outlet.F=self.Inlet.F
        self.Outlet.fluid = self.Inlet.fluid
        self.Outlet.T = self.Inlet.T
        self.Outlet.calculate_properties()

        # Stocker les données dans un DataFrame
        self.df = pd.DataFrame({
            'Débit (m3/h)': [self.q],
            'Nombre de tours': [self.nb_tours],
            'Diamètre nominal (DN)': [self.dn],
            'Perte de charge (Pa)': [self.delta_P],  
            'Pression de sortie (Pa)': [self.Outlet.P],
        }).T
    

