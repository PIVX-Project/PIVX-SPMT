#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from misc import  printDbg, printException, printOK, getCallerName, getFunctionName, writeToFile, now
from constants import masternodes_File
from masternode import Masternode
from apiClient import ApiClient
from threads import ThreadFuns
import simplejson as json
import time

from PyQt5.QtCore import pyqtSlot
from PyQt5.Qt import QApplication
from PyQt5.QtWidgets import QMessageBox

from qt.gui_tabMain import TabMain_gui
from qt.dlg_mnStatus import MnStatus_dlg
from qt.dlg_sweepAll import SweepAll_dlg

class TabMain():
    def __init__(self, caller):
        self.caller = caller
        self.all_masternodes = {}
        self.all_masternodes['last_update'] = 0
        self.mnToStartList = []
        self.ui = TabMain_gui(caller)
        self.caller.tabMain = self.ui
        self.sweepAllDlg = SweepAll_dlg(self)
        # Connect GUI buttons
        self.ui.button_addMasternode.clicked.connect(lambda: self.onNewMasternode())
        self.ui.button_startAll.clicked.connect(lambda: self.onStartAllMN())
        self.ui.button_getAllStatus.clicked.connect(lambda: self.onCheckAllMN())
        self.ui.button_sweepAllRewards.clicked.connect(lambda: self.onSweepAllRewards())
        for masternode in self.caller.masternode_list:
            name = masternode['name']
            self.ui.btn_remove[name].clicked.connect(lambda: self.onRemoveMN())
            self.ui.btn_edit[name].clicked.connect(lambda: self.onEditMN())
            self.ui.btn_start[name].clicked.connect(lambda: self.onStartMN())
            self.ui.btn_rewards[name].clicked.connect(lambda: self.onRewardsMN())         
            
            
            
    def displayMNlistUpdated(self):
        for masternode in self.caller.masternode_list:
            printOK("Checking %s (%s)..." % (masternode['name'], masternode['collateral'].get('address')))
            self.displayMNStatus(masternode)
            time.sleep(0.2)         
    
    
    
    
    def displayMNStatus(self, currMN):
        statusData = None
        for mn in self.all_masternodes.get('masternodes'):
            if mn.get('addr') == currMN['collateral'].get('address'):
                
                statusData = mn
                if statusData is not None:   
                    try:
                        statusData['balance'] = self.caller.apiClient.getBalance(mn.get('addr'))
                    except Exception as e:
                        err_msg = "error getting balance of %s" % mn.get('addr')
                        printException(getCallerName(), getFunctionName(), err_msg, e)
        
        masternode_alias = currMN['name']               
        self.ui.btn_details[masternode_alias].disconnect()
        self.ui.btn_details[masternode_alias].clicked.connect(lambda: self.onDisplayStatusDetails(masternode_alias, statusData))
        self.ui.btn_details[masternode_alias].show()
    
        if statusData is None:
            printDbg("%s (%s) not found" % (masternode_alias, currMN['collateral'].get('address')))
            self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledGrayV_icon)
            msg = "<b>Masternode not found.</b>"
            self.ui.mnStatusLabel[masternode_alias].setText(msg)
            self.ui.mnStatusLabel[masternode_alias].show()
            self.ui.btn_details[masternode_alias].setEnabled(False)
        else:
            display_text = ""
            if statusData['balance'] is not None:
                self.ui.mnBalance[masternode_alias].setText('&nbsp;<span style="color:purple">%s PIV</span>' % str(statusData['balance']))
                self.ui.mnBalance[masternode_alias].show()
            printDbg("Got status %s for %s (%s)" % (statusData['status'], masternode_alias, statusData['addr']))
            if statusData['status'] == 'ENABLED':
                self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledGreenV_icon)
                display_text += '<span style="color:green">%s</span>&nbsp;&nbsp;' % statusData['status']
                position = statusData.get('queue_pos')
                total_count = len(self.all_masternodes.get('masternodes'))
                display_text += '%d/%d' % (position, total_count) 
                
                self.ui.mnStatusProgress[masternode_alias].setRange(0, total_count)
                self.ui.mnStatusProgress[masternode_alias].setValue(total_count-position)
                self.ui.mnStatusProgress[masternode_alias].show()
            else:
                self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledRedV_icon)
                display_text += '<span style="color:red">%s</span>&nbsp;&nbsp;' % statusData['status']
       
            self.ui.mnStatusLabel[masternode_alias].setText(display_text)
            self.ui.mnStatusLabel[masternode_alias].show()
            self.ui.btn_details[masternode_alias].setEnabled(True)
        QApplication.processEvents()     
            
            
            
    @pyqtSlot()
    def onCheckAllMN(self):
        if not self.caller.rpcConnected:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw device check', "RPC server must be connected to perform this action.")
            printDbg("Unable to connect: %s" % self.caller.rpcStatusMess)
            return
        try:
            printOK("Check-All pressed")
            ThreadFuns.runInThread(self.updateAllMasternodes_thread, (), self.displayMNlistUpdated)
                   
        except Exception as e:
            err_msg = "error in checkAllMN"
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

            self.caller.tabs.insertTab(1, self.caller.tabMNConf, "Configuration")
            self.caller.tabs.setCurrentIndex(1)
            for masternode in self.caller.masternode_list:
                if masternode['name'] == masternode_alias:
                    self.caller.mnode_to_change = masternode
                    self.caller.tabMNConf.fillConfigForm(masternode)
                    break
                
                
                
    
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
                writeToFile(self.caller.masternode_list, masternodes_File)
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
            
            
    
    @pyqtSlot()
    def onSweepAllRewards(self):
        try:
            self.sweepAllDlg.load_data()
            self.sweepAllDlg.exec_()
            
            
        except Exception as e:
            err_msg = "exception in SweepAll_dlg"
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
        
        if json.dumps(ret2)[1:26] == "Masternode broadcast sent":
            message = "Start-message was successfully sent to the network.<br>"
            message += "If your remote server is correctly configured and connected to the network, "
            message += "the output of the <b>./pivx-cli masternode status</b> command on the VPS should show:<br>"
            message += "<br><em>\"message\": \"Masternode successfully started\"</em>"
            self.caller.myPopUp2(QMessageBox.Information, 'message relayed', message, QMessageBox.Ok)
        else:
            print(json.dumps(ret2)[1:26])
            print("\n")
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
                # wait for signal when masternode.work is ready then ---> sendBroadcast
            except Exception as e:
                err_msg = "error in startMN"
                printException(getCallerName(), getFunctionName(), err_msg, e)
                
      
                
                
    def updateAllMasternodes_thread(self, ctrl):
        # update only after 30 secs
        if now()-self.all_masternodes['last_update'] > 30:   
            self.all_masternodes = self.caller.rpcClient.getMasternodes()

            
