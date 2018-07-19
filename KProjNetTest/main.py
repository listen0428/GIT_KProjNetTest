cd# -*- coding: utf-8 -*-
__author__ = 'few'
# 创建时间 2018/3/16 11:36


from PyQt5 import QtWidgets, QtGui,QtCore
import sys,time,socket,struct,pickle
from ui_BurnControl import Ui_Test_Prj1    # 导入生成form.py里生成的类
import UDPServer
import threading
from Logger import logger
from InterfaceControl import mywindow

# pyinstaller -F -w main.py
# pyinstaller -F -w MainBegin.py --hidden-import=queue --paths E:\Qt\Qt5.10.1\Tools\QtCreator\bin
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = mywindow()
    window.setupUi(window)
    window.initSetup()
    window.show()
    sys.exit(app.exec_())