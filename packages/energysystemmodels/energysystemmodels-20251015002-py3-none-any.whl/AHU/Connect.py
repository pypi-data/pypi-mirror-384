from AHU.AirPort.AirPort import AirPort
def Air_connect( Inlet=AirPort(),Outlet=AirPort()): # a : port d'entrée d'un composant, b Outlet composant 
    Inlet.w=Outlet.w #humidité absolue en g/kgas"
    Inlet.P=Outlet.P
    Inlet.h=Outlet.h #kJ/kgas
    Inlet.F=Outlet.F # débit d'air humide
    Inlet.F_dry=Outlet.F_dry # débit d'air sec kg/
    
    Inlet.update_properties()

    return "connectés"