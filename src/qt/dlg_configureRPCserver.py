#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
from ipaddress import ip_address
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtWidgets import QDialog, QLabel, QSpinBox
from PyQt5.Qt import QPushButton, QGroupBox, QLineEdit, QHBoxLayout, QFormLayout
from PyQt5.QtCore import pyqtSlot
from threads import ThreadFuns

from misc import writeToFile, readRPCfile, printDbg
from constants import rpc_File


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
        
   

class Ui_ConfigureRPCserverDlg(object):
    def setupUi(self, ConfigureRPCserverDlg):
        ConfigureRPCserverDlg.setModal(True)
        ## -- Layout
        self.layout = QGroupBox(ConfigureRPCserverDlg)
        self.layout.setTitle("Local Pivx-Cli wallet Configuration")
        self.layout.setContentsMargins(80, 30, 10, 10)
        form = QFormLayout(ConfigureRPCserverDlg)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        ## -- ROW 1
        line1 = QHBoxLayout()
        self.edt_rpcIp = QLineEdit()
        self.edt_rpcIp.setToolTip("rpc server (local wallet) IP address\n-- example [IPv4] 88.172.23.1\n-- example [IPv6] 2001:db8:85a3::8a2e:370:7334")
        self.edt_rpcIp.setText(ConfigureRPCserverDlg.rpc_ip)
        line1.addWidget(self.edt_rpcIp)
        line1.addWidget(QLabel("IP Port"))
        self.edt_rpcPort = QSpinBox()
        self.edt_rpcPort.setRange(1, 65535)
        self.edt_rpcPort.setValue(ConfigureRPCserverDlg.rpc_port)
        self.edt_rpcPort.setFixedWidth(180)
        line1.addWidget(self.edt_rpcPort)
        form.addRow(QLabel("IP Address"), line1)   
        ## -- ROW 2
        self.edt_rpcUser = QLineEdit()
        self.edt_rpcUser.setText(ConfigureRPCserverDlg.rpc_user)
        form.addRow(QLabel("RPC Username"), self.edt_rpcUser)        
        ## -- ROW 3
        self.edt_rpcPassword = QLineEdit()
        self.edt_rpcPassword.setText(ConfigureRPCserverDlg.rpc_password)
        form.addRow(QLabel("RPC Password"), self.edt_rpcPassword)        
        ## -- ROW 4
        hBox = QHBoxLayout()
        self.buttonCancel = QPushButton("Cancel")
        self.buttonCancel.clicked.connect(lambda: self.onButtonCancel(ConfigureRPCserverDlg))
        hBox.addWidget(self.buttonCancel)
        self.buttonSave = QPushButton("Save")
        self.buttonSave.clicked.connect(lambda: self.onButtonSave(ConfigureRPCserverDlg))
        hBox.addWidget(self.buttonSave)
        form.addRow(hBox)
        ## Set Layout
        self.layout.setLayout(form)
        ConfigureRPCserverDlg.setFixedSize(self.layout.sizeHint())
        
        
    @pyqtSlot()
    def onButtonSave(self, main_dlg):
        main_dlg.rpc_ip = ip_address(self.edt_rpcIp.text().strip()).compressed
        main_dlg.rpc_port = int(self.edt_rpcPort.value())
        main_dlg.rpc_user = self.edt_rpcUser.text()
        main_dlg.rpc_password = self.edt_rpcPassword.text()
        conf = {}
        conf["rpc_ip"] = main_dlg.rpc_ip
        conf["rpc_port"] = main_dlg.rpc_port
        conf["rpc_user"] = main_dlg.rpc_user
        conf["rpc_password"] = main_dlg.rpc_password
        
        # Update File
        writeToFile(conf, rpc_File)
        
        # Update current RPC Server
        main_dlg.main_wnd.mainWindow.rpcClient = None
        main_dlg.main_wnd.mainWindow.rpcConnected = False
        printDbg("Trying to connect to RPC server [%s]:%s" % (conf["rpc_ip"], str(conf["rpc_port"])))
        self.runInThread = ThreadFuns.runInThread(main_dlg.main_wnd.mainWindow.updateRPCstatus, (), main_dlg.main_wnd.mainWindow.updateRPCled)
        main_dlg.close()
        
       
        
    @pyqtSlot()
    def onButtonCancel(self, main_wnd):
        main_wnd.close()