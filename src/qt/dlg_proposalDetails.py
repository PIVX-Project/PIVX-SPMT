#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
from PyQt5.QtGui import QPalette
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QLabel, QLineEdit,\
    QScrollArea, QFrame
from PyQt5.Qt import QPushButton
from PyQt5.QtCore import Qt
from time import strftime, gmtime

class ProposalDetails_dlg(QDialog):
    def __init__(self, main_wnd, proposal):
        QDialog.__init__(self, parent=main_wnd)
        self.data = proposal
        self.setWindowTitle('Proposal Details')
        self.setupUI()
        
    def setupUI(self):
        Ui_proposalDetailsDlg.setupUi(self, self)
        
        
    def selectable_line(self, item):
        line = QLineEdit(item)
        line.setMinimumWidth(420)
        line.setMinimumWidth(420)
        line.setReadOnly(True)
        line.setFrame(QFrame.NoFrame)
        return line
        
    
    def scroll(self, item):
        if isinstance(item, list):
            item = item if len(item) > 0 else ""
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setMaximumHeight(50)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setBackgroundRole(3)
        label = QLabel(str(item))
        label.setContentsMargins(5, 5, 5, 5)
        scroll.setWidget(label)
        return scroll

        

class Ui_proposalDetailsDlg(object):
    def setupUi(self, PropDetailsDlg):
        PropDetailsDlg.setModal(True)
        layout = QVBoxLayout(PropDetailsDlg)
        layout.setContentsMargins(10, 15, 10, 10)
        name = QLabel("<b><i>%s</i></b>" % PropDetailsDlg.data.name)
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)
        body = QFormLayout()
        body.setLabelAlignment(Qt.AlignRight)
        body.setVerticalSpacing(20)
        body.setContentsMargins(25, 10, 25, 30)
        link = "<a href='%s'>%s</a>" % (PropDetailsDlg.data.URL, PropDetailsDlg.data.URL)
        link_label = QLabel(link)
        link_label.setOpenExternalLinks(True)
        body.addRow(QLabel("<b>URL: </b>"), link_label)
        body.addRow(QLabel("<b>TotalPayment: </b>"), QLabel(str(PropDetailsDlg.data.ToalPayment)))
        body.addRow(QLabel("<b>MonthlyPayment: </b>"), QLabel(str(PropDetailsDlg.data.MonthlyPayment)))
        hashLabel = self.selectable_line(PropDetailsDlg.data.Hash)
        body.addRow(QLabel("<b>Hash: </b>"), hashLabel)
        feeHashLabel = self.selectable_line(PropDetailsDlg.data.FeeHash)
        body.addRow(QLabel("<b>FeeHash: </b>"), feeHashLabel)
        body.addRow(QLabel("<b>BlockStart: </b>"), QLabel(str(PropDetailsDlg.data.BlockStart)))
        body.addRow(QLabel("<b>BlockEnd: </b>"), QLabel(str(PropDetailsDlg.data.BlockEnd)))
        body.addRow(QLabel("<b>TotalPayCount: </b>"), QLabel(str(PropDetailsDlg.data.TotalPayCount)))
        body.addRow(QLabel("<b>RemainingPayCount: </b>"), QLabel(str(PropDetailsDlg.data.RemainingPayCount)))
        addyLabel = self.selectable_line(PropDetailsDlg.data.PaymentAddress)
        body.addRow(QLabel("<b>PaymentAddress: </b>"), addyLabel)
        votes = "<span style='color: green'>%d YEAS</span> / " % PropDetailsDlg.data.Yeas
        votes += "<span style='color: orange'>%d ABSTAINS</span> / " % PropDetailsDlg.data.Abstains
        votes += "<span style='color: red'>%d NAYS</span>" % PropDetailsDlg.data.Nays
        body.addRow(QLabel("<b>Votes: </b>"), QLabel(votes))
        my_yeas = ["%s <em style='color: green'>(%s)</em>" % (x[0], strftime('%Y-%m-%d %H:%M:%S', 
                                                        gmtime(x[1][1]))) for x in PropDetailsDlg.data.MyYeas]
        body.addRow(QLabel("<b>My Yeas: </b>"), self.scroll(my_yeas))
        my_abstains = ["%s <em style='color: orange'>(%s)</em>" % (x[0], strftime('%Y-%m-%d %H:%M:%S', 
                                                        gmtime(x[1][1]))) for x in PropDetailsDlg.data.MyAbstains]
        body.addRow(QLabel("<b>My Abstains: </b>"), self.scroll(my_abstains))
        my_nays = ["%s <em style='color: red'>(%s)</em>" % (x[0], strftime('%Y-%m-%d %H:%M:%S', 
                                                        gmtime(x[1][1]))) for x in PropDetailsDlg.data.MyNays]
        body.addRow(QLabel("<b>My Nays: </b>"), self.scroll(my_nays))
        layout.addLayout(body)
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.accept)
        layout.addWidget(self.okButton)
        sh = layout.sizeHint()
        self.setFixedSize(sh)