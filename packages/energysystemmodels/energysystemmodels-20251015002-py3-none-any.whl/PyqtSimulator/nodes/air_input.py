from PyQt5.QtCore import *
from PyqtSimulator.calc_conf import *
from PyqtSimulator.calc_node_base import *
from NodeEditor.nodeeditor.utils import dumpException

#from component.OpenWeatherMap import SQlite_OpenWeatherMap

#from CoolProp.CoolProp import PropsSI

#from AHU import FreshAir
from AHU import FreshAir
#from AHU.air_humide import air_humide
from AHU.air_humide import air_humide

import sched, time

class CalcAirInputContent(QDMNodeContentWidget):
    def initUI(self):
        
        
        
        # self.fluid_lbl = QLabel("Type de fluide", self)
        # self.fluid=QComboBox(self)
        
        # self.fluid.addItem("ammonia")
        # self.fluid.addItem("water")
        # listeDesFluides=Fluid().listeDesFluides()
        
        # for i in listeDesFluides:
        #     self.fluid.addItem(i)        
        
        # self.fluid.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)                   
        
        self.F_kgs_lbl=QLabel("Air humide (m3/h)", self) 
        self.V_flow_edit=QLineEdit("3000", self)
        
        self.T_lbl = QLabel("Température (°C)", self)  
        
        
          
          
        self.T_edit = QLineEdit("15", self)
        
        
        self.RH_lbl = QLabel("RH (%)", self)              
        self.RH_edit = QLineEdit("100", self)
        
        self.P_lbl = QLabel("Pression (bar)", self)                       
        self.P_edit = QLineEdit("1.01325", self)
        
        self.layout=QVBoxLayout()
        
        # self.layout.addWidget(self.fluid_lbl)
        # self.layout.addWidget(self.fluid)        
        self.layout.addWidget(self.F_kgs_lbl)
        self.layout.addWidget(self.V_flow_edit)        
        self.layout.addWidget(self.T_lbl)
        self.layout.addWidget(self.T_edit)
        
        self.layout.addWidget(self.RH_lbl)
        self.layout.addWidget(self.RH_edit)
        
        self.layout.addWidget(self.P_lbl)
        self.layout.addWidget(self.P_edit)
        
        
        
        
        self.setLayout(self.layout)
        
        self.layout.setAlignment(Qt.AlignRight)
        self.layout.setObjectName(self.node.content_label_objname)
        

    def serialize(self):
        res = super().serialize()
        res['value'] = self.T_edit.text()
        res2 = super().serialize()
        res2['P'] = self.P_edit.text()
        
        res3 = super().serialize()
        res3['RH'] = self.RH_edit.text()
        
        res4 = super().serialize()
        res4['V_flow'] = self.V_flow_edit.text()
        
        return res,res2,res3,res4

    def deserialize(self, data, hashmap={}):
        res = super().deserialize(data, hashmap)
        res2 = super().deserialize(data, hashmap)
        res3 = super().deserialize(data, hashmap)
        res4 = super().deserialize(data, hashmap)
       # print("res=",res,res2,res3,res4)
       # print("dataaaaaaaaaa=",data)
        try:
            
            T = data[0]["T"]
            P = data[1]['P']
            RH = data[2]['RH']
            V_flow = data[3]['V_flow']
            
          #  print("values=",value,P,RH,V_flow)
            
            self.T_edit.setText(T)
            self.P_edit.setText(P)
            self.RH_edit.setText(RH)
            self.V_flow_edit.setText(V_flow)
            
            return True & res & res2 & res3 & res4
        except Exception as e:
            dumpException(e)
        return res,res2,res3,res4


@register_node(OP_NODE_AIR_INPUT)
class CalcNode_AirInput(CalcNode):
    icon = "icons/in.png"
    op_code = OP_NODE_AIR_INPUT
    op_title = "Air Humide"
    content_label_objname = "calc_node_air_input"
    

    def __init__(self, scene):
        super().__init__(scene, inputs=[], outputs=[3])
        self.eval()

    def initInnerClasses(self):
        self.content = CalcAirInputContent(self)
        self.grNode = CalcGraphicsNode(self)
        self.grNode.height=300
        self.grNode.width=200
        self.content.T_edit.textChanged.connect(self.onInputChanged)
        self.content.P_edit.textChanged.connect(self.onInputChanged)
        self.content.V_flow_edit.textChanged.connect(self.onInputChanged)
        self.content.RH_edit.textChanged.connect(self.onInputChanged)

    def evalImplementation(self):
        
        s_T = float(self.content.T_edit.text())
        s_P = float(self.content.P_edit.text())  
        s_RH = float(self.content.RH_edit.text())
        s_F_kgs = float(self.content.V_flow_edit.text()) * air_humide.Air_rho_hum(s_T, s_RH, s_P*10**5)/3600 #kg/s
      #  print("masse vol=",air_humide.Air_rho_hum(s_T, s_RH, s_P*10**5))
        
         
        
        self.AN=FreshAir.Object()
        
        #lecture des données
        self.AN.F_m3h=s_F_kgs
        self.AN.T=s_T
      #  print("self.AN.T",self.AN.T)
        self.AN.RH=s_RH
        print("self.AN.RH",self.AN.RH)

        #Calculer les propriétés d'air neuf
        self.AN.calculate()
        
      #  print(self.AN.Inlet.propriete())
      #  print(self.AN.Outlet.propriete())
        
        
       
        
        
        
        self.value = [self.AN.w,s_F_kgs,s_P,self.AN.h]
     #   print("air humide",self.value)
        
        self.markDirty(False)
        self.markInvalid(False)

        self.markDescendantsInvalid(False)
        self.markDescendantsDirty()

        self.grNode.setToolTip("")

        self.evalChildren()
      #  print("données entrée = ",self.value)
        return self.value
   

       
            


        
    def propriete(self,Pro,I1,ValI1,I2,ValI2):
        result=PropsSI(Pro, I1, ValI1, I2, ValI2, self.fluid)
        return result