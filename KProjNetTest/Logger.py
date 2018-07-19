# -*- coding: utf-8 -*-

import logging #日志记录
from logging.handlers import RotatingFileHandler,DatagramHandler
import xlrd
import sys

class Logger():
    def __init__(self):
        self.udp_ip = '127.0.0.1'
        self.udp_port = 3333
        self.log_type = 0
        self.log_level = logging.DEBUG
        self.logger = logging.getLogger()
        self.logger.setLevel(self.log_level)
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
        # self.formatter = logging.Formatter('%(asctime)s - %(message)s')
        self.paraRead()

    def paraRead(self):
        console_handler = self.consoleHandler()
        try:
            data = xlrd.open_workbook('configFile.xls')#打开xls文件
        except IOError as err:
            self.logger.error(err,exc_info=True)#使用参数exc_info=True调用logger方法，trackback会输出到logger中。
            sys.exit(0)
        else:
            # table = data.sheets()[2]#选择第3个数据页
            table = data.sheet_by_name(u'Logger')#选择 Logger 数据页
            self.log_type = int(table.row_values(1)[1])
            self.log_level = int(table.row_values(2)[1])

        self.logger.info('log初始化设置')
        self.logger.removeHandler(console_handler)

    def logSetup(self):
        if self.log_type == 0:
            self.consoleHandler()
        elif self.log_type == 1:
            self.fileHandler()
        elif self.log_type == 2:
            self.rFileHandler()
        elif self.log_type == 3:
            self.rFileHandler()
            self.consoleHandler()
        else:
            self.udpHandler()
        return self.logger

    def consoleHandler(self):
        console_handler = logging.StreamHandler()#在控制台打印出日志
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
        return console_handler

    def fileHandler(self):
        file_handler = logging.FileHandler('logging.log')#在文本中打印日志
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def rFileHandler(self):
        # 定义RotatingFileHandler，参数配置最多备份5个日志文件，每个日志文件最大10M
        rFile_thandler = RotatingFileHandler('rlogging.log',maxBytes=20*1024*1024,backupCount=5)
        rFile_thandler.setLevel(self.log_level)
        rFile_thandler.setFormatter(self.formatter)
        self.logger.addHandler(rFile_thandler)

    def udpHandler(self):
        udp_handler = DatagramHandler('127.0.0.1',3333)
        udp_handler.setLevel(self.log_level)
        udp_handler.setFormatter(self.formatter)
        self.logger.addHandler(udp_handler)

logger = Logger().logSetup()