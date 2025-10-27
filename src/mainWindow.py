#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import logging
import os
import threading

from PyQt5.QtCore import pyqtSignal, Qt, QThread
from PyQt5.QtGui import QPixmap, QColor, QPalette, QTextCursor, QFont
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QGroupBox, QVBoxLayout, \
    QFileDialog, QTextEdit, QTabWidget, QLabel, QSplitter

from apiClient import ApiClient
from constants import starting_height, DefaultCache, wqueue
from hwdevice import HWdevice
from misc import printDbg, printException, printOK, getCallerName, getFunctionName, \
    WriteStreamReceiver, now, getRemoteSPMTversion, loadMNConfFile, \
    persistCacheSetting, appendMasternode, myPopUp_sb
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

    # signal: UTXO list loading percent (emitted by load_utxos_thread in tabRewards)
    sig_UTXOsLoading = pyqtSignal(int)

    # signal: Proposals list has been reloaded (emitted by loadProposals_thread in tabGovernance)
    sig_ProposalsLoaded = pyqtSignal()

    def __init__(self, parent, masternode_list, imgDir):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.imgDir = imgDir
        self.runInThread = ThreadFuns.runInThread
        self.lock = threading.Lock()

        # -- Masternode list
        self.masternode_list = masternode_list

        # -- Create clients and statuses
        self.hwStatus = 0
        self.hwModel = 0
        self.hwStatusMess = "Not Connected"
        self.rpcClient = None
        self.rpcConnected = False
        self.updatingRPCbox = False
        self.rpcStatusMess = "Not Connected"
        self.isBlockchainSynced = False
        # Changes when an RPC client is connected (affecting API client)
        self.isTestnetRPC = self.parent.cache['isTestnetRPC']

        # -- Load icons & images
        self.loadIcons()

        # -- Create main layout
        self.layout = QVBoxLayout()
        self.header = GuiHeader(self)
        self.initConsole()
        self.layout.addWidget(self.header)

        # -- Load RPC Servers list (init selection and self.isTestnet)
        self.updateRPClist()

        # -- Init HW selection
        self.header.hwDevices.setCurrentIndex(self.parent.cache['selectedHW_index'])

        # -- init HW Client
        self.hwdevice = HWdevice(self)

        # -- init Api Client
        self.apiClient = ApiClient(self.isTestnetRPC)

        # -- Create Queue to redirect stdout
        self.queue = wqueue

        # -- Init last logs
        logging.debug("STARTING SPMT")

        # -- Create the thread to update console log for stdout
        self.consoleLogThread = QThread()
        self.myWSReceiver = WriteStreamReceiver(self.queue)
        self.myWSReceiver.mysignal.connect(self.append_to_console)
        self.myWSReceiver.moveToThread(self.consoleLogThread)
        self.consoleLogThread.started.connect(self.myWSReceiver.run)
        self.consoleLogThread.start()
        printDbg("Console Log thread started")

        # -- Initialize tabs
        self.tabs = QTabWidget()
        self.t_main = TabMain(self)
        self.t_mnconf = TabMNConf(self)
        self.t_rewards = TabRewards(self)
        self.t_governance = TabGovernance(self)

        # -- Add tabs
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.addTab(self.tabMain, "Masternode List")
        # self.tabs.addTab(self.tabMNConf, "MN Configuration")
        self.tabs.addTab(self.tabRewards, "Rewards")
        self.tabs.addTab(self.tabGovernance, "Governance")

        # -- Connect change action
        self.tabs.currentChanged.connect(lambda: self.onTabChange())

        # -- Add tabs and console to Layout
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.tabs)
        self.splitter.addWidget(self.console)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.layout.addWidget(self.splitter)

        # -- Set Layout
        self.setLayout(self.layout)

        # -- Init Settings
        self.initSettings()

        # -- Connect buttons/signals
        self.connButtons()

        # -- Check version
        self.onCheckVersion()

        # -- Create RPC Whatchdog
        self.rpc_watchdogThread = QThread()
        self.myRpcWd = RpcWatchdog(self)
        self.myRpcWd.moveToThread(self.rpc_watchdogThread)
        self.rpc_watchdogThread.started.connect(self.myRpcWd.run)

        # -- Let's go
        self.mnode_to_change = None
        printOK(f"Hello! Welcome to {parent.title}")

    def append_to_console(self, text):
        self.consoleArea.moveCursor(QTextCursor.End)
        self.consoleArea.insertHtml(text)

    def clearHWstatus(self, message=''):
        self.hwStatus = 0
        self.hwStatusMess = "Not Connected"
        self.header.hwLed.setPixmap(self.ledGrayH_icon)
        if message != '':
            self.hwStatus = 1
            myPopUp_sb(self, "crit", "hw device Disconnected", message)

    def clearRPCstatus(self):
        with self.lock:
            self.rpcConnected = False
            self.header.lastPingBox.setHidden(False)
            self.header.rpcLed.setPixmap(self.ledGrayH_icon)
            self.header.lastBlockLabel.setText("<em>Connecting...</em>")
            self.header.lastPingIcon.setPixmap(self.connRed_icon)
            self.header.responseTimeLabel.setText("--")
            self.header.responseTimeLabel.setStyleSheet("color: red")
            self.header.lastPingIcon.setStyleSheet("color: red")

    def connButtons(self):
        self.header.button_checkRpc.clicked.connect(lambda: self.onCheckRpc())
        self.header.button_checkHw.clicked.connect(lambda: self.onCheckHw())
        self.header.rpcClientsBox.currentIndexChanged.connect(self.onChangeSelectedRPC)
        self.header.hwDevices.currentIndexChanged.connect(self.onChangeSelectedHW)

        # -- Connect signals
        self.sig_clearRPCstatus.connect(self.clearRPCstatus)
        self.sig_RPCstatusUpdated.connect(self.showRPCstatus)
        self.parent.sig_changed_rpcServers.connect(self.updateRPClist)
        self.tabMain.myList.model().rowsMoved.connect(self.saveMNListOrder)

    def getRPCserver(self):
        itemData = self.header.rpcClientsBox.itemData(self.header.rpcClientsBox.currentIndex())
        rpc_index = self.header.rpcClientsBox.currentIndex()
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
        self.consoleArea.setReadOnly(True)
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
        # -- Hide console if it was previously hidden
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
        if hot_masternodes is None:
            messText = f"Unable to load data from file '{fileName}'"
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
                final_message = f"{new_nodes} External Masternodes "
            final_message += "added to the list."
            if new_nodes > 0:
                final_message += f"<br>{[x['name'] for x in new_masternodes]}.  "
            printOK(final_message)
            if len(skip_masternodes) > 0:
                final_message = "Following entries skipped due to duplicate names:<br>" \
                f"{[x['name'] for x in skip_masternodes]}.  "
                printOK(final_message)

    def onCheckHw(self):
        printDbg("Checking for HW device...")
        self.updateHWstatus(None)
        self.showHWstatus()

    def onCheckRpc(self):
        self.runInThread(self.updateRPCstatus, (True,), )

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
                (remote_version[0] == local_version[0] and remote_version[1] == local_version[1] and remote_version[2] >
                 local_version[2]):
            self.versionMess = f'<b style="color:red">New Version Available:</b> {self.gitVersion}  ' \
                        '(<a href="https://github.com/PIVX-Project/PIVX-SPMT/releases/">download</a>)'
        else:
            self.versionMess = "You have the latest version of SPMT"

    def updateVersion(self):
        if self.versionMess is not None:
            self.versionLabel.setText(self.versionMess)
        printOK(f"Remote version: {self.gitVersion}")

    def onChangeSelectedHW(self, i):
        # Clear status
        self.clearHWstatus()

        # Persist setting
        self.parent.cache['selectedHW_index'] = persistCacheSetting('cache_HWindex', i)

    def onChangeSelectedRPC(self, i):
        # Don't update when we are clearing the box
        if not self.updatingRPCbox:
            # persist setting
            self.parent.cache['selectedRPC_index'] = persistCacheSetting('cache_RPCindex', i)
            self.runInThread(self.updateRPCstatus, (True,), )

    def onCleanConsole(self):
        self.consoleArea.clear()

    def onSaveConsole(self):
        timestamp = now().strftime('%Y-%m-%d_%H-%M-%S')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Logs to file", f"SPMT_Logs_{timestamp}.txt", "All Files (*);; Text Files (*.txt)", options=options)
        try:
            if fileName:
                printOK(f"Saving logs to {fileName}")
                log_file = open(fileName, 'w+', encoding="utf-8")
                log_text = self.consoleArea.toPlainText()
                log_file.write(log_text)
                log_file.close()

        except Exception as e:
            err_msg = f"error writing Log file"
            printException(f"{getCallerName()}", f"{getFunctionName()}", f"{err_msg}", f"{e.args}")

    def onTabChange(self):
        # tabRewards
        if self.tabs.currentWidget() == self.tabRewards:
            # reload last used address
            self.tabRewards.destinationLine.setText(self.parent.cache.get("lastAddress"))

        # tabGovernace
        if self.tabs.currentWidget() == self.tabGovernance:
            # update selectedMNlabel (since we might have edited them)
            self.t_governance.updateSelectedMNlabel()

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
        myPopUp_sb(self, "info", 'SPMT - hw check', f"{self.hwStatusMess}")

    def showRPCstatus(self, server_index, fDebug):
        # Update displayed status only if selected server is not changed
        if server_index == self.header.rpcClientsBox.currentIndex():
            self.updateRPCled(fDebug)
            if fDebug:
                myPopUp_sb(self, "info", 'SPMT - rpc check', f"{self.rpcStatusMess}")

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
            self.hwdevice.initDevice(self.header.hwDevices.currentIndex())
            self.hwModel, self.hwStatus, self.hwStatusMess = self.hwdevice.getStatus()
        except Exception as e:
            printDbg(str(e))
            pass

        printDbg(f"status:{self.hwStatus} - mess: {self.hwStatusMess}")

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
                self.header.responseTimeLabel.setText(f"{self.rpcResponseTime}")
                self.header.responseTimeLabel.setStyleSheet(f"color: {color}")
                self.header.lastPingIcon.setStyleSheet(f"color: {color}")

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
        rpc_index, rpc_protocol, rpc_host, rpc_user, rpc_password = self.getRPCserver()
        if fDebug:
            printDbg(f"Trying to connect to RPC {rpc_protocol}://{rpc_host}...")

        try:
            rpcClient = RpcClient(rpc_protocol, rpc_host, rpc_user, rpc_password)
            status, statusMess, lastBlock, r_time1, isTestnet = rpcClient.getStatus()
            isBlockchainSynced, r_time2 = rpcClient.isBlockchainSynced()
        except Exception as e:
            printException(getCallerName(), getFunctionName(), f"exception updating RPC status: {e}")
            # clear status
            self.rpcClient = None
            self.sig_clearRPCstatus.emit()
            return

        rpcResponseTime = None
        if r_time1 is None:
            r_time1 = 0.0
        if r_time2 is None:
            r_time2 = 0.0
            rpcResponseTime = round((r_time1 + r_time2) / 2, 3)

        # Do not update status if the user has selected a different server since the start of updateRPCStatus()
        if rpc_index != self.header.rpcClientsBox.currentIndex():
            return

        with self.lock:
            self.rpcClient = rpcClient
            self.rpcConnected = status
            self.rpcLastBlock = lastBlock
            self.rpcStatusMess = statusMess
            self.isBlockchainSynced = isBlockchainSynced
            self.rpcResponseTime = rpcResponseTime
            # if testnet flag is changed, update api client and persist setting
            if isTestnet != self.isTestnetRPC:
                self.isTestnetRPC = isTestnet
                self.parent.cache['isTestnetRPC'] = persistCacheSetting('isTestnetRPC', isTestnet)
                self.apiClient = ApiClient(isTestnet)
        self.sig_RPCstatusUpdated.emit(rpc_index, fDebug)
