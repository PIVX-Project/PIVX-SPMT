#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import simplejson as json

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,\
    QAbstractScrollArea, QHeaderView, QLabel, QLineEdit, QFormLayout, QDoubleSpinBox, QMessageBox,\
    QApplication, QProgressBar, QCheckBox

from constants import MINIMUM_FEE
from misc import printDbg, getCallerName, getFunctionName, printException, persistCacheSetting, \
    myPopUp_sb, DisconnectedException, myPopUp
from pivx_parser import ParseTx
from threads import ThreadFuns
from txCache import TxCache
from utils import checkPivxAddr


class SweepAll_dlg(QDialog):
    # Dialog initialized in TabMain constructor
    def __init__(self, main_tab):
        QDialog.__init__(self, parent=main_tab.ui)
        self.main_tab = main_tab
        self.setWindowTitle('Sweep All Rewards')
        ##--- Initialize Selection
        self.feePerKb = MINIMUM_FEE
        self.suggestedFee = MINIMUM_FEE
        ##--- Initialize GUI
        self.setupUI()
        # Connect GUI buttons
        self.connectButtons()
         # Connect Signals
        self.main_tab.caller.sig_RawTxesLoading.connect(self.update_loading_rawtxes)
        self.main_tab.caller.sig_RawTxesLoaded_sweep.connect(self.sendTx)
        self.main_tab.caller.sig_UTXOsLoading.connect(self.update_loading_utxos)
        self.main_tab.caller.sig_UTXOsLoaded.connect(self.display_utxos)



    # Called each time before exec_ in showDialog
    def load_data(self):
        # disable send button (re-enabled in display_utxos)
        self.ui.buttonSend.setEnabled(False)

        # clear table
        self.ui.tableW.setRowCount(0)
        # load last used destination from cache
        self.ui.edt_destination.setText(self.main_tab.caller.parent.cache.get("lastAddress"))
        # load useSwiftX check from cache
        if self.main_tab.caller.parent.cache.get("useSwiftX"):
            self.ui.swiftxCheck.setChecked(True)
        # Reload UTXOs
        ThreadFuns.runInThread(self.main_tab.caller.t_rewards.load_utxos_thread, ())



    def showDialog(self):
        self.load_data()
        self.exec_()



    def connectButtons(self):
        self.ui.buttonSend.clicked.connect(lambda: self.onButtonSend())
        self.ui.buttonCancel.clicked.connect(lambda: self.onButtonCancel())
        self.ui.swiftxCheck.clicked.connect(lambda: self.updateFee())



    def setupUI(self):
        self.ui = Ui_SweepAllDlg()
        self.ui.setupUi(self)



    def display_utxos(self):
        self.ui.buttonSend.setEnabled(True)
        rewards = self.main_tab.caller.parent.db.getRewardsList()
        self.rewardsArray = []
        for mn in [x for x in self.main_tab.caller.masternode_list if x['isHardware']]:
            x = {}
            x['name'] = mn['name']
            x['addr'] = mn['collateral'].get('address')
            x['path'] = "%d'/0/%d" % (mn['hwAcc'], mn['collateral'].get('spath'))
            x['utxos'] = [r for r in rewards
                          if r['mn_name'] == x['name']                      # this mn's UTXOs
                          and r['txid'] != mn['collateral'].get('txid')  # except the collateral
                          and r['confirmations'] > 100]                     # and immature rewards
            x['total_rewards'] = round(sum([reward['satoshis'] for reward in x['utxos']])/1e8, 8)
            self.rewardsArray.append(x)

        # update fee per Kb
        if self.main_tab.caller.rpcConnected:
            self.feePerKb = self.main_tab.caller.rpcClient.getFeePerKb()
            if self.feePerKb is None:
                self.feePerKb = MINIMUM_FEE
        else:
            self.feePerKb = MINIMUM_FEE

        def item(value):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.NoItemFlags)
            return item

        if len(self.rewardsArray) == 0:
            self.ui.lblMessage.setText("Unable to get raw TX from RPC server\nPlease wait for full synchronization and try again.")

        else:
            self.ui.tableW.setRowCount(len(self.rewardsArray))
            numOfInputs = 0
            for row, mnode in enumerate(self.rewardsArray):
                self.ui.tableW.setItem(row, 0, item(mnode['name']))
                self.ui.tableW.setItem(row, 1, item(mnode['addr']))
                newInputs = len(mnode['utxos'])
                numOfInputs += newInputs
                rewards_line = "%s PIV" % mnode['total_rewards']
                self.ui.tableW.setItem(row, 2, item(rewards_line))
                self.ui.tableW.setItem(row, 3, item(str(newInputs)))

            self.ui.tableW.resizeColumnsToContents()
            self.ui.lblMessage.setVisible(False)
            self.ui.tableW.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

            total = sum([float(mnode['total_rewards']) for mnode in self.rewardsArray])
            self.ui.totalLine.setText("<b>%s PIV</b>" % str(round(total,8)))
            self.ui.noOfUtxosLine.setText("<b>%s</b>" % str(numOfInputs))

            # update fee
            estimatedTxSize = (44+numOfInputs*148)*1.0 / 1000   # kB
            self.suggestedFee = round(self.feePerKb * estimatedTxSize, 8)
            self.updateFee()



    def onButtonCancel(self):
        self.AbortSend()
        self.close()



    def onButtonSend(self):
        # Check HW connection
        while self.main_tab.caller.hwStatus != 2:
            mess = "HW device not connected. Try to connect?"
            ans = myPopUp(self.main_tab.caller, QMessageBox.Question, 'SPMT - hw check', mess)
            if ans == QMessageBox.No:
                return
            # re connect
            self.main_tab.caller.onCheckHw()

        self.dest_addr = self.ui.edt_destination.text().strip()
        self.currFee = self.ui.feeLine.value() * 1e8

        # Check destination Address
        if not checkPivxAddr(self.dest_addr, self.main_tab.caller.isTestnetRPC):
            myPopUp_sb(self.main_tab.caller, "crit", 'SPMT - PIVX address check', "The destination address is missing, or invalid.")
            return None

        # LET'S GO
        printDbg("Sweeping rewards to PIVX address %s " % self.dest_addr)
        ThreadFuns.runInThread(self.load_rawTxes_thread, ())



    def load_rawTxes_thread(self, ctrl):
        # disable send button (re-enabled in AbortSend)
        self.ui.buttonSend.setEnabled(False)
        total_num_of_utxos = sum([len(x['utxos']) for x in self.rewardsArray])
        printDbg("Number of UTXOs to load: %d" % total_num_of_utxos)
        curr_utxo = 0

        for mn in self.rewardsArray:
            for utxo in mn['utxos']:
                rawtx = TxCache(self.main_tab.caller)[utxo['txid']]
                if rawtx is None:
                    printDbg("Unable to get raw TX with hash=%s from RPC server." % utxo['txid'])
                    # Don't save UTXO if raw TX is unavailable
                    mn['utxos'].remove(utxo)
                    continue
                utxo['raw_tx'] = rawtx

                # emit percent
                percent = int(100 * curr_utxo / total_num_of_utxos)
                self.main_tab.caller.sig_RawTxesLoading.emit(percent)
                curr_utxo += 1
        self.main_tab.caller.sig_RawTxesLoaded_sweep.emit()



    def sendTx(self):
        self.ui.lblMessage.hide()
        if sum([len(x['utxos']) for x in self.rewardsArray]) > 0:
            printDbg("Preparing transaction. Please wait...")
            self.ui.loadingLine.show()
            self.ui.loadingLinePercent.show()
            QApplication.processEvents()

            # save last destination address and swiftxCheck to cache and persist to settings
            self.main_tab.caller.parent.cache["lastAddress"] = persistCacheSetting('cache_lastAddress', self.dest_addr)
            self.main_tab.caller.parent.cache["useSwiftX"] = persistCacheSetting('cache_useSwiftX', self.useSwiftX())

            # re-connect signals
            try:
                self.main_tab.caller.hwdevice.api.sigTxdone.disconnect()
            except:
                pass
            try:
                self.main_tab.caller.hwdevice.api.sigTxabort.disconnect()
            except:
                pass
            try:
                self.main_tab.caller.hwdevice.api.tx_progress.disconnect()
            except:
                pass
            self.main_tab.caller.hwdevice.api.sigTxdone.connect(self.FinishSend)
            self.main_tab.caller.hwdevice.api.sigTxabort.connect(self.AbortSend)
            self.main_tab.caller.hwdevice.api.tx_progress.connect(self.updateProgressPercent)

            try:
                self.txFinished = False
                self.main_tab.caller.hwdevice.prepare_transfer_tx_bulk(self.main_tab.caller,
                                                                       self.rewardsArray,
                                                                       self.dest_addr,
                                                                       self.currFee,
                                                                       self.useSwiftX(),
                                                                       self.main_tab.caller.isTestnetRPC)
            except DisconnectedException as e:
                self.main_tab.caller.hwStatus = 0
                self.main_tab.caller.updateHWleds()

            except Exception as e:
                printException(getCallerName(), getFunctionName(), "exception in sendTx", str(e))

        else:
            myPopUp_sb(self.main_tab.caller, "warn", 'Transaction NOT sent', "No UTXO to send")



    # Activated by signal sigTxabort from hwdevice
    def AbortSend(self):
        self.ui.buttonSend.setEnabled(True)
        self.ui.loadingLine.hide()
        self.ui.loadingLinePercent.setValue(0)
        self.ui.loadingLinePercent.hide()



    # Activated by signal sigTxdone from hwdevice
    def FinishSend(self, serialized_tx, amount_to_send):
        self.AbortSend()
        if not self.txFinished:
            try:
                self.txFinished = True
                tx_hex = serialized_tx.hex()
                printDbg("Raw signed transaction: " + tx_hex)
                printDbg("Amount to send :" + amount_to_send)

                if len(tx_hex) > 90000:
                    mess = "Transaction's length exceeds 90000 bytes. Select less UTXOs and try again."
                    myPopUp_sb(self.main_tab.caller, "crit", 'transaction Warning', mess)

                else:
                    decodedTx = None
                    try:
                        decodedTx = ParseTx(tx_hex, self.main_tab.caller.isTestnetRPC)
                        destination = decodedTx.get("vout")[0].get("scriptPubKey").get("addresses")[0]
                        amount = decodedTx.get("vout")[0].get("value")
                        message = '<p>Broadcast signed transaction?</p><p>Destination address:<br><b>%s</b></p>' % destination
                        message += '<p>Amount: <b>%s</b> PIV<br>' % str(round(amount / 1e8, 8))
                        message += 'Fees: <b>%s</b> PIV <br>Size: <b>%d</b> Bytes</p>' % (str(round(self.currFee / 1e8, 8) ), len(tx_hex)/2)
                    except Exception as e:
                        printException(getCallerName(), getFunctionName(), "decoding exception", str(e))
                        message = '<p>Unable to decode TX- Broadcast anyway?</p>'

                    mess1 = QMessageBox(QMessageBox.Information, 'Send transaction', message)
                    if decodedTx is not None:
                        mess1.setDetailedText(json.dumps(decodedTx, indent=4, sort_keys=False))
                    mess1.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

                    reply = mess1.exec_()
                    if reply == QMessageBox.Yes:
                        txid = self.main_tab.caller.rpcClient.sendRawTransaction(tx_hex, self.useSwiftX())
                        if txid is None:
                            raise Exception("Unable to send TX - connection to RPC server lost.")
                        mess2_text = "<p>Transaction successfully sent.</p>"
                        mess2 = QMessageBox(QMessageBox.Information, 'transaction Sent', mess2_text)
                        mess2.setDetailedText(txid)
                        mess2.exec_()
                        # remove spent rewards (All of them except for collaterals)
                        self.removeSpentRewards()
                        # reload utxos
                        self.main_tab.caller.t_rewards.display_mn_utxos()
                        self.main_tab.caller.t_rewards.onCancel()

                    else:
                        myPopUp_sb(self.main_tab.caller, "warn", 'Transaction NOT sent', "Transaction NOT sent")

            except Exception as e:
                err_msg = "Exception in FinishSend"
                printException(getCallerName(), getFunctionName(), err_msg, e)

            finally:
                self.close()



    def removeSpentRewards(self):
        for mn in self.rewardsArray:
            for utxo in mn['utxos']:
                self.main_tab.caller.parent.db.deleteReward(utxo['txid'], utxo['vout'])



    def updateFee(self):
        if self.useSwiftX():
            self.ui.feeLine.setValue(0.01)
            self.ui.feeLine.setEnabled(False)
        else:
            self.ui.feeLine.setValue(self.suggestedFee)
            self.ui.feeLine.setEnabled(True)



    def update_loading_utxos(self, percent):
        self.ui.lblMessage.setVisible(True)
        self.ui.lblMessage.setText("Loading rewards...%d%%" % percent)



    def update_loading_rawtxes(self, percent):
        self.ui.lblMessage.setVisible(True)
        self.ui.lblMessage.setText("Loading raw tx inputs...%d%%" % percent)



    # Activated by signal tx_progress from hwdevice
    def updateProgressPercent(self, percent):
        self.ui.loadingLinePercent.setValue(percent)
        QApplication.processEvents()



    def useSwiftX(self):
        return self.ui.swiftxCheck.isChecked()




