#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from time import strftime, gmtime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QLabel, QLineEdit, \
    QScrollArea, QFrame, QPushButton


class ProposalDetails_dlg(QDialog):
    def __init__(self, main_wnd, proposal):
        QDialog.__init__(self, parent=main_wnd)
        self.data = proposal
        myVotes = main_wnd.caller.parent.db.getMyVotes(proposal.Hash)
        self.myYeas = [[v["mn_name"], v["time"]] for v in myVotes if v["vote"] == "YES"]
        self.myAbstains = [[v["mn_name"], v["time"]] for v in myVotes if v["vote"] == "ABSTAIN"]
        self.myNays = [[v["mn_name"], v["time"]] for v in myVotes if v["vote"] == "NO"]
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
        name = QLabel(f"<b><i>{PropDetailsDlg.data.name}</i></b>")
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)
        body = QFormLayout()
        body.setLabelAlignment(Qt.AlignRight)
        body.setVerticalSpacing(20)
        body.setContentsMargins(25, 10, 25, 30)
        link = f"<a href='{PropDetailsDlg.data.URL}'>{PropDetailsDlg.data.URL}</a>"
        link_label = QLabel(link)
        link_label.setOpenExternalLinks(True)
        body.addRow(QLabel(f"<b>URL: </b>"), QLabel(link_label))
        body.addRow(QLabel(f"<b>TotalPayment: </b>"), QLabel(f"{PropDetailsDlg.data.TotalPayment}"))
        body.addRow(QLabel(f"<b>MonthlyPayment: </b>"), QLabel(f"{PropDetailsDlg.data.MonthlyPayment}"))
        hashLabel = self.selectable_line(PropDetailsDlg.data.Hash)
        body.addRow(QLabel(f"<b>Hash: </b>"), hashLabel)
        feeHashLabel = self.selectable_line(PropDetailsDlg.data.FeeHash)
        body.addRow(QLabel(f"<b>FeeHash: </b>"), feeHashLabel)
        body.addRow(QLabel(f"<b>BlockStart: </b>"), QLabel(f"{PropDetailsDlg.data.BlockStart}"))
        body.addRow(QLabel(f"<b>BlockEnd: </b>"), QLabel(f"{PropDetailsDlg.data.BlockEnd}"))
        body.addRow(QLabel(f"<b>TotalPayCount: </b>"), QLabel(f"{PropDetailsDlg.data.TotalPayCount}"))
        body.addRow(QLabel(f"<b>RemainingPayCount: </b>"), QLabel(f"{PropDetailsDlg.data.RemainingPayCount}"))
        addyLabel = self.selectable_line(PropDetailsDlg.data.PaymentAddress)
        body.addRow(QLabel(f"<b>PaymentAddress: </b>"), addyLabel)
        votes = (f"<span style='color: green'>{PropDetailsDlg.data.Yeas} YEAS</span> / " +
                 f"<span style='color: orange'>{PropDetailsDlg.data.Abstains} ABSTAINS</span> / " +
                 f"<span style='color: red'>{PropDetailsDlg.data.Nays} NAYS</span>")
        body.addRow(QLabel(f"<b>Votes: </b>"), QLabel(votes))
        my_yeas = [f"{x[0]} <em style='color: green'>({strftime('%Y-%m-%d %H:%M:%S', gmtime(x[1]))})</em>"
           for x in PropDetailsDlg.myYeas]
        body.addRow(QLabel("<b>My Yeas: </b>"), self.scroll(my_yeas))
        my_abstains = [f"{x[0]} <em style='color: orange'>({strftime('%Y-%m-%d %H:%M:%S', gmtime(x[1]))})</em>"
               for x in PropDetailsDlg.myAbstains]
        body.addRow(QLabel("<b>My Abstains: </b>"), self.scroll(my_abstains))
        my_nays = [f"{x[0]} <em style='color: red'>({strftime('%Y-%m-%d %H:%M:%S', gmtime(x[1]))})</em>"
           for x in PropDetailsDlg.myNays]
        body.addRow(QLabel("<b>My Nays: </b>"), self.scroll(my_nays))
        layout.addLayout(body)
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.accept)
        layout.addWidget(self.okButton)
        sh = layout.sizeHint()
        self.setFixedSize(sh)
