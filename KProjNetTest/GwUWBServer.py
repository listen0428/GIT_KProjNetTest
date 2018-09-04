__author__ = 'ls'
import socket,struct
import ConfigFile
import time
from Logger import logger
class GwUWBServer():
    DWT_TIME_UNITS = 1.565e-11
    def __init__(self):
        self.pack_ble_dict ={}

    def udpReceiver(self,addr):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            server.bind(addr)
        except OSError as r:
            logger.error(r,exc_info=True)
            logger.error('警告：端口%d被占用！'%(addr[1]))
            return
        server.settimeout(2)#设置套接字超时时间，单位为s

        while True:
            try:
                data,self.udp_addr = server.recvfrom(1024)
                # logger.info(['data length: ',len(data),',data: ',''.join(["%02X"%(char) for char in data])])
            except socket.timeout :
                logger.error(socket.timeout,exc_info=0)
                # pass
            else:
                self.uwbReceiver(data,self.udp_addr[0])


    def uwbReceiver(self,data,udp_addr):
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
                        # 'FirstPathPower':FirstPathPower,
                        # 'ReceiverPower':ReceiverPower
                    }
                    if AddrT=="" or AddrT=='10205F1C100001A3':#分析定位包时间稳定性
                        logger.debug(data_dict)
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
                        # 'FirstPathPower':FirstPathPower,
                        # 'ReceiverPower':ReceiverPower
                    }
                    # logger.debug(data_dict)
                logger.debug(data_dict)
                # if AddrT!="10205F1C1000014C" and AddrT!="10205F1C1000046B":#分析定位包时间稳定性
                #     logger.debug(data_dict)
                    # self.testTimeStability('R-'+AddrR+',T-'+AddrT,data_dict['SN'],float(Tr)*self.DWT_TIME_UNITS)


if __name__ == "__main__":
    uwb = GwUWBServer()
    uwb.udpReceiver(('192.168.1.252',6788))