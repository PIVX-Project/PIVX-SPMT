#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import logging
import simplejson as json
import time

from PyQt5.Qt import QApplication
from PyQt5.QtWidgets import QMessageBox

from masternode import Masternode
from misc import printDbg, printException, printOK, getCallerName, getFunctionName, \
    removeMNfromList, myPopUp, myPopUp_sb
from qt.gui_tabMain import TabMain_gui
from qt.dlg_mnStatus import MnStatus_dlg
from qt.dlg_sweepAll import SweepAll_dlg
from threads import ThreadFuns


class TabMain:
    def __init__(self, caller):
        self.caller = caller
        self.all_masternodes = {}
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
            printDbg(f"Checking {masternode['name']} ({masternode['collateral'].get('txid')})...")
            self.displayMNStatus(masternode)
            time.sleep(0.1)

    def displayMNStatus(self, currMN):
        statusData = None
        for mn in self.all_masternodes.get('masternodes'):
            # find the balance of currMN and display it
            if mn.get('txhash') == currMN['collateral'].get('txid') and mn.get('outidx') == currMN['collateral'].get('txidn'):
                statusData = mn
                try:
                    statusData['balance'] = self.caller.apiClient.getBalance(mn.get('addr'))
                except Exception as e:
                    err_msg = f"error getting balance of {mn.get('addr')}"
                    printException(f"{getCallerName()}", f"{getFunctionName()}", f"{err_msg}", f"{e}")

        masternode_alias = currMN['name']
        self.ui.btn_details[masternode_alias].disconnect()
        self.ui.btn_details[masternode_alias].clicked.connect(lambda: self.onDisplayStatusDetails(masternode_alias, statusData))
        self.ui.btn_details[masternode_alias].show()

        if statusData is None:
            printOK(f"{masternode_alias} Not Found")
            self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledGrayV_icon)
            msg = "<b>Masternode not found.</b>"
            self.ui.mnStatusLabel[masternode_alias].setText(msg)
            self.ui.mnStatusLabel[masternode_alias].show()
            self.ui.btn_details[masternode_alias].setEnabled(False)
        else:
            display_text = ""
            if statusData['balance'] is not None:
                self.ui.mnBalance[masternode_alias].setText(f'&nbsp;<span style="color:purple">{statusData["balance"]} PIV</span>')
                self.ui.mnBalance[masternode_alias].show()
            printOK(f"Got status {statusData['status']} for {masternode_alias}")
            if statusData['status'] == 'ENABLED':
                self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledGreenV_icon)
                display_text += f'<span style="color:green">{statusData["status"]}</span>&nbsp;&nbsp;'
                position = statusData.get('queue_pos')
                total_count = len(self.all_masternodes.get('masternodes'))
                display_text += f'{position}/{total_count}'

                self.ui.mnStatusProgress[masternode_alias].setRange(0, total_count)
                self.ui.mnStatusProgress[masternode_alias].setValue(total_count - position)
                self.ui.mnStatusProgress[masternode_alias].show()
            else:
                self.ui.mnLed[masternode_alias].setPixmap(self.caller.ledRedV_icon)
                display_text += f'<span style="color:red">{statusData["status"]}</span>&nbsp;&nbsp;'

            self.ui.mnStatusLabel[masternode_alias].setText(display_text)
            self.ui.mnStatusLabel[masternode_alias].show()
            self.ui.btn_details[masternode_alias].setEnabled(True)
        QApplication.processEvents()

    def onCheckAllMN(self):
        if not self.caller.rpcConnected:
            myPopUp_sb(self.caller, "crit", 'SPMT - hw device check',
                       "RPC server must be connected to perform this action.")
            printDbg(f"Unable to connect: {self.caller.rpcStatusMess}")
            return
        if self.caller.masternode_list is None or self.caller.masternode_list == []:
            myPopUp_sb(self.caller, "crit", 'SPMT - Check-All masternodes',
                       "No masternode in list. Add masternodes first.")
            return
        try:
            printDbg("Check-All pressed")
            ThreadFuns.runInThread(self.updateAllMasternodes_thread, (), self.displayMNlistUpdated)

        except Exception as e:
            err_msg = "error in checkAllMN"
            printException(getCallerName(), getFunctionName(), err_msg, e)

    def onDisplayStatusDetails(self, masternode_alias, statusData):
        try:
            ui = MnStatus_dlg(self.ui, masternode_alias, statusData)
            ui.exec_()

        except Exception as e:
            err_msg = "error in displayStatusDetails"
            printException(f"{getCallerName()}", f"{getFunctionName()}", f"{err_msg}", f"{e.args}")

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

    def onNewMasternode(self):
        self.caller.tabs.insertTab(1, self.caller.tabMNConf, "Configuration")
        self.caller.tabMNConf.clearConfigForm()
        self.caller.tabs.setCurrentIndex(1)

    def onRemoveMN(self, data=None):
        if not data:
            target = self.ui.sender()
            masternode_alias = target.alias

            reply = myPopUp(self.caller, "warn", 'Confirm REMOVE',
                            f"Are you sure you want to remove\nmasternoode:'{masternode_alias}'", QMessageBox.No)

            if reply == QMessageBox.No:
                return

            for masternode in self.caller.masternode_list:
                if masternode['name'] == masternode_alias:
                    # remove from cache, QListWidget and DB
                    removeMNfromList(self.caller, masternode)
                    break

    def onRewardsMN(self, data=None):
        if not data:
            target = self.ui.sender()
            masternode_alias = target.alias
            tab_index = self.caller.tabs.indexOf(self.caller.tabRewards)
            self.caller.tabs.setCurrentIndex(tab_index)
            self.caller.tabRewards.mnSelect.setCurrentText(masternode_alias)

    def onStartAllMN(self):
        printOK("Start-All pressed")
        # Check RPC & HW device
        if not self.caller.rpcConnected or self.caller.hwStatus != 2:
            myPopUp_sb(self.caller, "crit", 'SPMT - hw/rpc device check', "Connect to RPC server and HW device first")
            printDbg("Hardware device or RPC server not connected")
            return None

        try:
            reply = myPopUp(self.caller, "quest", 'Confirm START',
                            "Are you sure you want to start ALL masternodes?", QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                mnList = [x for x in self.caller.masternode_list if x['isHardware']]
                for mn_conf in mnList:
                    self.masternodeToStart = Masternode(self, mn_conf['name'], mn_conf['ip'], mn_conf['port'],
                                                        mn_conf['mnPrivKey'], mn_conf['hwAcc'], mn_conf['collateral'],
                                                        mn_conf['isTestnet'])
                    # connect signal
                    self.masternodeToStart.sigdone.connect(self.sendBroadcast)
                    self.mnToStartList.append(self.masternodeToStart)

                self.startMN()

        except Exception as e:
            err_msg = "error before starting node"
            printException(f"{getCallerName()}", f"{getFunctionName()}", f"{err_msg}", f"{e}")

    def onStartMN(self, data=None):
        # Check RPC & HW device
        if not self.caller.rpcConnected or self.caller.hwStatus != 2:
            myPopUp_sb(self.caller, "crit", 'SPMT - hw/rpc device check', "Connect to RPC server and HW device first")
            printDbg("Hardware device or RPC server not connected")
            return None
        try:
            if not data:
                target = self.ui.sender()
                masternode_alias = target.alias
                printOK(f"Start-masternode {masternode_alias} pressed")
                for mn_conf in self.caller.masternode_list:
                    if mn_conf['name'] == masternode_alias:
                        reply = myPopUp(self.caller, QMessageBox.Question, 'Confirm START',
                                        f"Are you sure you want to start masternoode:\n'{mn_conf['name']}'?",
                                        QMessageBox.Yes)
                        if reply == QMessageBox.Yes:
                            self.masternodeToStart = Masternode(self, mn_conf['name'], mn_conf['ip'], mn_conf['port'],
                                                                mn_conf['mnPrivKey'], mn_conf['hwAcc'],
                                                                mn_conf['collateral'], mn_conf['isTestnet'])
                            # connect signal
                            self.masternodeToStart.sigdone.connect(self.sendBroadcast)
                            self.mnToStartList.append(self.masternodeToStart)
                            self.startMN()
                        break

        except Exception as e:
            err_msg = "error before starting node"
            printException(f"{getCallerName()}", f"{getFunctionName()}", f"{err_msg}", f"{e}")

    def onSweepAllRewards(self):
        if not self.caller.rpcConnected:
            myPopUp_sb(self.caller, "crit", 'SPMT - rpc check', "Connect to wallet / RPC server first")
            return None
        try:
            self.sweepAllDlg.showDialog()

        except Exception as e:
            err_msg = "exception in SweepAll_dlg"
            printException(f"{getCallerName()}", f"{getFunctionName()}", f"{err_msg}", f"{e}")

    # Activated by signal 'sigdone' from masternode
    def sendBroadcast(self, text):
        if text == "None":
            self.sendBroadcastCheck()
            return

        printOK("Start Message ready for being relayed...")
        logging.debug(f"Start Message: {text}")
        ret = self.caller.rpcClient.decodemasternodebroadcast(text)
        if ret is None:
            myPopUp_sb(self.caller, "crit", 'message decoding failed', 'message decoding failed')
            printDbg("Message decoding failed")
            self.sendBroadcastCheck()
            return

        msg = "Broadcast START message?\n" + json.dumps(ret, indent=4, sort_keys=True)
        reply = myPopUp(self.caller, "quest", 'message decoded', f"{msg}", QMessageBox.Yes)
        if reply == QMessageBox.No:
            self.sendBroadcastCheck()
            return

        ret2 = self.caller.rpcClient.relaymasternodebroadcast(text)

        if json.dumps(ret2)[1:26] == "Masternode broadcast sent":
            printOK("Masternode broadcast sent")
            message = "Start-message was successfully sent to the network.<br>"
            message += "If your remote server is correctly configured and connected to the network, "
            message += "the output of the <b>./pivx-cli getmasternodestatus</b> command on the VPS should show:<br>"
            message += "<br><em>\"message\": \"Masternode successfully started\"</em>"
            myPopUp_sb(self.caller, "info", 'message relayed', f"{message}")
        else:
            printDbg("Masternode broadcast NOT sent")
            printException(f"{getCallerName()}", f"{getFunctionName()}", f"{json.dumps(ret2)}", "Error sending masternode broadcast")

        self.sendBroadcastCheck()

    def sendBroadcastCheck(self):
        # If list is not empty, start other masternodes
        if self.mnToStartList:
            self.startMN()

    def startMN(self):
        if self.caller.hwStatus != 2:
            myPopUp_sb(self.caller, "warn", 'SPMT - hw device check', f"{self.caller.hwStatusMess}")
        elif not self.caller.rpcConnected:
            myPopUp_sb(self.caller, "warn", 'SPMT - rpc device check', f"{self.caller.rpcStatusMess}")
        else:
            self.masternodeToStart = self.mnToStartList.pop()
            printDbg(f"Starting...{self.masternodeToStart.name}")
            self.masternodeToStart.startMessage(self.caller.hwdevice, self.caller.rpcClient)
            # wait for signal when masternode.work is ready then ---> sendBroadcast

    def updateAllMasternodes_thread(self, ctrl):
        self.all_masternodes = self.caller.rpcClient.getMasternodes()
