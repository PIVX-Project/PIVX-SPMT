#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from ipaddress import ip_address

from PyQt5.QtWidgets import QMessageBox

from misc import printDbg, printOK, is_hex, appendMasternode, myPopUp, myPopUp_sb
from pivx_hashlib import generate_privkey
from qt.gui_tabMNConf import TabMNConf_gui
from qt.dlg_findCollTx import FindCollTx_dlg
from threads import ThreadFuns


class TabMNConf:
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
        # Check HW device
        if self.caller.hwStatus != 2:
            myPopUp_sb(self.caller, "crit", 'SPMT - hw device check', "Connect to HW device first")
            printDbg("Unable to connect to hardware device. The device status is: %d" % self.caller.hwStatus)
            return None
        self.runInThread(self.findSpath, (0, 10), self.findSpath_done)

    def findSpath(self, ctrl, starting_spath, spath_count):
        currAddr = self.ui.edt_address.text().strip()
        currHwAcc = self.ui.edt_hwAccount.value()
        # first scan. Subsequent called by findSpath_done
        self.spath_found, self.spath = self.caller.hwdevice.scanForBip32(currHwAcc, currAddr, starting_spath, spath_count, self.isTestnet())
        printOK("Bip32 scan complete. result=%s   spath=%s" % (self.spath_found, self.spath))
        self.curr_starting_spath = starting_spath
        self.curr_spath_count = spath_count

    def findSpath_done(self):
        currAddr = self.ui.edt_address.text().strip()
        currHwAcc = self.ui.edt_hwAccount.value()
        spath = self.spath
        starting_spath = self.curr_starting_spath
        spath_count = self.curr_spath_count

        if self.spath_found:
            printOK("spath is %d" % spath)
            mess = "Found address %s in HW account %s with spath_id %s" % (currAddr, currHwAcc, spath)
            myPopUp_sb(self.caller, "info", 'SPMT - spath search', mess)
            self.ui.edt_spath.setValue(spath)
            self.findPubKey()

        else:
            mess = "Scanned addresses <b>%d</b> to <b>%d</b> of HW account <b>%d</b>.<br>" % (starting_spath, starting_spath + spath_count - 1, currHwAcc)
            mess += "Unable to find the address <i>%s</i>.<br>Maybe it's on a different account.<br><br>" % currAddr
            mess += "Do you want to scan %d more addresses of account n.<b>%d</b> ?" % (spath_count, currHwAcc)
            ans = myPopUp(self.caller, "crit", 'SPMT - spath search', mess)
            if ans == QMessageBox.Yes:
                starting_spath += spath_count
                self.runInThread(self.findSpath, (starting_spath, spath_count), self.findSpath_done)

    def findPubKey(self):
        printDbg("Computing public key...")
        currSpath = self.ui.edt_spath.value()
        currHwAcc = self.ui.edt_hwAccount.value()
        # Check HW device
        if self.caller.hwStatus != 2:
            myPopUp_sb(self.caller, "crit", 'SPMT - hw device check', "Connect to HW device first")
            printDbg("Unable to connect to hardware device. The device status is: %d" % self.caller.hwStatus)
            return None

        result = self.caller.hwdevice.scanForPubKey(currHwAcc, currSpath, self.isTestnet())

        # Connection pop-up
        warningText = "Unable to find public key. The action was refused on the device or another application "
        warningText += "might have taken over the USB communication with the device.<br><br>"
        warningText += "To continue click the <b>Retry</b> button.\nTo cancel, click the <b>Abort</b> button."
        mBox = QMessageBox(QMessageBox.Critical, "WARNING", warningText, QMessageBox.Retry)
        mBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Abort)

        while result is None:
            ans = mBox.exec_()
            if ans == QMessageBox.Abort:
                return
            # we need to reconnect the device
            self.caller.hwdevice.clearDevice()
            self.caller.hwdevice.initDevice(self.caller.header.hwDevices.currentIndex())

            result = self.caller.hwdevice.scanForPubKey(currHwAcc, currSpath, self.isTestnet())

        mess = "Found public key:\n%s" % result
        myPopUp_sb(self.caller, "info", "SPMT - findPubKey", mess)
        printOK("Public Key: %s" % result)
        self.ui.edt_pubKey.setText(result)

    def findRow_mn_list(self, name):
        row = 0
        while self.caller.tabMain.myList.item(row)['name'] < name:
            row += 1
        return row

    def isTestnet(self):
        return self.ui.testnetCheck.isChecked()

    def onCancelMNConfig(self):
        self.caller.tabs.setCurrentIndex(0)
        self.caller.tabs.removeTab(1)
        self.caller.mnode_to_change = None

    def onChangeTestnet(self):
        if self.isTestnet():
            self.ui.edt_masternodePort.setValue(51474)
        else:
            self.ui.edt_masternodePort.setValue(51472)

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

    def onFindSpathAndPrivKey(self):
        self.ui.edt_spath.setValue(0)
        self.ui.edt_pubKey.setText('')
        self.addressToSpath()

    def onLookupTx(self):
        # address check
        currAddr = self.ui.edt_address.text().strip()
        # Check rpc connection
        printDbg("Checking RPC connection")
        if not self.caller.rpcConnected:
            myPopUp_sb(self.caller, "crit", 'SPMT - hw device check', "Connect to RPC server first")
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

    def onGenerateMNkey(self):
        printDbg("Generate MNkey pressed")
        reply = QMessageBox.Yes

        if self.ui.edt_mnPrivKey.text() != "":
            reply = myPopUp(self.caller, "warn", "GENERATE PRIV KEY",
                            "Are you sure?\nThis will overwrite current private key", QMessageBox.No)

        if reply == QMessageBox.No:
            return

        newkey = generate_privkey(self.isTestnet())
        self.ui.edt_mnPrivKey.setText(newkey)

    def onSaveMNConf(self):
        try:
            if self.ui.edt_pubKey.text() == "" or self.ui.edt_txid.text() == "" or self.ui.edt_mnPrivKey.text() == "":
                mess_text = 'Attention! Complete the form before saving.<br>'
                mess_text += "<b>pubKey = </b>%s<br>" % self.ui.edt_pubKey.text()
                mess_text += "<b>txId = </b>%s<br>" % self.ui.edt_txid.text()
                mess_text += "<b>mnPrivKey = </b>%s<br>" % self.ui.edt_mnPrivKey.text()
                myPopUp_sb(self.caller, "crit", 'Complete Form', mess_text)
                return

            if not is_hex(self.ui.edt_txid.text()):
                mess_text = 'Attention! txid format is not valid.<br>'
                mess_text += "<b>txId = </b>%s<br>" % self.ui.edt_txid.text()
                mess_text += 'transaction id must be in hex format.<br>'
                myPopUp_sb(self.caller, "crit", 'Complete Form', mess_text)
                return

            # check for duplicate names
            mn_alias = self.ui.edt_name.text().strip()
            # if we are changing a masternode check for duplicate only if name is changed
            old_alias = None
            if self.caller.mnode_to_change is not None:
                old_alias = self.caller.mnode_to_change['name']
            if self.caller.isMasternodeInList(mn_alias) and old_alias != mn_alias:
                mess_text = 'Attention! The name <b>%s</b> is already in use for another masternode.<br>' % mn_alias
                mess_text += 'Choose a different name (alias) for the masternode'
                myPopUp_sb(self.caller, "crit", 'Complete Form', mess_text)
                return

            # create new item
            new_masternode = {}
            new_masternode['name'] = mn_alias
            masternodeIp = self.ui.edt_masternodeIp.text().strip()
            if not masternodeIp.endswith('.onion'):
                masternodeIp = ip_address(masternodeIp).compressed
            new_masternode['ip'] = masternodeIp
            new_masternode['port'] = self.ui.edt_masternodePort.value()
            new_masternode['mnPrivKey'] = self.ui.edt_mnPrivKey.text().strip()
            new_masternode['isTestnet'] = 0 if not self.isTestnet() else 1
            new_masternode['isHardware'] = True
            new_masternode['hwAcc'] = self.ui.edt_hwAccount.value()

            coll = {}
            coll['address'] = self.ui.edt_address.text().strip()
            coll['spath'] = self.ui.edt_spath.value()
            coll['pubKey'] = self.ui.edt_pubKey.text().strip()
            coll['txid'] = self.ui.edt_txid.text().strip()
            coll['txidn'] = self.ui.edt_txidn.value()

            new_masternode['collateral'] = coll

            # Add to cache, QListWidget and database (and remove/edit mnode_to_change)
            appendMasternode(self.caller, new_masternode)

            # go back
            self.onCancelMNConfig()

        except Exception as e:
            error_msg = "ERROR: %s" % e
            printDbg(error_msg)
            myPopUp_sb(self.caller, "crit", 'ERROR', error_msg)

    def spathToAddress(self):
        printOK("spathToAddress pressed")
        currHwAcc = self.ui.edt_hwAccount.value()
        currSpath = self.ui.edt_spath.value()
        # Check HW device
        if self.caller.hwStatus != 2:
            myPopUp_sb(self.caller, "crit", 'SPMT - hw device check', "Connect to HW device first")
            printDbg("Unable to connect to hardware device. The device status is: %d" % self.caller.hwStatus)
            return None
        addr = self.caller.hwdevice.scanForAddress(currHwAcc, currSpath, self.isTestnet())
        if addr:
            self.ui.edt_address.setText(addr)
            self.findPubKey()
