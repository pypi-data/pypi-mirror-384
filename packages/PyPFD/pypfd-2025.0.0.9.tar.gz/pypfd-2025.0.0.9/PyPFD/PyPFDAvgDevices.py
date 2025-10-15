from PyPFD import PyPFDRBDAvg
from PyPFD import PyPFDMarkov




def pfd_RBD_avg_KooN_Device(device,proof_test,K,N):
    #(K,N,λ_du,λ_dd,β,βd,T1_month,MTTR)
    return PyPFDRBDAvg.pfd_RBD_avg_KooN(K,N,device.lambda_du,device.lambda_dd, device.beta, device.beta_d,proof_test.T1_month,device.MTTR)

def pfd_RBD_avg_KooN_Device_1pt(device,proof_test_1pt,K,N):
# pfd_avg_KooN_1pt(K,N,λ_du,λ_dd,β,βd,T1_month,T_pt_month,PDC,MTTR)
    return PyPFDRBDAvg.pfd_RBD_avg_KooN_1pt(K,N,device.lambda_du,device.lambda_dd, device.beta, device.beta_d,proof_test_1pt.T1_month,proof_test_1pt.T_pt,proof_test_1pt.DC_pt,device.MTTR)

def pfd_Mkv_avg_1oo1_Device_2pt(device,proof_test_2pt):
#(λ_du: float,λ_dd: float,λ_s: float,T_pt1_month: float,T_pt2_month: float,T1_month: float,PDC1: float,PDC2: float,MTTR: float)
    return PyPFDMarkov.pfd_Mkv_avg_1oo1_2pt(device.lambda_du,device.lambda_dd,device.lambda_s,proof_test_2pt.T_pt1_month,proof_test_2pt.T_pt2_month,proof_test_2pt.T1_month,proof_test_2pt.PDC_pt1,proof_test_2pt.PDC_pt2,device.MTTR)

def pfd_Mkv_avg_1oo1_Device_1pt(device,proof_test_1pt):
#(λ_du: float,λ_dd: float,λ_s: float,T_pt1_month: float,T_pt2_month: float,T1_month: float,PDC1: float,PDC2: float,MTTR: float)
    return PyPFDMarkov.pfd_Mkv_avg_1oo1_2pt(device.lambda_du,device.lambda_dd,device.lambda_s,proof_test_1pt.T_pt_month,proof_test_1pt.T1_month,proof_test_1pt.T1_month,proof_test_1pt.PDC_pt,0,device.MTTR)
