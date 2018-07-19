__author__ = 'ls'

class AverageData():
    def __init__(self):
        self.ave_data = 0
        self.var_data = 0
        self.ave_sn = 0
        self.var_sn = 0
    def averageData(self,data,en):
        if en:
            self.ave_sn = self.ave_sn + 1
            self.ave_data = self.ave_data*(self.ave_sn-1)/self.ave_sn+data/self.ave_sn
        else:
            self.ave_data = 0
            self.ave_sn = 0
        return [self.ave_sn,self.ave_data]

    def varianceData(self,data,en):
        if en:
            self.var_sn = self.var_sn + 1
            self.var_data = (self.var_data)*(self.var_sn-1)/self.var_sn+data**2/self.var_sn
        else:
            self.var_data = 0
            self.var_sn = 0

        return [self.var_data,self.var_data]



if __name__ == "__main__":
    ad = AverageData()
    ave_data=0
    ad.averageData(0,0)
    for i in range(100):
        print(ad.averageData(i,1))