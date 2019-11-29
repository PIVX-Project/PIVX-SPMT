#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from misc import myPopUp, myPopUp_sb, getCallerName, getFunctionName, printException
from pivx_hashlib import pubkey_to_address
from threads import ThreadFuns
from utils import checkPivxAddr, ecdsa_verify_addr

class SignMessage_dlg(QDialog):
    def __init__(self, main_wnd):
        QDialog.__init__(self, parent=main_wnd)
        self.setWindowTitle('Sign/Verify Message')
        self.initUI(main_wnd)

    def initUI(self, main_wnd):
        self.ui = Ui_SignMessageDlg()
        self.ui.setupUi(self, main_wnd)


class Ui_SignMessageDlg(object):
    def setupUi(self, SignMessageDlg, main_wnd):
        SignMessageDlg.setModal(True)
        SignMessageDlg.setMinimumWidth(600)
        SignMessageDlg.setMinimumHeight(400)
        self.layout = QVBoxLayout(SignMessageDlg)
        self.layout.setSpacing(10)
        self.tabs = QTabWidget()
        self.tabSign = TabSign(main_wnd)
        self.tabVerify = TabVerify(main_wnd)
        self.tabs.addTab(self.tabSign.ui, "Sign message")
        self.tabs.addTab(self.tabVerify.ui, "Verify message signature")
        self.layout.addWidget(self.tabs)


