
import json
from json import encoder

euro_MWhcumac=5.0 #euro/MWhcumac
H1=[1,2,3,5,8,10,14,15,19,21,23,25,27,28,38,39,42,43,45,51,52,54,55,57,58,59,60,61,62,63,67,68,69,70,71,73,74,75,76,77,78,80,87,88,89,90,91,92,93,94,95,975]
H2=[4,7,9,12,16,17,18,22,24,26,29,31,32,33,35,36,37,40,41,44,46,47,48,49,50,53,56,64,65,72,79,81,82,84,85,86]
H3=[6,11,13,20,30,34,66,83,971,972,973,974,976]

#################################Transport#########################

def TRA_EQ_101(longueur_uti,nb_voyage_an,nb_uti):
    global euro_MWhcumac

    if longueur_uti=="UTIinf9":
        kWh_cumac=9300*(float(nb_voyage_an)*float(nb_uti))
    if longueur_uti=="UTIsup9":
        kWh_cumac=18500*(float(nb_voyage_an)*float(nb_uti))
    MWh_cumac=kWh_cumac/1000
    euro=MWh_cumac*euro_MWhcumac

    value = {
         "fiche_cee": "TRA_EQ_101",
         "titre": "Unité de transport intermodal pour le transport combiné rail-route",
        "euro_MWhcumac": euro_MWhcumac,
        "MWh_cumac": MWh_cumac,
        "euro": euro,
    }
 
    # Dictionary to JSON Object using dumps() method
    # Return JSON Object
    return json.dumps(value,ensure_ascii=False)

def TRA_EQ_107(type_bateau,bassin_navigation,nb_voyage_uti):
    global euro_MWhcumac

    if type_bateau=="Bateau DEK (1 000 t)":
        if bassin_navigation=="Seine":
            Ga=3800
        if bassin_navigation=="Rhône":
            Ga=3200 
        if bassin_navigation=="Nord Pas-de-Calais":
            Ga=3300 
        if bassin_navigation=="Rhin/Moselle":
            Ga=1200 
        if bassin_navigation=="Interbassin":
            Ga=2900
    if type_bateau=="Bateau RHK (1 350 t)":
        if bassin_navigation=="Seine":
            Ga=7900 
        if bassin_navigation=="Rhône":
            Ga=7500  
        if bassin_navigation=="Nord Pas-de-Calais":
            Ga=4000 
        if bassin_navigation=="Rhin/Moselle":
            Ga=2600 
        if bassin_navigation=="Interbassin":
            Ga=5500
    if type_bateau=="Bateau Grand Rhénan (2 500 t)":
        if bassin_navigation=="Seine":
            Ga=8500 
        if bassin_navigation=="Rhône":
            Ga=7800 
        if bassin_navigation=="Nord Pas-de-Calais":
            Ga=4700
        if bassin_navigation=="Rhin/Moselle":
            Ga=4100
        if bassin_navigation=="Interbassin":
            Ga=6300

    if type_bateau=="Bateau Convois (4 400 t)":
        if bassin_navigation=="Seine":
            Ga=9000
        if bassin_navigation=="Rhône":
            Ga=8500 
        if bassin_navigation=="Nord Pas-de-Calais":
            Ga=8300
        if bassin_navigation=="Rhin/Moselle":
            Ga=6500 
        if bassin_navigation=="Interbassin":
            Ga=8000

    
    kWh_cumac=Ga*float(nb_voyage_uti)
    MWh_cumac=kWh_cumac/1000
    euro=MWh_cumac*euro_MWhcumac

    value = {
         "fiche_cee": "TRA_EQ_107",
         "titre": "Unité de transport intermodal pour le transport combiné fluvial-route",
        "euro_MWhcumac": euro_MWhcumac,
        "MWh_cumac": MWh_cumac,
        "euro": euro,
    }
 
    # Dictionary to JSON Object using dumps() method
    # Return JSON Object
    return json.dumps(value,ensure_ascii=False)

def TRA_EQ_108(type_ligne,nb_voyage_ligne,distance_routiere_france,distance_feroviaire_france):
    global euro_MWhcumac

    if type_ligne=="Calais_Folkstone":
        kWh_cumac=6290*float(nb_voyage_ligne)
    if type_ligne=="Autre":
        kWh_cumac=(145*float(distance_routiere_france)-72*float(distance_feroviaire_france))*float(nb_voyage_ligne)
        if kWh_cumac<0:
            kWh_cumac=0

    MWh_cumac=kWh_cumac/1000
    euro=MWh_cumac*euro_MWhcumac

    value = {
         "fiche_cee": "TRA_EQ_108",
         "titre": "Wagon d'autoroute ferroviaire",
        "euro_MWhcumac": euro_MWhcumac,
        "MWh_cumac": MWh_cumac,
        "euro": euro,
    }
 
    # Dictionary to JSON Object using dumps() method
    # Return JSON Object
    return json.dumps(value,ensure_ascii=False)


