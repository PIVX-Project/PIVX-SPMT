#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAbstractItemView, QHeaderView,\
    QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QCheckBox, QLabel, QProgressBar,\
    QFormLayout, QSpinBox
from PyQt5.Qt import QPixmap, QIcon


class TabGovernance_gui(QWidget):
    def __init__(self, caller, *args, **kwargs):
        QWidget.__init__(self)
        self.caller = caller
        self.initLayout()
        self.loadIcons()
        
        
    def initLayout(self):
        layout = QFormLayout()
        #layout.setContentsMargins(10, 10, 10, 10)
        #layout.setSpacing(13)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        ## -- ROW 1
        row = QHBoxLayout()
        self.refreshProposals_btn = QPushButton("Refresh List")
        row.addWidget(self.refreshProposals_btn)
        self.selectMN_btn = QPushButton("Select Masternodes...")
        row.addWidget(self.selectMN_btn)
        self.selectedMNlabel = QLabel("<em>0 masternodes selected for voting</em")
        row.addWidget(self.selectedMNlabel)
        row.addStretch(1)
        self.mnCountLabel = QLabel()
        row.addWidget(self.mnCountLabel) 
        layout.addRow(row)
        
        ## -- ROW 2
        self.proposalBox = QTableWidget()
        self.proposalBox.setMinimumHeight(280)
        self.proposalBox.setSelectionMode(QAbstractItemView.MultiSelection)
        self.proposalBox.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.proposalBox.setShowGrid(True)
        self.proposalBox.setColumnCount(7)
        self.proposalBox.setRowCount(0)
        self.proposalBox.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.proposalBox.setSortingEnabled(True)
        #self.proposalBox.verticalHeader().hide
        self.setProposalBoxHeader()
        self.proposalBox.setColumnWidth(1, 50)
        self.proposalBox.setColumnWidth(2, 110)
        self.proposalBox.setColumnWidth(3, 110)
        self.proposalBox.setColumnWidth(4, 150)
        self.proposalBox.setColumnWidth(5, 150)
        self.proposalBox.setColumnWidth(6, 50)
        layout.addRow(self.proposalBox)
        
        ## -- ROW 3
        row = QHBoxLayout()
        timeIcon = QPixmap(os.path.join(self.caller.imgDir, 'icon_clock.png'))
        timeIconLabel = QLabel()
        timeIconLabel.setPixmap(timeIcon.scaledToHeight(20, Qt.SmoothTransformation))
        timeIconLabel.setToolTip("Check to add a randomized time-delay offset when voting on multiple proposals")
        row.addWidget(timeIconLabel)
        self.randomDelayCheck = QCheckBox()
        self.randomDelayCheck.setToolTip("Check to add a randomized time-delay offset when voting on multiple proposals")
        row.addWidget(self.randomDelayCheck)
        self.randomDelaySecs_edt = QSpinBox()
        self.randomDelaySecs_edt.setSuffix(" secs")
        self.randomDelaySecs_edt.setToolTip("Maximum delay (in seconds) added to each vote")
        self.randomDelaySecs_edt.setFixedWidth(80)
        self.randomDelaySecs_edt.setMaximum(18000)
        self.randomDelaySecs_edt.setValue(300)
        row.addWidget(self.randomDelaySecs_edt)
        row.addStretch(1)
        self.loadingLine = QLabel("<b style='color:red'>Vote Signatures.</b> Completed: ")
        self.loadingLinePercent = QProgressBar()
        self.loadingLinePercent.setMaximumWidth(200)
        self.loadingLinePercent.setMaximumHeight(10)
        self.loadingLinePercent.setRange(0, 100)
        row.addWidget(self.loadingLine)
        row.addWidget(self.loadingLinePercent)
        self.loadingLine.hide()
        self.loadingLinePercent.hide()
        row.addStretch(1)
        self.selectedPropLabel = QLabel("<em>0 proposals selected</em>")
        row.addWidget(self.selectedPropLabel)
        layout.addRow(row)
        
        ## -- ROW 4
        row = QHBoxLayout()
        self.voteYes_btn = QPushButton("Vote YES")
        row.addWidget(self.voteYes_btn)
        self.voteAbstain_btn = QPushButton("Vote ABSTAIN")
        row.addWidget(self.voteAbstain_btn)
        self.voteNo_btn = QPushButton("Vote NO")
        row.addWidget(self.voteNo_btn)
        layout.addRow(row)

        self.setLayout(layout)
    
    
    def setProposalBoxHeader(self):
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Name")
        item.setToolTip("Proposal Name")
        self.proposalBox.setHorizontalHeaderItem(0, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Link")
        item.setToolTip("Link to Proposal Thread")
        self.proposalBox.setHorizontalHeaderItem(1, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("PIV/month")
        item.setToolTip("Monthly PIV Payment requested")
        self.proposalBox.setHorizontalHeaderItem(2, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Payments")
        item.setToolTip("Remaining Payment Count / Total Payment Count")
        self.proposalBox.setHorizontalHeaderItem(3, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Network Votes")
        item.setToolTip("Network Votes: YEAS/ABSTAINS/NAYS")
        self.proposalBox.setHorizontalHeaderItem(4, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("My Votes")
        item.setToolTip("My Votes: YEAS/ABSTAINS/NAYS")
        self.proposalBox.setHorizontalHeaderItem(5, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Details")
        item.setToolTip("Check Proposal Details")
        self.proposalBox.setHorizontalHeaderItem(6, item)
        
        
    def loadIcons(self):
        self.link_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_link.png'))
        self.search_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_search.png'))