class TabSign:
    def __init__(self, main_wnd):
        self.main_wnd = main_wnd
        self.ui = TabSign_gui()
        self.loadAddressComboBox(self.main_wnd.masternode_list)
        # connect signals/buttons
        self.ui.addressComboBox.currentIndexChanged.connect(lambda: self.onChangeSelectedAddress())
        self.ui.editBtn.clicked.connect(lambda: self.onEdit())
        self.ui.signBtn.clicked.connect(lambda: self.onSign())
        self.ui.copyBtn.clicked.connect(lambda: self.onCopy())
        self.ui.saveBtn.clicked.connect(lambda: self.onSave())
        self.ui.fromAddressRadioBtn.toggled.connect(lambda: self.onToggleRadio(True))
        self.ui.fromSpathRadioBtn.toggled.connect(lambda: self.onToggleRadio(False))
        self.ui.searchPKBtn.clicked.connect(lambda: self.onSearchPK())


    def loadAddressComboBox(self, mn_list):
        comboBox = self.ui.addressComboBox
        for x in mn_list:
            if x['isHardware']:
                name = x['name']
                address = x['collateral'].get('address')
                hwAcc = x['hwAcc']
                spath = x['collateral'].get('spath')
                hwpath = "%d'/0/%d" % (hwAcc, spath)
                isTestnet = x['isTestnet']
                comboBox.addItem(name, [address, hwpath, isTestnet])
        # add generic address (bold)
        comboBox.addItem("Generic address...", ["", "", False])
        boldFont = QFont("Times")
        boldFont.setBold(True)
        comboBox.setItemData(comboBox.count() - 1, boldFont, Qt.FontRole)
        # init selection
        self.onChangeSelectedAddress()


    def displaySignature(self, sig):
        if sig == "None":
            self.ui.signatureTextEdt.setText("Signature refused by the user")
            return
        from utils import b64encode
        self.ui.signatureTextEdt.setText(b64encode(sig))
        self.ui.copyBtn.setVisible(True)
        self.ui.saveBtn.setVisible(True)
        # verify sig
        ok = ecdsa_verify_addr(self.ui.messageTextEdt.toPlainText(), b64encode(sig), self.currAddress)
        if not ok:
            mess = "Signature doesn't verify."
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no signature', mess)


    def findPubKey(self):
        device = self.main_wnd.hwdevice

        pk = device.scanForPubKey(self.hwAcc, self.spath, self.currIsTestnet)
        if pk is None:
            mess = "Unable to find public key. The action was refused on the device or another application "
            mess += "might have taken over the USB communication with the device.<br><br>"
            mess += "The operation was canceled."
            myPopUp_sb(self.main_wnd, QMessageBox.Critical, 'SPMT - PK not found', mess)
            return
        self.updateGenericAddress(pk)


    def findSpath(self, ctrl, starting_spath, spath_count):
        addy = self.ui.addressLineEdit.text().strip()
        device = self.main_wnd.hwdevice
        self.spath_found, self.spath = device.scanForBip32(self.hwAcc, addy, starting_spath, spath_count,
                                                           self.currIsTestnet)
        self.curr_starting_spath = starting_spath
        self.curr_spath_count = spath_count


    def findSpath_done(self):
        if self.spath_found:
            self.findPubKey()
        else:
            addy = self.ui.addressLineEdit.text().strip()
            starting_spath = self.curr_starting_spath
            spath_count = self.curr_spath_count
            mess = "Scanned addresses <b>%d</b> to <b>%d</b> of HW account <b>%d</b>.<br>" % (
                starting_spath, starting_spath + spath_count - 1, self.hwAcc)
            mess += "Unable to find the address <i>%s</i>.<br>Maybe it's on a different account.<br><br>" % addy
            mess += "Do you want to scan %d more addresses of account n.<b>%d</b> ?" % (spath_count, self.hwAcc)
            ans = myPopUp(self.main_wnd, QMessageBox.Question, 'SPMT - spath search', mess)
            if ans == QMessageBox.Yes:
                # Look for 10 more addresses
                starting_spath += spath_count
                ThreadFuns.runInThread(self.findSpath, (starting_spath, spath_count), self.findSpath_done)


    def onChangeSelectedAddress(self):
        self.currName = None
        self.ui.editBtn.setVisible(False)
        comboBox = self.ui.addressComboBox
        i = comboBox.currentIndex()
        if i != comboBox.count() - 1:
            # masternode address
            self.setSignEnabled(True)
            self.currName = comboBox.itemText(i)
            self.currAddress = comboBox.itemData(i)[0]
            self.currHwPath = comboBox.itemData(i)[1]
            self.currIsTestnet = comboBox.itemData(i)[2]
            self.ui.addressLabel.setText(self.currAddress)
        else:
            # generic address
            self.setSignEnabled(False)


    def onCopy(self):
        if self.ui.signatureTextEdt.document().isEmpty():
            mess = "Nothing to copy. Sign message first."
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no signature', mess)
            return
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(self.ui.signatureTextEdt.toPlainText(), mode=cb.Clipboard)
        myPopUp_sb(self.main_wnd, QMessageBox.Information, 'SPMT - copied', "Signature copied to the clipboard")


    def onEdit(self):
        visible = self.ui.hiddenLine.isVisible()
        self.ui.hiddenLine.setVisible(not visible)


    def onSave(self):
        if self.ui.signatureTextEdt.document().isEmpty():
            mess = "Nothing to save. Sign message first."
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no signature', mess)
            return
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self.main_wnd, "Save signature to file", "sig.txt",
                                                  "All Files (*);; Text Files (*.txt)", options=options)
        try:
            if fileName:
                save_file = open(fileName, 'w')
                save_file.write(self.ui.signatureTextEdt.toPlainText())
                save_file.close()
                myPopUp_sb(self.main_wnd, QMessageBox.Information, 'SPMT - saved', "Signature saved to file")
                return
        except Exception as e:
            err_msg = "error writing signature to file"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - NOT saved', "Signature NOT saved to file")


    def onSearchPK(self):
        fromAddress = self.ui.fromAddressRadioBtn.isChecked()
        self.hwAcc = self.ui.hwAccountSpingBox.value()
        self.currIsTestnet = self.ui.testnetCheckBox.isChecked()
        if fromAddress:
            addy = self.ui.addressLineEdit.text().strip()
            if len(addy) == 0:
                mess = "No address. Insert PIVX address first."
                myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no address', mess)
                return

            if not checkPivxAddr(addy, self.currIsTestnet):
                net = "testnet" if self.currIsTestnet else "mainnet"
                mess = "PIVX address not valid. Insert valid PIVX %s address" % net
                myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - invalid address', mess)
                return

        # check hw connection
        while self.main_wnd.hwStatus != 2:
            mess = "HW device not connected. Try to connect?"
            ans = myPopUp(self.main_wnd, QMessageBox.Question, 'SPMT - hw check', mess)
            if ans == QMessageBox.No:
                return
            # re connect
            self.main_wnd.onCheckHw()

        # Go!
        if fromAddress:
            self.spath_found = False
            ThreadFuns.runInThread(self.findSpath, (0, 10), self.findSpath_done)
        else:
            self.spath_found = True
            self.spath = self.ui.spathSpinBox.value()
            self.findPubKey()


    def onSign(self):
        # check message
        if self.ui.messageTextEdt.document().isEmpty():
            mess = "Nothing to sign. Insert message."
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no message', mess)
            return
        # check hw connection
        while self.main_wnd.hwStatus != 2:
            mess = "HW device not connected. Try to connect?"
            ans = myPopUp(self.main_wnd, QMessageBox.Question, 'SPMT - hw check', mess)
            if ans == QMessageBox.No:
                return
            # re connect
            self.main_wnd.onCheckHw()
        # sign message on HW device
        serializedData = str(self.ui.messageTextEdt.toPlainText())
        device = self.main_wnd.hwdevice
        try:
            device.sig1done.disconnect()
        except:
            pass
        device.sig1done.connect(self.displaySignature)
        try:
            device.signMess(self.main_wnd, self.currHwPath, serializedData, self.currIsTestnet)
            # wait for signal when device.sig1 is ready then --> displaySignature
        except Exception as e:
            err_msg = "error during signature"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        except KeyboardInterrupt:
            err_msg = "Keyboard Interrupt"
            printException(getCallerName(), getFunctionName(), err_msg, '')


    def onToggleRadio(self, isFromAddress):
        self.ui.fromAddressBox.setVisible(isFromAddress)
        self.ui.fromSpathBox.setVisible(not isFromAddress)


    def setSignEnabled(self, enabled):
        self.ui.signBtn.setEnabled(enabled)
        self.ui.hiddenLine.setVisible(not enabled)
        tooltip = ""
        if not enabled:
            tooltip = "You need to find the address PK in your hardware device first.\n"\
                      "Insert the account number (usually 0) and either a PIVX address\n"\
                      "or the spath_id (address number) and click 'Search HW'."
            self.ui.addressLabel.setText("")
        self.ui.signBtn.setToolTip(tooltip)


    def updateGenericAddress(self, pk):
        genericAddy = pubkey_to_address(pk, self.currIsTestnet)
        if self.ui.fromAddressRadioBtn.isChecked():
            # double check address
            addy = self.ui.addressLineEdit.text().strip()
            if addy != genericAddy:
                mess = "Error! retrieved address (%s) different from input (%s)" % (genericAddy, addy)
                myPopUp_sb(self.main_wnd, QMessageBox.Critical, 'SPMT - address mismatch', mess)
                self.ui.addressLabel.setText("")
                return
        # update generic address
        self.setSignEnabled(True)
        self.currAddress = genericAddy
        self.currHwPath = "%d'/0/%d" % (self.hwAcc, self.spath)
        self.ui.addressLabel.setText(self.currAddress)
        self.ui.editBtn.setVisible(True)