class Ui_SweepAllDlg(object):
    def setupUi(self, SweepAllDlg):
        SweepAllDlg.setModal(True)
        layout = QVBoxLayout(SweepAllDlg)
        layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel("<b><i>Sweep Rewards From All Masternodes</i></b>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.lblMessage = QLabel(SweepAllDlg)
        self.lblMessage.setText("Loading rewards...")
        self.lblMessage.setWordWrap(True)
        layout.addWidget(self.lblMessage)
        self.tableW = QTableWidget(SweepAllDlg)
        self.tableW.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableW.setShowGrid(True)
        self.tableW.setColumnCount(4)
        self.tableW.setRowCount(0)
        self.tableW.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tableW.verticalHeader().hide()
        item = QTableWidgetItem()
        item.setText("Name")
        item.setTextAlignment(Qt.AlignCenter)
        self.tableW.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem()
        item.setText("Address")
        item.setTextAlignment(Qt.AlignCenter)
        self.tableW.setHorizontalHeaderItem(1, item)
        item = QTableWidgetItem()
        item.setText("Rewards")
        item.setTextAlignment(Qt.AlignCenter)
        self.tableW.setHorizontalHeaderItem(2, item)
        item = QTableWidgetItem()
        item.setText("n. of UTXOs")
        item.setTextAlignment(Qt.AlignCenter)
        self.tableW.setHorizontalHeaderItem(3, item)
        layout.addWidget(self.tableW)
        myForm = QFormLayout()
        myForm.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        hBox = QHBoxLayout()
        self.totalLine = QLabel("<b>0 PIV</b>")
        hBox.addWidget(self.totalLine)
        self.loadingLine = QLabel("<b style='color:red'>Preparing TX.</b> Completed: ")
        self.loadingLinePercent = QProgressBar()
        self.loadingLinePercent.setMaximumWidth(200)
        self.loadingLinePercent.setMaximumHeight(10)
        self.loadingLinePercent.setRange(0, 100)
        hBox.addWidget(self.loadingLine)
        hBox.addWidget(self.loadingLinePercent)
        self.loadingLine.hide()
        self.loadingLinePercent.hide()
        myForm.addRow(QLabel("Total Rewards: "), hBox)
        self.noOfUtxosLine = QLabel("<b>0</b>")
        myForm.addRow(QLabel("Total number of UTXOs: "), self.noOfUtxosLine)
        hBox = QHBoxLayout()
        self.edt_destination = QLineEdit()
        self.edt_destination.setToolTip("PIVX address to transfer rewards to")
        hBox.addWidget(self.edt_destination)
        hBox.addWidget(QLabel("Fee"))
        self.feeLine = QDoubleSpinBox()
        self.feeLine.setDecimals(8)
        self.feeLine.setPrefix("PIV  ")
        self.feeLine.setToolTip("Insert a small fee amount")
        self.feeLine.setFixedWidth(120)
        self.feeLine.setSingleStep(0.001)
        hBox.addWidget(self.feeLine)
        self.swiftxCheck = QCheckBox()
        self.swiftxCheck.setToolTip("check for SwiftX instant transaction (flat fee rate of 0.01 PIV)")
        hBox.addWidget(QLabel("Use SwiftX"))
        hBox.addWidget(self.swiftxCheck)
        myForm.addRow(QLabel("Destination Address"), hBox)
        layout.addLayout(myForm)
        hBox = QHBoxLayout()
        self.buttonCancel = QPushButton("Cancel")
        hBox.addWidget(self.buttonCancel)
        self.buttonSend = QPushButton("Send")
        hBox.addWidget(self.buttonSend)
        layout.addLayout(hBox)
        SweepAllDlg.resize(700, 300)
