from PyPFD import PyPFDClass


#                             name,                                 lambda_du,   lambda_dd,   lambda_su,  lambda_sd,    type,   SC,      beta,       beta_d,   HFT,     MTTR)
def sensor_analog_transmitter_generic():
    return PyPFDClass.device("Generic Analog Transmitter",               2e-7,      1.8e-6,        2e-7,     1.8e-6,     "B",    3,      0.04,        0.020,     0,      160)

def sensor_mechanical_switch():
    return PyPFDClass.device("Generic Mechanical Switch",                4e-6,           0,        4e-6,      4e-13,     "A",    2,      0.05,        0.025,     0,      100)

def ls_sil3_certified_plc_generic():
    return PyPFDClass.device("Generic SIL3 Certified PLC",            6.77e-9,           0,     1.85e-7,          0,     "B",    3,      0.05,        0.025,     1,      100)

def fe_valve_onoff_generic():
    return PyPFDClass.device("Generic ON-OFF Failsafe Valve",         3.37e-6,           0,     1.38e-6,          0,     "A",    3,      0.05,        0.025,     0,      100)

def st_IEC61508_Tableb9():
    return PyPFDClass.device("IEC61508-6 Table B9",                    0.5e-5,           0,           0,          0,     "A",    3,      0.10,        0.050,     0,       8)

def sensor_analog_transmitter_proof_test_year_AGAN():
    return PyPFDClass.proof_test("As Good As New Test", 24)



# name_pt:str, T_pt_month:float, PDC_pt:float, T1_month:float):

class proof_test:
    def __init__(self, name1:str, T1_month:float):
        self.name1 = name1
        self.T1_month = T1_month

def st_test():
    return PyPFDClass.proof_test("Std Test", 12)



def sensor_analog_transmitter_proof_test_1pt_handheld():
    return PyPFDClass.proof_test_1pt("HandHeld Simulate Test", 12, 0.54,24)

def st_IEC61508_Tableb0_1pt():
    return PyPFDClass.proof_test_1pt("IEC61508 Table B9 Examplo", 12, 0.90,120)

#name_pt1:str, T_pt1_month:float, PDC_pt1:float, name_pt2:str, T_pt2_month:float, PDC_pt2:float,T1_month:float):

def st_2pt():
    return PyPFDClass.proof_test_2pt("Partial Test1",6,0.3,"Partial test2",12,0.5,24)