class TabVerify:
    def __init__(self, main_wnd):
        self.main_wnd = main_wnd
        self.ui = TabVerify_gui()
        # connect signals/buttons
        self.ui.verifyBtn.clicked.connect(lambda: self.onVerify())

    def onVerify(self):
        # check fields
        addy = self.ui.addressLineEdit.text().strip()
        if len(addy) == 0:
            mess = "No address inserted"
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no address', mess)
            return
        if not checkPivxAddr(addy, True) and not checkPivxAddr(addy, False):
            mess = "PIVX address not valid. Insert valid PIVX address"
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - invalid address', mess)
            return
        if self.ui.messageTextEdt.document().isEmpty():
            mess = "No message inserted"
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no message', mess)
            return
        if self.ui.signatureTextEdt.document().isEmpty():
            mess = "No signature inserted"
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no signature', mess)
            return

        try:
            ok = ecdsa_verify_addr(self.ui.messageTextEdt.toPlainText(),
                                   self.ui.signatureTextEdt.toPlainText(),
                                   self.ui.addressLineEdit.text().strip())
        except Exception as e:
            mess = "Error decoding signature:\n" + str(e)
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - invalid signature', mess)
            ok = False
        if ok:
            mess = "<span style='color: green'>Signature OK"
        else:
            mess = "<span style='color: red'>Signature doesn't verify"
        mess = "<b>" + mess + "</span></b>"
        self.ui.resultLabel.setText(mess)
        self.ui.resultLabel.setVisible(True)


