# -*- coding: utf-8 -*-
from Logger import logger
import xlrd

ParaInit = {}

def configFile():
    try:
        data = xlrd.open_workbook('configFile.xls')#打开xls文件
    except IOError as err:
        logger.error(err,exc_info=True)#使用参数exc_info=True调用logger方法，trackback会输出到logger中。
    else:
        # table = data.sheets()[2]#选择第3个数据页
        table = data.sheet_by_name(u'ProcotolPara')#选择 ProcotolPara 数据页

        ParaInit['udp_ip'] = str(table.row_values(1)[1])
        ParaInit['udp_port'] = int(table.row_values(1)[2])
        ParaInit['mqtt_ip'] = str(table.row_values(2)[1])
        ParaInit['mqtt_port'] = int(table.row_values(2)[2])
        ParaInit['tcp_ip'] = str(table.row_values(3)[1])
        ParaInit['tcp_port'] = int(table.row_values(3)[2])


        table = data.sheet_by_name(u'BaseStation')#选择 Logger 数据页
        anchorunits = []
        BS_dict = {}
        anchorunit = []
        S_MAC = []
        for i in range(1,table.nrows):
            BS = table.row_values(i)[1:]
            BS_dict[BS[0]] = (BS[1], BS[2], BS[3], BS[4], BS[5], int(BS[6]), BS[7], BS[8])
            if BS[1]=='M':
                if len(anchorunit)!=0:
                    anchorunit.append(S_MAC)
                    anchorunits.append(anchorunit)
                    anchorunit = []
                anchorunit.append(str(BS[0]))
                anchorunit.append(str(BS[0]))
                S_MAC = []
            elif BS[1]=='S':
                S_MAC.append(str(BS[0]))
        anchorunit.append(S_MAC)
        anchorunits.append(anchorunit)
        # logger.debug(anchorunits)
        # logger.debug(BS_dict)
        Station_MAC_IP = {}
        Station_IP_MAC = {}
        MasterIP = []
        SlaveIP = []
        for k,v in BS_dict.items():
            Station_MAC_IP[k]=v[7]
            Station_IP_MAC[v[7]]=k
            if v[0]=='M':
                MasterIP.append(v[7])
            elif v[0]=='S':
                SlaveIP.append(v[7])
        ParaInit['master_ip'] = MasterIP
        ParaInit['slave_ip'] = SlaveIP
        ParaInit['station_mac_ip'] = Station_MAC_IP
        ParaInit['station_ip_mac'] = Station_IP_MAC
        ParaInit['slave_ip'] = SlaveIP
        ParaInit['base_station'] = BS_dict
        # logger.debug(Station_MAC_IP)


        # table = data.sheet_by_name(u'Parameter')#选择 ProcotolPara 数据页
        # DrawCtrl = int(table.row_values(1)[1])
        # ToAFlag = int(table.row_values(2)[1])
        # MqttFlag = int(table.row_values(3)[1])
        # TcpFlag = int(table.row_values(4)[1])
        # MqttDataType = int(table.row_values(5)[1])
        # logger.debug('DrawCtrl:%s,ToAFlag:%s,MqttFlag:%s,TcpFlag:%s,MqttDataType:%s',DrawCtrl,ToAFlag,MqttFlag,TcpFlag,MqttDataType)

        # table = data.sheet_by_name(u'AnchorIP')#选择 AnchorIP 数据页
        # i = 1
        # MasterIP = []
        # while True:
        #     try:
        #         ip = str(table.row_values(i)[1]).strip()
        #     except:
        #         break
        #     else:
        #         if ip=='':
        #             break
        #         else:
        #             i=i+1
        #             MasterIP.append(ip)
        # ParaInit['master_ip'] = MasterIP
        # logger.info(ParaInit)

configFile()




