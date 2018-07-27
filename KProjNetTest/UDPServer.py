# -*- coding: utf-8 -*-
__author__ = 'few'
# 创建时间 2018/3/2 10:48 


import socket,pickle,struct,logging
from Logger import logger
import PySqlite
import time,threading
from queue import Queue,Full
import DataAnalysis
SendQuene = Queue(10000)
DataTransmitQuene = Queue(1000)
LoraDevice = ['Lora接收','Lora发送','PS发送','other']
ControlOrder = [0]
class TestLossPackage():
    def __init__(self,init_cnt):
        self.init_cnt = init_cnt
        self.last_cnt = init_cnt
        self.loss_cnt = 0
        self.same_package_flag = 0


    def calculateLossPackage(self,cnt,flag):
        if cnt<3:
            self.init_cnt = cnt
            logger.warning(LoraDevice[flag]+'重启！')
        else:
            if cnt == self.last_cnt:
                self.same_package_flag = 1
            else:
                self.same_package_flag = 0
                self.loss_cnt = cnt - self.last_cnt - 1 + self.loss_cnt

        total_package = cnt -  self.init_cnt
        try:
            loss_package_probability = round(self.loss_cnt*100/total_package,2)
        except:
            loss_package_probability = -1
            logger.warning([LoraDevice[flag],'计数器未累加。'])
        # logger.info(loss_package_probability)
        data_list = [total_package,self.loss_cnt,loss_package_probability,self.last_cnt,self.same_package_flag]
        self.last_cnt = cnt
        return data_list