class TabSign_gui(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(13)
        # row 1: select address
        row1 = QFormLayout()
        row1.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        hBox = QHBoxLayout()
        self.addressComboBox = QComboBox()
        self.addressComboBox.setToolTip("Select address/masternode")
        hBox.addWidget(self.addressComboBox)
        self.addressLabel = QLabel()
        labelstyle = "QLabel { font-size: 11px; color: purple; font-style: italic;}"
        self.addressLabel.setStyleSheet(labelstyle)
        # make it selectable by mouse and change pointer on hover
        self.addressLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.addressLabel.setCursor(Qt.IBeamCursor)
        hBox.addWidget(self.addressLabel)
        hBox.addStretch(1)
        self.editBtn = QPushButton("Edit")
        self.editBtn.setVisible(False)
        hBox.addWidget(self.editBtn)
        row1.addRow(QLabel("Sign with"), hBox)
        layout.addLayout(row1)
        # rows 1-2B (hidden) - custom address
        self.hiddenLine = QWidget()
        hiddenLayout = QVBoxLayout()
        row1b = QHBoxLayout()
        self.testnetCheckBox = QCheckBox()
        self.testnetCheckBox.setToolTip("Check to look for testnet addresses")
        row1b.addWidget(QLabel("testnet"))
        row1b.addWidget(self.testnetCheckBox)
        row1b.addStretch(1)
        # address/spath radio
        self.fromAddressRadioBtn = QRadioButton("search PIVX address")
        self.fromAddressRadioBtn.setChecked(True)
        row1b.addWidget(self.fromAddressRadioBtn)
        self.fromSpathRadioBtn = QRadioButton("search from BIP44 path")
        self.fromSpathRadioBtn.setChecked(False)
        row1b.addWidget(self.fromSpathRadioBtn)
        row1b.addStretch(1)
        hiddenLayout.addLayout(row1b)
        # row2b fromAddress/fromSpath
        row2b = QHBoxLayout()
        self.hwAccountSpingBox = QSpinBox()
        self.hwAccountSpingBox.setFixedWidth(50)
        self.hwAccountSpingBox.setToolTip("account number of the hardware wallet.\nIf unsure put 0")
        self.hwAccountSpingBox.setValue(0)
        row2b.addWidget(QLabel("Account n."))
        row2b.addWidget(self.hwAccountSpingBox)
        row2b.addStretch(1)
        self.fromAddressBox = QWidget()
        hBox = QHBoxLayout()
        self.addressLineEdit = QLineEdit()
        self.addressLineEdit.setToolTip("the PIVX address to look for")
        self.addressLineEdit.setMinimumWidth(200)
        hBox.addWidget(QLabel("PIVX Address"))
        hBox.addWidget(self.addressLineEdit)
        self.fromAddressBox.setLayout(hBox)
        row2b.addWidget(self.fromAddressBox)
        self.fromSpathBox = QWidget()
        hBox = QHBoxLayout()
        self.spathSpinBox = QSpinBox()
        self.spathSpinBox.setToolTip("BIP44 spath for the address (address_index level)")
        self.spathSpinBox.setFixedWidth(75)
        self.spathSpinBox.setValue(0)
        hBox.addWidget(QLabel("spath_id"))
        hBox.addWidget(self.spathSpinBox)
        self.fromSpathBox.setLayout(hBox)
        self.fromSpathBox.setVisible(False)
        row2b.addWidget(self.fromSpathBox)
        self.searchPKBtn = QPushButton("Search HW")
        self.searchPKBtn.setToolTip("find public key of given address/spath_id")
        row2b.addWidget(self.searchPKBtn)
        hiddenLayout.addLayout(row2b)
        self.hiddenLine.setLayout(hiddenLayout)
        self.hiddenLine.setVisible(False)
        layout.addWidget(self.hiddenLine)
        # row 2: message
        self.messageTextEdt = QTextEdit()
        self.messageTextEdt.setReadOnly(False)
        self.messageTextEdt.setAcceptRichText(False)
        self.messageTextEdt.setPlaceholderText("Write message here...")
        layout.addWidget(self.messageTextEdt)
        # row 3: sign message button
        self.signBtn = QPushButton("Sign Message")
        layout.addWidget(self.signBtn)
        # row 4: signature
        self.signatureTextEdt = QTextEdit()
        self.signatureTextEdt.setReadOnly(True)
        self.signatureTextEdt.setMaximumHeight(100)
        almostBlack = QColor(40, 40, 40)
        palette = QPalette()
        palette.setColor(QPalette.Base, almostBlack)
        green = QColor(0, 255, 0)
        palette.setColor(QPalette.Text, green)
        self.signatureTextEdt.setPalette(palette)
        layout.addWidget(self.signatureTextEdt)
        # row 5: copy/save buttons
        row5 = QHBoxLayout()
        self.copyBtn = QPushButton("Copy")
        self.copyBtn.setToolTip("Copy signature to clipboard")
        self.copyBtn.setVisible(False)
        row5.addWidget(self.copyBtn)
        self.saveBtn = QPushButton("Save")
        self.saveBtn.setToolTip("Save signature to ca file")
        self.saveBtn.setVisible(False)
        row5.addWidget(self.saveBtn)
        layout.addLayout(row5)
        # ---
        self.setLayout(layout)


class TabVerify_gui(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(13)
        # row 1: select address
        row1 = QFormLayout()
        row1.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        hBox = QHBoxLayout()
        self.addressLineEdit = QLineEdit()
        self.addressLineEdit.setToolTip("insert address to verify signature with")
        hBox.addWidget(self.addressLineEdit)
        row1.addRow(QLabel("PIVX address"), hBox)
        layout.addLayout(row1)
        # row 2: message
        self.messageTextEdt = QTextEdit()
        self.messageTextEdt.setReadOnly(False)
        self.messageTextEdt.setAcceptRichText(False)
        self.messageTextEdt.setPlaceholderText("Write message here...")
        layout.addWidget(self.messageTextEdt)
        # row 3: signature
        self.signatureTextEdt = QTextEdit()
        self.signatureTextEdt.setReadOnly(False)
        self.signatureTextEdt.setMaximumHeight(100)
        self.signatureTextEdt.setAcceptRichText(False)
        self.signatureTextEdt.setPlaceholderText("Write signature here...")
        layout.addWidget(self.signatureTextEdt)
        # row 4: verify message button
        self.verifyBtn = QPushButton("Verify Message")
        layout.addWidget(self.verifyBtn)
        # row 5: result
        self.resultLabel = QLabel()
        self.resultLabel.setVisible(False)
        layout.addWidget(self.resultLabel)
        # ---
        self.setLayout(layout)