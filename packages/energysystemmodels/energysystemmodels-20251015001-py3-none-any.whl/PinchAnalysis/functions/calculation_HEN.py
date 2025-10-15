import pandas as pd
from gekko import GEKKO




def calculate_stream_numbers(self):
    # Expressions for N_HS and N_CS
    self.N_HS = len(self.stream_list[self.stream_list['StreamType'] == 'HS'])
    self.N_CS = len(self.stream_list[self.stream_list['StreamType'] == 'CS'])
    # Determine the number of stages
    self.N_stage = max(self.N_CS, self.N_HS)

def hen_stream_list(self):
    flux_chaud = self.stream_list[self.stream_list['StreamType'] == 'HS']
    flux_froid = self.stream_list[self.stream_list['StreamType'] == 'CS']
    self.TiHS = flux_chaud['Ti'].tolist()
    self.ToHS = flux_chaud['To'].tolist()
    self.TiCS = flux_froid['Ti'].tolist()
    self.ToCS = flux_froid['To'].tolist()
    self.mCpHS=flux_chaud['mCp'].tolist()
    self.mCpCS=flux_froid['mCp'].tolist()
    self.nameHS=flux_chaud['name'].tolist()
    self.nameCS=flux_froid['name'].tolist()


###############################"GHE#############################################"""  
def HeatExchangerNetwork(self,disp=False,dTmin=10.0):
    # Initialiser le modèle Gekko
    m = GEKKO(remote=False)
    # Utiliser les données extraites par HeatExchangerNetwork
    N_HS = self.N_HS
    N_CS = self.N_CS
    N_stage = self.N_stage
    TiHS = self.TiHS
    ToHS = self.ToHS
    TiCS = self.TiCS
    ToCS = self.ToCS
    mCpHS = self.mCpHS
    mCpCS = self.mCpCS
    nameHS=self.nameHS
    nameCS=self.nameCS

    # Autres paramètres
    ToCU, ToHU, TiCU, TiHU = 25, 150, 20, 200
    CCU, CHU =100, 100
    CF=100 #coût lié au nombre d'échangeur)
    U = 1.0
    B = 0.6

    #Variables:
    # Redéfinition des variables q et z comme des listes tridimensionnelles
    q = [[[m.Var(lb=0, name=f'q_{i}_{j}_{k}') for k in range(N_stage+1)] for j in range(N_CS)] for i in range(N_HS)]
    # Définition de z en tant que variable binaire
    z = [[[m.Var(lb=0, ub=1, integer=True, name=f'z_{i}_{j}_{k}') for k in range(N_stage+1)] for j in range(N_CS)] for i in range(N_HS)]
    qcu = [m.Var(lb=0, name=f'qcu_{i}') for i in range(N_HS)]
    qhu = [m.Var(lb=0, name=f'qhu_{j}') for j in range(N_CS)]

    # Températures aux étages pour les flux chauds et froids
    tHS = [[m.Var(TiHS[i], lb=ToHS[i], ub=TiHS[i], name=f'tHS_{i}_{k}') for k in range(N_stage+1)] for i in range(N_HS)]
    tCS = [[m.Var(TiCS[j], lb=TiCS[j], ub=ToCS[j], name=f'tCS_{j}_{k}') for k in range(N_stage+1)] for j in range(N_CS)]

    # Variables dt
    dtcu = [m.Var(value=0.0, lb=0.0) for i in range(N_HS)]
    dthu = [m.Var(value=0.0, lb=0.0) for j in range(N_CS)]
    dt = [[[m.Var(lb=0, name=f'dt_{i}_{j}_{k}') for k in range(N_stage+1)] for j in range(N_CS)] for i in range(N_HS)]

    # Contraintes pour fixer les températures d'entrée
    for i in range(N_HS):
        m.Equation(tHS[i][0] == TiHS[i])
    for j in range(N_CS):
        m.Equation(tCS[j][N_stage] == TiCS[j])

    # Définition de z en fonction de q
    for k in range(N_stage+1):
        for i in range(N_HS):
            for j in range(N_CS):
                m.Equation(z[i][j][k] == 1 - m.if3(q[i][j][k], 1, 0))
                #m.Equation(z[i][j][k]<1)

    for k in range(N_stage+1):
        for i in range(N_HS):
            for j in range(N_CS):
                m.Equation(dt[i][j][k] <= (tHS[i][k] - tCS[j][k])+1000000.0*(1-z[i][j][k]))
                m.Equation(dt[i][j][k] >=dTmin)
        

    for k in range(N_stage):
        for i in range(N_HS):
            for j in range(N_CS):
                m.Equation(dt[i][j][k+1] <= (tHS[i][k+1] - tCS[j][k+1])+1000000.0*(1-z[i][j][k]))
                m.Equation(dt[i][j][k] >=dTmin)

    # Bilan d'énergie à chaque étage
    for i in range(N_HS):
        for k in range(N_stage):
            m.Equation((tHS[i][k] - tHS[i][k+1]) * mCpHS[i] == sum(q[i][j][k] for j in range(N_CS)))
    for j in range(N_CS):
        for k in range(N_stage):
            m.Equation((tCS[j][k] - tCS[j][k+1]) * mCpCS[j] == sum(q[i][j][k] for i in range(N_HS)))
            

    # Bilan d'énergie global pour chaque flux
    for i in range(N_HS):
        m.Equation((TiHS[i] - ToHS[i]) * mCpHS[i] == sum(q[i][j][k] for j in range(N_CS) for k in range(N_stage+1)) + qcu[i])
    for j in range(N_CS):
        m.Equation((ToCS[j] - TiCS[j]) * mCpCS[j] == sum(q[i][j][k] for i in range(N_HS) for k in range(N_stage+1)) + qhu[j])

    # Contraintes pour les utilités froides et chaudes

    for i in range(N_HS):
        m.Equation((tHS[i][N_stage] - ToHS[i]) * mCpHS[i] == qcu[i])
    for j in range(N_CS):
        m.Equation((ToCS[j] - tCS[j][0]) * mCpCS[j] == qhu[j])



    # Fonction objectif pour minimiser la somme de qcu et qhu
    cost = sum(CCU*qcu[i] for i in range(N_HS)) + sum(CHU*qhu[j] for j in range(N_CS))-0.0*sum(CF * z[i][j][k] for i in range(N_HS) for j in range(N_CS) for k in range(1, N_stage+1))

    m.Minimize(cost)

    # Résolution
    m.solve(disp=disp)
    #m.solve(disp=True, solver='ipopt')

    #calcul de mCpHS_ijk
    mCpCS_ijk = [[[0 for k in range(N_stage)] for j in range(N_CS)] for i in range(N_HS)]
    mCpHS_ijk = [[[0 for k in range(N_stage)] for j in range(N_CS)] for i in range(N_HS)]

    for i in range(N_HS):
        for j in range(N_CS):
            for k in range(N_stage):
                if tCS[j][k].value[0]>tCS[j][k+1].value[0]:
                    mCpCS_ijk[i][j][k]=q[i][j][k].value[0]/(tCS[j][k].value[0]-tCS[j][k+1].value[0])
                else:
                    mCpCS_ijk[i][j][k]=0
                
                if tHS[i][k].value[0]>tHS[i][k+1].value[0]:
                    mCpHS_ijk[i][j][k]=q[i][j][k].value[0]/(tHS[i][k].value[0]-tHS[i][k+1].value[0])
                else:
                    mCpHS_ijk[i][j][k]=0

                #print(f'mCpCS_ijk[{i}][{j}][{k}]={mCpCS_ijk[i][j][k]}')
                #print(f'mCpHS_ijk[{i}][{j}][{k}]={mCpHS_ijk[i][j][k]}')

    ############################"""""" Affichage des résultats############################

    # Créer des listes pour stocker les valeurs de q et z ainsi que les indices i, j, k
    q_values = []
    i_values = []
    j_values = []
    k_values = []
    mCpCS_values=[]
    mCpHS_values=[]
    nameCS_values=[]
    nameHS_values=[]
    TiCS_values=[]
    TiHS_values=[]
    ToCS_values=[]
    ToHS_values=[]

    for i in range(N_HS):
        for j in range(N_CS):
            for k in range(N_stage):
                mCpCS_value=mCpCS_ijk[i][j][k]
                mCpHS_value=mCpHS_ijk[i][j][k]
                q_value = round(q[i][j][k].value[0],3)
                q_values.append(q_value)
                i_values.append(i)
                j_values.append(j)
                k_values.append(k)

                mCpCS_values.append(mCpCS_value)
                mCpHS_values.append(mCpHS_value)
                nameCS_values.append(nameCS[j])
                nameHS_values.append(nameHS[i])
                ToCS_values.append(round(tCS[j][k].value[0],1))
                TiHS_values.append(round(tHS[i][k].value[0],1))
                
                TiCS_values.append(round(tCS[j][k+1].value[0],1))
                ToHS_values.append(round(tHS[i][k+1].value[0],1))
    




    # Créer un DataFrame pour q avec les valeurs et les indices i, j, k correspondants
    self.hen_results = pd.DataFrame({'stage k': k_values, 'HS name':nameHS_values, 'CS name':nameCS_values,'q(kW)': q_values,'mCpCS(kW/K)': mCpCS_values,'Ti_CS(°C)':TiCS_values,'To_CS(°C)':ToCS_values,'mCpHS(kW/K)': mCpHS_values,'Ti_HS(°C)':TiHS_values,'To_HS(°C)':ToHS_values})
                # Créer un DataFrame pour les utilités froides (qcu) et chaudes (qhu)
    qcu_values = [round(qcu[i].value[0],3) for i in range(N_HS)]
    qhu_values = [round(qhu[j].value[0],3) for j in range(N_CS)]

    #print("\nBilan d'énergie pour les utilités froides (qcu):", qcu_total)
    #print("Bilan d'énergie pour les utilités chaudes (qhu):", qhu_total)

    self.hen_qcu = pd.DataFrame({'qcu_values': qcu_values,'nameHS':nameHS})
    self.hen_qhu = pd.DataFrame({'qhu_values': qhu_values,'nameCS':nameCS})

    # Calculer les bilans d'énergie
    self.hen_qcu_total = sum(qcu_values)
    self.hen_qhu_total = sum(qhu_values)

    ###########Supprimer les lignes vides ##################
    # Supprimer les lignes où qcu est égal à zéro
    self.hen_results = self.hen_results[self.hen_results['q(kW)'] != 0]

    # Supprimer les lignes où qcu_values est égal à zéro
    self.hen_qcu = self.hen_qcu[self.hen_qcu['qcu_values'] != 0]

    # Supprimer les lignes où qhu_values est égal à zéro
    self.hen_qhu = self.hen_qhu[self.hen_qhu['qhu_values'] != 0]



