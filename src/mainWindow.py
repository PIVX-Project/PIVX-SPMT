#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from queue import Queue
from time import strftime, gmtime
import threading
import sys

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QThread, QSettings
from PyQt5.QtGui import QPixmap, QColor, QPalette, QTextCursor, QIcon, QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QGroupBox, QVBoxLayout, \
    QFileDialog, QMessageBox, QTextEdit, QTabWidget, QLabel, QSplitter

from apiClient import ApiClient
from constants import starting_height, log_File, DefaultCache
from hwdevice import HWdevice
from misc import  printDbg, printException, printOK, getCallerName, getFunctionName, \
    WriteStream, WriteStreamReceiver, now, getRemoteSPMTversion, loadMNConfFile, \
    persistCacheSetting,  appendMasternode, myPopUp_sb
from tabGovernance import TabGovernance
from tabMain import TabMain
from tabMNConf import TabMNConf
from tabRewards import TabRewards
from qt.guiHeader import GuiHeader
from rpcClient import RpcClient
from threads import ThreadFuns
from watchdogThreads import RpcWatchdog


class MainWindow(QWidget):
    
    # signal: clear RPC status label and icons (emitted by updateRPCstatus)
    sig_clearRPCstatus = pyqtSignal()
    
    # signal: RPC status (for server id) is changed (emitted by updateRPCstatus)
    sig_RPCstatusUpdated = pyqtSignal(int, bool)
    
    # signal: RPC list has been reloaded (emitted by updateRPClist)
    sig_RPClistReloaded = pyqtSignal()
    
    def __init__(self, parent, masternode_list, imgDir):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.imgDir = imgDir 
        self.runInThread = ThreadFuns.runInThread
        
        ###-- Masternode list 
        self.masternode_list = masternode_list

        ###-- Create clients and statuses
        self.hwStatus = 0
        self.hwStatusMess = "Not Connected"
        self.rpcClient = None
        self.rpcConnected = False
        self.rpcCheckLock = threading.Lock()
        self.updatingRPCbox = False
        self.rpcStatusMess = "Not Connected"
        self.isBlockchainSynced = False
        
        ###-- Load icons & images
        self.loadIcons()
        ###-- Create main layout
        self.layout = QVBoxLayout()
        self.header = GuiHeader(self)
        self.initConsole()
        self.layout.addWidget(self.header)
        
        ##-- Load RPC Servers list
        self.updateRPClist()
        
        ##-- init HW Client
        self.hwdevice = HWdevice()
        
        ##-- init Api Client
        self.apiClient = ApiClient()
        
        ###-- Create Queues and redirect stdout and stderr
        self.queue = Queue()
        self.queue2 = Queue()
        #sys.stdout = WriteStream(self.queue)
        #sys.stderr = WriteStream(self.queue2)

        ###-- Init last logs
        logFile = open(log_File, 'w+')
        timestamp = strftime('%Y-%m-%d %H:%M:%S', gmtime(now()))
        log_line = '<b style="color: blue">{}</b><br>'.format('STARTING SPMT at '+ timestamp)
        logFile.write(log_line)
        logFile.close()
        
        ###-- Create the thread to update console log for stdout
        self.consoleLogThread = QThread()
        self.myWSReceiver = WriteStreamReceiver(self.queue)
        self.myWSReceiver.mysignal.connect(self.append_to_console)
        self.myWSReceiver.moveToThread(self.consoleLogThread)
        self.consoleLogThread.started.connect(self.myWSReceiver.run)
        self.consoleLogThread.start()
        printDbg("Console Log thread started")
        ###-- Create the thread to update console log for stderr
        self.consoleLogThread2 = QThread()
        self.myWSReceiver2 = WriteStreamReceiver(self.queue2)
        self.myWSReceiver2.mysignal.connect(self.append_to_console)
        self.myWSReceiver2.moveToThread(self.consoleLogThread2)
        self.consoleLogThread2.started.connect(self.myWSReceiver2.run)
        self.consoleLogThread2.start()
        printDbg("Console Log thread 2 started")       
        
        ###-- Initialize tabs
        self.tabs = QTabWidget()
        self.t_main = TabMain(self)
        self.t_mnconf = TabMNConf(self)
        self.t_rewards = TabRewards(self)
        self.t_governance = TabGovernance(self)
        ###-- Add tabs
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.addTab(self.tabMain, "Masternode List")
        #self.tabs.addTab(self.tabMNConf, "MN Configuration")
        self.tabs.addTab(self.tabRewards, "Rewards")
        self.tabs.addTab(self.tabGovernance, "Governance")            
        ###-- Connect change action
        self.tabs.currentChanged.connect(lambda: self.onTabChange())                    
        ###-- Draw Tabs 
        self.splitter = QSplitter(Qt.Vertical)
        ###-- Add tabs and console to Layout        
        self.splitter.addWidget(self.tabs)
        self.splitter.addWidget(self.console)
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)
        self.layout.addWidget(self.splitter)

        ###-- Set Layout
        self.setLayout(self.layout)
        ###-- Init Settings
        self.initSettings()
        ###-- Connect buttons/signals
        self.connButtons()
        
        ##-- Check version
        self.onCheckVersion()
        
        ###-- Create RPC Whatchdog
        self.rpc_watchdogThread = QThread()
        self.myRpcWd = RpcWatchdog(self)
        self.myRpcWd.moveToThread(self.rpc_watchdogThread)
        self.rpc_watchdogThread.started.connect(self.myRpcWd.run)
        
        ###-- Let's go
        self.mnode_to_change = None
        printOK("Hello! Welcome to " + parent.title)
               
        
    
        
    @pyqtSlot(str)    
    def append_to_console(self, text):
        self.consoleArea.moveCursor(QTextCursor.End)
        self.consoleArea.insertHtml(text)
        
    
    
    @pyqtSlot(str)
    def clearHWstatus(self, message):
        self.hwStatus = 1
        self.hwStatusMess = 'Unable to connect to the device. Please check that the PIVX app on the device is open, and try again.'
        self.header.hwLed.setPixmap(self.ledGrayH_icon)
        if message != '':
            myPopUp_sb(self, "crit", "Ledger Disconnected", message)
        
        
            
    @pyqtSlot()
    def clearRPCstatus(self):
        self.rpcConnected = False
        self.header.lastPingBox.setHidden(True)
        self.header.rpcLed.setPixmap(self.ledGrayH_icon)
        
        
        
    def connButtons(self):
        self.header.button_checkRpc.clicked.connect(lambda: self.onCheckRpc())
        self.header.button_checkHw.clicked.connect(lambda: self.onCheckHw())
        self.header.rpcClientsBox.currentIndexChanged.connect(self.onChangeSelectedRPC)
        ##-- Connect signals
        self.sig_clearRPCstatus.connect(self.clearRPCstatus)
        self.sig_RPCstatusUpdated.connect(self.showRPCstatus)
        self.parent.sig_changed_rpcServers.connect(self.updateRPClist)
        self.hwdevice.sig_ledger_disconnected.connect(self.clearHWstatus)
        self.hwdevice.sigTxdone.connect(self.t_rewards.FinishSend)
        self.hwdevice.sigTxabort.connect(self.t_rewards.onCancel)
        self.hwdevice.tx_progress.connect(self.t_rewards.updateProgressPercent)
        self.tabMain.myList.model().rowsMoved.connect(self.saveMNListOrder)
            
            
            
    def getRPCserver(self):
        itemData = self.header.rpcClientsBox.itemData(self.header.rpcClientsBox.currentIndex())
        rpc_index  = self.header.rpcClientsBox.currentIndex()
        rpc_protocol = itemData["protocol"]
        rpc_host = itemData["host"]
        rpc_user = itemData["user"]
        rpc_password = itemData["password"]
            
        return rpc_index, rpc_protocol, rpc_host, rpc_user, rpc_password
    
    
    
    def getServerListIndex(self, server):
        return self.header.rpcClientsBox.findData(server)
        
        
        
                
    def initConsole(self):
        self.console = QGroupBox()
        self.console.setTitle("Console Log")
        layout = QVBoxLayout()
        self.btn_consoleToggle = QPushButton('Hide')
        self.btn_consoleToggle.setToolTip('Show/Hide console')
        self.btn_consoleToggle.clicked.connect(lambda: self.onToggleConsole())
        consoleHeader = QHBoxLayout()
        consoleHeader.addWidget(self.btn_consoleToggle)
        self.consoleSaveButton = QPushButton('Save')
        self.consoleSaveButton.clicked.connect(lambda: self.onSaveConsole())
        consoleHeader.addWidget(self.consoleSaveButton)
        self.btn_consoleClean = QPushButton('Clean')
        self.btn_consoleClean.setToolTip('Clean console log area')
        self.btn_consoleClean.clicked.connect(lambda: self.onCleanConsole())
        consoleHeader.addWidget(self.btn_consoleClean)
        consoleHeader.addStretch(1)
        self.versionLabel = QLabel("--")
        self.versionLabel.setOpenExternalLinks(True)
        consoleHeader.addWidget(self.versionLabel)
        self.btn_checkVersion = QPushButton("Check SPMT version")
        self.btn_checkVersion.setToolTip("Check latest stable release of SPMT")
        self.btn_checkVersion.clicked.connect(lambda: self.onCheckVersion())
        consoleHeader.addWidget(self.btn_checkVersion)
        layout.addLayout(consoleHeader)
        self.consoleArea = QTextEdit()
        almostBlack = QColor(40, 40, 40)
        palette = QPalette()
        palette.setColor(QPalette.Base, almostBlack)
        green = QColor(0, 255, 0)
        palette.setColor(QPalette.Text, green)
        self.consoleArea.setPalette(palette)
        layout.addWidget(self.consoleArea)
        self.console.setLayout(layout) 
        
        
    
    def initSettings(self):
        self.splitter.setSizes([self.parent.cache.get("splitter_x"), self.parent.cache.get("splitter_y")])
        ###-- Hide console if it was previously hidden
        if self.parent.cache.get("console_hidden"):
            self.onToggleConsole()


        
    
    def isMasternodeInList(self, mn_alias):
        return (mn_alias in [x['name'] for x in self.masternode_list])    
        
    
        
    def loadIcons(self):
        # Load Icons        
        self.ledPurpleH_icon = QPixmap(os.path.join(self.imgDir, 'icon_purpleLedH.png')).scaledToHeight(17, Qt.SmoothTransformation)
        self.ledGrayH_icon = QPixmap(os.path.join(self.imgDir, 'icon_grayLedH.png')).scaledToHeight(17, Qt.SmoothTransformation)
        self.ledHalfPurpleH_icon = QPixmap(os.path.join(self.imgDir, 'icon_halfPurpleLedH.png')).scaledToHeight(17, Qt.SmoothTransformation)
        self.ledRedV_icon = QPixmap(os.path.join(self.imgDir, 'icon_redLedV.png')).scaledToHeight(17, Qt.SmoothTransformation)
        self.ledGrayV_icon = QPixmap(os.path.join(self.imgDir, 'icon_grayLedV.png')).scaledToHeight(17, Qt.SmoothTransformation)
        self.ledGreenV_icon = QPixmap(os.path.join(self.imgDir, 'icon_greenLedV.png')).scaledToHeight(17, Qt.SmoothTransformation)
        self.lastBlock_icon = QPixmap(os.path.join(self.imgDir, 'icon_lastBlock.png')).scaledToHeight(15, Qt.SmoothTransformation)
        self.connGreen_icon = QPixmap(os.path.join(self.imgDir, 'icon_greenConn.png')).scaledToHeight(15, Qt.SmoothTransformation)
        self.connRed_icon = QPixmap(os.path.join(self.imgDir, 'icon_redConn.png')).scaledToHeight(15, Qt.SmoothTransformation)
        self.connOrange_icon = QPixmap(os.path.join(self.imgDir, 'icon_orangeConn.png')).scaledToHeight(15, Qt.SmoothTransformation)
       
    
    
    def loadMNConf(self, fileName):
        hot_masternodes = loadMNConfFile(fileName)
        if hot_masternodes == None:
            messText = "Unable to load data from file '%s'" % fileName
            myPopUp_sb(self, "warn", "SPMT - Load MN Conf", messText)
        else:
            new_masternodes = []
            skip_masternodes = []
            for x in hot_masternodes:
                # If masternode name is not in list
                if not self.isMasternodeInList(x['name']):
                    # Add to cache, QListWidget and database 
                    appendMasternode(self, x)
                    new_masternodes.append(x)
                # Otherwise skip it
                else:
                    skip_masternodes.append(x)

            # Print number of nodes added
            new_nodes = len(new_masternodes)
            final_message = ""
            if new_nodes == 0:
                final_message = "No External Masternode "
            elif new_nodes == 1:
                final_message = "1 External Masternode "
            else:
                final_message = "%d External Masternodes " % new_nodes
            final_message += "added to the list."
            if new_nodes > 0:
                final_message +=  "<br>" + str([x['name'] for x in new_masternodes]) + ".  "
            printOK(final_message)
            if len(skip_masternodes) > 0:
                final_message = "Following entries skipped due to duplicate names:<br>"
                final_message += str([x['name'] for x in skip_masternodes]) + ".  "
                printOK(final_message)
        
        
        
    
    @pyqtSlot()        
    def onCheckHw(self):
        printDbg("Checking for HW device...")
        self.updateHWstatus(None)
        self.showHWstatus()


        
    
    @pyqtSlot()
    def onCheckRpc(self):
        self.runInThread(self.updateRPCstatus, (True,),) 
        
        
        
    @pyqtSlot()
    def onCheckVersion(self):
        printDbg("Checking SPMT version...")
        self.versionLabel.setText("--")      
        self.runInThread(self.checkVersion, (), self.updateVersion) 
        
        
    def checkVersion(self, ctrl):
        local_version = self.parent.version['number'].split('.')
        self.gitVersion = getRemoteSPMTversion()
        remote_version = self.gitVersion.split('.')
        
        if (remote_version[0] > local_version[0]) or \
        (remote_version[0] == local_version[0] and remote_version[1] > local_version[1]) or \
        (remote_version[0] == local_version[0] and remote_version[1] == local_version[1] and remote_version[2] > local_version[2]):
            self.versionMess = '<b style="color:red">New Version Available:</b> %s  ' % (self.gitVersion)
            self.versionMess += '(<a href="https://github.com/PIVX-Project/PIVX-SPMT/releases/">download</a>)'
        else:
            self.versionMess = "You have the latest version of SPMT"
            
            
    def updateVersion(self):
        if self.versionMess is not None:
            self.versionLabel.setText(self.versionMess)
        printOK("Remote version: %s" % str(self.gitVersion))
            
            
            
    @pyqtSlot(int)
    def onChangeSelectedRPC(self, i):
        # Don't update when we are clearing the box
        if not self.updatingRPCbox:
            # persist setting
            self.parent.cache['selectedRPC_index'] = persistCacheSetting('cache_RPCindex',i)
            # close connection and try to open new one
            self.runInThread(self.updateRPCstatus, (True,), )

        
        
        
    @pyqtSlot()
    def onCleanConsole(self):
        self.consoleArea.clear()
        
      
      
      
    @pyqtSlot()
    def onSaveConsole(self):
        timestamp = strftime('%Y-%m-%d_%H-%M-%S', gmtime(now()))
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"Save Logs to file","SPMT_Logs_%s.txt" % timestamp,"All Files (*);; Text Files (*.txt)", options=options)
        try:
            if fileName:
                printOK("Saving logs to %s" % fileName)
                log_file = open(fileName, 'w+')
                log_text = self.consoleArea.toPlainText()
                log_file.write(log_text)
                log_file.close()
                
        except Exception as e:
            err_msg = "error writing Log file"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
                
            
            
            
    @pyqtSlot()
    def onTabChange(self):
        # tabRewards
        if self.tabs.currentWidget() == self.tabRewards:
            # reload last used address
            self.tabRewards.destinationLine.setText(self.parent.cache.get("lastAddress"))
            # reload UTXOs from DB
            self.t_rewards.display_mn_utxos()           

        # tabGovernace
        if self.tabs.currentWidget() == self.tabGovernance:
            # reload proposal list
            self.t_governance.onRefreshProposals()
            self.t_governance.updateSelectedMNlabel()
            
            
        

    @pyqtSlot()
    def onToggleConsole(self):
        if self.btn_consoleToggle.text() == 'Hide':
            self.btn_consoleToggle.setText('Show')
            self.consoleArea.hide()
            self.console.setMinimumHeight(70)
            self.console.setMaximumHeight(70)
        else:
            self.console.setMinimumHeight(70)
            self.console.setMaximumHeight(starting_height)
            self.btn_consoleToggle.setText('Hide')
            self.consoleArea.show()




    def saveMNListOrder(self):
        # Update mnList order to cache settings and sort
        mnOrder = {}
        mnList = self.tabMain.myList
        for i in range(mnList.count()):
            mnName = mnList.itemWidget(mnList.item(i)).alias
            mnOrder[mnName] = i
        self.parent.cache['mnList_order'] = persistCacheSetting('cache_mnOrder', mnOrder)
        self.masternode_list.sort(key=self.parent.extract_order)
        # reload MnSelect in tabRewards
        self.t_rewards.loadMnSelect()



    
    def showHWstatus(self):
        self.updateHWleds()
        myPopUp_sb(self, "info", 'SPMT - hw check', "%s" % self.hwStatusMess)
        
        
    
    @pyqtSlot(int, bool)
    def showRPCstatus(self, server_index, fDebug):
        # Update displayed status only if selected server is not changed
        if server_index == self.header.rpcClientsBox.currentIndex():
            self.updateRPCled(fDebug)
            if fDebug:
                myPopUp_sb(self, "info", 'SPMT - rpc check', "%s" % self.rpcStatusMess)
        else:
            printDbg("RPC server changed while checking... aborted.")

            
            
            
    def updateHWleds(self):
        if self.hwStatus == 1:
            self.header.hwLed.setPixmap(self.ledHalfPurpleH_icon)
        elif self.hwStatus == 2:
            self.header.hwLed.setPixmap(self.ledPurpleH_icon)
        else:
            self.header.hwLed.setPixmap(self.ledGrayH_icon)
        self.header.hwLed.setToolTip(self.hwStatusMess)
        
        
 
        
    def updateHWstatus(self, ctrl):
        # re-initialize device
        try:
            self.hwdevice.initDevice()       
            self.hwStatus, self.hwStatusMess = self.hwdevice.getStatus()
            printDbg("mess: %s" % statusMess)
        except:
            pass
        
        printDbg("status:%s - mess: %s" % (self.hwStatus, self.hwStatusMess))
            
            

  
        
    def updateLastBlockLabel(self):
        text = '--'
        if self.rpcLastBlock == 1:
            text = "Loading block index..."
        elif self.rpcConnected and self.rpcLastBlock > 0:
            text = str(self.rpcLastBlock)
            if not self.isBlockchainSynced:
                text += " (Synchronizing)"
                
        self.header.lastBlockLabel.setText(text)
        
        
        
    def updateLastBlockPing(self):
        if not self.rpcConnected:
            self.header.lastPingBox.setHidden(True)
        else:
            self.header.lastPingBox.setHidden(False)
            if self.rpcResponseTime > 2:
                color = "red"
                self.header.lastPingIcon.setPixmap(self.connRed_icon)
            elif self.rpcResponseTime > 1:
                color = "orange"
                self.header.lastPingIcon.setPixmap(self.connOrange_icon)
            else:
                color = "green"
                self.header.lastPingIcon.setPixmap(self.connGreen_icon)
            if self.rpcResponseTime is not None:
                self.header.responseTimeLabel.setText("%.3f" % self.rpcResponseTime)
                self.header.responseTimeLabel.setStyleSheet("color: %s" % color)
                self.header.lastPingIcon.setStyleSheet("color: %s" % color)
       
        

                  
    def updateRPCled(self, fDebug=False):
        if self.rpcConnected:
            self.header.rpcLed.setPixmap(self.ledPurpleH_icon)
            if fDebug:
                printDbg("Connected to RPC server.")
        else:
            if self.rpcLastBlock == 1:
                self.header.rpcLed.setPixmap(self.ledHalfPurpleH_icon)
                if fDebug:
                    printDbg("Connected to RPC server - Still syncing...")
            else:
                self.header.rpcLed.setPixmap(self.ledGrayH_icon)
                if fDebug:
                    printDbg("Connection to RPC server failed.")

        self.header.rpcLed.setToolTip(self.rpcStatusMess)
        self.updateLastBlockLabel()
        self.updateLastBlockPing()
        


    #@pyqtSlot()   
    def updateRPClist(self):
        # Clear old stuff
        self.updatingRPCbox = True
        self.header.rpcClientsBox.clear()
        public_servers = self.parent.db.getRPCServers(custom=False)
        custom_servers = self.parent.db.getRPCServers(custom=True)
        self.rpcServersList = public_servers + custom_servers
        # Add public servers (italics)
        italicsFont = QFont("Times", italic=True)
        for s in public_servers:
            url = s["protocol"] + "://" + s["host"].split(':')[0]
            self.header.rpcClientsBox.addItem(url, s)
            self.header.rpcClientsBox.setItemData(self.getServerListIndex(s), italicsFont, Qt.FontRole)
        # Add Local Wallet (bold)
        boldFont = QFont("Times")
        boldFont.setBold(True)
        self.header.rpcClientsBox.addItem("Local Wallet", custom_servers[0])
        self.header.rpcClientsBox.setItemData(self.getServerListIndex(custom_servers[0]), boldFont, Qt.FontRole)
        # Add custom servers
        for s in custom_servers[1:]:
            url = s["protocol"] + "://" + s["host"].split(':')[0]
            self.header.rpcClientsBox.addItem(url, s)
        # reset index
        if self.parent.cache['selectedRPC_index'] >= self.header.rpcClientsBox.count():
            # (if manually removed from the config files) replace default index
            self.parent.cache['selectedRPC_index'] = persistCacheSetting('cache_RPCindex', DefaultCache["selectedRPC_index"])
        self.header.rpcClientsBox.setCurrentIndex(self.parent.cache['selectedRPC_index'])
        self.updatingRPCbox = False
        # reload servers in configure dialog
        self.sig_RPClistReloaded.emit()
        
        
        
    def updateRPCstatus(self, ctrl, fDebug=False):
        with self.rpcCheckLock:
            self.sig_clearRPCstatus.emit()
            self.rpcClient = None
            
            self.rpcResponseTime = None
            rpc_index, rpc_protocol, rpc_host, rpc_user, rpc_password = self.getRPCserver()
            
            rpc_url = "%s://%s:%s@%s" % (rpc_protocol, rpc_user, rpc_password, rpc_host)
            self.rpcClient = RpcClient(rpc_protocol, rpc_host, rpc_user, rpc_password)
 
            if fDebug:
                printDbg("Trying to connect to RPC %s://%s..." % (rpc_protocol, rpc_host))
            
            status, statusMess, lastBlock, r_time1 = self.rpcClient.getStatus()
            
            self.rpcConnected = status
            self.rpcLastBlock = lastBlock
            self.rpcStatusMess = statusMess
            self.isBlockchainSynced, r_time2  = self.rpcClient.isBlockchainSynced()
            
            if r_time1 is not None and r_time2 is not None:
                self.rpcResponseTime = round((r_time1+r_time2)/2, 3)

            self.sig_RPCstatusUpdated.emit(rpc_index, fDebug)

            
    