#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from misc import  printDbg, printException, printOK, getCallerName, getFunctionName, writeMNfile
from masternode import Masternode
from threads import ThreadFuns
import json

from PyQt5.QtCore import pyqtSlot
from PyQt5.Qt import QApplication
from PyQt5.QtWidgets import QMessageBox

from qt.gui_tabMain import TabMain_gui
from qt.dlg_mnStatus import MnStatus_dlg

class TabMain():
    def __init__(self, caller):
        self.caller = caller
        self.runInThread = ThreadFuns.runInThread
        self.curr_masternode_alias = None
        self.curr_masternode_address = None
        self.curr_statusData = None
        self.mnToStartList = []
        self.ui = TabMain_gui(caller)
        self.caller.tabMain = self.ui       
        # Connect GUI buttons
        self.ui.button_addMasternode.clicked.connect(lambda: self.onNewMasternode())
        self.ui.button_startAll.clicked.connect(lambda: self.onStartAllMN())
        self.ui.button_getAllStatus.clicked.connect(lambda: self.onCheckAllMN())
        for masternode in self.caller.masternode_list:
            name = masternode['name']
            self.ui.btn_remove[name].clicked.connect(lambda: self.onRemoveMN())
            self.ui.btn_edit[name].clicked.connect(lambda: self.onEditMN())
            self.ui.btn_start[name].clicked.connect(lambda: self.onStartMN())
            self.ui.btn_rewards[name].clicked.connect(lambda: self.onRewardsMN())
            self.ui.btn_status[name].clicked.connect(lambda: self.onCheckMN())            
        
        
        
        
    def checkMN(self, ctrl):
        address = self.curr_masternode_address
        # Check rpc connection   
        if not self.caller.rpcConnected:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw device check', "Connect to RPC server first")
            printDbg("Unable to connect: %s" % self.caller.rpcStatusMess)
            return None
        
        self.curr_statusData = self.caller.rpcClient.getMNStatus(address)  
    
    
    
    
    def displayMNStatus(self):
        statusData = self.curr_statusData
        masternode_alias = self.curr_masternode_alias
        self.ui.btn_details[masternode_alias].disconnect()
        self.ui.btn_details[masternode_alias].clicked.connect(lambda: self.onDisplayStatusDetails(masternode_alias, statusData))
        self.ui.btn_details[masternode_alias].show()
        
        if statusData is None:
            self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledGrayV_icon)
            msg = "<b>ERROR! Masternode not found</b>"
            self.ui.mnStatusLabel[masternode_alias].setText(msg)
            self.ui.mnStatusLabel[masternode_alias].show()
            self.ui.btn_details[masternode_alias].setEnabled(False)
        else:
            printDbg("Got status %s for %s (%s)" % (statusData['status'], masternode_alias, statusData['addr']))
            if statusData['status'] == 'ENABLED':
                self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledGreenV_icon)
                display_text = '<b>Status: </b><span style="color:green">%s</span>' % statusData['status']
            else:
                self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledRedV_icon)
                display_text = '<b>Status: </b><span style="color:red">%s</span>' % statusData['status']
               
            self.ui.mnStatusLabel[masternode_alias].setText(display_text)
            self.ui.mnStatusLabel[masternode_alias].show()
                        
            self.ui.btn_details[masternode_alias].setEnabled(True)
            
            
            
            
    @pyqtSlot()
    def onCheckAllMN(self):
        try:
            printOK("Check-All pressed")
            for masternode in self.caller.masternode_list:
                self.curr_masternode_address = masternode['collateral'].get('address')
                self.curr_masternode_alias = masternode['name']
                printOK("Checking %s (%s)..." % (self.curr_masternode_alias, self.curr_masternode_address))
                self.checkMN(None)
                self.displayMNStatus()
                QApplication.processEvents()        
        
        except Exception as e:
            err_msg = "error in checkAllMN"
            printException(getCallerName(), getFunctionName(), err_msg, e)        
            
            
            
            
    @pyqtSlot()
    def onCheckMN(self, data=None):
        if not data:
            try:
                target = self.ui.sender()
                masternode_alias = target.alias
                for mn_conf in self.caller.masternode_list:
                    if mn_conf['name'] == masternode_alias:
                        masternodeAddr = mn_conf['collateral'].get('address')
                        self.curr_masternode_alias = masternode_alias
                        self.curr_masternode_address = masternodeAddr
                        self.runInThread(self.checkMN, (), self.displayMNStatus)
                        break
                    
            except Exception as e:
                err_msg = "error in onCheckMN"
                printException(getCallerName(), getFunctionName(), err_msg, e)           
        
        
        
        
    @pyqtSlot()
    def onDisplayStatusDetails(self, masternode_alias, statusData):
        try:
            ui = MnStatus_dlg(self.ui, masternode_alias, statusData)
            ui.exec_()
                
        except Exception as e:
            err_msg = "error in displayStatusDetails"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        
        
        
        
    @pyqtSlot()     
    def onEditMN(self, data=None):       
        if not data:
            target = self.ui.sender()
            masternode_alias = target.alias
            try: 
                self.caller.tabs.insertTab(1, self.caller.tabMNConf, "Configuration")
                self.caller.tabs.setCurrentIndex(1)
                for masternode in self.caller.masternode_list:
                    if masternode['name'] == masternode_alias:
                        self.caller.mnode_to_change = masternode
                        self.caller.tabMNConf.fillConfigForm(masternode)
                        break
            except Exception as e:
                print(e)
                
                
                
    
    @pyqtSlot()
    def onNewMasternode(self):
        self.caller.tabs.insertTab(1, self.caller.tabMNConf, "Configuration")
        self.caller.tabMNConf.clearConfigForm()
        self.caller.tabs.setCurrentIndex(1)
                
    
                
                
    @pyqtSlot()    
    def onRemoveMN(self, data=None):
        if not data:    
            target = self.ui.sender()
            masternode_alias = target.alias

            reply = self.caller.myPopUp(QMessageBox.Warning, 'Confirm REMOVE', 
                                 "Are you sure you want to remove\nmasternoode:'%s'" % masternode_alias, QMessageBox.No)

            if reply == QMessageBox.No:
                return
        
            for masternode in self.caller.masternode_list:
                if masternode['name'] == masternode_alias:
                    self.caller.masternode_list.remove(masternode)
                    break
            try:
                writeMNfile(self.caller.masternode_list)
                self.ui.myList.takeItem(self.ui.myList.row(self.ui.current_mn[masternode_alias]))
            except Exception as e:
                err_msg = "Error writing masternode file"
                printException(getCallerName(), getFunctionName(), err_msg, e)
            
    
    
    @pyqtSlot()
    def onRewardsMN(self, data=None):
        if not data:    
            target = self.ui.sender()
            masternode_alias = target.alias
            tab_index = self.caller.tabs.indexOf(self.caller.tabRewards)
            self.caller.tabs.setCurrentIndex(tab_index) 
            self.caller.tabRewards.mnSelect.setCurrentText(masternode_alias)   
    
           
    @pyqtSlot()
    def onStartAllMN(self):
        printOK("Start-All pressed")
        # Check RPC & dongle
        if not self.caller.rpcConnected or self.caller.hwStatus != 2:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw/rpc device check', "Connect to RPC server and HW device first")
            printDbg("Hardware device or RPC server not connected")
            return None
        try:
            reply = self.caller.myPopUp(QMessageBox.Question, 'Confirm START', 
                                                 "Are you sure you want to start ALL masternodes?", QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                for mn_conf in self.caller.masternode_list:
                    self.masternodeToStart = Masternode(self, mn_conf['name'], mn_conf['ip'], mn_conf['port'], 
                                                                mn_conf['mnPrivKey'], mn_conf['hwAcc'], mn_conf['collateral'])
                    # connect signal
                    self.masternodeToStart.sigdone.connect(self.sendBroadcast) 
                    self.mnToStartList.append(self.masternodeToStart)
                
                self.startMN()
                
        except Exception as e:
            err_msg = "error before starting node"
            printException(getCallerName(), getFunctionName(), err_msg, e)
           
           
        
    
        
    @pyqtSlot()
    def onStartMN(self, data=None):
        # Check RPC & dongle  
        if not self.caller.rpcConnected or self.caller.hwStatus != 2:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw/rpc device check', "Connect to RPC server and HW device first")
            printDbg("Hardware device or RPC server not connected")
            return None
        try:
            if not data:
                target = self.ui.sender()
                masternode_alias = target.alias
                printOK("Start-masternode %s pressed" % masternode_alias)
                for mn_conf in self.caller.masternode_list:
                    if mn_conf['name'] == masternode_alias:
                        reply = self.caller.myPopUp(QMessageBox.Question, 'Confirm START', 
                                                 "Are you sure you want to start masternoode:\n'%s'?" % mn_conf['name'], QMessageBox.Yes)
                        if reply == QMessageBox.Yes:
                            self.masternodeToStart = Masternode(self, mn_conf['name'], mn_conf['ip'], mn_conf['port'], 
                                                                mn_conf['mnPrivKey'], mn_conf['hwAcc'], mn_conf['collateral'])
                            # connect signal
                            self.masternodeToStart.sigdone.connect(self.sendBroadcast) 
                            self.mnToStartList.append(self.masternodeToStart)
                            self.startMN()
    
                        break
        except Exception as e:
            err_msg = "error before starting node"
            printException(getCallerName(), getFunctionName(), err_msg, e)
            
            
            
            
    # Activated by signal 'sigdone' from masternode       
         
    def sendBroadcast(self, text):
        if text == "None":
            self.sendBroadcastCheck()
            return
        
        printOK("Start Message: %s" % text)
        ret = self.caller.rpcClient.decodemasternodebroadcast(text)
        if ret is None:
            self.caller.myPopUp2(QMessageBox.Critical, 'message decoding failed', 'message decoding failed')
            self.sendBroadcastCheck()
            return
        
        msg = "Broadcast START message?\n" + json.dumps(ret, indent=4, sort_keys=True)  
        reply = self.caller.myPopUp(QMessageBox.Question, 'message decoded', msg, QMessageBox.Yes)
        if reply == QMessageBox.No:
            self.sendBroadcastCheck()
            return
        
        ret2 = self.caller.rpcClient.relaymasternodebroadcast(text)
        self.caller.myPopUp2(QMessageBox.Information, 'message relayed', json.dumps(ret2, indent=4, sort_keys=True), QMessageBox.Ok)
        self.sendBroadcastCheck()
    
       
            
    def sendBroadcastCheck(self):
        # If list is not empty, start other masternodes
        if self.mnToStartList:
            self.startMN()
            
            
            
        
    def startMN(self):       
        if self.caller.hwStatus != 2:
            self.caller.myPopUp2(QMessageBox.Question, 'SPMT - hw device check', self.caller.hwStatusMess, QMessageBox.Ok)
        elif not self.caller.rpcConnected:
            self.caller.myPopUp2(QMessageBox.Question, 'SPMT - rpc device check', self.caller.rpcStatusMess, QMessageBox.Ok)
        else:           
            try:
                self.masternodeToStart = self.mnToStartList.pop()
                printDbg("Starting...%s" % self.masternodeToStart.name)
                self.masternodeToStart.startMessage(self.caller.hwdevice, self.caller.rpcClient)
                # wait for signal when masternode.work is ready then ---> showBroadcast
            except Exception as e:
                err_msg = "error in startMN"
                printException(getCallerName(), getFunctionName(), err_msg, e)
