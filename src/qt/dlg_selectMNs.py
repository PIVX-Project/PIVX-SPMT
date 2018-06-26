#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTableWidget, QVBoxLayout, QAbstractItemView, QHeaderView,\
    QTableWidgetItem, QLabel, QHBoxLayout, QPushButton
    
from misc import writeToFile
from constants import cache_File
    
class masternodeItem(QTableWidgetItem):
    def __init__(self, name, txid):
        super().__init__(name)
        self.txid = txid

class SelectMNs_dlg(QDialog):
    def __init__(self, main_wnd):
        QDialog.__init__(self, parent=main_wnd.ui)
        self.main_wnd = main_wnd
        self.setWindowTitle('Masternode List')
        self.initUI()
        self.loadMasternodes()
        ## connect buttons
        self.ui.selectAll_btn.clicked.connect(lambda: self.selectAll())
        self.ui.deselectAll_btn.clicked.connect(lambda: self.ui.mnList.clearSelection())
        self.ui.ok_btn.clicked.connect(lambda: self.onOK())
    
        
    def getSelection(self):
        items = self.ui.mnList.selectedItems()
        #print("Selected MNs " + str([[x.txid, x.text()] for x in items]))
        return [[x.txid, x.text()] for x in items]
        
    def initUI(self):
        self.ui = Ui_SelectMNsDlg()
        self.ui.setupUi(self)
        
    def loadMasternodes(self):
        for row, mn in enumerate(self.main_wnd.caller.masternode_list):
            name = mn.get('name')
            txid = mn.get('collateral').get('txid')
            item = masternodeItem(name, txid)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.ui.mnList.setItem(row, 0, item)
            # check if already selected
            if name in [x[1] for x in self.main_wnd.votingMasternodes]:
                item.setSelected(True)
            
            
    def onOK(self):
        self.main_wnd.votingMasternodes = self.getSelection()
        self.main_wnd.updateSelectedMNlabel()
        # save voting masternodes to cache
        self.main_wnd.caller.parent.cache['votingMasternodes'] = self.main_wnd.votingMasternodes
        writeToFile(self.main_wnd.caller.parent.cache, cache_File)
        self.accept()
        
        
    def selectAll(self):
        self.ui.mnList.selectAll()
        self.ui.mnList.setFocus()
    
        
class Ui_SelectMNsDlg(object):
    def setupUi(self, SelectMNsDlg):
        SelectMNsDlg.setModal(True)
        layout = QVBoxLayout(SelectMNsDlg)
        layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel("<b><i>Select Masternodes for voting:</i></b>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.mnList = QTableWidget()
        self.mnList.setSelectionMode(QAbstractItemView.MultiSelection)
        self.mnList.setColumnCount(1)
        self.mnList.setRowCount(len(SelectMNsDlg.main_wnd.caller.masternode_list))
        self.mnList.setShowGrid(True)
        self.mnList.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.mnList.verticalHeader().hide
        item = QTableWidgetItem("Name")
        item.setTextAlignment(Qt.AlignCenter)
        self.mnList.setHorizontalHeaderItem(0, item)
        layout.addWidget(self.mnList)
        ## buttons
        hBox = QHBoxLayout()
        self.selectAll_btn = QPushButton("Select All")
        self.selectAll_btn.setToolTip("Select all masternodes")
        self.deselectAll_btn = QPushButton("Deselect All")
        self.deselectAll_btn.setToolTip("Deselect current selection")
        self.ok_btn = QPushButton("OK")
        hBox.addWidget(self.selectAll_btn)
        hBox.addWidget(self.deselectAll_btn)
        hBox.addStretch(1)
        hBox.addWidget(self.ok_btn)
        layout.addLayout(hBox)
        self.layout = layout