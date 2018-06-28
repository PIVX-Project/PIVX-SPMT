#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget,\
    QAbstractItemView, QHeaderView, QTableWidgetItem, QPushButton, QLabel,\
    QGroupBox, QHBoxLayout, QFormLayout

from misc import printException
    
from misc import sec_to_time
from threads import ThreadFuns

class BudgetProjection_dlg(QDialog):
    def __init__(self, main_wnd):
        QDialog.__init__(self, parent=main_wnd.ui)
        self.main_wnd = main_wnd
        self.setWindowTitle('Budget Projection')
        self.initUI()
        self.ui.ok_btn.clicked.connect(lambda: self.accept())
        self.next_superBlock = 0
        ThreadFuns.runInThread(self.loadBudgetProjection_thread, (), self.displayBudgetProjection)
        
        
    def initUI(self):
        self.ui = Ui_BudgetProjectionDlg()
        self.ui.setupUi(self)
        
        
        
    def displayBudgetProjection(self):
        total_num_of_proposals = len(self.projection)
        if total_num_of_proposals == 0 or self.next_superBlock == 0:
            return
        
        # header
        ## blocks to next superBlock (== minutes)
        blocks_to_SB = self.next_superBlock - self.main_wnd.caller.rpcLastBlock
        
        self.ui.nextSuperBlock_label.setText("<b>%s</b>" % str(self.next_superBlock))
        timeToNextSB = "<em style='color: blue'>%s</em>" % sec_to_time(60*blocks_to_SB)
        self.ui.timeToNextSB_label.setText(timeToNextSB)
        total = self.projection[-1].get('Total_Allotted')
        total_label = "<em style='color: purple'>%s PIV</em>" % str(total)
        self.ui.allottedBudget_label.setText(total_label)
        self.ui.remainingBudget_label.setText("%s PIV" % str(round(43200.0-total,8)))
        self.ui.passingProposals_label.setText("<b style='color: purple'>%s</b>" % str(len(self.projection)))
        
        def item(value):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            return item
        
        self.ui.proposals_lst.setRowCount(total_num_of_proposals)
        for row, prop in enumerate(self.projection):
            self.ui.proposals_lst.setItem(row, 0, item(self.projection[row].get('Name')))
            self.ui.proposals_lst.setItem(row, 1, item(self.projection[row].get('Allotted')))
            self.ui.proposals_lst.setItem(row, 2, item(self.projection[row].get('Votes')))
            self.ui.proposals_lst.setItem(row, 3, item(self.projection[row].get('Total_Allotted')))
            
        
        
    def loadBudgetProjection_thread(self, ctrl):
        self.projection = []
        if not self.main_wnd.caller.rpcConnected:
            printException(getCallerName(), getFunctionName(), "RPC server not connected", "")
            return
        ## get next superBlock
        self.next_superBlock = self.main_wnd.caller.rpcClient.getNextSuperBlock()
        ## get budget projection
        self.projection = self.main_wnd.caller.rpcClient.getProposalsProjection()
        



class Ui_BudgetProjectionDlg(object):
    def setupUi(self, BudgetProjectionDlg):
        BudgetProjectionDlg.setModal(True)
        layout = QVBoxLayout(BudgetProjectionDlg)
        layout.setContentsMargins(8, 8, 8, 8)
        ## tile
        title = QLabel("<b>Budget Projection Overview</b>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        ## header
        header = QGroupBox("Budget Projection Details")
        header_layout = QFormLayout()
        header_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        ## row 1
        row = QHBoxLayout()
        self.availableBudget_label = QLabel("43200.0 PIV")
        row.addWidget(self.availableBudget_label)
        row.addStretch(1)
        row.addWidget(QLabel("Next SuperBlock: "))
        self.nextSuperBlock_label = QLabel("--")
        row.addWidget(self.nextSuperBlock_label)
        header_layout.addRow(QLabel("Available Budget: "), row)
        ## row 2
        row = QHBoxLayout()
        self.allottedBudget_label = QLabel("--")
        row.addWidget(self.allottedBudget_label)
        row.addStretch(1)
        row.addWidget(QLabel("Time to next SuperBlock (approx): "))
        header_layout.addRow(QLabel("Total Allotted Budget: "), row)
        ## row 3       
        row = QHBoxLayout()
        self.remainingBudget_label = QLabel("--")
        row.addWidget(self.remainingBudget_label)
        row.addStretch(1)
        self.timeToNextSB_label = QLabel("--")
        row.addWidget(self.timeToNextSB_label)
        header_layout.addRow(QLabel("Remaining Budget: "), row)
        ## row 4
        self.passingProposals_label = QLabel("--")
        header_layout.addRow(QLabel("Passing Proposals: "), self.passingProposals_label)
        ##
        header.setLayout(header_layout)
        layout.addWidget(header)
        ## LIST
        self.proposals_lst = QTableWidget()
        self.proposals_lst.setSelectionMode(QAbstractItemView.NoSelection)
        self.proposals_lst.setColumnCount(4)
        self.proposals_lst.setRowCount(0)
        self.proposals_lst.setShowGrid(True)
        self.proposals_lst.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        item = QTableWidgetItem("Name")
        item.setTextAlignment(Qt.AlignCenter)
        self.proposals_lst.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem("Allotted Budget")
        item.setTextAlignment(Qt.AlignCenter)
        self.proposals_lst.setHorizontalHeaderItem(1, item)
        item = QTableWidgetItem("Net Votes")
        item.setTextAlignment(Qt.AlignCenter)
        self.proposals_lst.setHorizontalHeaderItem(2, item)
        item = QTableWidgetItem("Total Allotted Budget")
        item.setTextAlignment(Qt.AlignCenter)
        self.proposals_lst.setHorizontalHeaderItem(3, item)
        self.proposals_lst.setColumnWidth(1, 130)
        self.proposals_lst.setColumnWidth(2, 130)
        self.proposals_lst.setColumnWidth(3, 160)
        layout.addWidget(self.proposals_lst)
        ## button ok
        self.ok_btn = QPushButton("Ok")
        layout.addWidget(self.ok_btn)
        BudgetProjectionDlg.resize(650, 500)