##################"print#######################"""""
    for i in range(N_HS):
        for j in range(N_CS):
            for k in range(N_stage):
                pass
                # print(f'Chaleur échangée q[{i}][{j}][{k}]: {q[i][j][k].value[0]}')  
                # print(f'z[{i}][{j}][{k}]: {z[i][j][k].value[0]}')     
                # print(f'qCS[i][j][k]: ({tCS[j][k].value[0]}-{tCS[j][k+1].value[0]})*{mCpCS[j]}={q[i][j][k].value[0]}')
                # print(f'qHS[i][j][k]: ({tHS[i][k].value[0]}-{tHS[i][k+1].value[0]})*{mCpHS[i]}={q[i][j][k].value[0]}')

    for i in range(N_HS):
        for j in range(N_CS):
            for k in range(N_stage+1):
                print(f'pinch dt[{i}][{j}][{k}]: {dt[i][j][k].value[0]}')



    for i in range(N_HS):
        #print(f'Températures aux étages pour le flux chaud {i}:')
        for k in range(N_stage+1):
            pass
            #print(f'tHS_{i}_{k}: {tHS[i][k].value[0]}')

    for j in range(N_CS):
        #print(f'Températures aux étages pour le flux froid {j}:')
        for k in range(N_stage+1):
            pass
            #print(f'tCS_{j}_{k}: {tCS[j][k].value[0]}')
