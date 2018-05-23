#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtCore import Qt
from PyQt5.Qt import QLabel, QIcon, QAbstractItemView
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QGroupBox, QVBoxLayout, QListWidget
from PyQt5.QtWidgets import QListWidgetItem, QProgressBar, QToolButton
from PyQt5.QtGui import QPixmap


class TabMain_gui(QWidget):
    def __init__(self, caller, *args, **kwargs):
        QWidget.__init__(self)
        self.caller = caller
        ###-- Initialize
        self.loadIcons()
        self.initGlobalButtons()
        self.initMNList()        
        ###-- Compose layout
        mainVertical = QVBoxLayout()
        mainVertical.setSpacing(10)
        mainVertical.addLayout(self.globalButtons)
        mainVertical.addWidget(self.body)
        ###-- Set Layout
        self.setLayout(mainVertical)
        
        
        
        
    def initGlobalButtons(self):
        ###-- Global Buttons
        globalButtons = QHBoxLayout()
        self.button_addMasternode = QPushButton("New Masternode")
        globalButtons.addWidget(self.button_addMasternode)
        self.button_startAll = QPushButton("Start All Masternodes")
        globalButtons.addWidget(self.button_startAll)
        self.button_getAllStatus = QPushButton("Get Status of All Masternodes")
        globalButtons.addWidget(self.button_getAllStatus)
        self.globalButtons = globalButtons
        
        
        
        
    def initMNList(self):
        ###-- CENTRAL PART
        self.body = QGroupBox()
        self.body.setTitle("My Masternodes")
        # masternode list
        self.myList = QListWidget()
        self.myList.setUpdatesEnabled(True)
        self.myList.setDragDropMode(QAbstractItemView.InternalMove)
        self.myList.setDefaultDropAction(Qt.MoveAction)
        self.current_mn = {}
        self.mnLed = {}
        self.mnLabel = {}
        self.btn_details = {}
        self.mnStatusLabel = {}
        self.btn_remove = {}
        self.btn_edit = {}
        self.btn_start = {}
        self.btn_rewards = {}
        self.btn_status = {}
        
        for masternode in self.caller.masternode_list:
            name = masternode['name']
            self.insert_mn_list(name, masternode['ip'], masternode['port'])  
        
        vBox = QVBoxLayout()
        vBox.addWidget(self.myList)
        vBox.stretch(1)
        self.body.setLayout(vBox)  
        
    
          
     
    def insert_mn_list(self, name, ip, port, row=None):   
        mnRow = QWidget()
        mnRow.setToolTip("Drag rows to re-order.")
        mnRowLayout = QHBoxLayout()
        ##--- Led
        self.mnLed[name] = QLabel()
        self.mnLed[name].setPixmap(self.caller.ledGrayV_icon)
        mnRowLayout.addWidget(self.mnLed[name])
        ##--- Label        
        self.mnLabel[name] = QLabel()
        self.mnLabel[name].setText("%s &nbsp; [<i style='color: #2f005f'>%s:%s</i>]" % (name, ip, port))
        mnRowLayout.addWidget(self.mnLabel[name])
        mnRowLayout.addStretch(1)
        ##--- Status Label
        self.mnStatusLabel[name] = QLabel()
        mnRowLayout.addWidget(self.mnStatusLabel[name])
        self.mnStatusLabel[name].hide()
        ##--- Details button
        self.btn_details[name] = QToolButton()
        self.btn_details[name].setIcon(self.details_icon)
        self.btn_details[name].setToolTip('Check status of "%s"' % name)
        mnRowLayout.addWidget(self.btn_details[name])
        self.btn_details[name].hide()         
        ##--- Status button
        self.btn_status[name] = QPushButton()
        self.btn_status[name].setToolTip('Check status of "%s"' % name)      
        self.btn_status[name].setIcon(self.getMNstatus_icon)
        self.btn_status[name].alias = name
        mnRowLayout.addWidget(self.btn_status[name])
        ##--- Rewards button
        self.btn_rewards[name] = QPushButton()
        self.btn_rewards[name].setToolTip('Transfer rewards from "%s"' % name)           
        self.btn_rewards[name].setIcon(self.rewards_icon)
        self.btn_rewards[name].alias = name
        mnRowLayout.addWidget(self.btn_rewards[name])
        ##--- Start button
        self.btn_start[name] = QPushButton()
        self.btn_start[name].setToolTip('Start masternode "%s"' % name)          
        self.btn_start[name].setIcon(self.startMN_icon)
        self.btn_start[name].alias = name
        mnRowLayout.addWidget(self.btn_start[name])
        ##--- Edit button
        self.btn_edit[name] = QPushButton()
        self.btn_edit[name].setToolTip('Edit masternode "%s"' % name)   
        self.btn_edit[name].setIcon(self.editMN_icon)
        self.btn_edit[name].alias = name
        mnRowLayout.addWidget(self.btn_edit[name])
        ##--- Remove button
        self.btn_remove[name] = QPushButton()
        self.btn_remove[name].setToolTip('Delete masternode "%s"' % name)        
        self.btn_remove[name].setIcon(self.removeMN_icon)
        self.btn_remove[name].alias = name
        mnRowLayout.addWidget(self.btn_remove[name])
        ##--- Three Dots
        threeDots = QLabel()
        threeDots.setPixmap(self.threeDots_icon.scaledToHeight(20, Qt.SmoothTransformation))
        mnRowLayout.addWidget(threeDots)
        ##--- Set Row Layout
        mnRow.setLayout(mnRowLayout)
        ##--- Append Row
        self.current_mn[name] = QListWidgetItem()
        #self.current_mn[name].setFlags(Qt.ItemIsSelectable)
        self.current_mn[name].setSizeHint(mnRow.sizeHint())
        if row is not None:
            self.myList.insertItem(row, self.current_mn[name])
        else:
            self.myList.addItem(self.current_mn[name])
        self.myList.setItemWidget(self.current_mn[name], mnRow)
        
        
        
        
    def loadIcons(self):
        self.removeMN_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_delete.png'))
        self.editMN_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_edit.png'))
        self.startMN_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_rocket.png'))
        self.rewards_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_money.png'))
        self.getMNstatus_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_dashboard.png'))
        self.details_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_search.png'))
        self.ledgerImg = QPixmap(os.path.join(self.caller.imgDir, 'ledger.png'))
        self.threeDots_icon = QPixmap(os.path.join(self.caller.imgDir, 'icon_3dots.png'))
    