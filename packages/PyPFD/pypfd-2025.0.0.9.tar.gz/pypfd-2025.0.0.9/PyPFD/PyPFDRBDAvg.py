
def factorial(n:int) -> float:
    resultado = 1
    for i in range(2, n + 1):
        resultado *= i
    return resultado

#IEC61508
def Tce( λ_du: float,λ_dd: float,T1_month: float,MTTR: float) -> float:
    λ_d =  λ_du + λ_dd
    T1_hour = T1_month*730
    val = (λ_du/λ_d)*((T1_hour/2)+MTTR)+(λ_dd/λ_d)*MTTR
    return val

def Tce_1pt(λ_du: float,λ_dd: float,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:

    λ_d =  λ_du + λ_dd
    T1_hour = T1_month*730
    T_pt_hour = T_pt1_month*730
    val = (λ_du*(1-PDC)/λ_d)*((T1_hour/2)+MTTR)+(λ_du*(PDC)/λ_d)*((T_pt_hour/2)+MTTR)+(λ_dd/λ_d)*MTTR
    return val

#IEC61508
def Tge(λ_du: float,λ_dd: float,T1_month: float,MTTR: float) -> float:
    λ_d =  λ_du + λ_dd
    T1_hour = T1_month*730
    val = (λ_du/λ_d)*((T1_hour/3)+MTTR)+λ_dd/λ_d*MTTR
    return val

def Tge_1pt(λ_du: float,λ_dd: float,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:
    
    λ_d =  λ_du + λ_dd
    T1_hour = T1_month*730
    T_pt_hour = T_pt1_month*730
    val = (λ_du*(1-PDC)/λ_d)*((T1_hour/3)+MTTR)+(λ_du*(PDC)/λ_d)*((T_pt_hour/3)+MTTR)+(λ_dd/λ_d)*MTTR
    return val

#IEC61508
def Tg2e(λ_du: float,λ_dd: float,T1_month: float,MTTR: float) -> float:
    λ_d =  λ_du + λ_dd
    T1_hour = T1_month*730
    val = (λ_du/λ_d)*((T1_hour/4)+MTTR)+λ_dd/λ_d*MTTR
    return val

def Tg2e_1pt(λ_du: float,λ_dd: float,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:
    λ_d =  λ_du + λ_dd
    T1_hour = T1_month*730
    T_pt_hour = T_pt1_month*730
    val = (λ_du*(1-PDC)/λ_d)*((T1_hour/4)+MTTR)+(λ_du*(PDC)/λ_d)*((T_pt_hour/4)+MTTR)+(λ_dd/λ_d)*MTTR
    return val

def Tne(λ_du: float,λ_dd: float,n: int,T1_month: float,MTTR: float) -> float:
    λ_d =  λ_du + λ_dd
    T1_hour = T1_month*730
    val = 1 
    for i in range(1,n+1):
       val *= (λ_du/λ_d)*((T1_hour/(i+1))+MTTR)+λ_dd/λ_d*MTTR
    return val

def Tne_1pt(λ_du: float,λ_dd: float,n: int,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:
    λ_d =  λ_du + λ_dd
    T1_hour = T1_month*730
    T_pt_hour = T_pt1_month*730
    val = 1 
    for i in range(1,n+1):
       val *= (λ_du*(1-PDC)/λ_d)*((T1_hour/(i+1))+MTTR)+(λ_du*(PDC)/λ_d)*((T_pt_hour/(i+1))+MTTR)+(λ_dd/λ_d)*MTTR
    return val

def pfd_RBD_avg_1oo1(λ_du: float,λ_dd: float,T1_month: float,MTTR: float) -> float:
    val = (λ_du+λ_dd)*Tne(λ_du,λ_dd,1,T1_month,MTTR)
    return  val

def pfd_RBD_avg_1oo1_pt(λ_du: float,λ_dd: float,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:
    val = (λ_du+λ_dd)*Tce_1pt(λ_du,λ_dd,T1_month,T_pt1_month,PDC,MTTR)
    return  val

def pfd_RBD_avg_1oo2(λ_du: float,λ_dd: float,β: float,βd: float,T1_month: float,MTTR: float) -> float:
    T1_hour = T1_month*730
    val = 2 * (((1-βd)*λ_dd + (1- β)*λ_du)**2)*Tne(λ_du,λ_dd,2,T1_month,MTTR) + βd*λ_dd*MTTR + β*λ_du*(T1_hour/2+MTTR)
    return   val

def pfd_RBD_avg_1oo2_pt(λ_du: float,λ_dd: float,β: float,βd: float,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:
    T1_hour = T1_month*730
    T_pt_hour = T_pt1_month*730
    
    val = 2 * (((1-βd)*λ_dd + (1- β)*λ_du)**2)*Tce_1pt(λ_du,λ_dd,T1_month,T_pt1_month,PDC,MTTR)*Tge_1pt(λ_du,λ_dd,T1_month,T_pt1_month,PDC,MTTR) + \
          βd*λ_dd*MTTR + β*λ_du*(1-PDC)*(T1_hour/2+MTTR)+β*λ_du*(PDC)*(T_pt_hour/2+MTTR)
    
    return   val

def pfd_RBD_avg_1oo3(λ_du: float,λ_dd: float,β: float,βd: float,T1_month: float,MTTR: float) -> float:
    T1_hour = T1_month*730
    val = 6 * (((1-βd)*λ_dd + (1- β)*λ_du)**3)*Tne(λ_du,λ_dd,3,T1_month,MTTR) + βd*λ_dd*MTTR + β*λ_du*(T1_hour/2+MTTR)
    return   val

def pfd_RBD_avg_2oo2(λ_du: float,λ_dd: float,T1_month: float,MTTR: float) -> float:
    return  pfd_RBD_avg_1oo1(λ_du,λ_dd,T1_month,MTTR)*2

def pfd_RBD_avg_3oo3(λ_du: float,λ_dd: float,T1_month: float,MTTR: float) -> float:
    return  pfd_RBD_avg_1oo1(λ_du,λ_dd,T1_month,MTTR)*3

def pfd_RBD_avg_2oo2_pt(λ_du: float,λ_dd: float,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:
    return  pfd_RBD_avg_1oo1_pt(λ_du,λ_dd,T1_month,T_pt1_month,PDC,MTTR)*2

def pfd_RBD_avg_3oo3_pt(λ_du: float,λ_dd: float,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:
    return  pfd_RBD_avg_1oo1_pt(λ_du,λ_dd,T1_month,T_pt1_month,PDC,MTTR)*3

def pfd_RBD_avg_2oo3(λ_du: float,λ_dd: float,β: float,βd: float,T1_month: float,MTTR: float) -> float:
    T1_hour = T1_month*730
    val = 6 * (((1-βd)*λ_dd + (1- β)*λ_du)**2)*Tne(λ_du,λ_dd,2,T1_month,MTTR) + βd*λ_dd*MTTR + β*λ_du*(T1_hour/2+MTTR)
    return   val

def pfd_RBD_avg_KooN(K: int,N: int,λ_du: float,λ_dd: float,β: float,βd: float,T1_month: float,MTTR: float) -> float:

    T1_hour = T1_month*730
    
    if K == N:
       val = (λ_du+λ_dd)*Tne(λ_du,λ_dd,1,T1_month,MTTR) * K
    else:
       fator = N - K +1
       val = factorial(N) * (((1-βd)*λ_dd + (1- β)*λ_du)**(fator))*Tne(λ_du,λ_dd,fator,T1_month,MTTR) + βd*λ_dd*MTTR + β*λ_du*(T1_hour/2+MTTR)
    return   val

def pfd_RBD_avg_KooN_1pt(K: int,N: int,λ_du: float,λ_dd: float,β: float,βd: float,T1_month: float,T_pt1_month: float,PDC: float,MTTR: float) -> float:

    T1_hour = T1_month*730
    T_pt_hour = T_pt1_month *730
    if K == N:
       val = (λ_du+λ_dd)*Tne_1pt(λ_du,λ_dd,1,T1_month,T_pt1_month,PDC,MTTR) * K
    else:
       fator = N - K +1
       val = factorial(N) * (((1-βd)*λ_dd + (1- β)*λ_du)**(fator))*Tne_1pt(λ_du,λ_dd,fator,T1_month,T_pt1_month,PDC,MTTR) + βd*λ_dd*MTTR + β*λ_du*(1.0-PDC)*(T1_hour/2+MTTR) + β*λ_du*(PDC)*(T_pt_hour/2+MTTR)
    return   val


#in development
def pfh_RBD_KooN(K:int,N:int,λ_d: float,β: float,T1_month: float) -> float:
    T1_hour = T1_month*730
    val = factorial(N)/(factorial(N-K)*factorial(K-1)) * (1-β) * λ_d * ((1-β)*λ_d*T1_hour/2)**(N-K) + (β*λ_d)
    
    return   val

#in development
def pfd_RBD_avg_1oo2_dif(λ_du1: float,λ_dd1: float,T1_month1: float,MTTR1: float,β1: float,βd1: float,λ_du2: float,λ_dd2: float,T1_month2: float,MTTR2: float,β2: float,βd2: float) -> float:

    λ_d1 = λ_du1 + λ_dd1
    T1_hour1 = T1_month1*730
    λ_d2 = λ_du2 + λ_dd2
    T1_hour2 = T1_month2*730

    Tce1 = (λ_du1/λ_d1)*((T1_hour1/2)+MTTR1)+(λ_dd1/λ_d1)*MTTR1
    Tce2 = (λ_du2/λ_d2)*((T1_hour2/2)+MTTR2)+(λ_dd2/λ_d2)*MTTR2   

    Tge1 = (λ_du1/λ_d1)*((T1_hour1/3)+MTTR1)+(λ_dd1/λ_d1)*MTTR1
    Tge2 = (λ_du2/λ_d2)*((T1_hour2/3)+MTTR2)+(λ_dd2/λ_d2)*MTTR2   
    
    val = (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2))*Tce1*Tge2 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2))*Tce2*Tge1 + \
          (βd1+βd2)/2*(λ_dd1+λ_dd2)/2*(MTTR1+MTTR2)/2 + \
          (β1+β2)/2*(λ_du1+λ_du2)/2*((T1_hour1+T1_hour2)/2/2+(MTTR1+MTTR2)/2)

    return   val


def pfd_RBD_avg_2oo3_dif(λ_du1: float,λ_dd1: float,T1_month1: float,MTTR1: float,β1: float,βd1: float,λ_du2: float,λ_dd2: float,T1_month2: float,MTTR2: float,β2: float,βd2: float,λ_du3: float,λ_dd3: float,T1_month3: float,MTTR3: float,β3: float,βd3: float) -> float:

    λ_d1 = λ_du1 + λ_dd1
    T1_hour1 = T1_month1*730

    λ_d2 = λ_du2 + λ_dd2
    T1_hour2 = T1_month2*730

    λ_d3 = λ_du3 + λ_dd3
    T1_hour3 = T1_month3*730


    Tce1 = (λ_du1/λ_d1)*((T1_hour1/2)+MTTR1)+(λ_dd1/λ_d1)*MTTR1
    Tce2 = (λ_du2/λ_d2)*((T1_hour2/2)+MTTR2)+(λ_dd2/λ_d2)*MTTR2
    Tce3 = (λ_du3/λ_d3)*((T1_hour3/2)+MTTR3)+(λ_dd3/λ_d3)*MTTR3 
   
    Tge1 = (λ_du1/λ_d1)*((T1_hour1/3)+MTTR1)+(λ_dd1/λ_d1)*MTTR1
    Tge2 = (λ_du2/λ_d2)*((T1_hour2/3)+MTTR2)+(λ_dd2/λ_d2)*MTTR2   
    Tge3 = (λ_du3/λ_d3)*((T1_hour3/3)+MTTR3)+(λ_dd3/λ_d3)*MTTR3

    val = (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2))*Tce1*Tge2 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd3)*λ_dd3 + (1- β3)*λ_du3))*Tce1*Tge3 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2))*Tce2*Tge1 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd3)*λ_dd3 + (1- β3)*λ_du3))*Tce3*Tge1 + \
          (((1-βd3)*λ_dd3 + (1- β3)*λ_du3)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2))*Tce2*Tge3 + \
          (((1-βd3)*λ_dd3 + (1- β3)*λ_du3)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2))*Tce3*Tge2 + \
          (βd1+βd2+βd3)/3*(λ_dd1+λ_dd2+λ_dd3)/3*(MTTR1+MTTR2+MTTR3)/3 + \
          (β1+β2+β3)/3*(λ_du1+λ_du2+λ_du3)/3*((T1_hour1+T1_hour2+T1_hour3)/3/2+(MTTR1+MTTR2+MTTR3)/3)
      
    return   val 
      
      
