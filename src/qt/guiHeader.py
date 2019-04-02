#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QPushButton, QLabel, QGridLayout, QHBoxLayout, QComboBox, QWidget

from constants import HW_devices
from PyQt5.Qt import QSizePolicy

class GuiHeader(QWidget):
    def __init__(self, caller, *args, **kwargs):
        QWidget.__init__(self)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        # --- 1) Check Box
        self.centralBox = QGridLayout()
        self.centralBox.setContentsMargins(0, 0, 0, 0)
        # --- 1a) Select & Check RPC
        label1 = QLabel("PIVX RPC Server")
        self.centralBox.addWidget(label1, 0, 0)
        self.rpcClientsBox = QComboBox()
        self.rpcClientsBox.setToolTip("Select RPC server.")
        self.centralBox.addWidget(self.rpcClientsBox, 0, 1)
        self.button_checkRpc = QPushButton("Connect/Update")
        self.button_checkRpc.setToolTip("try to connect to RPC server")
        self.centralBox.addWidget(self.button_checkRpc, 0, 2)
        self.rpcLed = QLabel()
        self.rpcLed.setToolTip("%s" % caller.rpcStatusMess)
        self.rpcLed.setPixmap(caller.ledGrayH_icon)
        self.centralBox.addWidget(self.rpcLed, 0, 3)
        self.lastPingBox = QWidget()
        sp_retain = QSizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.lastPingBox.setSizePolicy(sp_retain)
        self.lastPingBox.setContentsMargins(0, 0, 0, 0)
        lastPingBoxLayout = QHBoxLayout()
        self.lastPingIcon = QLabel()
        self.lastPingIcon.setToolTip("Last ping server response time.\n(The lower, the better)")
        self.lastPingIcon.setPixmap(caller.connRed_icon)
        lastPingBoxLayout.addWidget(self.lastPingIcon)
        self.responseTimeLabel = QLabel()
        self.responseTimeLabel.setToolTip("Last ping server response time.\n(The lower, the better)")
        lastPingBoxLayout.addWidget(self.responseTimeLabel)
        lastPingBoxLayout.addSpacing(10)
        self.lastBlockIcon = QLabel()
        self.lastBlockIcon.setToolTip("Last ping block number")
        self.lastBlockIcon.setPixmap(caller.lastBlock_icon)
        lastPingBoxLayout.addWidget(self.lastBlockIcon)
        self.lastBlockLabel = QLabel()
        self.lastBlockLabel.setToolTip("Last ping block number")
        lastPingBoxLayout.addWidget(self.lastBlockLabel)
        self.lastPingBox.setLayout(lastPingBoxLayout)
        self.centralBox.addWidget(self.lastPingBox, 0, 4)
        # -- 1b) Select & Check hardware
        label3 = QLabel("Hardware Device")
        self.centralBox.addWidget(label3, 1, 0)
        self.hwDevices = QComboBox()
        self.hwDevices.setToolTip("Select hardware device")
        self.hwDevices.addItems(HW_devices)
        self.centralBox.addWidget(self.hwDevices, 1, 1)
        self.button_checkHw = QPushButton("Connect")
        self.button_checkHw.setToolTip("try to connect to hardware device")
        self.centralBox.addWidget(self.button_checkHw, 1, 2)
        self.hwLed = QLabel()
        self.hwLed.setToolTip("Status: %s" % caller.hwStatusMess)
        self.hwLed.setPixmap(caller.ledGrayH_icon)
        self.centralBox.addWidget(self.hwLed, 1, 3)
        self.layout.addLayout(self.centralBox)
        self.layout.addStretch(1)
        # --- 3) SPMT logo
        spmtLogo = QLabel()
        spmtLogo_file = os.path.join(caller.imgDir, 'spmtLogo_horiz.png')
        spmtLogo.setPixmap(QPixmap(spmtLogo_file).scaledToHeight(55, Qt.SmoothTransformation))
        self.layout.addWidget(spmtLogo)
        self.setLayout(self.layout)
