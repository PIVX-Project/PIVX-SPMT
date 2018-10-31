#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import simplejson as json

from PyQt5.Qt import QApplication, pyqtSignal
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView

from apiClient import ApiClient
from constants import MPATH, MINIMUM_FEE
from hwdevice import DisconnectedException
from misc import printDbg, printException, getCallerName, getFunctionName, persistCacheSetting, myPopUp, myPopUp_sb
from qt.gui_tabRewards import TabRewards_gui
from threads import ThreadFuns
from utils import checkPivxAddr
from time import sleep


class TabRewards():
    
    def __init__(self, caller):
        self.caller = caller
        ##--- Lock for loading UTXO thread
        self.runInThread = ThreadFuns.runInThread
        self.Lock = threading.Lock()
        
        ##--- Initialize Selection
        self.utxoLoaded = False
        self.selectedRewards = None
        self.feePerKb = MINIMUM_FEE
        self.suggestedFee = MINIMUM_FEE
        
        ##--- Initialize GUI
        self.ui = TabRewards_gui(caller)
        self.caller.tabRewards = self.ui
        
        # load last used destination from cache
        self.ui.destinationLine.setText(self.caller.parent.cache.get("lastAddress")) 
        # load useSwiftX check from cache
        if self.caller.parent.cache.get("useSwiftX"):
            self.ui.swiftxCheck.setChecked(True)
        
        # init first selected MN
        self.loadMnSelect()         # loads masternodes list in MnSelect and display utxos
        self.updateFee()
        
        # Connect GUI buttons
        self.ui.mnSelect.currentIndexChanged.connect(lambda: self.onChangeSelectedMN())
        self.ui.btn_toggleCollateral.clicked.connect(lambda: self.onToggleCollateral())
        self.ui.rewardsList.box.itemClicked.connect(lambda: self.updateSelection())
        self.ui.btn_selectAllRewards.clicked.connect(lambda: self.onSelectAllRewards())
        self.ui.btn_deselectAllRewards.clicked.connect(lambda: self.onDeselectAllRewards())
        self.ui.swiftxCheck.clicked.connect(lambda: self.updateFee())
        self.ui.btn_sendRewards.clicked.connect(lambda: self.onSendRewards())
        self.ui.btn_Cancel.clicked.connect(lambda: self.onCancel())
        self.ui.btn_ReloadUTXOs.clicked.connect(lambda: self.onReloadUTXOs())
        
        # show UTXOs from DB
        self.display_mn_utxos() 
        


        
        
    @pyqtSlot()
    def display_mn_utxos(self):
        if self.curr_name is None:
            return
        
        # update fee
        if self.caller.rpcConnected:
            self.feePerKb = self.caller.rpcClient.getFeePerKb()
        
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
                txId = utxo.get('tx_hash', None)
                pivxAmount = round(int(utxo.get('value', 0))/1e8, 8)
                self.ui.rewardsList.box.setItem(row, 0, item(str(pivxAmount)))
                self.ui.rewardsList.box.setItem(row, 1, item(str(utxo.get('confirmations', None))))
                self.ui.rewardsList.box.setItem(row, 2, item(txId))
                self.ui.rewardsList.box.setItem(row, 3, item(str(utxo.get('tx_ouput_n', None))))
                self.ui.rewardsList.box.showRow(row)
                # MARK COLLATERAL UTXO
                if txId == self.curr_txid:
                    for i in range(0,4):
                        self.ui.rewardsList.box.item(row, i).setFont(QFont("Arial", 9, QFont.Bold))
                    self.ui.rewardsList.box.collateralRow = row

                # make immature rewards unselectable
                if utxo.get('confirmations') < 101:
                    for i in range(0,4):
                        self.ui.rewardsList.box.item(row, i).setFlags(Qt.NoItemFlags)
                        self.ui.rewardsList.box.item(row, i).setToolTip("Immature - 100 confirmations required")
 
            self.ui.rewardsList.box.resizeColumnsToContents()
            
            if self.ui.rewardsList.box.collateralRow is not None:
                    self.ui.rewardsList.box.hideRow(self.ui.rewardsList.box.collateralRow)    

            if len(rewards) > 1:  # (collateral is a reward)
                self.ui.rewardsList.statusLabel.setVisible(False)
                self.ui.rewardsList.box.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
                                
            else:
                if not self.caller.rpcConnected:
                    self.ui.resetStatusLabel('<b style="color:red">PIVX wallet not connected</b>')
                elif self.apiConnected:
                    self.ui.resetStatusLabel('<b style="color:red">Found no Rewards for %s</b>' % self.curr_addr)
                else:
                    self.ui.resetStatusLabel('<b style="color:red">Unable to connect to API provider</b>')        

            
            
            
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
    
            
            
    def loadMnSelect(self):
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
                path = MPATH + "%d'/0/%d" % (hwAcc, spath)
                self.ui.mnSelect.addItem(name, [address, txid, txidn, path])
                
        # restore previous index
        if index < self.ui.mnSelect.count():
            self.ui.mnSelect.setCurrentIndex(index)
            
        self.onChangeSelectedMN()
                     
           
    
    
    def load_utxos_thread(self, ctrl):
        with self.Lock:
            self.apiConnected = False
            # clear rewards DB
            printDbg("Updating rewards...")
            self.caller.parent.db.clearTable('REWARDS')
            self.utxoLoaded = False

            # If rpc is not connected warn and return.
            if not self.caller.rpcConnected:
                printDbg('PIVX daemon not connected - Unable to update UTXO list')
                return

            api_status = self.caller.apiClient.getStatus()
            if  api_status != 200:
                printDbg("Wrong response from API client. Status: %s" % status)
                return

            self.apiConnected = True
            self.blockCount = self.caller.rpcClient.getBlockCount()

            for mn in self.caller.masternode_list:
                # Load UTXOs from API client
                rewards = self.caller.apiClient.getAddressUtxos(
                    mn['collateral'].get('address'))['unspent_outputs']

                if rewards is None:
                    printDbg('Error occurred while calling getaddressutxos method.')
                    return

                # for each UTXO
                for utxo in rewards:
                    # get raw TX from RPC client
                    rawtx = self.caller.rpcClient.getRawTransaction(utxo['tx_hash'])
 
                    # Don't save UTXO if raw TX is unavailable
                    if rawtx is None:
                        printDbg("Unable to get raw TX with hash=%s from RPC server" % utxo['tx_hash'])
                        continue

                    # Add mn_name and raw_tx to UTXO and save it to DB
                    else:
                        utxo['mn_name'] = mn['name']
                        utxo['raw_tx'] = rawtx
                        self.caller.parent.db.addReward(utxo)                
            
            printDbg("--# REWARDS table updated")
            self.utxoLoaded = True
            self.caller.sig_UTXOsLoaded.emit()
    
    
    
    #@pyqtSlot()
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
    
    
    
        
    @pyqtSlot()
    def onChangeSelectedMN(self):
        
        self.curr_name = None
        if self.ui.mnSelect.currentIndex() >= 0:
            self.ui.resetStatusLabel()
            self.curr_name = self.ui.mnSelect.itemText(self.ui.mnSelect.currentIndex())
            self.curr_addr = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[0]
            self.curr_txid = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[1]
            self.curr_txidn = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[2]
            self.curr_path = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[3]            
            self.ui.rewardsList.box.collateralRow = None
            self.onCancel()
            self.display_mn_utxos()
            
      
        
        
    @pyqtSlot()
    def onSelectAllRewards(self):
        self.ui.rewardsList.box.selectAll()
        self.updateSelection() 


            
    @pyqtSlot()
    def onDeselectAllRewards(self):
        self.ui.rewardsList.box.clearSelection()
        self.updateSelection()
    
    
    
    @pyqtSlot()
    def onReloadUTXOs(self):
        if not self.Lock.locked():
            self.ui.resetStatusLabel()
            self.runInThread(self.load_utxos_thread, ())
        
            
            
            
    @pyqtSlot()
    def onSendRewards(self):
        self.dest_addr = self.ui.destinationLine.text().strip() 
    
        # Check dongle
        printDbg("Checking HW device")
        if self.caller.hwStatus != 2:
            myPopUp_sb(self.caller, "crit", 'SPMT - hw device check', "Connect to HW device first")
            printDbg("Unable to connect to hardware device. The device status is: %d" % self.caller.hwStatus)
            return None
        
        # Check destination Address      
        if not checkPivxAddr(self.dest_addr):
            myPopUp_sb(self.caller, "crit", 'SPMT - PIVX address check', "The destination address is missing, or invalid.")
            return None
        
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
                    if ans3 == QMessageBox.No:
                        return None
                    
        # LET'S GO    
        if self.selectedRewards: 
            printDbg("Sending from PIVX address  %s  to PIVX address  %s " % (self.curr_addr, self.dest_addr))
            printDbg("Preparing transaction. Please wait...")
            self.ui.loadingLine.show()
            self.ui.loadingLinePercent.show()
            QApplication.processEvents()            
            
            # save last destination address and swiftxCheck to cache and persist to settings
            self.caller.parent.cache["lastAddress"] = persistCacheSetting('cache_lastAddress', self.dest_addr)
            self.caller.parent.cache["useSwiftX"] = persistCacheSetting('cache_useSwiftX', self.useSwiftX())                            
            
            self.currFee = self.ui.feeLine.value() * 1e8

            try:
                self.txFinished = False
                self.caller.hwdevice.prepare_transfer_tx(self.caller, self.curr_path, self.selectedRewards, self.dest_addr, self.currFee, self.useSwiftX())
            
            except DisconnectedException as e:
                self.caller.hwStatus = 0
                self.caller.updateHWleds()
                
            except Exception as e:
                err_msg = "Error while preparing transaction. <br>"
                err_msg += "Probably Blockchain wasn't synced when trying to fetch raw TXs.<br>" 
                err_msg += "<b>Wait for full synchronization</b> then hit 'Clear/Reload'"
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
        else:
            myPopUp_sb(self.caller, "warn", 'Transaction NOT sent', "No UTXO to send")         
                    
            
            
    @pyqtSlot()
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
        for utxo in self.selectedRewards:
            self.caller.parent.db.deleteReward(utxo['tx_hash'], utxo['tx_ouput_n'])
            
            
            

    # Activated by signal sigTxdone from hwdevice       
    #@pyqtSlot(bytearray, str)            
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
                    myPopUp_sb(self.caller, "crit", 'transaction Warning', mess)
                
                else:
                    decodedTx = self.caller.rpcClient.decodeRawTransaction(tx_hex)
                    destination = decodedTx.get("vout")[0].get("scriptPubKey").get("addresses")[0]
                    amount = decodedTx.get("vout")[0].get("value")
                    message = '<p>Broadcast signed transaction?</p><p>Destination address:<br><b>%s</b></p>' % destination
                    message += '<p>Amount: <b>%s</b> PIV<br>' % str(amount)
                    message += 'Fees: <b>%s</b> PIV <br>Size: <b>%d</b> Bytes</p>' % (str(round(self.currFee / 1e8, 8) ), len(tx_hex)/2)
                    
                    mess1 = QMessageBox(QMessageBox.Information, 'Send transaction', message)
                    mess1.setDetailedText(json.dumps(decodedTx, indent=4, sort_keys=False))
                    mess1.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    reply = mess1.exec_()
                    if reply == QMessageBox.Yes:                
                        txid = self.caller.rpcClient.sendRawTransaction(tx_hex, self.useSwiftX())
                        mess2_text = "<p>Transaction successfully sent.</p>"
                        mess2 = QMessageBox(QMessageBox.Information, 'transaction Sent', mess2_text)
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
        
        
        
        
    @pyqtSlot()
    def updateFee(self):
        if self.useSwiftX():
            self.ui.feeLine.setValue(0.01)
            self.ui.feeLine.setEnabled(False)
        else:
            self.ui.feeLine.setValue(self.suggestedFee)
            self.ui.feeLine.setEnabled(True)
        
        
             
    # Activated by signal tx_progress from hwdevice
    #@pyqtSlot(str)
    def updateProgressPercent(self, percent):
        self.ui.loadingLinePercent.setValue(int(percent))
        QApplication.processEvents()
        
 
 
 
    def updateSelection(self, clicked_item=None):
        total = 0
        self.selectedRewards = self.getSelection()
        numOfInputs = len(self.selectedRewards)
        if numOfInputs:
            for i in range(0, numOfInputs):
                total += int(self.selectedRewards[i].get('value'))
                                    
            # update suggested fee and selected rewards
            estimatedTxSize = (44+numOfInputs*148)*1.0 / 1000   # kB
            self.suggestedFee = round(self.feePerKb * estimatedTxSize, 8)
            printDbg("estimatedTxSize is %s kB" % str(estimatedTxSize))
            printDbg("suggested fee is %s PIV (%s PIV/kB)" % (str(self.suggestedFee), str(self.feePerKb)))
            
            self.ui.selectedRewardsLine.setText(str(round(total/1e8, 8)))
            
        else:
            self.ui.selectedRewardsLine.setText("")
        
        self.updateFee()

    
                

    
    def updateTotalBalance(self, rewards):
        nAmount = 0
        if rewards is not None:
            for utxo in rewards:
                nAmount = nAmount + utxo['value']
                
        totalBalance = str(round(nAmount/1e8, 8))
        self.ui.addrAvailLine.setText("<i>%s PIVs</i>" % totalBalance)
        
        
        
            
    def useSwiftX(self):
        return self.ui.swiftxCheck.isChecked()
    
        