# -*- coding: utf-8 -*-
__author__ = 'few'
# 创建时间 2018/3/16 11:36


from PyQt5 import QtWidgets, QtGui,QtCore
import sys
from Logger import logger
from InterfaceControl import mywindow

# pyinstaller -F -w MainBegin.py

if __name__ == '__main__':
    logger.warning('Hello,ls')
    app = QtWidgets.QApplication(sys.argv)
    window = mywindow()
    window.setupUi(window)
    window.initSetup()
    window.show()
    sys.exit(app.exec_())