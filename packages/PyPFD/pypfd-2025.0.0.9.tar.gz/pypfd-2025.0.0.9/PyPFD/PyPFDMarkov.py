from PyPFD import PyPFDMarkovTransition

def matrix_mul(A,B):
    resultado = [[0 for _ in range(len(B[0]))] for _ in range(len(A))]

# Multiplicação
    for i in range(len(A)):
        for j in range(len(B[0])):
            for k in range(len(B)):
                resultado[i][j] += A[i][k] * B[k][j]


    return resultado




def markov_cal_1test(stateM,transitionM,safeM,testsM,testV,maxT):
    
    rM = stateM
    pfd = 0
    
    for i in range(1,maxT):
       rM = matrix_mul(rM,transitionM)

       if i % testV[0] == 0:
           rM = matrix_mul(rM,testsM[0])
  
       for j in range(len(rM[0])):
           if safeM[0][j] == 0:
              pfd+=rM[0][j]

    pfd = pfd/maxT

    return {"stateVector": rM, "pfdavg":pfd}

def markov_cal_2test(stateM,transitionM,safeM,testsM,testV,maxT):
    
    rM = stateM
    pfd = 0
    
    for i in range(1,maxT):
       rM = matrix_mul(rM,transitionM)

       if i % testV[0] == 0:
           rM = matrix_mul(rM,testsM[0])

       if i % testV[1] == 0:
           rM = matrix_mul(rM,testsM[1])
  
       for j in range(len(rM[0])):
           if safeM[0][j] == 0:
              pfd+=rM[0][j]

    pfd = pfd/maxT

    #{"transitionM": tmatrix, "testM": testM, "testM_pt1": testM_pt1, "testM_pt2": testM_pt2, "stateVector":stateVector,"safeVector":safeVector}
    return {"stateVector": rM, "pfdavg":pfd}

def markov_cal_3test(stateM,transitionM,safeM,testsM,testV,maxT):
    
    rM = stateM
    pfd = 0
    
    for i in range(1,maxT):
       rM = matrix_mul(rM,transitionM)

       if i % testV[0] == 0:
           rM = matrix_mul(rM,testsM[0])

       if i % testV[1] == 0:
           rM = matrix_mul(rM,testsM[1])

       if i % testV[2] == 0:
           rM = matrix_mul(rM,testsM[2])    

       for j in range(len(rM[0])):
           if safeM[0][j] == 0:
              pfd+=rM[0][j]

    pfd = pfd/maxT

    #{"transitionM": tmatrix, "testM": testM, "testM_pt1": testM_pt1, "testM_pt2": testM_pt2, "stateVector":stateVector,"safeVector":safeVector}
    return {"stateVector": rM, "pfdavg":pfd}


def markov_cal_1test_plot(stateM,transitionM,safeM,testsM,testV,maxT,interval):
    
    rM = stateM
    pfd = 0

    returnV = stateM

    for i in range(1,maxT):
       rM = matrix_mul(rM,transitionM)

       if i % testV[0] == 0:
           rM = matrix_mul(rM,testsM[0]) 

       for j in range(len(rM[0])):
           if safeM[0][j] == 0:
              pfd+=rM[0][j]

       if i % interval == 0:
           returnV = returnV + rM 

    return returnV

def markov_cal_2test_plot(stateM,transitionM,safeM,testsM,testV,maxT,interval):
    
    rM = stateM
    pfd = 0

    returnV = stateM

    for i in range(1,maxT):
       rM = matrix_mul(rM,transitionM)

       if i % testV[0] == 0:
           rM = matrix_mul(rM,testsM[0])

       if i % testV[1] == 0:
           rM = matrix_mul(rM,testsM[1])  

       for j in range(len(rM[0])):
           if safeM[0][j] == 0:
              pfd+=rM[0][j]

       if i % interval == 0:
           returnV = returnV + rM 

    return returnV

def markov_cal_3test_plot(stateM,transitionM,safeM,testsM,testV,maxT,interval):
    
    rM = stateM
    pfd = 0

    returnV = stateM

    for i in range(1,maxT):
       rM = matrix_mul(rM,transitionM)

       if i % testV[0] == 0:
           rM = matrix_mul(rM,testsM[0])

       if i % testV[1] == 0:
           rM = matrix_mul(rM,testsM[1])

       if i % testV[2] == 0:
           rM = matrix_mul(rM,testsM[2])    

       for j in range(len(rM[0])):
           if safeM[0][j] == 0:
              pfd+=rM[0][j]

       if i % interval == 0:
           returnV = returnV + rM 

    return returnV


def pfd_Mkv_avg_1oo1_2pt(λ_du: float,λ_dd: float,λ_s: float,T_pt1_month: float,T_pt2_month: float,T1_month: float,PDC1: float,PDC2: float,MTTR: float):

    T1_hour = T1_month*730
    T_pt1_hour = T_pt1_month*730
    T_pt2_hour = T_pt2_month*730

    markovDictonary = PyPFDMarkovTransition.markovMatrixDict_1oo1_2pt(λ_du, PDC1,PDC2,MTTR,λ_dd,λ_s)
    markovResult = markov_cal_2test(markovDictonary["stateVector"],markovDictonary["transitionM"],markovDictonary["safeVector"],[markovDictonary["testM_pt1"],markovDictonary["testM_pt2"]],[T_pt1_hour,T_pt2_hour],T1_hour)
    return markovResult["pfdavg"]

def pfd_plot_Mkv_avg_1oo1_2pt(λ_du: float,λ_dd: float,λ_s: float,T_pt1_month: float,T_pt2_month: float,T1_month: float,PDC1: float,PDC2: float,MTTR: float,interval:int):

    T1_hour = T1_month*730
    T_pt1_hour = T_pt1_month*730
    T_pt2_hour = T_pt2_month*730

    markovDictonary = PyPFDMarkovTransition.markovMatrixDict_1oo1_2pt(λ_du, PDC1,PDC2,MTTR,λ_dd,λ_s)
    markovResult = markov_cal_2test_plot(markovDictonary["stateVector"],markovDictonary["transitionM"],markovDictonary["safeVector"],[markovDictonary["testM_pt1"],markovDictonary["testM_pt2"]],[T_pt1_hour,T_pt2_hour],T1_hour,interval)
    return markovResult

def pfd_Mkv_avg_1oo2(λ_du: float,λ_dd: float,λ_su: float,λ_sd: float,β:float, βd:float,T1_month: float,MTTR:float):
    T1_hour = T1_month*730
    markovDictonary = PyPFDMarkovTransition.markovMatrixDict_1oo2(λ_du,λ_dd,λ_su,λ_sd, β, βd,  MTTR)
    markovResult = markov_cal_1test(markovDictonary["stateVector"],markovDictonary["transitionM"],markovDictonary["safeVector"],[markovDictonary["testM"]],[T1_hour],T1_hour)
    return markovResult["pfdavg"]

def pfd_plot_Mkv_avg_1oo2(λ_du: float,λ_dd: float,λ_su: float,λ_sd: float,β:float, βd:float,T1_month: float,MTTR:float,interval:int):
    T1_hour = T1_month*730
    markovDictonary = PyPFDMarkovTransition.markovMatrixDict_1oo2(λ_du,λ_dd,λ_su,λ_sd, β, βd,  MTTR)
    markovResult = markov_cal_1test_plot(markovDictonary["stateVector"],markovDictonary["transitionM"],markovDictonary["safeVector"],[markovDictonary["testM"]],[T1_hour],T1_hour,interval)
    return markovResult