def pfd_RBD_avg_1oo3_dif(λ_du1: float,λ_dd1: float,T1_month1: float,MTTR1: float,β1: float,βd1: float,λ_du2: float,λ_dd2: float,T1_month2: float,MTTR2: float,β2: float,βd2: float,λ_du3: float,λ_dd3: float,T1_month3: float,MTTR3: float,β3: float,βd3: float) -> float:

    λ_d1 = λ_du1 + λ_dd1
    T1_hour1 = T1_month1*730

    λ_d2 = λ_du2 + λ_dd2
    T1_hour2 = T1_month2*730

    λ_d3 = λ_du3 + λ_dd3
    T1_hour3 = T1_month3*730


    Tce1 = (λ_du1/λ_d1)*((T1_hour1/2)+MTTR1)+(λ_dd1/λ_d1)*MTTR1
    Tce2 = (λ_du2/λ_d2)*((T1_hour2/2)+MTTR2)+(λ_dd2/λ_d2)*MTTR2
    Tce3 = (λ_du3/λ_d3)*((T1_hour3/2)+MTTR3)+(λ_dd3/λ_d3)*MTTR3 
   
    Tge1 = (λ_du1/λ_d1)*((T1_hour1/3)+MTTR1)+(λ_dd1/λ_d1)*MTTR1
    Tge2 = (λ_du2/λ_d2)*((T1_hour2/3)+MTTR2)+(λ_dd2/λ_d2)*MTTR2   
    Tge3 = (λ_du3/λ_d3)*((T1_hour3/3)+MTTR3)+(λ_dd3/λ_d3)*MTTR3

    Tg2e1 = (λ_du1/λ_d1)*((T1_hour1/4)+MTTR1)+(λ_dd1/λ_d1)*MTTR1
    Tg2e2 = (λ_du2/λ_d2)*((T1_hour2/4)+MTTR2)+(λ_dd2/λ_d2)*MTTR2   
    Tg2e3 = (λ_du3/λ_d3)*((T1_hour3/4)+MTTR3)+(λ_dd3/λ_d3)*MTTR3
    
    val = (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2)*((1-βd3)*λ_dd3 + (1- β3)*λ_du3))*Tce1*Tge2*Tg2e3 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2)*((1-βd3)*λ_dd3 + (1- β3)*λ_du3))*Tce1*Tge3*Tg2e2 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2)*((1-βd3)*λ_dd3 + (1- β3)*λ_du3))*Tce2*Tge1*Tg2e3 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2)*((1-βd3)*λ_dd3 + (1- β3)*λ_du3))*Tce2*Tge3*Tg2e1 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2)*((1-βd3)*λ_dd3 + (1- β3)*λ_du3))*Tce3*Tge1*Tg2e2 + \
          (((1-βd1)*λ_dd1 + (1- β1)*λ_du1)*((1-βd2)*λ_dd2 + (1- β2)*λ_du2)*((1-βd3)*λ_dd3 + (1- β3)*λ_du3))*Tce3*Tge2*Tg2e1 + \
          ((βd1*λ_dd1*MTTR1)+(βd2*λ_dd2*MTTR2)+(βd3*λ_dd3*MTTR3))/3 + \
          (β1*λ_du1*(T1_hour1/2+MTTR1)+β2*λ_du2*(T1_hour2/2+MTTR2)+β3*λ_du3*(T1_hour3/2+MTTR3))/3  
      
    return val
      
      


