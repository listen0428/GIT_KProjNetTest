# -*- coding: utf-8 -*-
__author__ = 'ls'
from threading import Condition
from Logger import logger
import time
CLOCK_OVERFLOW = 17.20735697467875
class Anchor():
    """
    anchor can be master anchor or slave anchor,
    what they share in common is that both receive
    blink packet from tagcard.
    """
    def __init__(self, MAC, x, y, z, delay, field,area):
        self.measureScale = 0.01
        self.MAC = MAC
        self.x = float(x)*self.measureScale
        self.y = float(y)*self.measureScale
        self.z = float(z)*self.measureScale
        self.delay = float(delay)/2000000000
        self.field = int(field)
        # dict of blink packets info, k:v = sn : (t, TC_MAC)
        # t is time when receiving blink packet
        self.T_receive_blink = {}
        # dict of blink packets info classified by TC, k:v = TC_MAC : sn
        # this dict only aims at deleting sn
        self.blink_TC = {}
        self.conTrb = Condition()

    # Trb: T/ime when R/eceiving B/link packet
    # @profile
    def setTrb(self, sn, t, TC_MAC):
        with self.conTrb:
            for value1,value2 in self.T_receive_blink.items():
                if sn[1]==value1[1] and (int(sn[0])-int(value1[0]))%256>10:
                    self.T_receive_blink.pop(value1, value2)
            self.T_receive_blink[sn] = t, TC_MAC
            self.conTrb.notifyAll()

    # @profile
    def getTrb(self, sn):
        # get receive time and TC_MAC identified by sn.
        Trb = None
        with self.conTrb:
            Trb = self.T_receive_blink.get(sn, (None, None))
            if sn in self.T_receive_blink:
                del self.T_receive_blink[sn]
            self.conTrb.notifyAll()
        return Trb

    # @profile
    def hasTrb(self, sn):
        # find if receive time and TC_MAC exist by sn.
        result = False
        with self.conTrb:
            if sn in self.T_receive_blink:
                result = True
            self.conTrb.notifyAll()
        return result

    def removeTrb(self, sn):
        self.getTrb(sn)

class Slave(Anchor):
    """
    a slave anchor handles sync packet.
    it also stores time compensations to all
    related master anchors.
    """
    def __init__(self, MAC, x, y, z, delay, field,area):
        Anchor.__init__(self, MAC, x, y, z, delay, field,area)
        # list of sync packets info, k:v = M_MAC : (sn , t)
        # t is time when receiving sync packet
        self.T_receive_sync = {}
        self.conTrs = Condition()

        # linear clock drift estimation and compensation
        # compensation dict, k: v = M_MAC: (Sync_sn, k, B, x, y), Tdrift = k * Trs + B
        self.T_Drift_Compensation = {}
        self.conTDC = Condition()
        self.P=0
        self.xhat=0
        self.R=0.001 # estimate of measurement variance, change to see effect，该值越小，历史值对结果的影响越小
        self.Q = 1e-5
    # Trs: T/ime when R/eceiving S/ync packet
    # @profile
    def setTrs(self, sn, t, M_MAC):
        with self.conTrs:
            self.T_receive_sync[M_MAC] = (sn, t)#因为mac地址相同，所以被替换
            logger.debug(self.T_receive_sync)
            self.conTrs.notifyAll()

    def getTrs(self, sn, M_MAC):
        Trs = None
        with self.conTrs:
            if sn == self.T_receive_sync[M_MAC][0]:
                Trs = self.T_receive_sync[M_MAC][1]
            self.conTrs.notifyAll()
        return Trs

    def hasTrs(self, sn, M_MAC):
        result = False
        with self.conTrs:
            if M_MAC in self.T_receive_sync and abs(int(sn) - int(self.T_receive_sync[M_MAC][0]))<2:
                result = True
            else:
                logger.info('sn=%s,M_MAC=%s,T_receive_sync=%s,result=%s',sn,M_MAC,self.T_receive_sync,result)
                logger.debug(self.T_receive_sync)
            self.conTrs.notifyAll()
        return result

    def getTDC(self, Trs, M_MAC):
        Tss = None
        with self.conTDC:
            if M_MAC in self.T_Drift_Compensation:
                _, k, B, Trs1, _,_,_ = self.T_Drift_Compensation[M_MAC]
                if k is not None and B is not None:
                    if Trs-Trs1>16:
                        Tss = k * (Trs-CLOCK_OVERFLOW) + B
                    else:
                        Tss = k * Trs + B
                    logger.debug([Tss,k,B,Trs1,Trs])
            self.conTDC.notifyAll()
        return Tss


    def calcu(self,value,xhat,P):#卡尔曼滤波计算
        xhatminus = xhat
        Pminus = P+self.Q

        K = Pminus/(Pminus+self.R)
        xhat = xhatminus + K*(value-xhatminus)
        P = (1-K)*Pminus
        return xhat,P

    def updateTDC(self, sn, Trs, Tss, M_MAC):
        """
        Trs - Tss = k * Trs + B
        we update k and B every time we get Trs and Tss.
        """
        with self.conTDC:
            x2 = Trs
            y2 = Tss
            if M_MAC in self.T_Drift_Compensation:
                last_sn, last_k, last_B, x1, y1,last_fir_k,last_fir_P = self.T_Drift_Compensation.pop(M_MAC)
                if y1>y2:
                    y1 = y1 - CLOCK_OVERFLOW
                if x1>x2:
                    x1 = x1 - CLOCK_OVERFLOW
                # insure that Sync SN is not too early
                if int(sn) - last_sn <5 or int(sn) + 4294967296 - last_sn < 5:#2^32
                    try:
                        k = (y1 - y2) / (x1 - x2)
                        B = (y2 * x1 - y1 * x2) / (x1 - x2)
                        if last_fir_k==0:
                            fir_k,fir_P = self.calcu(k,k,last_fir_P)
                        else:
                            fir_k,fir_P = self.calcu(k,last_fir_k,last_fir_P)
                        if abs(fir_k-k)<1e-8:
                            self.T_Drift_Compensation[M_MAC] = (int(sn), k, B, x2, y2,fir_k,fir_P)
                        else:
                            self.T_Drift_Compensation[M_MAC] = (last_sn, last_k, last_B, x1, y1,fir_k,fir_P)
                            logger.warning([M_MAC,self.MAC,int(sn),k,fir_k,fir_k-k,B,x1,x2,x1 - x2,y1,y2,y1 - y2])
                    except ZeroDivisionError as e:
                        logger.error(e)
                    finally:
                        self.conTDC.notifyAll()
                    return
            self.T_Drift_Compensation[M_MAC] = (int(sn), 0, None, x2, y2,0,0)#若不满足if，则不计算k，b，直接存入x2，y2
            self.conTDC.notifyAll()

