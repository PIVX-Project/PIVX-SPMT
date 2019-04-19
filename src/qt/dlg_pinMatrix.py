#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QGridLayout, \
    QLineEdit, QHBoxLayout, QWidget

from misc import myPopUp_sb

class PinMatrix_dlg(QDialog):
    def __init__(self, text='', title='Enter PIN', fHideBtns=True):
        QDialog.__init__(self)
        self.text = text if text != '' else "Check device and enter PIN"
        self.hideBtns = fHideBtns
        self.pin = ''
        self.setWindowTitle(title)
        self.setupUI()


    def btn_clicked(self, num):
        self.pin += num
        self.lbl_pin.setText('*' * len(self.pin))


    def getPin(self):
        return self.pin


    def onCancel(self):
        self.pin = ''
        self.reject()


    def onDel(self):
        self.pin = self.pin[:-1]
        self.lbl_pin.setText('*' * len(self.pin))


    def onOK(self):
        if self.pin:
            if len(self.pin) > 9:
                text = "The PIN entered exceeds the 9-character limit."
                myPopUp_sb(self, "warn", 'Wrong PIN!', text)
            else:
                self.accept()
        else:
            text = "No PIN entered"
            myPopUp_sb(self, "warn", 'Wrong PIN!', text)


    def setupUI(self):
        Ui_pinMatrixDlg.setupUi(self, self)
        # Connect buttons matrix
        for i in range(9):
            self.btn[i].clicked.connect(lambda _, b=i+1: self.btn_clicked(str(b)))
        # Connect del/ok/cancel
        self.btn_del.clicked.connect(self.onDel)
        self.btn_ok.clicked.connect(self.onOK)
        self.btn_cancel.clicked.connect(self.onCancel)




class Ui_pinMatrixDlg(object):
    def setupUi(self, PinMatrixDlg):
        PinMatrixDlg.setModal(True)
        layout = QVBoxLayout(PinMatrixDlg)
        layout.setContentsMargins(10, 8, 10, 10)

        # Header
        title = QLabel("<b>%s</b>" % PinMatrixDlg.text)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Label
        lbl_style = """
                    QLabel {margin-top: 10px; color: purple; font-size: 15pt}
                    """
        self.lbl_pin = QLabel()
        self.lbl_pin.setAlignment(Qt.AlignCenter)
        self.lbl_pin.setStyleSheet(lbl_style)
        layout.addWidget(self.lbl_pin)

        # Buttons
        btn_style = """
                    QPushButton {padding: 1px 1px 1px; border: 1px solid purple; min-width: 90px; min-height:90px}
                    QPushButton:enabled {background-color: white}
                    QPushButton:pressed {background-color: purple; color:white; border: 1px solid purple}
                    """
        self.btn = []
        for i in range(9):
            btn_lab = '\u2022' if PinMatrixDlg.hideBtns else str(i+1)
            btn = QPushButton(btn_lab)
            self.btn.append(btn)

        # Grid
        btnMatrix = QWidget(self)
        btnMatrix.setStyleSheet(btn_style)
        grid = QGridLayout()
        grid.addWidget(self.btn[0], 2, 0, Qt.AlignCenter)
        grid.addWidget(self.btn[1], 2, 1, Qt.AlignCenter)
        grid.addWidget(self.btn[2], 2, 2, Qt.AlignCenter)
        grid.addWidget(self.btn[3], 1, 0, Qt.AlignCenter)
        grid.addWidget(self.btn[4], 1, 1, Qt.AlignCenter)
        grid.addWidget(self.btn[5], 1, 2, Qt.AlignCenter)
        grid.addWidget(self.btn[6], 0, 0, Qt.AlignCenter)
        grid.addWidget(self.btn[7], 0, 1, Qt.AlignCenter)
        grid.addWidget(self.btn[8], 0, 2, Qt.AlignCenter)
        btnMatrix.setLayout(grid)
        layout.addWidget(btnMatrix)

        # Del/OK/Cancel button
        self.btn_del = QPushButton('\u232b')
        self.btn_del.setToolTip("Remove last entered key")
        layout.addWidget(self.btn_del)
        hBox = QHBoxLayout()
        self.btn_ok = QPushButton('OK')
        self.btn_cancel = QPushButton('Cancel')
        hBox.addWidget(self.btn_ok)
        hBox.addWidget(self.btn_cancel)
        layout.addLayout(hBox)

        sh = layout.sizeHint()
        self.setFixedSize(sh)
