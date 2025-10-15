from ThermodynamicCycles.FluidPort.FluidPort import FluidPort
def Fluid_connect( inlet=FluidPort(),outlet=FluidPort()):
    inlet.fluid=outlet.fluid
    if inlet.P is not None:
        #print("inlet.P....",inlet.P)
        outlet.P=inlet.P
    else:
        inlet.P=outlet.P
    inlet.h=outlet.h
    inlet.F=outlet.F
    inlet.S=outlet.S
    inlet.T=outlet.T
    inlet.calculate_properties()
    outlet.calculate_properties()
    return "connectés"