# ########################################Industrie##################################
#fonctionnement : "1*8h" ,"2*8h" ,"8h_ArrWE" ,"3*8h_sansArrWE"
#Equipement_type : "pump","fan","air compressor","chiller"
#puissance_nominale : <=1000 kW , Puissance électrique nominale du moteur entraînant le système moto-régulé (en kW)
#Heat_Use : "chauffage de locaux","ECS","procédé industriel"
# puissance_nominale : Puissance nominal de l'échangeur ou au max la puissance électrique nominale du compresseur

def IND_UT_103(fonctionnement, Department, Heat_Use, puissance_nominale):

    global euro_MWhcumac
    global H1,H2,H3

    if Heat_Use=="chauffage de locaux" or Heat_Use=="ECS":

        if Department in H1:
            if fonctionnement=="1*8h" :
                kWhcumac_kW=6400
            if fonctionnement=="2*8h" :
                kWhcumac_kW=15900
            if fonctionnement=="3*8h_ArrWE" :
                kWhcumac_kW=19700
            if fonctionnement=="3*8h_sansArrWE":
                kWhcumac_kW=26700              

        if Department in H2:
            if fonctionnement=="1*8h" :
                kWhcumac_kW=6000
            if fonctionnement=="2*8h" :
                kWhcumac_kW=15000
            if fonctionnement=="3*8h_ArrWE" :
                kWhcumac_kW=18600
            if fonctionnement=="3*8h_sansArrWE":
                kWhcumac_kW=25200

        if Department in H3:
            if fonctionnement=="1*8h" :
                kWhcumac_kW=5000
            if fonctionnement=="2*8h" :
                kWhcumac_kW=12600
            if fonctionnement=="3*8h_ArrWE" :
                kWhcumac_kW=15600
            if fonctionnement=="3*8h_sansArrWE":
                kWhcumac_kW=21100

    if Heat_Use=="procédé industriel":
        if fonctionnement=="1*8h" :
            kWhcumac_kW=10300
        if fonctionnement=="2*8h" :
            kWhcumac_kW=25600
        if fonctionnement=="3*8h_ArrWE" :
            kWhcumac_kW=31800
        if fonctionnement=="3*8h_sansArrWE":
            kWhcumac_kW=43100

    kWh_cumac=kWhcumac_kW*puissance_nominale
    MWh_cumac=kWh_cumac/1000
    euro=MWh_cumac*euro_MWhcumac

    return "Système de récupération de chaleur sur un compresseur d’air : ",MWh_cumac, euro

def IND_UT_131(*Data):
    #fonctionnement,  Temperature,Geometry,S (Plan)
    #fonctionnement,Temperature, Geometry ,D,L (Cylindre)

    fonctionnement=Data[0]
    Temperature=Data[1]
    Geometery=Data[2]
    if Geometery=="cylindre":
        D=Data[3]
        L=Data[4]
        if D>=508:
            S=3.141592653589793*D/1000*L
        if D<508:
            S=None
    if Geometery=="plan":
        S=Data[3]
    
    if fonctionnement=="1*8h" :
        Coef=1.0
    if fonctionnement=="2*8h" :
        Coef=2.2
    if fonctionnement=="3*8h_ArrWE" :
        Coef=3.0
    if fonctionnement=="3*8h_sansArrWE":
        Coef=4.2
    
    if S is not None:
        print("equation plan ou grand diamètre")
        if -60 < Temperature <=0:
            kWhcumac_m2=80
        if 0 < Temperature <=40:
            kWhcumac_m2=0
        if 40 < Temperature <=100:
            kWhcumac_m2=190
        if 100 < Temperature <=300:
            kWhcumac_m2=490
        if 300 < Temperature <=600:
            kWhcumac_m2=1100
        kWh_cumac=kWhcumac_m2*Coef*S
    

    else:
        print("equation cylindre avec D<508 mm")
        if -60 < Temperature <=0:
            kWhcumac_m=53
        if 0 < Temperature <=40:
            kWhcumac_m=0
        if 40 < Temperature <=100:
            kWhcumac_m=110
        if 100 < Temperature <=300:
            kWhcumac_m=310
        if 300 < Temperature <=600:
            kWhcumac_m=850
        kWh_cumac=kWhcumac_m*Coef*L

    MWh_cumac=kWh_cumac/1000
    euro=MWh_cumac*euro_MWhcumac
    

    return "Isolation thermique des parois planes ou cylindriques sur des installations industrielles (France métropolitaine) : ",MWh_cumac, euro

