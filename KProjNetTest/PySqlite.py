# -*- coding: utf-8 -*-
__author__ = 'few'
# 创建时间 2018/3/26 10:55 
import sqlite3
from Logger import logger

class DataBase():
    def __init__(self,db_name):
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()

    def createTable(self):
        # try:
        #     self.deleteTable('ADDRESS')
        #     logger.warning('nihao add')
        # except:
        #     pass
        #     logger.warning('nihao pass')
        # else:
        #     logger.warning('nihao')
            self.cur.execute('''CREATE TABLE IF NOT EXISTS ADDRESS
                            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            IP CHAR(20) NOT NULL ,
                            PORT INT);''')
            self.cur.execute('''CREATE TABLE IF NOT EXISTS STOCK_IN
                            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            BLE CHAR(20) NOT NULL);''')
            self.cur.execute('''CREATE TABLE IF NOT EXISTS STOCK_OUT
                            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                            BLE CHAR(20) NOT NULL);''')
            self.cur.execute('''CREATE TABLE IF NOT EXISTS STOCK
                            (BLE CHAR(20) PRIMARY KEY NOT NULL);''')
            self.conn.commit()#该方法提交当前的事务。如果您未调用该方法，那么自您上一次调用 commit() 以来所做的任何动作对其他数据库连接来说是不可见的。

    def addRow(self,*para):
        if para[-1]=='ADDRESS':
            try:
                if len(para)==4:
                    if self.inquireTable(para[1],para[-1]):
                        return False
                    self.cur.execute("INSERT INTO '%s' (ID,IP,PORT) VALUES ('%d','%s','%d')" %(para[-1],para[0],para[1],para[2]))
                else:
                    if self.inquireTable(para[0],para[-1]):
                        return False
                    # self.cur.execute("INSERT INTO '%s'(IP,PORT) VALUES ('192.168.1.11',9999)" %(para[2]))
                    self.cur.execute("INSERT INTO '%s'(IP,PORT) VALUES ('%s','%d')" %(para[-1],para[0],para[1]))
            except sqlite3.IntegrityError:
                logger.info('id=%s已经存在！'%(para[0]))
        elif para[-1]=='STOCK_IN' or para[-1]=='STOCK_OUT':
            self.cur.execute("INSERT INTO '%s'(BLE) VALUES ('%s')" %(para[-1],para[0]))
        elif para[-1]=='STOCK':
            try:
                self.cur.execute("INSERT INTO '%s'(BLE) VALUES ('%s')" %(para[-1],para[0]))
            except sqlite3.IntegrityError as r:
                logger.info(r,exc_info=True)
                return False
        self.conn.commit()
        return True

    def readTable(self,table_name):
        table = self.cur.execute("SELECT id,ip,port FROM '%s'"%(table_name))
        ip_list = []
        for row in table:
            ip_list.append(row[1])
        ip_list.reverse()#该方法没有返回值，但是会对列表的元素进行反向排序。
        ip_list_temp = list(set(ip_list)) #会改变原来的排序
        ip_list_temp.sort(key=ip_list.index)#保持原来的排序
        return ip_list_temp

    def updateRow(self,id,ip,table_name):
        self.cur.execute("UPDATE '%s' set IP = '%s' where ID='%d'" %(table_name,ip,id))
        self.conn.commit()

    def deleteRow(self,table_name,key,value):
        if key=='BLE' and table_name=='STOCK':
            self.cur.execute("DELETE FROM STOCK WHERE BLE='%s'"%(value))
        # self.cur.execute("DELETE from '%s' where ID='%d'" %(table_name,id))
            self.conn.commit()

    def deleteTable(self,table_name):
        self.cur.execute("DROP TABLE '%s'"%(table_name))
        self.conn.commit()

    def inquireTable(self,ip,table_name):
        table = self.cur.execute("SELECT ip FROM '%s'"%(table_name))
        for row in table:
            if ip == row[0]:
                return True
        return False

if __name__ == "__main__":
    db = DataBase()
    # db.deleteTable()
    db.readTable()
    db.addRow('192.168.1.10',9999)
    db.addRow(2,'192.168.1.2',9999)
    db.addRow(3,'192.168.1.3',9999)
    db.addRow('192.168.1.10',9999)
    db.addRow('192.168.1.10',9999)
    # db.updateRow(2,'192.168.2.2')
    db.deleteRow(2)
    # db.readTable()
    # db.deleteTable()
    # db.readTable()
    # db.addRow(5,'192.168.1.3',9999)
    # print(db.inquireTable('192.168.1.1'))
    # db.deleteTable()
    # conn = sqlite3.connect('address_data.db')
    # c = conn.cursor()
    # # print(c.execute("table"))
    # c.execute('''CREATE TABLE IF NOT EXISTS COMPANY
    #        (ID INT PRIMARY KEY     NOT NULL,
    #        NAME           TEXT    NOT NULL,
    #        AGE            INT     NOT NULL,
    #        ADDRESS        CHAR(50),
    #        SALARY         REAL);''')
    # c.execute("INSERT INTO COMPANY (ID,NAME,AGE,ADDRESS,SALARY) \
    #   VALUES (1, 'Paul', 32, 'California', 20000.00 )");
    # c.execute("UPDATE COMPANY set SALARY = 25000.00 where ID=1")
    # # conn.commit()
    # # c.execute("DELETE from COMPANY where ID=1;")
    #
    # cursor = c.execute("SELECT id, name,AGE, address, salary  from COMPANY")
    # for row in cursor:
    #     print(len(row))
    #     print("ID = ", row[0])
    #     print("NAME = ", row[1])
    #     print("ADDRESS = ", row[2])
    #     print("ADDRESS = ", row[3])
    #     print("ADDRESS = ", row[4])
    #
    # # c.execute("DROP TABLE COMPANY")
    #
    # conn.commit()
    # conn.close()