#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QLabel, QPushButton

from misc import sec_to_time


class MnStatus_dlg(QDialog):
    def __init__(self, main_wnd, mnAlias, statusData):
        QDialog.__init__(self, parent=main_wnd)
        self.main_wnd = main_wnd
        self.mnAlias = mnAlias
        self.statusData = statusData
        self.setWindowTitle('Masternode Details')
        self.setupUI()

    def setupUI(self):
        Ui_MnStatusDlg.setupUi(self, self)


class Ui_MnStatusDlg(object):
    def setupUi(self, MnStatusDlg):
        MnStatusDlg.setModal(True)
        layout = QVBoxLayout(MnStatusDlg)
        layout.setContentsMargins(10, 15, 10, 10)
        name = QLabel(f"<b><i>{self.mnAlias}</i></b>")
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)
        body = QFormLayout()
        body.setLabelAlignment(Qt.AlignRight)
        body.setVerticalSpacing(20)
        body.setContentsMargins(25, 10, 25, 30)
        body.addRow(QLabel("<b>Address</b>"), QLabel(self.statusData['addr']))
        body.addRow(QLabel("<b>Tx Hash: idx</b>"), QLabel(self.statusData['txhash']+": "+str(self.statusData['outidx'])))
        body.addRow(QLabel("<b>Network</b>"), QLabel(self.statusData['network']))
        body.addRow(QLabel("<b>Version</b>"), QLabel(str(self.statusData['version'])))
        body.addRow(QLabel("<b>Rank</b>"), QLabel(str(self.statusData['rank'])))
        body.addRow(QLabel("<b>Queue Position</b>"), QLabel(str(self.statusData['queue_pos'])))
        body.addRow(QLabel("<b>Active Time</b>"), QLabel(sec_to_time(self.statusData['activetime'])))
        body.addRow(QLabel("<b>Last Seen</b>"), QLabel(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(self.statusData['lastseen']))))
        body.addRow(QLabel("<b>Last Paid</b>"), QLabel(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(self.statusData['lastpaid']))))
        layout.addLayout(body)
        self.okButton = QPushButton('OK')
        self.okButton.clicked.connect(self.accept)
        layout.addWidget(self.okButton)
        sh = layout.sizeHint()
        self.setFixedSize(sh)
