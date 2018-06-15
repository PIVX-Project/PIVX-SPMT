#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
from threads import ThreadFuns
from ipaddress import ip_address
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from misc import printDbg, printOK, writeToFile
from constants import masternodes_File
from pivx_hashlib import generate_privkey

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMessageBox

from qt.gui_tabMNConf import TabMNConf_gui
from qt.dlg_findCollTx import FindCollTx_dlg

class TabMNConf():
    def __init__(self, caller, masternode_alias=None):
        self.caller = caller
        self.ui = TabMNConf_gui(masternode_alias)
        self.caller.tabMNConf = self.ui
        self.runInThread = ThreadFuns.runInThread
        self.spath_found = False
        self.spath = -1
        # Lookup Collateral dialog
        self.dlg = FindCollTx_dlg(self)
        # Connect GUI buttons
        self.ui.btn_genKey.clicked.connect(lambda: self.onGenerateMNkey())
        self.ui.btn_addressToSpath.clicked.connect(lambda: self.onFindSpathAndPrivKey())
        self.ui.btn_findTxid.clicked.connect(lambda: self.onLookupTx())
        self.ui.btn_editTxid.clicked.connect(lambda: self.onEditTx())
        self.ui.edt_txid.returnPressed.connect(lambda: self.onEditTx())
        self.ui.btn_cancelMNConf.clicked.connect(lambda: self.onCancelMNConfig())
        self.ui.btn_saveMNConf.clicked.connect(lambda: self.onSaveMNConf())
        self.ui.btn_spathToAddress.clicked.connect(lambda: self.spathToAddress())
        self.ui.testnetCheck.clicked.connect(lambda: self.onChangeTestnet())
        
        
     
        
    def addressToSpath(self):
        printOK("addressToSpath pressed")
        self.spath_found = False
        # Check dongle
        printDbg("Checking HW device")
        if self.caller.hwStatus != 2:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw device check', "Connect to HW device first")
            printDbg("Unable to connect to hardware device. The device status is: %d" % self.caller.hwStatus)
            return None
        self.runInThread(self.findSpath, (0, 10), self.findSpath_done)     
    
          
                
    @pyqtSlot(object, int, int)            
    def findSpath(self, ctrl, starting_spath, spath_count):
        currAddr = self.ui.edt_address.text().strip()
        currHwAcc = self.ui.edt_hwAccount.value()
        # first scan. Subsequent called by findSpath_done
        self.spath_found, self.spath = self.caller.hwdevice.scanForBip32(currHwAcc, currAddr, starting_spath, spath_count, self.isTestnet())
        printOK("Bip32 scan complete. result=%s   spath=%s" % (self.spath_found, self.spath))
        self.curr_starting_spath = starting_spath
        self.curr_spath_count = spath_count
        
        
                
                
    @pyqtSlot()            
    def findSpath_done(self):
        currAddr = self.ui.edt_address.text().strip()
        currHwAcc = self.ui.edt_hwAccount.value()
        spath = self.spath
        starting_spath = self.curr_starting_spath
        spath_count = self.curr_spath_count
        
        if self.spath_found:
            printOK("spath is %d" % spath)
            mess = "Found address %s in HW account %s with spath_id %s" % (currAddr, currHwAcc, spath)
            self.caller.myPopUp2(QMessageBox.Information, 'SPMT - spath search', mess)
            self.ui.edt_spath.setValue(spath)
            self.findPubKey()
            
        else:
            mess = "Scanned addresses <b>%d</b> to <b>%d</b> of HW account <b>%d</b>.<br>" % (starting_spath, starting_spath+spath_count-1, currHwAcc)
            mess += "Unable to find the address <i>%s</i>.<br>Maybe it's on a different account.<br><br>" % currAddr
            mess += "Do you want to scan %d more addresses of account n.<b>%d</b> ?" % (spath_count, currHwAcc)
            ans = self.caller.myPopUp(QMessageBox.Critical, 'SPMT - spath search', mess)
            if ans == QMessageBox.Yes:
                starting_spath += spath_count
                self.runInThread(self.findSpath, (starting_spath, spath_count), self.findSpath_done)

    
    
    @pyqtSlot()
    def findPubKey(self):
        printDbg("Computing public key...")
        currSpath = self.ui.edt_spath.value()
        currHwAcc = self.ui.edt_hwAccount.value()      
        # Check dongle
        printDbg("Checking HW device")
        if self.caller.hwStatus != 2:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw device check', "Connect to HW device first")
            printDbg("Unable to connect to hardware device. The device status is: %d" % self.caller.hwStatus)
            return None
        
        try:
            result = self.caller.hwdevice.scanForPubKey(currHwAcc, currSpath)
            
        except Exception as e:
            error_msg = "ERROR: %s" % e.args[0]
            printDbg(error_msg)
            result = None
        
        # Connection pop-up
        warningText = "Another application (such as Ledger Wallet app) has probably taken over "
        warningText += "the communication with the Ledger device.<br><br>To continue, close that application and "
        warningText += "click the <b>Retry</b> button.\nTo cancel, click the <b>Abort</b> button"
        mBox = QMessageBox(QMessageBox.Critical, "WARNING", warningText, QMessageBox.Retry)
        mBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Abort);
        
        while result is None:      
            ans = mBox.exec_()
            if ans == QMessageBox.Abort:
                return
            # we need to reconnect the device
            self.caller.hwdevice.dongle.close()
            self.caller.hwdevice.initDevice()
            
            result = self.caller.hwdevice.scanForPubKey(currHwAcc, currSpath)
    
        mess = "Found public key:\n%s" % result
        self.caller.myPopUp2(QMessageBox.Information, "SPMT - findPubKey", mess)
        printOK("Public Key: %s" % result)
        self.ui.edt_pubKey.setText(result)
        
        
   
        
    def findRow_mn_list(self, name):
        row = 0
        while self.caller.tabMain.myList.item(row)['name'] < name:
            row += 1
        return row
    
    
    
    def isTestnet(self):
        return self.ui.testnetCheck.isChecked()
        
        
        
    @pyqtSlot()
    def onCancelMNConfig(self):
        self.caller.tabs.setCurrentIndex(0)
        self.caller.tabs.removeTab(1)
        self.caller.mnode_to_change = None
        
        
        
    @pyqtSlot()
    def onChangeTestnet(self):
        if self.isTestnet():
            self.ui.edt_masternodePort.setValue(51474)
        else:
            self.ui.edt_masternodePort.setValue(51472)
        
     
     
            
    @pyqtSlot()
    def onEditTx(self):
        if not self.ui.edt_txid.isEnabled():
            self.ui.btn_editTxid.setText("OK")
            self.ui.edt_txid.setEnabled(True)
            self.ui.edt_txidn.setEnabled(True)
            self.ui.btn_findTxid.setEnabled(False)
            self.ui.btn_saveMNConf.setEnabled(False)
            
        else:
            self.ui.btn_editTxid.setText("edit")
            self.ui.edt_txid.setEnabled(False)
            self.ui.edt_txidn.setEnabled(False)
            self.ui.btn_findTxid.setEnabled(True)
            self.ui.btn_saveMNConf.setEnabled(True)
    
            
    
        
    @pyqtSlot()
    def onFindSpathAndPrivKey(self):
        self.ui.edt_spath.setValue(0)
        self.ui.edt_pubKey.setText('')
        self.addressToSpath()
        
            
            
            
    @pyqtSlot()
    def onLookupTx(self):
        # address check
        currAddr = self.ui.edt_address.text().strip()
        # Check rpc connection
        printDbg("Checking RPC connection")
        if not self.caller.rpcConnected:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw device check', "Connect to RPC server first")
            printDbg("Unable to connect: %s" % self.caller.rpcStatusMess)
            return None
        try:
            # Update Lookup dialog
            self.dlg.load_data(currAddr)
            if self.dlg.exec_():
                txid, txidn = self.dlg.getSelection()
                self.ui.edt_txid.setText(txid)
                self.ui.edt_txidn.setValue(txidn)
       
        except Exception as e:
            printDbg(e)
            
        
        
        
    @pyqtSlot()
    def onGenerateMNkey(self):
        printDbg("Generate MNkey pressed")
        reply = QMessageBox.Yes
        
        if self.ui.edt_mnPrivKey.text() != "":
            reply = self.caller.myPopUp(QMessageBox.Warning, "GENERATE PRIV KEY", 
                                 "Are you sure?\nThis will overwrite current private key", QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        newkey = generate_privkey(self.isTestnet())
        self.ui.edt_mnPrivKey.setText(newkey)
        
        
        
        
    @pyqtSlot()            
    def onSaveMNConf(self):
        try:
            if self.ui.edt_pubKey.text() == "" or self.ui.edt_txid.text() == "" or self.ui.edt_mnPrivKey.text() == "":
                mess_text = 'Attention! Complete the form before saving.<br>'
                mess_text += "<b>pubKey = </b>%s<br>" % self.ui.edt_pubKey.text()
                mess_text += "<b>txId = </b>%s<br>" % self.ui.edt_txid.text()
                mess_text += "<b>mnPrivKey = </b>%s<br>" % self.ui.edt_mnPrivKey.text()
                self.caller.myPopUp2(QMessageBox.Critical, 'Complete Form', mess_text)
                return
            # remove previous element
            if not self.caller.mnode_to_change is None:
                # remove from memory list
                self.caller.masternode_list.remove(self.caller.mnode_to_change)
                # remove from tabMain list
                row = self.caller.tabMain.myList.row
                name = self.caller.tabMain.current_mn[self.caller.mnode_to_change['name']]
                self.caller.tabMain.myList.takeItem(row(name))
                self.caller.mnode_to_change = None

            # create new item
            new_masternode = {}
            new_masternode['name'] = self.ui.edt_name.text().strip()
            masternodeIp = self.ui.edt_masternodeIp.text().strip()
            if not masternodeIp.endswith('.onion'):    
                masternodeIp = ip_address(masternodeIp).compressed
            new_masternode['ip'] = masternodeIp
            new_masternode['port'] = self.ui.edt_masternodePort.value()
            new_masternode['mnPrivKey'] = self.ui.edt_mnPrivKey.text().strip()
            new_masternode['hwAcc'] = self.ui.edt_hwAccount.value()
            new_masternode['isTestnet'] = 0 if not self.isTestnet() else 1

            coll = {}
            coll['address'] = self.ui.edt_address.text().strip()
            coll['spath'] = self.ui.edt_spath.value()
            coll['pubKey'] = self.ui.edt_pubKey.text().strip()
            coll['txid'] = self.ui.edt_txid.text().strip()
            coll['txidn'] = self.ui.edt_txidn.value()
            
            new_masternode['collateral'] = coll

            # add new item
            self.caller.masternode_list.append(new_masternode)
            # Write to file
            printDbg("saving MN configuration for %s" % new_masternode['name'])
            writeToFile(self.caller.masternode_list, masternodes_File)
            printDbg("saved")
            # Insert item in list of Main tab and connect buttons
            name = new_masternode['name']
            namelist = [x['name'] for x in self.caller.masternode_list]
            row = namelist.index(name)
            if row == -1:
                row = None
            self.caller.tabMain.insert_mn_list(name, new_masternode['ip'], new_masternode['port'], row)
            self.caller.tabMain.btn_remove[name].clicked.connect(lambda: self.caller.t_main.onRemoveMN())
            self.caller.tabMain.btn_edit[name].clicked.connect(lambda: self.caller.t_main.onEditMN())
            self.caller.tabMain.btn_start[name].clicked.connect(lambda: self.caller.t_main.onStartMN())
            self.caller.tabMain.btn_rewards[name].clicked.connect(lambda: self.caller.t_main.onRewardsMN())   
            # go back
            self.onCancelMNConfig()
            
        except Exception as e:
            error_msg = "ERROR: %s" % e
            printDbg(error_msg)
            self.caller.myPopUp2(QMessageBox.Critical, 'ERROR', error_msg)
            
    
    
    
    @pyqtSlot()     
    def spathToAddress(self):
        printOK("spathToAddress pressed") 
        currHwAcc = self.ui.edt_hwAccount.value()
        currSpath = self.ui.edt_spath.value()
        # Check dongle
        printDbg("Checking HW device")
        if self.caller.hwStatus != 2:
            self.caller.myPopUp2(QMessageBox.Critical, 'SPMT - hw device check', "Connect to HW device first")
            printDbg("Unable to connect to hardware device. The device status is: %d" % self.caller.hwStatus)
            return None
        addr = self.caller.hwdevice.scanForAddress(currHwAcc, currSpath, self.isTestnet())
        self.ui.edt_address.setText(addr)
        self.findPubKey()