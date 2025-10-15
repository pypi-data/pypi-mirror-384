class device:
    def __init__(self, name: str, lambda_du:float, lambda_dd:float=0, lambda_su:float=0,lambda_sd:float=0,type:str="B", SC:int=1, beta:float=0.05, beta_d:float=0.025, HFT:int=0,MTTR:float=100):
        self._name = name
        if lambda_du > 0.1:
            raise ValueError("λdu/h must be <= 0.1")
        if lambda_dd > 0.1:
            raise ValueError("λdu/h must be <= 0.1")
        if lambda_su > 0.1:
            raise ValueError("λdu/h must be <= 0.1")
        if lambda_sd > 0.1:
            raise ValueError("λdu/h must be <= 0.1")
        if type != "A" and type != "B":
            raise ValueError("Tyepe must be A or B")
        if SC != 1 and SC != 2 and SC != 3 and SC != 4:
            raise ValueError("SC must be 1,2,3 or 4")
        if beta > 0.5:
            raise ValueError("beta must be < 0.5")
        if beta_d > 0.5:
            raise ValueError("beta_d must be < 0.5")
        if HFT != 0 and HFT != 1 and HFT != 2 and HFT != 3 and HFT != 4:
            raise ValueError("HFT must be 0,1,2,3 or 4")
        if MTTR < 0:
            raise ValueError("MTTR must be > 0")
        self._lambda_du = lambda_du
        self._lambda_dd = lambda_dd
        self._lambda_su = lambda_su
        self._lambda_sd = lambda_sd
        self._type = type
        self._SC = SC
        self._beta = beta
        self._beta_d = beta_d
        self._HFT = HFT
        self._MTTR = MTTR
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, new_name):
        self._name = new_name
    @property
    def lambda_du(self):
        return self._lambda_du
    @property
    def lambda_du_fit(self):
        return self._lambda_du/1e-9    
    @lambda_du.setter
    def lambda_du(self, new_lambda_du):
        if new_lambda_du > 0.1:
            raise ValueError("λdu/h must be <= 0.1")
        else:
            self._lambda_du = new_lambda_du
    def lambda_du_FIT(self, FIT:float):
        if FIT < 0:
            raise ValueError("λdu FIT must be >= 0")
        else:
            self._lambda_du = FIT*1e-9
    @property
    def lambda_dd(self):
        return self._lambda_dd
    @property
    def lambda_dd_fit(self):
        return self._lambda_dd/1e-9    
    @lambda_dd.setter
    def lambda_dd(self, new_lambda_dd:float):
        if new_lambda_dd > 0.1:
            raise ValueError("λdd/h must be <= 0.1")
        else:
            self._lambda_dd = new_lambda_dd
    def lambda_dd_FIT(self, FIT:float):
        if FIT < 0:
            raise ValueError("λdd FIT must be >= 0")
        else:
            self._lambda_dd = FIT*1e-9
    @property
    def lambda_su(self):
        return self._lambda_su
    @property
    def lambda_su_fit(self):
        return self._lambda_su/1e-9    
    @lambda_su.setter
    def lambda_su(self, new_lambda_su:float):
        if new_lambda_su > 0.1:
            raise ValueError("λsu/h must be <= 0.1")
        else:
            self._lambda_su = new_lambda_su
    def lambda_su_FIT(self, FIT:float):
        if FIT < 0:
            raise ValueError("λsu FIT must be >= 0")
        else:
            self._lambda_su = FIT*1e-9
    @property
    def lambda_sd(self):
        return self._lambda_sd
    @property
    def lambda_sd_fit(self):
        return self._lambda_sd/1e-9    
    @lambda_sd.setter
    def lambda_sd(self, new_lambda_sd:float):
        if new_lambda_sd > 0.1:
            raise ValueError("λsd/h must be <= 0.1")
        else:
            self._lambda_sd = new_lambda_sd
    def lambda_sd_FIT(self, FIT:float):
        if FIT < 0:
            raise ValueError("λsd FIT must be >= 0")
        else:
            self._lambda_sd = FIT*1e-9
    @property
    def type(self):
        return self._type  
    @type.setter
    def type(self, new_type:str):
        if new_type != "A" and new_type != "B":
            raise ValueError("Tyepe must be A or B")
        else:
            self._type = new_type
    @property
    def SC(self):
        return self._SC  
    @SC.setter
    def SC(self, new_SC:int):
        if new_SC != 1 and new_SC != 2 and new_SC != 3 and new_SC != 4:
            raise ValueError("SC must be 1,2,3 or 4")
        else:
            self._SC = new_SC
    @property
    def beta(self):
        return self._beta
    @beta.setter
    def beta(self, new_beta:float):
        if new_beta>0.5:
            raise ValueError("Beta must be < 0.5")
        else:
            self._beta = new_beta
    @property
    def beta_d(self):
        return self._beta_d
    @beta_d.setter
    def beta_d(self, new_beta_d:float):
        if new_beta_d>0.5:
            raise ValueError("Beta_d must be < 0.5")
        else:
            self._beta_d = new_beta_d
    @property
    def HFT(self):
        return self._HFT
    @HFT.setter
    def HFT(self, new_HFT:int):
        if new_HFT != 0 and new_HFT != 1 and new_HFT != 2 and new_HFT != 3 and new_HFT != 4:
            raise ValueError("HFT must be 0,1,2,3 or 4")
        else:
            self._HFT = new_HFT
    @property
    def MTTR(self):
        return self._MTTR
    @MTTR.setter
    def MTTR(self, new_MTTR:float):
        if new_MTTR < 0:
            raise ValueError("MTTR must be >0")
        else:
            self._MTTR = new_MTTR
    @property
    def DC_d(self):
        return self._lambda_dd/(self.lambda_d)
    @DC_d.setter
    def DC_d(self, new_DC_d:float):
        if new_DC_d < 0 or new_DC_d > 1:
            raise ValueError("DC must be 0 < DC < 1")
        lambdad= self.lambda_d
        self._lambda_du = lambdad * (1-new_DC_d)
        self._lambda_dd = lambdad * new_DC_d
    @property
    def lambda_s(self):
        return self._lambda_su + self._lambda_sd
    @property
    def lambda_d(self):
        return self._lambda_du + self._lambda_dd
    @property
    def lambda_t(self):
        return self.lambda_d + self.lambda_s
    @property
    def SFF(self):
        return ((self._lambda_dd + self.lambda_s))/(self.lambda_t) #Considering trip if lambda_dd occurs
    @property
    def MTBF_d(self):
        return (1/self.lambda_d)/8760
    @property
    def FS(self):
        return self.lambda_s/self.lambda_t
    def lambda_FIT(self, lambda_du:float, lambda_dd:float, lambda_su:float,lambda_sd:float):
        if lambda_du < 0:
            raise ValueError("λdu FIT must be >= 0 ")
        if lambda_dd < 0:
            raise ValueError("λdd FIT must be >= 0 ")
        if lambda_su < 0:
            raise ValueError("λsu FIT must be >= 0 ")
        if lambda_sd < 0:
            raise ValueError("λsd FIT must be >= 0 ")
        self._lambda_du = lambda_du*1e-9
        self._lambda_dd = lambda_dd*1e-9
        self._lambda_su = lambda_su*1e-9
        self._lambda_sd = lambda_sd*1e-9
    def lambda_hour(self, lambda_du:float, lambda_dd:float, lambda_su:float,lambda_sd:float):
        if lambda_du < 0:
            raise ValueError("λdu hour must be >= 0 ")
        if lambda_dd < 0:
            raise ValueError("λdd hour must be >= 0 ")
        if lambda_su < 0:
            raise ValueError("λsu hour must be >= 0 ")
        if lambda_sd < 0:
            raise ValueError("λsd hour must be >= 0 ")
        self._lambda_du = lambda_du
        self._lambda_dd = lambda_dd
        self._lambda_su = lambda_su
        self._lambda_sd = lambda_sd
    def lambda_year(self, lambda_du:float, lambda_dd:float, lambda_su:float,lambda_sd:float):
        if lambda_du < 0:
            raise ValueError("λdu year must be >= 0 ")
        if lambda_dd < 0:
            raise ValueError("λdd year must be >= 0 ")
        if lambda_su < 0:
            raise ValueError("λsu year must be >= 0 ")
        if lambda_sd < 0:
            raise ValueError("λsd year must be >= 0 ")
        self._lambda_du = lambda_du/8760
        self._lambda_dd = lambda_dd/8760
        self._lambda_su = lambda_su/8760
        self._lambda_sd = lambda_sd/8760
    def header_matrix(self):
        return ["name","λdu","λdd","λsu","λsd","λdu_FIT","λdd_FIT","λsu_FIT","λsd_FIT","type","SC","beta","beta_d","SFF","DC_d","MTBF_d","FS"]
    def val_matrix(self):
        return [self.name, self.lambda_du,self.lambda_dd,self.lambda_su,self.lambda_sd,self.lambda_du_fit,self.lambda_dd_fit,self.lambda_su_fit,
                self.lambda_sd_fit,self.type,self.SC,self.beta,self.beta_d,self.SFF,self.DC_d,self.MTBF_d,self.FS]
class proof_test:
    def __init__(self, name1:str, T1_month:float):
        self.name1 = name1
        self.T1_month = T1_month

class proof_test_1pt:
    def __init__(self, name_pt:str, T_pt_month:float, PDC_pt:float, T1_month:float):
        self.name_pt = name_pt
        self.T_pt_month = T_pt_month
        self.PDC_pt = PDC_pt
        self.T1_month = T1_month

class proof_test_2pt:
    def __init__(self, name_pt1:str, T_pt1_month:float, PDC_pt1:float, name_pt2:str, T_pt2_month:float, PDC_pt2:float,T1_month:float):
        self.name_pt1 = name_pt1
        self.T_pt1_month = T_pt1_month
        self.T_pt2_month = T_pt2_month
        self.PDC_pt1 = PDC_pt1
        self.PDC_pt2 = PDC_pt2
        self.name_pt2 = name_pt2
        self.T1_month = T1_month
        