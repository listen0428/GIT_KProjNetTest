# -*- coding: utf-8 -*-
__author__ = 'few'
# 创建时间 2018/3/4 19:16
from PyQt5 import QtWidgets, QtGui,QtCore
import sys,time,socket,struct,pickle,datetime
from ui_BurnControl import Ui_Test_Prj1    # 导入生成form.py里生成的类
import UDPServer
import PySqlite
import threading,re
from Logger import logger
import ConfigFile

GMT_FORMAT = '%Y-%m-%d %X'
class mywindow(QtWidgets.QWidget,Ui_Test_Prj1):
    def __init__(self):
        super(mywindow,self).__init__()
        self.udp_server_en = False
        self.write_count = 0
        self.log_data = ''
        self.upd_log_en = False
        self.client_address = ('127.0.0.1', 1111)
        # self.order_list = ['ble入库','ble出库','ble烧写','ble复位','uwb烧写','uwb复位']
        self.order_dict = {'ble入库':'0AFF',
                           'ble出库':'0A55',
                           'ble烧写':'FA02',
                           'ble复位':'FAF2',
                           'uwb烧写':'FA01',
                           'uwb复位为主':'FAF1A0',
                           'uwb复位为从':'FAF1A1'}
        self.order_dict_exchange = {v:k for k,v in self.order_dict.items()}#key和value交换

    def initSetup(self):
        self.cB_ip.addItems(socket.gethostbyname_ex(socket.gethostname())[2])
        self.cB_ip.addItem('127.0.0.1')
        self.cB_order.addItems(self.order_dict)
        self.rB_byte.setChecked(True)
        self.lE_port.completer()
        self.lE_port_2.completer()
        self.lE_incnt.setText('0')
        self.lE_outcnt.setText('0')
        self.window().setWindowTitle('网关测试软件')
        self.lE_port.setText(str(ConfigFile.ParaInit['udp_port']))
        self.lE_port_2.setText('1111')
        self.tE_send.setPlainText('0AFF')
        self.tB_log.document().setMaximumBlockCount(1000)#设置文本最大长度
        self.tB_log_2.document().setMaximumBlockCount(1000)#设置文本最大长度
        self.cB_txmac.addItem('ALL')
        self.cB_ip_2.addItem('ALL')
        self.lE_avenum.setText(str(0))
        self.lE_avetime.setText(str(0.000))
        self.lE_avetime_2.setText(str(0.000))
        self.initDataBase()

    def initDataBase(self):
        db = PySqlite.DataBase('address_data')
        db.createTable()#数据库里面没有ip，所以不用读
        # try:
        #     UDPServer.Tx_IP_Addr = db.readTable('ADDRESS')
        #     logger.info(UDPServer.Tx_IP_Addr)
        # except:
        #     pass
        self.cB_ip_2.addItems(UDPServer.Tx_IP_Addr)
        logger.info(UDPServer.Tx_IP_Addr)
        db.conn.close()

    def onActivated(self,text):
        logger.info(self.cB_ip.currentText())

    #定义槽函数
    def uwbBurn(self):
        logger.info('更新uwb程序...')
        self.udpSend('FA01')

    def bleBurn(self):
        logger.info('更新ble程序...')
        self.udpSend('FA02')

    def sendString(self):
        pass
    def sendByte(self):
        pass

    def udpOrder(self):
        send_content = self.cB_order.currentText()
        self.tE_send.setText(self.order_dict[send_content])
        logger.info(self.order_dict[send_content])

    def udpSend(self):
        data = self.tE_send.toPlainText()
        try:
            order = self.order_dict_exchange[data]
        except KeyError as reason:
            logger.info(reason)
        else:
            time_now =  str(time.strftime(GMT_FORMAT,time.localtime()))
            context =  '时间：'+time_now+'-'*5+order+'-'*5
            if data == '0AFF':
                UDPServer.input_cnt = 0
                self.lE_incnt.setText(str(UDPServer.input_cnt))
            elif data == '0A55':
                UDPServer.output_cnt = 0
                self.lE_incnt.setText(str(UDPServer.output_cnt))
            self.tB_log.append(context)
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_address = self.client_address
        # if self.chB_allip.isChecked():
        if self.cB_ip_2.currentText()=='ALL':
            if UDPServer.Tx_IP_Addr==[]:
                logger.info('发送IP列表为空！')
                self.tB_log.append('发送IP列表为空！')
            for current_ip in UDPServer.Tx_IP_Addr:
                client_address = (current_ip,self.client_address[1])
                self.tB_log.append(str(client_address))
                logger.info([client_address,data])
                if self.rB_string.isChecked():#字符串格式发送
                    server.sendto(data.encode(),client_address)
                elif self.rB_byte.isChecked():#16进制发送
                    data_hex = []
                    for i in range(1,len(data),2):
                        try:
                            data_hex.append(int(data[i-1:i+1],16))
                        except ValueError:
                            logger.error('输入值异常！')
                            server.close()
                            return


                    data_pack = struct.pack('%dB'%len(data_hex),*data_hex)
                    logger.info('data_pack:'+str(data_pack))
                    server.sendto(data_pack,client_address)
                time.sleep(2)
        else:
            client_address = (self.cB_ip_2.currentText(),self.client_address[1])
            logger.info([client_address,data])
            self.tB_log.append(str(client_address))
            if self.rB_string.isChecked():#字符串格式发送
                server.sendto(data.encode(),client_address)
            elif self.rB_byte.isChecked():#16进制发送
                data_hex = []
                for i in range(1,len(data),2):
                    try:
                        data_hex.append(int(data[i-1:i+1],16))
                    except ValueError:
                        logger.error('输入值异常！')
                        server.close()
                        return


                data_pack = struct.pack('%dB'%len(data_hex),*data_hex)
                logger.info('data_pack:'+str(data_pack))
                server.sendto(data_pack,client_address)
        server.close()

    def udpBegin(self):
        self.addr_recv = (str(self.cB_ip.currentText()),int(self.lE_port.text()))
        logger.info(self.addr_recv)
        logger.info(UDPServer.upd_en)
        if UDPServer.upd_en:
            self.pB_udpbegin.setEnabled(False)#按钮不使能
            self.cB_ip.setEnabled(True)
            UDPServer.upd_en = False
            self.pB_udpbegin.setText("udp打开")
        else:
            #启动udp服务器
            UDPServer.upd_en = True
            self.udp_server_recv = UDPServer.UDPServer()

            t1 = threading.Thread(target=self.udp_server_recv.receive,
                                      args=(self.addr_recv,self.pB_udpbegin,self.cB_ip,self.cB_ip_2,self.tB_log,self.tB_log_2,self.cB_txmac,))
            t1.setDaemon(True)
            t1.start()
            self.cB_ip.setEnabled(False)
            self.pB_udpbegin.setText("udp关闭")

            t2 = threading.Thread(target=self.queneDataReceive,args=())#加逗号有问题，感觉每个地方的用法都不一样
            t2.setDaemon(True)
            t2.start()

    def udpSet(self):
        ip = str(self.cB_ip_2.currentText())
        if ip =='ALL':
            return
        result = re.search('(^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',ip)
        if result:
            if result.span()[1]==len(ip):
                for temp in re.split('\.',ip):
                    if int(temp)>256:
                        result = False
            else:
                result = False
        time_now =  str(time.strftime(GMT_FORMAT,time.localtime()))
        if result:
            self.client_address = (str(self.cB_ip_2.currentText()),int(self.lE_port_2.text()))
            logger.info('设置udp目标:'+str(self.client_address))
            context =  '时间：'+time_now+'，设置udp目标为'+str(self.client_address)+'\n'
        else:
            logger.info('ip地址格式异常,请重新输入！')
            context =  '时间：'+time_now+'，ip地址格式异常,请重新输入！'+'\n'
        self.tB_log.append(context)

        if self.client_address[0] not in UDPServer.Tx_IP_Addr:#当前只考虑IP，不考虑port
            db = PySqlite.DataBase('address_data')
            if db.addRow(self.client_address[0],self.client_address[1],'ADDRESS'):
                logger.info('addItem')
                self.cB_ip_2.addItem(self.client_address[0])
            db.conn.close()
    def autoComp(self):
        pass

    def clearLog(self):
        self.tE_log.clear()
        self.tB_log.clear()
        self.tB_log_2.clear()

    def uwbAveTime(self):
        if UDPServer.ControlOrder[0]:
            UDPServer.ControlOrder[0]=0
            self.pB_avetime.setText('开始统计')
        else:
            UDPServer.ControlOrder[0]=1
            self.pB_avetime.setText('结束统计')

    def queneDataReceive(self):
        while True:
            self.pB_avetime.setEnabled(False) if self.cB_txmac.currentText()=='ALL' else self.pB_avetime.setEnabled(True)
            if not UDPServer.DataTransmitQuene.empty():
                data_list = UDPServer.DataTransmitQuene.get()
                if data_list[0]==0:
                    self.lE_avenum.setText(str(data_list[1]))
                    self.lE_avetime.setText(str(round(data_list[2],3)))
                    self.lE_avetime_2.setText(str(round(data_list[3]**0.5,3)))
                logger.info(data_list)

    def recvLog(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind(self.addr_log)
        while True:
            if self.upd_log_en:
                data,udp_addr = server.recvfrom(8192)
                # print(struct.unpack(">L",data[0:4]))#udp日志格式，前4字符为长度，后面的内容
                # print((pickle.loads(data[4:])))
                # print(self.upd_log_en)
                self.log_data = (str(pickle.loads(data[4:])['msg']))
            else:
                server.close()
                break

    def bleIn(self):
        logger.info('ble标签入库...')
        self.udpSend('0AFF')
        UDPServer.input_cnt = 0
        self.lE_incnt.setText(str(UDPServer.input_cnt))
        time_now =  str(time.strftime(GMT_FORMAT,time.localtime()))
        context =  '时间：'+time_now+'-'*5+'入库'+'-'*5
        self.tB_log.append(context)

    def bleOut(self):
        logger.info('ble标签出库...')
        self.udpSend('0A55')
        UDPServer.output_cnt = 0
        self.lE_outcnt.setText(str(UDPServer.output_cnt))
        time_now =  str(time.strftime(GMT_FORMAT,time.localtime()))
        context =  '时间：'+time_now+'-'*5+'出库'+'-'*5
        self.tB_log.append(context)

    def cntUpdated(self):
        self.lE_incnt.setText(str(UDPServer.input_cnt))
        self.lE_outcnt.setText(str(UDPServer.output_cnt))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = mywindow()
    window.setupUi(window)
    window.initSetup()
    window.show()
    sys.exit(app.exec_())
