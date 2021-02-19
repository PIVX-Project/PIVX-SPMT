#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import threading
import simplejson as json

from PyQt5.Qt import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView

from constants import MINIMUM_FEE
from misc import printDbg, printError, printException, getCallerName, getFunctionName, \
    persistCacheSetting, myPopUp, myPopUp_sb, DisconnectedException, checkTxInputs
from pivx_parser import ParseTx, IsPayToColdStaking, GetDelegatedStaker
from qt.gui_tabRewards import TabRewards_gui
from threads import ThreadFuns
from txCache import TxCache
from utils import checkPivxAddr


class TabRewards():

    def __init__(self, caller):
        self.caller = caller
        # --- Lock for loading UTXO thread
        self.runInThread = ThreadFuns.runInThread
        self.Lock = threading.Lock()

        # --- Initialize Selection
        self.selectedRewards = None
        self.feePerKb = MINIMUM_FEE
        self.suggestedFee = MINIMUM_FEE

        # --- Initialize GUI
        self.ui = TabRewards_gui(caller.imgDir)
        self.caller.tabRewards = self.ui

        # load last used destination from cache
        self.ui.destinationLine.setText(self.caller.parent.cache.get("lastAddress"))

        # init first selected MN
        self.loadMnSelect(True)         # loads masternodes list in MnSelect and display utxos
        self.updateFee()

        # Connect GUI buttons
        self.ui.mnSelect.currentIndexChanged.connect(lambda: self.onChangeSelectedMN())
        self.ui.btn_toggleCollateral.clicked.connect(lambda: self.onToggleCollateral())
        self.ui.rewardsList.box.itemClicked.connect(lambda: self.updateSelection())
        self.ui.btn_selectAllRewards.clicked.connect(lambda: self.onSelectAllRewards())
        self.ui.btn_deselectAllRewards.clicked.connect(lambda: self.onDeselectAllRewards())
        self.ui.btn_sendRewards.clicked.connect(lambda: self.onSendRewards())
        self.ui.btn_Cancel.clicked.connect(lambda: self.onCancel())
        self.ui.btn_ReloadUTXOs.clicked.connect(lambda: self.onReloadUTXOs())

        # Connect Signals
        self.caller.sig_UTXOsLoading.connect(self.update_loading_utxos)

    def display_mn_utxos(self):
        if self.curr_name is None:
            return

        # update fee
        if self.caller.rpcConnected:
            self.feePerKb = self.caller.rpcClient.getFeePerKb()
            if self.feePerKb is None:
                self.feePerKb = MINIMUM_FEE
        else:
            self.feePerKb = MINIMUM_FEE

        rewards = self.caller.parent.db.getRewardsList(self.curr_name)
        self.updateTotalBalance(rewards)

        if rewards is not None:
            def item(value):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                return item

            # Clear up old list
            self.ui.rewardsList.box.setRowCount(0)
            # Make room for new list
            self.ui.rewardsList.box.setRowCount(len(rewards))
            # Insert items
            for row, utxo in enumerate(rewards):
                txId = utxo.get('txid', None)
                pivxAmount = round(int(utxo.get('satoshis', 0))/1e8, 8)
                self.ui.rewardsList.box.setItem(row, 0, item(str(pivxAmount)))
                self.ui.rewardsList.box.setItem(row, 1, item(str(utxo.get('confirmations', None))))
                self.ui.rewardsList.box.setItem(row, 2, item(txId))
                self.ui.rewardsList.box.setItem(row, 3, item(str(utxo.get('vout', None))))
                self.ui.rewardsList.box.showRow(row)
                # mark cold utxos
                if utxo['staker'] != "":
                    self.ui.rewardsList.box.item(row, 2).setIcon(self.caller.tabMain.coldStaking_icon)
                    self.ui.rewardsList.box.item(row, 2).setToolTip("Staked by <b>%s</b>" % utxo['staker'])

                # MARK COLLATERAL UTXO
                if txId == self.curr_txid:
                    for i in range(0,4):
                        self.ui.rewardsList.box.item(row, i).setFont(QFont("Arial", 9, QFont.Bold))
                    self.ui.rewardsList.box.collateralRow = row

                # make immature rewards unselectable
                if utxo['coinstake']:
                    required = 16 if self.caller.isTestnetRPC else 101
                    if utxo['confirmations'] < required:
                        for i in range(0,4):
                            self.ui.rewardsList.box.item(row, i).setFlags(Qt.NoItemFlags)
                            ttip = self.ui.rewardsList.box.item(row, i).toolTip()
                            self.ui.rewardsList.box.item(row, i).setToolTip(
                                ttip + "\n(Immature - %d confirmations required)" % required)

            self.ui.rewardsList.box.resizeColumnsToContents()

            if self.ui.rewardsList.box.collateralRow is not None:
                    self.ui.rewardsList.box.hideRow(self.ui.rewardsList.box.collateralRow)

            if len(rewards) > 1:  # (collateral is a reward)
                self.ui.rewardsList.statusLabel.setVisible(False)
                self.ui.rewardsList.box.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            else:
                if not self.caller.rpcConnected:
                    self.ui.resetStatusLabel('<b style="color:red">PIVX wallet not connected</b>')
                else:
                    self.ui.resetStatusLabel('<b style="color:red">Found no Rewards for %s</b>' % self.curr_addr)

    def getSelection(self):
        # Get selected rows indexes
        items = self.ui.rewardsList.box.selectedItems()
        rows = set()
        for i in range(0, len(items)):
            row = items[i].row()
            rows.add(row)
        indexes = list(rows)
        # Get UTXO info from DB for each
        selection = []
        for idx in indexes:
            txid = self.ui.rewardsList.box.item(idx, 2).text()
            txidn = int(self.ui.rewardsList.box.item(idx, 3).text())
            selection.append(self.caller.parent.db.getReward(txid, txidn))

        return selection

    def loadMnSelect(self, isInitializing=False):
        # save previous index
        index = 0
        if self.ui.mnSelect.count() > 0:
            index = self.ui.mnSelect.currentIndex()

        self.ui.mnSelect.clear()

        for x in self.caller.masternode_list:
            if x['isHardware']:
                name = x['name']
                address = x['collateral'].get('address')
                txid = x['collateral'].get('txid')
                txidn = x['collateral'].get('txidn')
                hwAcc = x['hwAcc']
                spath = x['collateral'].get('spath')
                hwpath = "%d'/0/%d" % (hwAcc, spath)
                self.ui.mnSelect.addItem(name, [address, txid, txidn, hwpath])

        # restore previous index
        if index < self.ui.mnSelect.count():
            self.ui.mnSelect.setCurrentIndex(index)

        self.onChangeSelectedMN(isInitializing)

    def load_utxos_thread(self, ctrl):
        with self.Lock:
            # clear rewards DB
            printDbg("Updating rewards...")
            self.caller.parent.db.clearTable('REWARDS')
            self.caller.parent.db.clearTable('MY_VOTES')

            # If rpc is not connected and hw device is Ledger, warn and return.
            if not self.caller.rpcConnected and self.caller.hwModel == 0:
                printError(getCallerName(), getFunctionName(), 'PIVX daemon not connected - Unable to update UTXO list')
                return

            total_num_of_utxos = 0
            mn_rewards = {}
            for mn in self.caller.masternode_list:
                # Load UTXOs from API client
                rewards = self.caller.apiClient.getAddressUtxos(mn['collateral'].get('address'))

                if rewards is None:
                    printError(getCallerName(), getFunctionName(), 'API client not responding.')
                    return

                mn_rewards[mn['name']] = rewards
                total_num_of_utxos += len(rewards)

            printDbg("Number of UTXOs to load: %d" % total_num_of_utxos)
            curr_utxo = 0

            for mn in mn_rewards:
                for utxo in mn_rewards[mn]:
                    # Add mn_name to UTXO
                    utxo['mn_name'] = mn
                    # Get raw tx
                    rawtx = TxCache(self.caller)[utxo['txid']]
                    if rawtx is None:
                        printDbg("Unable to get raw TX with hash=%s from RPC server." % utxo['txid'])
                        # Don't save UTXO if raw TX is unavailable
                        mn_rewards[mn].remove(utxo)
                        continue
                    utxo['raw_tx'] = rawtx
                    utxo['staker'] = ""
                    p2cs, utxo['coinstake'] = IsPayToColdStaking(rawtx, utxo['vout'])
                    if p2cs:
                        utxo['staker'] = GetDelegatedStaker(rawtx, utxo['vout'], self.caller.isTestnetRPC)
                    # Add utxo to database
                    self.caller.parent.db.addReward(utxo)

                    # emit percent
                    percent = int(100 * curr_utxo / total_num_of_utxos)
                    self.caller.sig_UTXOsLoading.emit(percent)
                    curr_utxo += 1

            printDbg("--# REWARDS table updated")
            self.caller.sig_UTXOsLoading.emit(100)

    def onCancel(self):
        self.ui.rewardsList.box.clearSelection()
        self.selectedRewards = None
        self.ui.selectedRewardsLine.setText("0.0")
        self.suggestedFee = MINIMUM_FEE
        self.updateFee()
        self.ui.btn_toggleCollateral.setText("Show Collateral")
        self.ui.collateralHidden = True
        self.AbortSend()

    def onChangedMNlist(self):
        # reload MnSelect
        self.loadMnSelect()
        # reload utxos
        self.onReloadUTXOs()

    def onChangeSelectedMN(self, isInitializing=False):
        self.curr_name = None
        if self.ui.mnSelect.currentIndex() >= 0:
            self.curr_name = self.ui.mnSelect.itemText(self.ui.mnSelect.currentIndex())
            self.curr_addr = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[0]
            self.curr_txid = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[1]
            self.curr_txidn = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[2]
            self.curr_hwpath = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[3]
            self.ui.rewardsList.box.collateralRow = None
            self.onCancel()
            # If we are initializing the class, don't display_mn_utxos. It's still empty
            if not isInitializing:
                self.ui.resetStatusLabel()
                self.display_mn_utxos()

    def onSelectAllRewards(self):
        self.ui.rewardsList.box.selectAll()
        self.updateSelection()

    def onDeselectAllRewards(self):
        self.ui.rewardsList.box.clearSelection()
        self.updateSelection()

    def onReloadUTXOs(self):
        if not self.Lock.locked():
            self.ui.resetStatusLabel()
            self.runInThread(self.load_utxos_thread, ())

    def onSendRewards(self):
        self.dest_addr = self.ui.destinationLine.text().strip()
        self.currFee = self.ui.feeLine.value() * 1e8
        # Check spending collateral
        if (not self.ui.collateralHidden and
                self.ui.rewardsList.box.collateralRow is not None and
                self.ui.rewardsList.box.item(self.ui.rewardsList.box.collateralRow, 0).isSelected() ):
            warning1 = "Are you sure you want to transfer the collateral?"
            warning2 = "Really?"
            warning3 = "Take a deep breath. Do you REALLY want to transfer your collateral?"
            ans = myPopUp(self.caller, "warn", 'SPMT - warning', warning1)
            if ans == QMessageBox.No:
                return None
            else:
                ans2 = myPopUp(self.caller, "warn", 'SPMT - warning', warning2)
                if ans2 == QMessageBox.No:
                    return None
                else:
                    ans2 = myPopUp(self.caller, "crit", 'SPMT - warning', warning3)
                    if ans2 == QMessageBox.No:
                        return None
        # Check HW device
        while self.caller.hwStatus != 2:
            mess = "HW device not connected. Try to connect?"
            ans = myPopUp(self.caller, QMessageBox.Question, 'SPMT - hw check', mess)
            if ans == QMessageBox.No:
                return
            # re connect
            self.caller.onCheckHw()
        # SEND
        self.SendRewards()

    def SendRewards(self, inputs=None, gui=None):
        # Default slots on tabRewards
        if gui is None:
            gui = self

        # re-connect signals
        try:
            self.caller.hwdevice.api.sigTxdone.disconnect()
        except:
            pass
        try:
            self.caller.hwdevice.api.sigTxabort.disconnect()
        except:
            pass
        try:
            self.caller.hwdevice.api.tx_progress.disconnect()
        except:
            pass
        self.caller.hwdevice.api.sigTxdone.connect(gui.FinishSend)
        self.caller.hwdevice.api.sigTxabort.connect(gui.AbortSend)
        self.caller.hwdevice.api.tx_progress.connect(gui.updateProgressPercent)

        # Check destination Address
        if not checkPivxAddr(self.dest_addr, self.caller.isTestnetRPC):
            myPopUp_sb(self.caller, "crit", 'SPMT - PIVX address check', "The destination address is missing, or invalid.")
            return None

        if inputs is None:
            # send from single path
            num_of_inputs = len(self.selectedRewards)
        else:
            # bulk send
            num_of_inputs = sum([len(x['utxos']) for x in inputs])
        ans = checkTxInputs(self.caller, num_of_inputs)
        if ans is None or ans == QMessageBox.No:
            # emit sigTxAbort and return
            self.caller.hwdevice.api.sigTxabort.emit()
            return None

        # LET'S GO
        if inputs is None:
            printDbg("Sending from PIVX address  %s  to PIVX address  %s " % (self.curr_addr, self.dest_addr))
        else:
            printDbg("Sweeping rewards to PIVX address %s " % self.dest_addr)
        printDbg("Preparing transaction. Please wait...")
        self.ui.loadingLine.show()
        self.ui.loadingLinePercent.show()
        QApplication.processEvents()

        # save last destination address to cache and persist to settings
        self.caller.parent.cache["lastAddress"] = persistCacheSetting('cache_lastAddress', self.dest_addr)

        try:
            self.txFinished = False
            if inputs is None:
                # send from single path
                self.caller.hwdevice.prepare_transfer_tx(self.caller,
                                                         self.curr_hwpath,
                                                         self.selectedRewards,
                                                         self.dest_addr,
                                                         self.currFee,
                                                         self.caller.isTestnetRPC)
            else:
                # bulk send
                self.caller.hwdevice.prepare_transfer_tx_bulk(self.caller,
                                                              inputs,
                                                              self.dest_addr,
                                                              self.currFee,
                                                              self.caller.isTestnetRPC)

        except DisconnectedException as e:
            self.caller.hwStatus = 0
            self.caller.updateHWleds()

        except Exception as e:
            err_msg = "Error while preparing transaction. <br>"
            err_msg += "Probably Blockchain wasn't synced when trying to fetch raw TXs.<br>"
            err_msg += "<b>Wait for full synchronization</b> then hit 'Clear/Reload'"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)

    def onToggleCollateral(self):
        if self.ui.rewardsList.box.collateralRow is not None:
            if not self.ui.collateralHidden:
                try:
                    # If collateral row was selected, deselect it before hiding
                    if self.ui.rewardsList.box.item(self.ui.rewardsList.box.collateralRow, 0).isSelected():
                        self.ui.rewardsList.box.selectRow(self.ui.rewardsList.box.collateralRow)
                except Exception as e:
                    err_msg = "Error toggling collateral"
                    printException(getCallerName(), getFunctionName(), err_msg, e.args)

                self.ui.rewardsList.box.hideRow(self.ui.rewardsList.box.collateralRow)
                self.ui.btn_toggleCollateral.setText("Show Collateral")
                self.ui.collateralHidden = True
                self.updateSelection()
            else:
                self.ui.rewardsList.box.showRow(self.ui.rewardsList.box.collateralRow)
                self.ui.btn_toggleCollateral.setText("Hide Collateral")
                self.ui.collateralHidden = False
                self.updateSelection()
                self.ui.rewardsList.box.resizeColumnsToContents()
                self.ui.rewardsList.box.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        else:
            myPopUp_sb(self.caller, "warn", 'No Collateral', "No collateral selected")

    def removeSpentRewards(self):
        if self.selectedRewards is not None:
            for utxo in self.selectedRewards:
                self.caller.parent.db.deleteReward(utxo['txid'], utxo['vout'])
        else:
            self.caller.parent.db.clearTable('REWARDS')

    # Activated by signal sigTxdone from hwdevice
    def FinishSend(self, serialized_tx, amount_to_send):
        self.AbortSend()
        self.FinishSend_int(serialized_tx, amount_to_send)

    def FinishSend_int(self, serialized_tx, amount_to_send):
        if not self.txFinished:
            try:
                self.txFinished = True
                tx_hex = serialized_tx.hex()
                printDbg("Raw signed transaction: " + tx_hex)
                printDbg("Amount to send :" + amount_to_send)

                if len(tx_hex) > 90000:
                    mess = "Transaction's length exceeds 90000 bytes. Select less UTXOs and try again."
                    myPopUp_sb(self.caller, "crit", 'transaction Warning', mess)

                else:
                    decodedTx = None
                    try:
                        decodedTx = ParseTx(tx_hex, self.caller.isTestnetRPC)
                        destination = decodedTx.get("vout")[0].get("scriptPubKey").get("addresses")[0]
                        amount = decodedTx.get("vout")[0].get("value")
                        message = '<p>Broadcast signed transaction?</p><p>Destination address:<br><b>%s</b></p>' % destination
                        message += '<p>Amount: <b>%s</b> PIV<br>' % str(round(amount / 1e8, 8))
                        message += 'Fees: <b>%s</b> PIV <br>Size: <b>%d</b> Bytes</p>' % (str(round(self.currFee / 1e8, 8) ), len(tx_hex)/2)
                    except Exception as e:
                        printException(getCallerName(), getFunctionName(), "decoding exception", str(e))
                        message = '<p>Unable to decode TX- Broadcast anyway?</p>'

                    mess1 = QMessageBox(QMessageBox.Information, 'Send transaction', message, parent=self.caller)
                    if decodedTx is not None:
                        mess1.setDetailedText(json.dumps(decodedTx, indent=4, sort_keys=False))
                    mess1.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

                    reply = mess1.exec_()
                    if reply == QMessageBox.Yes:
                        txid = self.caller.rpcClient.sendRawTransaction(tx_hex)
                        if txid is None:
                            raise Exception("Unable to send TX - connection to RPC server lost.")
                        printDbg("Transaction sent. ID: %s" % txid)
                        mess2_text = "<p>Transaction successfully sent.</p>"
                        mess2 = QMessageBox(QMessageBox.Information, 'transaction Sent', mess2_text, parent=self.caller)
                        mess2.setDetailedText(txid)
                        mess2.exec_()
                        # remove spent rewards from DB
                        self.removeSpentRewards()
                        # reload utxos
                        self.display_mn_utxos()
                        self.onCancel()

                    else:
                        myPopUp_sb(self.caller, "warn", 'Transaction NOT sent', "Transaction NOT sent")
                        self.onCancel()

            except Exception as e:
                err_msg = "Exception in FinishSend"
                printException(getCallerName(), getFunctionName(), err_msg, e.args)

    # Activated by signal sigTxabort from hwdevice
    def AbortSend(self):
        self.ui.loadingLine.hide()
        self.ui.loadingLinePercent.setValue(0)
        self.ui.loadingLinePercent.hide()

    def updateFee(self):
        self.ui.feeLine.setValue(self.suggestedFee)
        self.ui.feeLine.setEnabled(True)

    # Activated by signal tx_progress from hwdevice
    def updateProgressPercent(self, percent):
        self.ui.loadingLinePercent.setValue(percent)
        QApplication.processEvents()

    def updateSelection(self, clicked_item=None):
        total = 0
        self.selectedRewards = self.getSelection()
        numOfInputs = len(self.selectedRewards)
        if numOfInputs:
            for i in range(0, numOfInputs):
                total += int(self.selectedRewards[i].get('satoshis'))

            # update suggested fee and selected rewards
            estimatedTxSize = (44+numOfInputs*148)*1.0 / 1000   # kB
            self.suggestedFee = round(self.feePerKb * estimatedTxSize, 8)
            printDbg("estimatedTxSize is %s kB" % str(estimatedTxSize))
            printDbg("suggested fee is %s PIV (%s PIV/kB)" % (str(self.suggestedFee), str(self.feePerKb)))

            self.ui.selectedRewardsLine.setText(str(round(total/1e8, 8)))

        else:
            self.ui.selectedRewardsLine.setText("")

        self.updateFee()

    def update_loading_utxos(self, percent):
        if percent < 100:
            self.ui.resetStatusLabel('<em><b style="color:purple">Checking explorer... %d%%</b></em>' % percent)
        else:
            self.display_mn_utxos()

    def updateTotalBalance(self, rewards):
        nAmount = 0
        if rewards is not None:
            for utxo in rewards:
                nAmount = nAmount + utxo['satoshis']

        totalBalance = str(round(nAmount/1e8, 8))
        self.ui.addrAvailLine.setText("<i>%s PIVs</i>" % totalBalance)
