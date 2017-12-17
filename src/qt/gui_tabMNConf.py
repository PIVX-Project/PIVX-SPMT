#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.Qt import QLabel, QFormLayout, QSpinBox
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QGroupBox, QVBoxLayout
from PyQt5.QtWidgets import QLineEdit



class TabMNConf_gui(QWidget):
    def __init__(self, masternode_alias=None, *args, **kwargs):
        QWidget.__init__(self)
        self.initConfigForm(masternode_alias)
        ###-- Compose tab2 layout
        mainVertical2 = QVBoxLayout()
        mainVertical2.setSpacing(10)
        mainVertical2.addWidget(self.configForm)      
        vBox = QVBoxLayout()
        vBox.addStretch(1)
        mainVertical2.addLayout(vBox)
        mainVertical2.addLayout(self.footer)
        self.setLayout(mainVertical2)       
        
    
        
        
    def clearConfigForm(self):
        self.edt_name.setText('')
        self.edt_rpcIp_byte1.setValue(127)
        self.edt_rpcIp_byte2.setValue(0)
        self.edt_rpcIp_byte3.setValue(0)
        self.edt_rpcIp_byte4.setValue(1)
        self.edt_rpcPort.setValue(51472)
        self.edt_mnPrivKey.setText('')
        self.edt_hwAccount.setValue(0)
        self.edt_address.setText('')
        self.edt_spath.setValue(0)
        self.edt_pubKey.setText('')
        self.edt_txid.setText('')
        self.edt_txidn.setValue(0)
        self.configForm.setTitle('New Masternode')
        
        
        
        
    def fillConfigForm(self, masternode):
        ip_bytes = [int(x) for x in masternode['ip'].split('.')]
        self.edt_name.setText(masternode['name'])
        self.edt_rpcIp_byte1.setValue(ip_bytes[0])
        self.edt_rpcIp_byte2.setValue(ip_bytes[1])
        self.edt_rpcIp_byte3.setValue(ip_bytes[2])
        self.edt_rpcIp_byte4.setValue(ip_bytes[3])
        self.edt_rpcPort.setValue(masternode['port'])
        self.edt_mnPrivKey.setText(masternode['mnPrivKey'])
        self.edt_hwAccount.setValue(masternode['hwAcc'])
        self.edt_address.setText(masternode['collateral'].get('address'))
        self.edt_spath.setValue(masternode['collateral'].get('spath'))
        self.edt_pubKey.setText(masternode['collateral'].get('pubKey'))
        self.edt_txid.setText(masternode['collateral'].get('txid'))
        self.edt_txidn.setValue(masternode['collateral'].get('txidn'))
        self.configForm.setTitle("Edit Masternode") 
         
        
        
        
        
        
    def initConfigForm(self, masternode_alias=None):
        self.configForm = QGroupBox()
        if not masternode_alias:
            self.configForm.setTitle("New Masternode")
        else:
            self.configForm.setTitle("Edit Masternode [%s]" % masternode_alias)
            
        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(13)
        ##--- ROW 1
        self.edt_name = QLineEdit()
        self.edt_name.setToolTip("masternode Alias.\n-- example: My Masternode 1")
        layout.addRow(QLabel("Name"), self.edt_name)
        ##--- ROW 2
        line1 = QHBoxLayout()
        self.edt_rpcIp_byte1 = QSpinBox()
        self.edt_rpcIp_byte1.setRange(0, 255)
        self.edt_rpcIp_byte1.setValue(127)
        self.edt_rpcIp_byte1.setFixedWidth(50)
        self.edt_rpcIp_byte1.setToolTip("remote masternode ip address \n-- example: 66.171.50.151")
        line1.addWidget(self.edt_rpcIp_byte1)
        line1.addWidget(QLabel("."))
        self.edt_rpcIp_byte2 = QSpinBox()
        self.edt_rpcIp_byte2.setRange(0, 255)
        self.edt_rpcIp_byte2.setValue(0)
        self.edt_rpcIp_byte2.setFixedWidth(50)
        self.edt_rpcIp_byte2.setToolTip("remote masternode ip address \n-- example: 66.171.50.151")
        line1.addWidget(self.edt_rpcIp_byte2)
        line1.addWidget(QLabel("."))
        self.edt_rpcIp_byte3 = QSpinBox()
        self.edt_rpcIp_byte3.setRange(0, 255)
        self.edt_rpcIp_byte3.setValue(0)
        self.edt_rpcIp_byte3.setFixedWidth(50)
        self.edt_rpcIp_byte3.setToolTip("remote masternode ip address \n-- example: 66.171.50.151")
        line1.addWidget(self.edt_rpcIp_byte3)
        line1.addWidget(QLabel("."))
        self.edt_rpcIp_byte4 = QSpinBox()
        self.edt_rpcIp_byte4.setRange(0, 255)
        self.edt_rpcIp_byte4.setValue(1)
        self.edt_rpcIp_byte4.setFixedWidth(50)
        self.edt_rpcIp_byte4.setToolTip("remote masternode ip address \n-- example: 66.171.50.151")
        line1.addWidget(self.edt_rpcIp_byte4)
        line1.addStretch(1)
        line1.addWidget(QLabel("IP Port"))
        self.edt_rpcPort = QSpinBox()
        self.edt_rpcPort.setRange(1, 65535)
        self.edt_rpcPort.setValue(51472)
        self.edt_rpcPort.setToolTip("remote masternode tcp port \n-- example: 51472")
        self.edt_rpcPort.setFixedWidth(180)
        line1.addWidget(self.edt_rpcPort)
        layout.addRow(QLabel("IP Address"), line1)
        ##--- ROW 3
        self.edt_mnPrivKey = QLineEdit()
        self.edt_mnPrivKey.setToolTip("masternode private key \n-- output of 'masternode genkey' command")
        self.btn_genKey = QPushButton("Generate")
        self.btn_genKey.setToolTip("generate masternode privKey from hardware wallet")
        hBox2 = QHBoxLayout()
        hBox2.addWidget(self.edt_mnPrivKey)
        hBox2.addWidget(self.btn_genKey)
        #hBox2.setContentsMargins(0, 0, 0, 5)
        layout.addRow(QLabel("MN Priv Key"), hBox2)
        
        ##--- ROW 4/5
        hBox2 = QHBoxLayout()
        self.edt_hwAccount = QSpinBox()
        self.edt_hwAccount.setFixedWidth(50)
        self.edt_hwAccount.setToolTip("account number of the hardware wallet.\nIf unsure put 0")
        self.edt_hwAccount.setValue(0)
        hBox2.addWidget(self.edt_hwAccount)
        hBox2.addStretch(1)
        hBox2.addWidget(QLabel("<i>Collateral</i>"))
        layout.addRow(QLabel("Account HW"), hBox2)
        hBox3 = QHBoxLayout()
        self.edt_address = QLineEdit()
        self.edt_address.setToolTip("the address containing 10000 PIV")
        self.edt_spath = QSpinBox()
        self.edt_spath.setToolTip("BIP44 spath for the address")
        self.edt_spath.setFixedWidth(100)
        self.edt_spath.setValue(0)
        self.edt_spath.setEnabled(False)
        self.btn_addressToSpath = QPushButton(">>")
        self.btn_addressToSpath.setToolTip("find spath_id and public key of address with hardware device")
        hBox3.addWidget(self.edt_address)
        hBox3.addWidget(self.btn_addressToSpath)
        hBox3.addWidget(QLabel("spath_id"))
        hBox3.addWidget(self.edt_spath)
        layout.addRow(QLabel("PIVX Address"), hBox3)
        
        ##--- ROW 6
        self.edt_pubKey = QLineEdit()
        self.edt_pubKey.setToolTip("public key corresponding to address")
        self.edt_pubKey.setEnabled(False)
        layout.addRow(QLabel("Public Key"), self.edt_pubKey)
        
        ##--- ROW 7
        hBox5 = QHBoxLayout()
        self.btn_findTxid = QPushButton("Lookup")
        self.btn_findTxid.setToolTip("look for txid and txidn on explorer")
        hBox5.addWidget(self.btn_findTxid)
        hBox5.addWidget(QLabel("/"))
        self.btn_editTxid = QPushButton("Edit")
        self.btn_editTxid.setToolTip("edit txid and txidn manually")
        hBox5.addWidget(self.btn_editTxid)
        hBox5.addWidget(QLabel("txid"))        
        self.edt_txid = QLineEdit()
        self.edt_txid.setToolTip("txid for the collateral")
        self.edt_txid.setEnabled(False)
        hBox5.addWidget(self.edt_txid)
        hBox5.addWidget(QLabel("txidn"))
        self.edt_txidn = QSpinBox()
        self.edt_txidn.setFixedWidth(50)
        self.edt_txidn.setToolTip("txidn for the collateral")
        self.edt_txidn.setEnabled(False)
        hBox5.addWidget(self.edt_txidn)
        layout.addRow(QLabel("Transaction"), hBox5)
        
        self.configForm.setLayout(layout)
        
        self.footer = QHBoxLayout()
        self.footer.addStretch(1)
        self.btn_cancelMNConf = QPushButton('Cancel')
        self.btn_cancelMNConf.setToolTip("cancel changes and go back to main list")
        self.footer.addWidget(self.btn_cancelMNConf)
        self.btn_saveMNConf = QPushButton('Save')
        self.btn_saveMNConf.setToolTip("save configuration and go back to main list")
        self.footer.addWidget(self.btn_saveMNConf)
            