class TagDevice():
    def __init__(self):
        self.pack_lora_dict = {}
        self.tag_uwb_cnt = 0
        self.tag_uwb_cnt = 0
        self.test_loss_package = {}

    def tagReceiver(self,data,type):
        if type:
            if len(data)<28:
                SendQuene.put_nowait([0,self.time+' : '+'forklift length is '+str(len(data))])
                logger.error('forklift length is '+str(len(data)))
                return
        else:
            if len(data)<38:
                SendQuene.put_nowait([0,self.time+' : '+'scale length is '+str(len(data))])
                logger.error('scale length is '+str(len(data)))
                return
        self.pack_lora_dict['GWMAC']=''.join(["%02X"%(char) for char in data[1:9]])
        # self.pack_lora_dict['State']=struct.unpack("3B",data[10:13])
        # self.pack_lora_dict['Weight']=struct.unpack("6B",data[13:19])

        self.pack_lora_dict['Work']=bin(int(data[19-type*10]/2**5))
        self.pack_lora_dict['Count']=int(data[19-type*10]/2**2%8)
        unpack_data = struct.unpack(">IIH",data[20-type*10:30-type*10])
        Date = unpack_data[1]//2**17
        Time_s = unpack_data[1]%2**16
        self.pack_lora_dict['UWBcnt']=unpack_data[0]
        self.pack_lora_dict['Date']='%04d-%02d-%02d'%(2000+(Date//2**9),Date//2**5%2**4,Date%2**5)
        self.pack_lora_dict['Time']='%02d:%02d:%02d,%03d'%((Time_s//3600+8)%24,Time_s%3600//60,Time_s%60,unpack_data[2]) #str(Time_s//3600+8)+':'+str(Time_s%3600//60)+':'+str(Time_s%60)
        self.time = self.pack_lora_dict['Date'] + ' ' + self.pack_lora_dict['Time']
        # self.pack_lora_dict['Time_s']=str(Time_s//3600+8)+':'+str(Time_s%3600//60)+':'+str(Time_s%60)
        # self.pack_lora_dict['Time_ms']=unpack_data[2]
        # if len(data)%10==8:
        #     self.pack_lora_dict['LoraCnt']=struct.unpack(">3H",data[-6:])
        # elif len(data)%10==9:
        self.pack_lora_dict['LoraCnt']=struct.unpack(">3HB",data[-7:])
        if unpack_data[0] < self.tag_uwb_cnt:
            logger.error(self.pack_lora_dict)
            content = ''.join([self.time+' : '+self.pack_lora_dict['GWMAC'],',cnt:',str(unpack_data[0]),',LoraCnt:',str(self.pack_lora_dict['LoraCnt']),',lora包错误!'])
            SendQuene.put_nowait([0,content])
        else:
            logger.info(self.pack_lora_dict)
        self.tag_uwb_cnt = unpack_data[0]

        self.loraCountProcess(self.pack_lora_dict['GWMAC'],self.pack_lora_dict['LoraCnt'])

    def scaleReceiver(self,data):
        if len(data)>=38:
            self.pack_lora_dict['GWMAC']=''.join(["%02X"%(char) for char in data[1:9]])
            # self.pack_lora_dict['State']=struct.unpack("3B",data[10:13])
            # self.pack_lora_dict['Weight']=struct.unpack("6B",data[13:19])
            self.pack_lora_dict['Work']=bin(int(data[19]/2**5))
            self.pack_lora_dict['Count']=int(data[19]/2**2%8)
            unpack_data = struct.unpack(">IIH",data[20:30])
            Date = unpack_data[1]//2**17
            Time_s = unpack_data[1]%2**16
            self.pack_lora_dict['UWBcnt']=unpack_data[0]
            self.pack_lora_dict['Date']='%04d-%02d-%02d'%(2000+(Date//2**9),Date//2**5%2**4,Time_s%2**5)
            self.pack_lora_dict['Time']='%02d:%02d:%02d,%03d'%((Time_s//3600+8)%24,Time_s%3600//60,Time_s%60,unpack_data[2]) #str(Time_s//3600+8)+':'+str(Time_s%3600//60)+':'+str(Time_s%60)
            self.time = self.pack_lora_dict['Date'] + ' ' + self.pack_lora_dict['Time']
            # self.pack_lora_dict['Time_s']=str(Time_s//3600+8)+':'+str(Time_s%3600//60)+':'+str(Time_s%60)
            # self.pack_lora_dict['Time_ms']=unpack_data[2]
            n = self.pack_lora_dict['Count']
            self.pack_lora_dict['LoraCnt']=struct.unpack(">3H",data[-6:])
            if unpack_data[0] < self.tag_uwb_cnt:
                logger.error(self.pack_lora_dict)
                content = ''.join([self.time+' : '+self.pack_lora_dict['GWMAC'],',cnt:',str(unpack_data[0]),',LoraCnt:',str(self.pack_lora_dict['LoraCnt']),',lora包错误!'])
                SendQuene.put_nowait([0,content])
            else:
                logger.info(self.pack_lora_dict)
            logger.info([self.tag_uwb_cnt,unpack_data[0]])
            self.tag_uwb_cnt = unpack_data[0]
        else:
            SendQuene.put_nowait([0,self.time+' : '+'scale length is '+str(len(data))])
            logger.error('scale length is '+str(len(data)))
            return
        self.loraCountProcess(self.pack_lora_dict['GWMAC'],self.pack_lora_dict['LoraCnt'])

    def forkliftReceiver(self,data):
        if len(data)>=28:
            self.pack_lora_dict['GWMAC']=''.join(["%02X"%(char) for char in data[1:9]])
            self.pack_lora_dict['Work']=bin(int(data[9]/2**5))
            self.pack_lora_dict['Count']=int(data[9]/2**2%8)
            unpack_data = struct.unpack(">IIHH",data[10:22])
            self.pack_lora_dict['UWBcnt']=unpack_data[0]
            Date = unpack_data[1]//2**17
            Time_s = unpack_data[1]%2**17
            self.pack_lora_dict['Date']='%04d-%02d-%02d'%(2000+(Date//2**9),Date//2**5%2**4,Time_s%2**5)
            self.pack_lora_dict['Time']='%02d:%02d:%02d,%03d'%((Time_s//3600+8)%24,Time_s%3600//60,Time_s%60,unpack_data[2]) #str(Time_s//3600+8)+':'+str(Time_s%3600//60)+':'+str(Time_s%60)
            self.time = self.pack_lora_dict['Date'] + ' ' + self.pack_lora_dict['Time']
            # self.pack_lora_dict['Time_ms']=unpack_data[2]
            self.pack_lora_dict['Press']=unpack_data[3]

            # self.pack_lora_dict['BLE']=''.join(["%02X"%(char) for char in data[22:29]])
            n = self.pack_lora_dict['Count']
            self.pack_lora_dict['LoraCnt']=struct.unpack(">3H",data[-6:])
            if unpack_data[0] < self.tag_uwb_cnt:
                logger.error(self.pack_lora_dict)
                content = ''.join([self.time+' : '+self.pack_lora_dict['GWMAC'],',cnt:',str(unpack_data[0]),',LoraCnt:',str(self.pack_lora_dict['LoraCnt']),',lora包错误!'])
                SendQuene.put_nowait([0,content])
            else:
                logger.info(self.pack_lora_dict)
            logger.info([self.tag_uwb_cnt,unpack_data[0]])
            self.tag_uwb_cnt = unpack_data[0]
        else:
            SendQuene.put_nowait([0,self.time+' : '+'forklift length is '+str(len(data))])
            logger.error('forklift length is '+str(len(data)))
            return

        self.loraCountProcess(self.pack_lora_dict['GWMAC'],self.pack_lora_dict['LoraCnt'])

    def loraCountProcess(self,gw_mac,cnt_list):
        logger.info([gw_mac,cnt_list])
        content = ''
        total_package = 0
        for i in range(3):
            try:
                loss_pack = self.test_loss_package[gw_mac+str(i)].calculateLossPackage(cnt_list[i],i)
                if loss_pack[3]>cnt_list[i]:
                    logger.error([gw_mac+','+LoraDevice[i],'总包数:',loss_pack[0],'丢包数:',loss_pack[1],'丢包率%:',loss_pack[2]])
                    SendQuene.put_nowait([0,''.join([self.time+' : '+gw_mac+','+LoraDevice[i],'计数器逆序,LoraCnt: ',str(cnt_list[i])])])
                elif cnt_list[i]-loss_pack[3]>1:
                    logger.error([gw_mac+','+LoraDevice[i],'总包数:',loss_pack[0],'丢包数:',loss_pack[1],'丢包率%:',loss_pack[2]])
                    SendQuene.put_nowait([0,''.join([self.time+' : '+gw_mac+','+LoraDevice[i],'丢包数:',str(cnt_list[i]-loss_pack[3]-1),',LoraCnt: ',str(cnt_list[i])])])
                else:
                    # pass
                    logger.info([gw_mac+','+LoraDevice[i],'总包数:',loss_pack[0],'丢包数:',loss_pack[1],'丢包率%:',loss_pack[2]])
                if loss_pack[4]==1:
                    logger.error([self.time+' : '+gw_mac+','+LoraDevice[i],'重复包, LoraCnt: ',str(cnt_list[i])])
                    SendQuene.put_nowait([0,''.join([self.time+' : '+gw_mac+','+LoraDevice[i],'重复包, LoraCnt: ',str(cnt_list[i])])])
                content = content + ''.join([str(loss_pack[2]),'    '])
                total_package = loss_pack[0] if i==1 else total_package
            except:
                self.test_loss_package[gw_mac+str(i)] = TestLossPackage(cnt_list[i])
        content = ''.join([gw_mac,',发送总包数:',str(total_package),'\n','丢包率%:']) + content + '\n'
        SendQuene.put_nowait([1,content])
        


upd_en = False
upd_log_en = False
Tx_IP_Addr = []

input_cnt = output_cnt = 0
class UDPServer():
    # DWT_TIME_UNITS = 1.565e-11
    # CLOCK_OVERFLOW = 17.20735697467875
    # Velocity_Light = 299792458
    # TimeRx = [1,2,3]
    # TimeRx_dict = {}
    # Package_dict = {}
    # delta_time_last = {}
    SN = [1,2,3]
    def __init__(self):
        self.pack_ble_dict = {}
        self.pack_lora_dict = {}
        self.DWT_TIME_UNITS = 1.565e-11
        self.CLOCK_OVERFLOW = 17.20735697467875
        self.Velocity_Light = 299792458
        self.TimeRx_dict = {}
        self.Package_dict = {}
        self.delta_time_last = {}
        self.cB_txmac_currentText = 0
        self.test_loss_package = {}
        self.tag_divece = {}
        self.average_data = {}
        self.uwb_average_time = {}
        self.ave_time ={}
        self.var_time ={}
        self.ip_mac = {}
        self.thread_lock = threading.Lock()
    def receive(self,addr,pB_udpbegin,cB_ip,cB_ip_2,tB_log,tB_log_2,cB_txmac):
        logger.info(addr)
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            server.bind(addr)
        except OSError as r:
            logger.error(r,exc_info=True)
            tB_log.append('警告：端口%d被占用！'%(addr[1]))
            pB_udpbegin.setText("udp启动")
            pB_udpbegin.setEnabled(True)
            cB_ip.setEnabled(True)
            global upd_en
            upd_en = False
            return
        server.settimeout(2)#设置套接字超时时间，单位为s
        self.t = threading.Thread(target=self.quenePrint, args=(tB_log,tB_log_2,))
        self.t.setDaemon(True)
        self.t.start()

        while True:
            if upd_en:
                try:
                    data,udp_addr = server.recvfrom(1024)
                    logger.info(['data length: ',len(data),',data: ',''.join(["%02X"%(char) for char in data])])
                except socket.timeout :
                    logger.error(socket.timeout,exc_info=0)
                    # pass
                else:

                    if data[0]==1:#表示接收到uwb数据
                        self.uwbReceiver(data,cB_txmac,udp_addr)
                    elif data[0]==2:#表示接收到ble数据
                        logger.debug('ble')
                        self.bleReceiver(data,cB_txmac)
                    elif data[0]==0x10:#表示接收到lora-scale数据
                        self.tagDevice(data,0)
                    elif data[0]==0x80:#表示接收到lora-forklift数据
                        self.tagDevice(data,1)
                    elif data[0]==0xfa:#设备管理器
                        self.deviceManager(data,udp_addr,cB_ip_2)
                    elif data[0]==0xaa:#节点蓝牙
                        self.tagBleReceiver(data,cB_txmac)
            else:
                server.close()
                logger.info('udp stop')
                pB_udpbegin.setEnabled(True)
                break

    def tagDevice(self,data,type):
        flag=''.join(["%02X"%(char) for char in data[1:9]])
        try:
            # self.tag_divece[flag+'1'].forkliftReceiver(data) if type else self.tag_divece[flag+'1'].scaleReceiver(data)
            self.tag_divece[flag].tagReceiver(data,type)
        except:
            self.tag_divece[flag+'1'] = TagDevice()
            self.tag_divece[flag] = TagDevice()


    def tagBleReceiver(self,data,cB_txmac):
        self.pack_ble_dict['BLE']=''.join(["%02X"%(char) for char in data[0:7]])
        unpack_data = struct.unpack(">II",data[24:32])
        Time_s = unpack_data[0]%2**16
        self.pack_ble_dict['Time_s']=str(Time_s//3600+8)+':'+str(Time_s%3600//60)+':'+str(Time_s%60)
        try:
            self.pack_ble_dict['Time_ms_last']=self.pack_ble_dict['Time_ms']
        except:
            self.pack_ble_dict['Time_ms_last']=0
        self.pack_ble_dict['Time_ms']=unpack_data[1]//50000
        self.pack_ble_dict['Time_ms_diff']=(self.pack_ble_dict['Time_ms']-self.pack_ble_dict['Time_ms_last'])%1000

        logger.info(self.pack_ble_dict)


    def deviceManager(self,data,udp_addr,cB_ip_2):
        logger.info([udp_addr,''.join(["%02X"%(char) for char in data[0:len(data)]])])
        if cB_ip_2.currentText()=="ALL" or udp_addr[0]==cB_ip_2.currentText():
            content = ''.join([udp_addr[0],'：',''.join(["%02X"%(char) for char in data[0:len(data)]])])
            SendQuene.put_nowait([0,content])

        global Tx_IP_Addr
        if udp_addr[0] not in Tx_IP_Addr:#当接收到来自新ip的数据时，更新数据库和客户端ip列表
            if self.thread_lock.acquire():
                Tx_IP_Addr.append(udp_addr[0])
                cB_ip_2.addItem(udp_addr[0])
                db = PySqlite.DataBase('address_data.db')
                db.addRow(udp_addr[0],udp_addr[1],'ADDRESS')
                logger.info('addItem news ip')
                db.conn.close()
                self.thread_lock.release()

    def bleReceiver(self,data,cB_txmac):
        unpack_data = struct.unpack(">BBHI",data[0:8])
        self.pack_ble_dict['Header']=unpack_data[0]
        self.pack_ble_dict['Site']=unpack_data[1]
        self.pack_ble_dict['PackNum']=unpack_data[2]
        self.pack_ble_dict['BleSum']=unpack_data[3]
        self.pack_ble_dict['GWMAC']=''.join(["%02X"%(char) for char in data[8:16]])
        self.pack_ble_dict['End']=''.join(["%02X"%(char) for char in data[-2:]])
        # content = ''.join(str(self.pack_ble_dict.values()))
        # SendQuene.put_nowait([1,content])
        logger.info(self.pack_ble_dict)
        if self.pack_ble_dict['PackNum']*10+20 == len(data) and self.pack_ble_dict['End']=='FFEE':
            for i in range(unpack_data[2]):
                ble_data = data[i*10+16:i*16+26]
                bleAddr = ''.join(["%02X"%(char) for char in ble_data[0:7]])
                data_dict ={
                        'bleAddr':bleAddr,
                        'Active':ble_data[7]/2**6,
                        'TagState':ble_data[7]/2**4%4,
                        'Cause':ble_data[7]%16,
                        'Voltage': ble_data[8],
                        'RSSI':ble_data[9]
                    }
                logger.info(data_dict)
        else:
            logger.error(['ble包错误：',self.pack_ble_dict])
            content = ''.join(['cnt:',str(unpack_data[1]),',ble包错误!'])
            SendQuene.put_nowait([1,content])

    def uwbReceiver(self,data,cB_txmac,udp_addr):
        self.pack_ble_dict['Header']=str(data[0])
        self.pack_ble_dict['PackNum']=data[1]
        self.pack_ble_dict['FPGACnt']=data[2]*256+data[3]
        if len(data)==data[2]*256+data[3]:
            for i in range(data[1]):
                uwb_data = data[i*48+4:i*48+52]

                unpack_data = struct.unpack("4x2L4xQ",uwb_data[0:24])
                sn_8 = unpack_data[0]
                Tt = unpack_data[1]
                Tr = unpack_data[2]

                AddrT = ''.join(["%02X"%(char) for char in uwb_data[24:32]])
                AddrR = ''.join(["%02X"%(char) for char in uwb_data[32:40]])

                if udp_addr[0] not in self.ip_mac:
                    self.ip_mac[udp_addr[0]]=AddrR
                    logger.warning([udp_addr[0],AddrR])
                    content = ''.join([udp_addr[0],' : ',AddrR])
                    SendQuene.put_nowait([0,content])
                # AddrR = ''
                # for char in uwb_data[32:40]:
                #     AddrR = AddrR + "%02X"%(char)

                if uwb_data[0]==0xAA:
                    # return
                    data_dict ={
                        'type':'B',
                        'SN':sn_8,
                        'TimeRx': float(Tr)*self.DWT_TIME_UNITS,
                        'AddrT':AddrT,
                        'AddrA':AddrR,
                        'Time':int(time.time()*1000),
                        'IP':udp_addr
                    }
                    # logger.debug(data_dict)
                    # self.testTimeStability('R-'+AddrR+',T-'+AddrT,data_dict['SN'],float(Tr)*self.DWT_TIME_UNITS)
                elif uwb_data[0]==0x55:
                    # return
                    data_dict = {
                        'type': 'S',
                        'SN': sn_8,
                        'TimeRxS': float(Tr)*self.DWT_TIME_UNITS,#16表示安装16进制处理
                        'TimeTxM': float(Tt)*self.DWT_TIME_UNITS*256,
                        'AddrM': AddrT,
                        'AddrS': AddrR
                    }
                    # if AddrR=="01AA2145CCF0CB1F":#分析定位包时间稳定性
                    # self.testTimeStability('R-'+AddrR+',T-'+AddrT,data_dict['SN'],float(Tr)*self.DWT_TIME_UNITS)

            # logger.debug(self.pack_ble_dict)
                if cB_txmac.findText(AddrT)==-1:
                    cB_txmac.addItem(AddrT)
                if cB_txmac.currentText()=='ALL' or cB_txmac.currentText() == AddrT:
                    logger.debug(data_dict)
                    if self.cB_txmac_currentText!=cB_txmac.currentText():
                        self.TimeRx_dict = {}
                    self.cB_txmac_currentText = cB_txmac.currentText()
                    self.testTimeStability(AddrT+'-'+AddrR,data_dict['SN'],float(Tr)*self.DWT_TIME_UNITS)

    def testTimeStability(self,flag,sn,rx_time):#分析包时间稳定性,计算导致的距离误差
        # logger.debug(self.TimeRx_dict)
        try:
            if self.TimeRx_dict[flag]:
                self.TimeRx_dict[flag][0][0:3] = self.TimeRx_dict[flag][0][1:3]+[sn]
                self.TimeRx_dict[flag][1] = self.TimeRx_dict[flag][1][1:]+[rx_time]
                # logger.debug(self.TimeRx_dict)
                #距离精度
                logger.warning([self.TimeRx_dict[flag][0][2],self.TimeRx_dict[flag][0][1]])
                delta_time = (self.TimeRx_dict[flag][1][2]-self.TimeRx_dict[flag][1][1])/(self.TimeRx_dict[flag][0][2]-self.TimeRx_dict[flag][0][1])
                delta_time= delta_time+self.CLOCK_OVERFLOW if delta_time<-10 else delta_time
                error_time = (delta_time-self.delta_time_last[flag])*self.Velocity_Light
                if abs(delta_time)>2 or abs(error_time)>10000:
                    self.delta_time_last[flag] = delta_time
                    return

                logger.info([flag,'时间s:',rx_time,'时间差s:',delta_time,'距离精度m:',round(error_time,2)])
                content = ''.join([flag,',距离精度m: ',str(round(error_time,2))])
                SendQuene.put_nowait([0,content])
                # tB_log.append(content)
                self.delta_time_last[flag] = delta_time

                # self.average_data[flag].averageData(error_time,1)
                if delta_time<1 and ControlOrder[0]==1:
                    self.ave_time[flag] = self.average_data[flag].averageData(error_time,1)
                    self.var_time[flag] = self.average_data[flag].varianceData(error_time,1)
                    logger.info([flag,'平均精度：',self.ave_time[flag],'，标准差：',self.var_time[flag],error_time])
                try:
                    if self.uwb_average_time[flag]==1 and ControlOrder[0]==0:
                        logger.info([0,self.ave_time[flag],self.var_time[flag]])
                        DataTransmitQuene.put_nowait([0,self.ave_time[flag][0],self.ave_time[flag][1],self.var_time[flag][1]])
                        self.ave_time[flag] = self.average_data[flag].averageData(0,0)
                        self.var_time[flag] = self.average_data[flag].varianceData(0,0)
                except:
                    self.uwb_average_time[flag] = ControlOrder[0]
                self.uwb_average_time[flag] = ControlOrder[0]
                # 丢包概率
                # total_package = sn - self.TimeRx_dict[flag][0][4]
                # self.TimeRx_dict[flag][0][3] = self.TimeRx_dict[flag][0][3] + self.TimeRx_dict[flag][0][2] - self.TimeRx_dict[flag][0][1] - 1
                # loss_package_probability = self.TimeRx_dict[flag][0][3]*100/total_package
                # logger.info([flag,'总包数:',total_package,'丢包数:',self.TimeRx_dict[flag][0][3],'丢包率%:',round(loss_package_probability,2)])
                # content = ''.join([flag,',总包数:',str(total_package),',丢包率%:',str(round(loss_package_probability,2))])
                # SendQuene.put_nowait([1,content])
                # tB_log.append(content)

                loss_pack = self.test_loss_package[flag].calculateLossPackage(sn,-1)
                logger.info([flag,'总包数:',loss_pack[0],'丢包数:',loss_pack[1],'丢包率%:',loss_pack[2]])
                content = ''.join([flag,',总包数:',str(loss_pack[0]),',丢包率%:',str(loss_pack[2])])
                SendQuene.put_nowait([1,content])

        except (KeyError,Full) as Err:
            logger.error(Err,exc_info=False)
            self.delta_time_last[flag] = 0
            self.TimeRx_dict[flag] = []
            self.TimeRx_dict[flag].append([1,2,sn,0,sn])
            self.TimeRx_dict[flag].append([1,2,3])
            logger.debug(self.TimeRx_dict)
            self.test_loss_package[flag] = TestLossPackage(sn)
            self.average_data[flag] = DataAnalysis.AverageData()

    def quenePrint(self,tB_log,tB_log_2):
        while True:
            if not SendQuene.empty():
                time.sleep(0.001)
                content = SendQuene.get()
                if content[0]:
                    tB_log.append(content[1])
                else:
                    tB_log_2.append(content[1])

    def send(self,addr,order):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.info([addr,order])
        server.sendto(order,addr)
        server.close()

    def bleManeger(self):
        pass
        # global input_cnt,output_cnt
        # # logger.info(type(data))
        # # logger.info('len: '+str(len(data))+',content: '+str(data))
        # for char in data:
        #     string = ''
        #     try:
        #         string = string + chr(char)
        #     except TypeError as r:
        #         logger.info(r,exc_info=True)
        # # logger.info('len: '+str(len(data))+',content: '+string)
        # if len(data)==13:
        #     string = ''
        #     for char in data[1:]:
        #         try:
        #             string = string + chr(char)
        #             # string = string + chr(ord(char))
        #         except TypeError as r:
        #             logger.info(r,exc_info=True)
        #     logger.info(data[0])
        #     # if data[0] == 0x0b:
        #     if data[0] == 0x0b:
        #         db = PySqlite.DataBase('address_data.db')
        #         db.addRow(string,'STOCK_IN')
        #         if not db.addRow(string,'STOCK'):
        #             logger.info('重复ble标签：'+string)
        #         logger.info(string+',STOCK_IN')
        #         db.conn.close()
        #         input_cnt = input_cnt + 1
        #         content = '入库ble标签：'+string
        #         logger.info(content)
        #         tB_log.append(content)
        #     # elif data[0] == 0x0d:
        #     elif data[0] == 0x0d:
        #         db = PySqlite.DataBase('address_data.db')
        #         db.addRow(string,'STOCK_OUT')
        #         db.deleteRow('STOCK','BLE',string)
        #         logger.info(string+',STOCK_OUT')
        #         db.conn.close()
        #         output_cnt = output_cnt + 1
        #         content = '出库ble标签：'+string
        #         logger.info(content)
        #         tB_log.append(content)
        #     # elif data[0] == 0x0e:
        #     elif data[0] == 0x0e:
        #         content = '回收ble标签：'+string
        #         logger.info(content)
        #         tB_log.append(content)
        #     # elif data[0] == 0x0f:
        #     elif data[0] == 0x0f:
        #         content = '未知ble标签：'+string
        #         logger.info(content)
        #         tB_log.append(content)

    def socketExit(self):
        self.server.close()



if __name__ == '__main__':
    a=TestLossPackage(10)
    b=TestLossPackage(100)
    for i in range(100):
        a.calculateLossPackage(i+11)
        b.calculateLossPackage(i+105)
    # udp = UDPServer()
    # udp.receive(('192.168.1.253', 6788))
    #
    # i=0
    # while True:
    #     i=i+1


