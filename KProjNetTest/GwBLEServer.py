# -*- coding: utf-8 -*-
__author__ = 'ls'
import socket,struct
import ConfigFile
from Logger import logger
class GwBLEServer():
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
                self.bleReceiver(data)


    def bleReceiver(self,data):
        unpack_data = struct.unpack(">BBHI",data[0:8])
        self.pack_ble_dict['Header']=unpack_data[0]
        self.pack_ble_dict['Site']=unpack_data[1]
        self.pack_ble_dict['PackNum']=unpack_data[2]
        self.pack_ble_dict['Length']=unpack_data[3]
        self.pack_ble_dict['GWMAC']=''.join(["%02X"%(char) for char in data[8:16]])
        self.pack_ble_dict['End']=''.join(["%02X"%(char) for char in data[-2:]])
        content = ''.join(["%02X"%(char) for char in data])
        # SendQuene.put_nowait([1,content])
        # logger.info(self.pack_ble_dict)
        if self.pack_ble_dict['PackNum']*12+20 == len(data) and self.pack_ble_dict['End']=='FFEE':
            for i in range(unpack_data[2]):
                ble_data = data[i*12+16:i*12+28]
                bleAddr = ''.join(["%02X"%(char) for char in ble_data[0:7]])
                self.data_dict ={
                        'GWMAC':''.join(["%02X"%(char) for char in data[8:16]]),
                        'IP':self.udp_addr[0],
                        'bleAddr':bleAddr,
                        'Active':ble_data[7]/2**4,
                        'TagState':ble_data[7]%2**4,
                        'Cause':ble_data[7]%16,
                        'Voltage': ble_data[8],
                        'RSSI':-ble_data[11]
                    }
                # logger.info(self.data_dict)
        else:
            logger.error([self.udp_addr[0],'ble包错误：',self.pack_ble_dict])
            logger.error(['data length: ',len(data),',data: ',''.join(["%02X"%(char) for char in data])])

        AREA=4
        # if (self.data_dict['GWMAC']=='01AA2145CCF0CAAB'and self.data_dict['bleAddr']=='A171A9C7E2E790'):
        if (self.udp_addr[0]=='192.168.1.158'):
        # if (ConfigFile.ParaInit['base_station'][self.data_dict['GWMAC']][5]==AREA) and self.data_dict['bleAddr']=='A171A9C7E2E790':
        #     logger.info([self.pack_ble_dict,len(content)/2])
        #     logger.info(content)
            logger.info(self.data_dict)

if __name__ == "__main__":
    ble = GwBLEServer()
    ble.udpReceiver(('192.168.1.215',6789))