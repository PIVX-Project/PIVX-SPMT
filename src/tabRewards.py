#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from misc import printDbg, printException, getCallerName, getFunctionName
from threads import ThreadFuns
from utils import checkPivxAddr
from apiClient import ApiClient
from constants import MPATH, MINIMUM_FEE

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.Qt import QTableWidgetItem, QHeaderView, QItemSelectionModel
from PyQt5.QtWidgets import QMessageBox

from qt.gui_tabRewards import TabRewards_gui


class TabRewards():
    def __init__(self, caller):
        self.caller = caller
        self.apiClient = ApiClient()
        ##--- Initialize Selection
        self.rewards = None
        self.selectedRewards = None
        self.rawtransactions = {}
        ##--- Initialize GUI
        self.ui = TabRewards_gui()
        self.caller.tabRewards = self.ui
        self.ui.feeLine.setValue(MINIMUM_FEE)
        # Connect GUI buttons
        self.ui.mnSelect.currentIndexChanged.connect(lambda: self.onChangeSelectedMN())
        self.ui.btn_toggleCollateral.clicked.connect(lambda: self.onToggleCollateral())
        self.ui.rewardsList.box.itemClicked.connect(lambda: self.updateSelection())
        self.ui.btn_selectAllRewards.clicked.connect(lambda: self.onSelectAllRewards())
        self.ui.btn_deselectAllRewards.clicked.connect(lambda: self.onDeselectAllRewards())
        self.ui.btn_sendRewards.clicked.connect(lambda: self.onSendRewards())
        self.ui.btn_Cancel.clicked.connect(lambda: self.onCancel())
        # Init first selection
        self.loadMnSelect()

        
        
        
    def display_utxos(self):
        if self.rewards is not None:
            def item(value):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                return item
    
            self.ui.rewardsList.box.setRowCount(len(self.rewards))
            for row, utxo in enumerate(self.rewards):
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
                
            if self.ui.rewardsList.box.collateralRow is not None:
                    self.ui.rewardsList.box.hideRow(self.ui.rewardsList.box.collateralRow)    
                    
            if len(self.rewards) > 1:
                self.ui.rewardsList.box.resizeColumnsToContents()
                self.ui.rewardsList.statusLabel.setVisible(False)
                self.ui.rewardsList.box.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
                                
            else:
                if not self.caller.rpcConnected:
                    self.ui.rewardsList.statusLabel.setText('<b style="color:purple">PIVX wallet not connected</b>')
                else:
                    if self.apiConnected:
                        self.ui.rewardsList.statusLabel.setText('<b style="color:red">Found no Rewards for %s</b>' % self.curr_addr)
                    else:
                        self.ui.rewardsList.statusLabel.setText('<b style="color:purple">Unable to connect to API provider</b>')
                self.ui.rewardsList.statusLabel.setVisible(True)
            
            
            
            
    def getSelection(self):
        try:
            returnData = []
            items = self.ui.rewardsList.box.selectedItems()
            # Save row indexes to a set to avoid repetition
            rows = set()
            for i in range(0, len(items)):
                row = items[i].row()
                rows.add(row)
            rowList = list(rows)
            
            return [self.rewards[row] for row in rowList]
                
            return returnData 
        except Exception as e:
            print(e)
                       
            
            
            
    def loadMnSelect(self):
        try:
            self.ui.mnSelect.clear()            
            for x in self.caller.masternode_list:
                    name = x['name']
                    address = x['collateral'].get('address')
                    txid = x['collateral'].get('txid')
                    hwAcc = x['hwAcc']
                    spath = x['collateral'].get('spath')
                    path = MPATH + "%d'/0/%d" % (hwAcc, spath)
                    self.ui.mnSelect.addItem(name, [address, txid, path])
        except Exception as e:
            print(e)        
                        
           
    
    
    def load_utxos_thread(self, ctrl):
        self.apiConnected = False
        try:
            if not self.caller.rpcConnected:
                self.rewards = []
                printDbg('PIVX daemon not connected')
            
            else:
                try:
                    if self.apiClient.getStatus() != 200:
                        return
                    self.apiConnected = True
                    self.blockCount = self.caller.rpcClient.getBlockCount()
                    self.rewards = self.apiClient.getAddressUtxos(self.curr_addr)['unspent_outputs']
                    for utxo in self.rewards:
                        self.rawtransactions[utxo['tx_hash']] = self.caller.rpcClient.getRawTransaction(utxo['tx_hash'])
                            
                except Exception as e:
                    self.errorMsg = 'Error occurred while calling getaddressutxos method: ' + str(e)
                    printDbg(self.errorMsg)
                    
        except Exception as e:
            print(e)
            pass
        
    
    
    
    @pyqtSlot()
    def onCancel(self):
        self.ui.selectedRewardsLine.setText("0.0")
        self.ui.mnSelect.setCurrentIndex(0)
        self.ui.destinationLine.setText('')
        self.ui.feeLine.setValue(MINIMUM_FEE)
        self.ui.btn_toggleCollateral.setText("Show Collateral")
        self.ui.collateralHidden = True
        self.onChangeSelectedMN()
    
    
    
        
    @pyqtSlot()
    def onChangeSelectedMN(self):
        if self.ui.mnSelect.currentIndex() >= 0:
            self.curr_addr = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[0]
            self.curr_txid = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[1]
            self.curr_path = self.ui.mnSelect.itemData(self.ui.mnSelect.currentIndex())[2] 
            if self.curr_addr is not None:
                result = self.apiClient.getBalance(self.curr_addr)
                self.ui.addrAvailLine.setText("<i>%s PIVs</i>" % result)
            self.ui.selectedRewardsLine.setText("0.0")
            self.ui.rewardsList.box.clearSelection()
            self.ui.rewardsList.box.collateralRow = None
            self.ui.collateralHidden = True
            self.ui.btn_toggleCollateral.setText("Show Collateral")
            if result is not None:
                self.runInThread = ThreadFuns.runInThread(self.load_utxos_thread, (), self.display_utxos)
            
      
        
        
    @pyqtSlot()
    def onSelectAllRewards(self):
        self.ui.rewardsList.box.selectAll()
        self.updateSelection()                

            
    @pyqtSlot()
    def onDeselectAllRewards(self):
        self.ui.rewardsList.box.clearSelection()
        self.updateSelection()
    
            
            
            
    @pyqtSlot()
    def onSendRewards(self):
        self.dest_addr = self.ui.destinationLine.text()
        printDbg("Sending rewards from masternode address %s to PIVX address %s" % (self.curr_addr, self.dest_addr))      
    
        # Check dongle
        printDbg("Checking HW device")
        if self.caller.hwStatus != 2:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw device check', "Connect to HW device first")
            printDbg("Unable to connect - hw status: %d" % self.caller.hwStatus)
            return None
        
        # Check destination Address      
        if not checkPivxAddr(self.dest_addr):
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - PIVX address check', "Invalid Destination Address")
            return None
        
        # Check Noob spending collateral
        if (self.ui.rewardsList.box.collateralRow is not None and 
                self.ui.rewardsList.box.item(self.ui.rewardsList.box.collateralRow, 0).isSelected() ): 
            warning1 = "Are you sure you want to transfer the collateral?"
            warning2 = "Really?"
            warning3 = "Take a deep breath. Do you REALLY want to transfer your collateral?"
            ans = self.caller.myPopUp(QMessageBox.Warning, 'SPMT - warning', warning1)
            if ans == QMessageBox.No:
                return None
            else:
                ans2 = self.caller.myPopUp(QMessageBox.Warning, 'SPMT - warning', warning2)
                if ans2 == QMessageBox.No:
                    return None
                else:
                    ans3 = self.caller.myPopUp(QMessageBox.Critical, 'SPMT - warning', warning3)
                    if ans3 == QMessageBox.No:
                        return None
                    
        # LET'S GO    
        if self.selectedRewards:                      
            self.currFee = self.ui.feeLine.value() * 1e8
            # connect signal
            self.caller.hwdevice.sigTxdone.connect(self.FinishSend)
            try:
                self.txFinished = False
                self.caller.hwdevice.prepare_transfer_tx(self.caller, self.curr_path, self.selectedRewards, self.dest_addr, self.currFee, self.rawtransactions)
            except Exception as e:
                err_msg = "Error while preparing transaction"
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
        else:
            self.caller.myPopUp2(QMessageBox.Information, 'transaction NOT Sent', "No UTXO to send")         
                    
            
            
    @pyqtSlot()
    def onToggleCollateral(self):
        if(self.rewards is not None):
            
            if len(self.rewards) and self.ui.rewardsList.box.collateralRow is not None:
                if not self.ui.collateralHidden:
                    try:
                        if self.ui.rewardsList.box.item(self.ui.rewardsList.box.collateralRow, 0).isSelected():
                            self.ui.rewardsList.box.selectRow(self.ui.rewardsList.box.collateralRow)
                    except Exception as e:
                        err_msg = "Error while preparing transaction"
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
            self.caller.myPopUp2(QMessageBox.Information, 'No Collateral', "No collateral selected")
            
    # Activated by signal sigTxdone from hwdevice       
    @pyqtSlot(bytearray, str)            
    def FinishSend(self, serialized_tx, amount_to_send):
        if not self.txFinished:
            try:
                self.txFinished = True
                tx_hex = serialized_tx.hex()
                printDbg("Raw signed transaction: " + tx_hex)
                printDbg("Amount to send :" + amount_to_send)
                
                if len(tx_hex) > 90000:
                    mess = "Transaction's length exceeds 90000 bytes. Select less UTXOs and try again."
                    self.caller.myPopUp2(QMessageBox.Warning, 'transaction Warning', mess)
                
                else:
                    message = 'Broadcast signed transaction?\n\nDestination address: %s\nAmount to send: %s Piv' % (self.curr_addr, amount_to_send)
                    message += 'Fee: %s Piv\nSize: %d bytes' % (str(round(self.currFee / 1e8, 8) ), len(tx_hex)/2)
                    reply = self.caller.myPopUp(QMessageBox.Information, 'Send transaction', message)
                    if reply == QMessageBox.Yes:                   
                        txid = self.caller.rpcClient.sendRawTransaction(tx_hex)
                        mess = QMessageBox(QMessageBox.Information, 'transaction Sent', 'transaction Sent')
                        mess.setDetailedText(txid)
                        mess.exec_()
                        self.onCancel()
                        
                    else:
                        self.caller.myPopUp2(QMessageBox.Information, 'transaction NOT Sent', "transaction NOT sent")
                        self.onCancel()
                        
            except Exception as e:
                err_msg = "Exception in sendRewards"
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
                
   
 
 
    def updateSelection(self, clicked_item=None):
        total = 0
        self.selectedRewards = self.getSelection()
        numOfInputs = len(self.selectedRewards)
        if numOfInputs:
            
            for i in range(0, numOfInputs):
                total += int(self.selectedRewards[i].get('value'))
                                     
            # update suggested fee and selected rewards
            estimatedTxSize = (44+numOfInputs*148)*1.0 / 1000   # kB
            feePerKb = self.caller.rpcClient.getFeePerKb()
            suggestedFee = round(feePerKb * estimatedTxSize, 8)
            printDbg("estimatedTxSize is %s kB" % str(estimatedTxSize))
            printDbg("suggested fee is %s PIV (%s PIV/kB)" % (str(suggestedFee), str(feePerKb)))
            
            self.ui.selectedRewardsLine.setText(str(round(total/1e8, 8)))
            self.ui.feeLine.setValue(suggestedFee)
            
        else:
            self.ui.selectedRewardsLine.setText("")
            self.ui.feeLine.setValue(MINIMUM_FEE)
        