def IND_UT_130(fonctionnement,puissance_nominale):
    global euro_MWhcumac
    if puissance_nominale<=20000:
        
        
        if fonctionnement=="1*8h" :
            kWhcumac_kW=340
        if fonctionnement=="2*8h" :
            kWhcumac_kW=740
        if fonctionnement=="3*8h_ArrWE" :
            kWhcumac_kW=1000
        if fonctionnement=="3*8h_sansArrWE"  :
            kWhcumac_kW=1400
        
       

       
            
        kWh_cumac=kWhcumac_kW*puissance_nominale
        MWh_cumac=kWh_cumac/1000
        euro=MWh_cumac*euro_MWhcumac

    else:
        MWh_cumac=0
        euro=0
    return "Condenseur sur les effluents gazeux d’une chaudière de production de vapeur : ",MWh_cumac, euro,

def IND_UT_134(fonctionnement, duree_contrat,puissance_nominale):
    global euro_MWhcumac
    if duree_contrat==1.0:
        F=1
    if duree_contrat==2.0:
        F=1.96
    if duree_contrat==3.0:
        F=2.89
    if duree_contrat==4.0:
        F=3.78
    if duree_contrat==5.0:
        F=4.63
    if duree_contrat>=6.0:
        F=5.45
    
    if fonctionnement=="1*8h" :
        kWh_cumac=29.4*1*puissance_nominale*F
    if fonctionnement=="2*8h" :
        kWh_cumac=29.4*2.2*puissance_nominale*F
    if fonctionnement=="3*8h_ArrWE" :
        kWh_cumac=29.4*3*puissance_nominale*F
    if fonctionnement=="3*8h_sansArrWE"  :
        kWh_cumac=29.4*4.2*puissance_nominale*F
    MWh_cumac=kWh_cumac/1000
    euro=MWh_cumac*euro_MWhcumac

    # données de Outlet
    value = {
         "fiche_cee": "IND_UT_134",
         "titre": "Système de mesurage d’indicateurs de performance énergétique",
        "euro_MWhcumac": euro_MWhcumac,
        "MWh_cumac": MWh_cumac,
        "euro": euro,
       
    }
 
    # Dictionary to JSON Object using dumps() method
    # Return JSON Object
    return json.dumps(value,ensure_ascii=False)

def IND_UT_135(fonctionnement, Department, Supply_Temperature, puissance_nominale):

    global euro_MWhcumac
    global H1,H2,H3

    if Department in H1:
        if 12 <= Supply_Temperature <15:
            kWhcumac_kW=7400
        if 15 <= Supply_Temperature <18:
            kWhcumac_kW=9900
        if 18 <= Supply_Temperature <=21:
            kWhcumac_kW=12300

    if Department in H2:
        if 12 <= Supply_Temperature <15:
            kWhcumac_kW=4900
        if 15 <= Supply_Temperature <18:
            kWhcumac_kW=8200
        if 18 <= Supply_Temperature <=21:
            kWhcumac_kW=11500

    if Department in H3:
        if 12 <= Supply_Temperature <15:
            kWhcumac_kW=3300
        if 15 <= Supply_Temperature <18:
            kWhcumac_kW=5800
        if 18 <= Supply_Temperature <=21:
            kWhcumac_kW=9000

    if fonctionnement=="1*8h" :
        Coef=1.0
    if fonctionnement=="2*8h" :
        Coef=2.2
    if fonctionnement=="3*8h_ArrWE" :
        Coef=3.0
    if fonctionnement=="3*8h_sansArrWE":
        Coef=4.2

    kWh_cumac=kWhcumac_kW*Coef*puissance_nominale
    MWh_cumac=kWh_cumac/1000
    euro=MWh_cumac*euro_MWhcumac


    return "Freecooling par eau de refroidissement en substitution d’un groupe froid : ",MWh_cumac, euro

def IND_UT_136(fonctionnement, Equipement_type,puissance_nominale):
    global euro_MWhcumac


    if puissance_nominale<=1000:
        if Equipement_type=="pump" or Equipement_type=="fan":
        
            if fonctionnement=="1*8h" :
                kWh_cumac=7800*puissance_nominale
            if fonctionnement=="2*8h" :
                kWh_cumac=17100*puissance_nominale
            if fonctionnement=="3*8h_ArrWE" :
                kWh_cumac=23300*puissance_nominale
            if fonctionnement=="3*8h_sansArrWE"  :
                kWh_cumac=32600*puissance_nominale
            MWh_cumac=kWh_cumac/1000
            euro=MWh_cumac*euro_MWhcumac

        if Equipement_type=="air compressor" or Equipement_type=="chiller":
        
            if fonctionnement=="1*8h" :
                kWhcumac_kW=4400
            if fonctionnement=="2*8h" :
                kWhcumac_kW=9800
            if fonctionnement=="3*8h_ArrWE" :
                kWhcumac_kW=13300
            if fonctionnement=="3*8h_sansArrWE":
                kWhcumac_kW=18600
            
            kWh_cumac=kWhcumac_kW*puissance_nominale
            MWh_cumac=kWh_cumac/1000
            euro=MWh_cumac*euro_MWhcumac

    else:
        MWh_cumac=0
        euro=0
    return "Systèmes moto-régulés : ",MWh_cumac, euro,


