#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtWidgets import QDialog, QLabel, QSpinBox
from PyQt5.Qt import QPushButton, QGroupBox, QLineEdit, QHBoxLayout, QFormLayout
from PyQt5.QtCore import pyqtSlot

from misc import writeRPCfile, readRPCfile


class ConfigureRPCserver_dlg(QDialog):
    def __init__(self, main_wnd):
        QDialog.__init__(self, parent=main_wnd)
        self.main_wnd = main_wnd
        self.setWindowTitle('RPC Server Configuration')
        self.loadRPCfile()
        self.initUI()
        
        
    def initUI(self):
        self.ui = Ui_ConfigureRPCserverDlg()
        self.ui.setupUi(self)
        
        
    def loadRPCfile(self):
        self.rpc_ip, self.rpc_port, self.rpc_user, self.rpc_password = readRPCfile()
        
        self.rpc_ipbytes = [int(x) for x in self.rpc_ip.split('.')]
        
        
   

class Ui_ConfigureRPCserverDlg(object):
    def setupUi(self, ConfigureRPCserverDlg):
        ConfigureRPCserverDlg.setModal(True)
        
        self.layout = QGroupBox(ConfigureRPCserverDlg)
        self.layout.setTitle("Local Pivx-Cli wallet Configuration")
        self.layout.setContentsMargins(80, 30, 10, 10)
        form = QFormLayout(ConfigureRPCserverDlg)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        ##-- ROW 1
        line1 = QHBoxLayout()
        self.edt_rpcIp_byte1 = QSpinBox()
        self.edt_rpcIp_byte1.setRange(0, 255)
        self.edt_rpcIp_byte1.setValue(ConfigureRPCserverDlg.rpc_ipbytes[0])
        self.edt_rpcIp_byte1.setFixedWidth(50)
        line1.addWidget(self.edt_rpcIp_byte1)
        line1.addWidget(QLabel("."))
        self.edt_rpcIp_byte2 = QSpinBox()
        self.edt_rpcIp_byte2.setRange(0, 255)
        self.edt_rpcIp_byte2.setValue(ConfigureRPCserverDlg.rpc_ipbytes[1])
        self.edt_rpcIp_byte2.setFixedWidth(50)
        line1.addWidget(self.edt_rpcIp_byte2)
        line1.addWidget(QLabel("."))
        self.edt_rpcIp_byte3 = QSpinBox()
        self.edt_rpcIp_byte3.setRange(0, 255)
        self.edt_rpcIp_byte3.setValue(ConfigureRPCserverDlg.rpc_ipbytes[2])
        self.edt_rpcIp_byte3.setFixedWidth(50)
        line1.addWidget(self.edt_rpcIp_byte3)
        line1.addWidget(QLabel("."))
        self.edt_rpcIp_byte4 = QSpinBox()
        self.edt_rpcIp_byte4.setRange(0, 255)
        self.edt_rpcIp_byte4.setValue(ConfigureRPCserverDlg.rpc_ipbytes[3])
        self.edt_rpcIp_byte4.setFixedWidth(50)
        line1.addWidget(self.edt_rpcIp_byte4)
        line1.addWidget(QLabel("IP Port"))
        self.edt_rpcPort = QSpinBox()
        self.edt_rpcPort.setRange(1, 65535)
        self.edt_rpcPort.setValue(ConfigureRPCserverDlg.rpc_port)
        self.edt_rpcPort.setFixedWidth(180)
        line1.addWidget(self.edt_rpcPort)
        form.addRow(QLabel("IP Address"), line1)
        
        ##-- ROW 2
        self.edt_rpcUser = QLineEdit()
        self.edt_rpcUser.setText(ConfigureRPCserverDlg.rpc_user)
        form.addRow(QLabel("RPC Username"), self.edt_rpcUser)
        
        ##-- ROW 3
        self.edt_rpcPassword = QLineEdit()
        self.edt_rpcPassword.setText(ConfigureRPCserverDlg.rpc_password)
        form.addRow(QLabel("RPC Password"), self.edt_rpcPassword)
        
        ##-- ROW 4
        hBox = QHBoxLayout()
        self.buttonCancel = QPushButton("Cancel")
        self.buttonCancel.clicked.connect(lambda: self.onButtonCancel(ConfigureRPCserverDlg))
        hBox.addWidget(self.buttonCancel)
        self.buttonSave = QPushButton("Save")
        self.buttonSave.clicked.connect(lambda: self.onButtonSave(ConfigureRPCserverDlg))
        hBox.addWidget(self.buttonSave)
        form.addRow(hBox)

        self.layout.setLayout(form)
        ConfigureRPCserverDlg.setFixedSize(self.layout.sizeHint())
        
        
    @pyqtSlot()
    def onButtonSave(self, main_dlg):
        try:
            main_dlg.rpc_ip = "%d.%d.%d.%d" % (self.edt_rpcIp_byte1.value(), self.edt_rpcIp_byte2.value(), self.edt_rpcIp_byte3.value(), self.edt_rpcIp_byte4.value())
            main_dlg.rpc_port = int(self.edt_rpcPort.value())
            main_dlg.rpc_user = self.edt_rpcUser.text()
            main_dlg.rpc_password = self.edt_rpcPassword.text()
            conf = {}
            conf["rpc_ip"] = main_dlg.rpc_ip
            conf["rpc_port"] = main_dlg.rpc_port
            conf["rpc_user"] = main_dlg.rpc_user
            conf["rpc_password"] = main_dlg.rpc_password
            
            # Update File
            writeRPCfile(conf)
            
            # Update current RPC Server
            main_dlg.main_wnd.mainWindow.rpcClient = None
            main_dlg.main_wnd.mainWindow.rpcConnected = False
            main_dlg.main_wnd.mainWindow.updateRPCstatus(None)
            main_dlg.main_wnd.mainWindow.updateRPCled()
            
        except Exception as e:
            print(e)
        
        main_dlg.close()
       
        
    @pyqtSlot()
    def onButtonCancel(self, main_wnd):
        main_wnd.close()