class Master(Slave):
    def __init__(self, MAC, x, y, z, delay, field,area):
        Slave.__init__(self, MAC, x, y, z, delay, field,area)
        # dict of sync packets info, k:v = sn : [(t, S_MAC)]
        # t is time when sending sync packet
        self.T_send_sync = {}
        self.conTss = Condition()
        self.ble_addr = ''
        self.time_dict = {}
        self.area = area

    # Tss: T/ime when S/ending S/ync packet
    def setTss(self, sn, t, S_MAC):
        with self.conTss:
            if sn not in self.T_send_sync:
                self.T_send_sync[sn] = []
            self.T_send_sync[sn].append((t, S_MAC))
            # clean up Tss that not used
            for unused_sn in self.T_send_sync.keys():
                if unused_sn > sn or int(sn) - int(unused_sn) > 10:
                    self.T_send_sync.pop(unused_sn, None)
                    logger.debug('Master %s popped unsued sync SN %s' %(self.MAC, unused_sn))
            self.conTss.notifyAll()

    def getTss(self, sn, S_MAC):
        Tss = None
        with self.conTss:
            Tss_list = self.T_send_sync[sn]
            if len(Tss_list):
                for ele in Tss_list:
                    if S_MAC == ele[1]:
                        Tss = ele[0]
                        break
            self.conTss.notifyAll()
        return Tss

    def hasTss(self, sn, S_MAC):
        result = False
        with self.conTss:
            if sn in self.T_send_sync:
                for _, MAC in self.T_send_sync[sn]:
                    if S_MAC == MAC:
                        result = True
            if not result:
                logger.debug('sn=%s,S_MAC=%s,T_receive_sync=%s,result=%s',sn,S_MAC,self.T_send_sync,result)
            self.conTss.notifyAll()
        return result

    def removeTss(self, sn):
        with self.conTss:
            self.T_send_sync.pop(sn, None)
            self.conTss.notifyAll()

    def setTime(self,sn,receive_time):
        self.time_dict[sn] = receive_time

    def getTime(self,sn):
        try:
            receive_time = self.time_dict.pop(sn)
        except KeyError:
            logger.info('%s不存在！',sn)

            receive_time = int(time.time()*1000)
        # else:
        #
        #     for key in self.time_dict:
        #         print(self.time_dict[key])
        #         if sn[1]==key[1]:
        #             if (abs(int(sn[0])-int(key[0])))%65536>=5:
        #                 self.time_dict.pop(key)
        #                 logger.debug('当前time_dict长度为：%s',len(self.time_dict))
        return receive_time
def main():
    pass

if __name__ == '__main__':
    main()