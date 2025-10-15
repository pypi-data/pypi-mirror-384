#def identityMatrix(n: int):
#    """Cria uma matriz identidade de dimensão n×n."""
#    matriz = [[0 for _ in range(n)] for _ in range(n)]
#    for i in range(n):
#        matriz[i][i] = 1
#    return matriz


def markovMatrixDict_1oo1_2pt(λ_du:float, PDC1:float,PDC2:float,MTTR:float=0,λ_dd:float=0,λ_s:float=0):

#0->OK
#1->FS
#2->FDD
#3->FDU1 - Dicovered by Partial Test 1
#4->FDU2 - Dicovered by Partial Test 2
#5->FDU3 - Dicovered by AGAN Test

    λ_du1 = λ_du*PDC1
    λ_du2 = λ_du*PDC2
    λ_du3 = λ_du*(1-PDC1-PDC2)
    mRT = 1/MTTR

    tmatrix = [[-1,λ_s,λ_dd,λ_du1,λ_du2,λ_du3],
              [mRT,-1,0,0,0,0],
              [mRT,0,-1,0,0,0],
              [0,0,0,-1,0,0],
              [0,0,0,0,-1,0],
              [0,0,0,0,0,-1]]

    for i in range(0, 5+1):
        tmatrix[i][i] = 1
        for j in range(0,5+1):
            if i != j:
                tmatrix[i][i] -= tmatrix[i][j] 

    testM=  [[1,0,0,0,0,0],
          [0,1,0,0,0,0],
          [0,0,1,0,0,0],
          [1,0,0,0,0,0],
          [1,0,0,0,0,0],
          [1,0,0,0,0,0]]

    testM_pt1= [[1,0,0,0,0,0],
             [0,1,0,0,0,0],
             [0,0,1,0,0,0],
             [1,0,0,0,0,0],
             [0,0,0,0,1,0],
             [0,0,0,0,0,1]]
    
    testM_pt2= [[1,0,0,0,0,0],
             [0,1,0,0,0,0],
             [0,0,1,0,0,0],
             [1,0,0,0,0,0],
             [1,0,0,0,0,0],
             [0,0,0,0,0,1]]

    stateVector = [[1,0,0,0,0,0]]

    safeVector= [[1,1,0,0,0,0]]

    return {"transitionM": tmatrix, "testM": testM, "testM_pt1": testM_pt1, "testM_pt2": testM_pt2, "stateVector":stateVector,"safeVector":safeVector}


def markovMatrixDict_1oo2(λ_du:float,λ_dd:float,λ_su:float,λ_sd:float, β:float, βd:float,  MTTR:float):

    mRT = 1/MTTR

    λ_dun= λ_du*(1-β)
    λ_duc= λ_du*(β)
    λ_ddn= λ_dd*(1-βd)
    λ_ddc= λ_dd*(βd)
    λ_sun= λ_su*(1-β)
    λ_suc= λ_su*(β)
    λ_sdn= λ_sd*(1-βd)
    λ_sdc= λ_sd*(βd)
    λ_s = λ_sd+λ_su



    
    tmatrix = [[-1,    2*λ_ddn,   2*λ_dun,   λ_sdc+λ_suc+2*λ_sdn+2*λ_sun,   λ_ddc,   λ_duc],
              [mRT,         -1,         0,                           λ_s,    λ_dd,       0],
              [  0,          0,        -1,                           λ_s,    λ_dd,    λ_du],
              [mRT,          0,         0,                            -1,       0,       0],
              [mRT,          0,         0,                             0,      -1,       0],
              [0,            0,         0,                             0,       0,      -1]]

    for i in range(0, 5+1):
        tmatrix[i][i] = 1
        for j in range(0,5+1):
            if i != j:
                tmatrix[i][i] -= tmatrix[i][j] 

    testM=  [[1,0,0,0,0,0],
          [0,1,0,0,0,0],
          [0,0,1,0,0,0],
          [1,0,0,0,0,0],
          [1,0,0,0,0,0],
          [1,0,0,0,0,0]]

    stateVector = [[1,0,0,0,0,0]]

    safeVector= [[1,1,1,1,0,0]]

    return {"transitionM": tmatrix, "testM": testM, "stateVector":stateVector,"safeVector":safeVector}



