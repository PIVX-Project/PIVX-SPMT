#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from misc import myPopUp, myPopUp_sb, getCallerName, getFunctionName, printException

class SignMessage_dlg(QDialog):
    def __init__(self, main_wnd):
        QDialog.__init__(self, parent=main_wnd)
        self.setWindowTitle('Sign/Verify Message')
        self.initUI(main_wnd)

    def initUI(self, main_wnd):
        self.ui = Ui_SignMessageDlg()
        self.ui.setupUi(self, main_wnd)


class Ui_SignMessageDlg(object):
    def setupUi(self, SignMessageDlg, mn_list):
        SignMessageDlg.setModal(True)
        SignMessageDlg.setMinimumWidth(600)
        SignMessageDlg.setMinimumHeight(400)
        self.layout = QVBoxLayout(SignMessageDlg)
        self.layout.setSpacing(10)
        self.tabs = QTabWidget()
        self.tabSign = TabSign(mn_list)
        self.tabVerify = TabVerify()
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
        self.ui.signBtn.clicked.connect(lambda: self.onSign())
        self.ui.copyBtn.clicked.connect(lambda: self.onCopy())
        self.ui.saveBtn.clicked.connect(lambda: self.onSave())


    def loadAddressComboBox(self, mn_list):
        for x in mn_list:
            if x['isHardware']:
                name = x['name']
                address = x['collateral'].get('address')
                hwAcc = x['hwAcc']
                spath = x['collateral'].get('spath')
                hwpath = "%d'/0/%d" % (hwAcc, spath)
                isTestnet = x['isTestnet']
                self.ui.addressComboBox.addItem(name, [address, hwpath, isTestnet])
        # init selection
        self.onChangeSelectedAddress()


    def displaySignature(self, sig):
        from utils import b64encode, ecdsa_verify_addr
        if sig == "None":
            sig = "Signature refused by the user"
        self.ui.signatureTextEdt.setText(b64encode(sig))
        self.ui.copyBtn.setVisible(True)
        self.ui.saveBtn.setVisible(True)
        # verify sig
        ok = ecdsa_verify_addr(self.ui.messageTextEdt.toPlainText(), b64encode(sig), self.currAddress)
        if not ok:
            mess = "Signature doesn't verify."
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no signature', mess)


    def onChangeSelectedAddress(self):
        self.currName = None
        comboBox = self.ui.addressComboBox
        i = comboBox.currentIndex()
        self.currName = comboBox.itemText(i)
        self.currAddress = comboBox.itemData(i)[0]
        self.currHwPath = comboBox.itemData(i)[1]
        self.currIsTestnet = comboBox.itemData(i)[2]
        self.ui.addressLabel.setText(self.currAddress)


    def onCopy(self):
        if self.ui.signatureTextEdt.document().isEmpty():
            mess = "Nothing to copy. Sign message first."
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no signature', mess)
            return
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(self.ui.signatureTextEdt.toPlainText(), mode=cb.Clipboard)
        myPopUp_sb(self.main_wnd, QMessageBox.Information, 'SPMT - copied', "Signature copied to the clipboard")


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




class TabVerify:
    def __init__(self):
        self.ui = TabVerify_gui()
        # connect signals/buttons
        self.ui.verifyBtn.clicked.connect(lambda: self.onVerify())

    def onVerify(self):
        # check fields
        if len(self.ui.addressLineEdit.text()) == 0:
            mess = "No address inserted"
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no address', mess)
            return
        if self.ui.messageTextEdt.document().isEmpty():
            mess = "No message inserted"
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no message', mess)
            return
        if self.ui.signatureTextEdt.document().isEmpty():
            mess = "No signature inserted"
            myPopUp_sb(self.main_wnd, QMessageBox.Warning, 'SPMT - no signature', mess)
            return
        from utils import ecdsa_verify_addr
        ok = ecdsa_verify_addr(self.ui.messageTextEdt.toPlainText(),
                               self.ui.signatureTextEdt.toPlainText(),
                               self.ui.addressLineEdit.text())
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
        row1.addRow(QLabel("Sign with"), hBox)
        layout.addLayout(row1)
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