class VangenuchtenTheta():
    def __init__(
        self,
        theta_r,    # residual water content [L3L-3]
        theta_s,    # saturated water content [L3L-3]
        n,          # measure of the pore-size distribution, >1
        alpha,      # related to the inverse of the air entry suction [cm^-1], >0
    ):
        super().__init__()
        self.theta_r = theta_r
        self.theta_s = theta_s
        self.alpha = alpha
        self.n = n

    def __call__(self, u):
        f = (self.theta_s - self.theta_r) / ((1.0 + abs(self.alpha * u) ** self.n) ** (1.0 - 1.0 / self.n)) + self.theta_r
        return f    # [hPa]
    
    def get_thetaFC(self):
        return self.__call__(-330)
    
    def get_thetaWP(self):
        return self.__call__(-15000)