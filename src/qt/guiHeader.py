#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtCore import Qt
from PyQt5.Qt import QLabel, QGridLayout, QHBoxLayout, QComboBox, QWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPixmap, QFont

class GuiHeader(QWidget):
    def __init__(self, caller, *args, **kwargs):
        QWidget.__init__(self)
        myFont = QFont("Times", italic=True)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # --- 1) Check Box
        self.centralBox = QGridLayout()
        self.centralBox.setContentsMargins(0, 0, 0, 5)
        # --- 1a) Select & Check RPC
        label1 = QLabel("PIVX server")
        self.centralBox.addWidget(label1, 0, 0)
        self.rpcClientsBox = QComboBox()
        self.rpcClientsBox.setToolTip("Select RPC server.\nLocal must be configured.")
        rpcClients = ["Local Wallet"]
        self.rpcClientsBox.addItems(rpcClients)
        self.centralBox.addWidget(self.rpcClientsBox, 0, 1)
        self.button_checkRpc = QPushButton("Connect")
        self.button_checkRpc.setToolTip("try to connect to RPC server")
        self.button_checkRpc.clicked.connect(caller.onCheckRpc)
        self.centralBox.addWidget(self.button_checkRpc, 0, 2)
        self.rpcLed = QLabel()
        self.rpcLed.setToolTip("status: %s" % caller.rpcStatusMess)
        self.rpcLed.setPixmap(caller.ledGrayH_icon)
        self.centralBox.addWidget(self.rpcLed, 0, 3)
        label2 = QLabel("Last Ping Block:")
        self.centralBox.addWidget(label2, 0, 4)
        self.lastBlockLabel = QLabel()
        self.lastBlockLabel.setFont(myFont)
        self.centralBox.addWidget(self.lastBlockLabel, 0, 5)
        # -- 1b) Select & Check hardware
        label3 = QLabel("HW device")
        self.centralBox.addWidget(label3, 1, 0)
        self.hwDevices = QComboBox()
        self.hwDevices.setToolTip("Select hardware device")
        hwDevices = ["Ledger Nano S"]
        self.hwDevices.addItems(hwDevices)
        self.centralBox.addWidget(self.hwDevices, 1, 1) 
        self.button_checkHw = QPushButton("Connect")
        self.button_checkHw.setToolTip("try to connect to Hardware Wallet")
        self.button_checkHw.clicked.connect(caller.onCheckHw) 
        self.centralBox.addWidget(self.button_checkHw, 1, 2)
        self.hwLed = QLabel()
        self.hwLed.setToolTip("status: %s" % caller.hwStatusMess)
        self.hwLed.setPixmap(caller.ledGrayH_icon)
        self.centralBox.addWidget(self.hwLed, 1, 3)
        layout.addLayout(self.centralBox)
        layout.addStretch(1)
        # --- 3) SPMT logo
        spmtLogo = QLabel()
        spmtLogo_file = os.path.join(caller.imgDir, 'spmtLogo_horiz.png')
        spmtLogo.setPixmap(QPixmap(spmtLogo_file).scaledToHeight(87, Qt.SmoothTransformation))
        layout.addWidget(spmtLogo)
        self.setLayout(layout)