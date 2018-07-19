# -*- coding: utf-8 -*-
from Logger import logger
import xlrd

ParaInit = {}
DrawCtrl = 0

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


    table = data.sheet_by_name(u'Parameter')#选择 ProcotolPara 数据页
    DrawCtrl = int(table.row_values(1)[1])
    ToAFlag = int(table.row_values(2)[1])
    MqttFlag = int(table.row_values(3)[1])
    TcpFlag = int(table.row_values(4)[1])
    MqttDataType = int(table.row_values(5)[1])
    logger.debug('DrawCtrl:%s,ToAFlag:%s,MqttFlag:%s,TcpFlag:%s,MqttDataType:%s',DrawCtrl,ToAFlag,MqttFlag,TcpFlag,MqttDataType)




