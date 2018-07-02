#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAbstractItemView, QHeaderView,\
    QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QCheckBox, QLabel, QProgressBar,\
    QFormLayout, QSpinBox, QMessageBox, QScrollArea, QDialog
from PyQt5.Qt import QPixmap, QIcon


class TabGovernance_gui(QWidget):
    def __init__(self, caller, *args, **kwargs):
        QWidget.__init__(self)
        self.caller = caller
        self.initLayout()
        self.loadIcons()
        self.refreshProposals_btn.setIcon(self.refresh_icon)
        self.budgetProjection_btn.setIcon(self.list_icon)
        self.timeIconLabel.setPixmap(self.time_icon.scaledToHeight(20, Qt.SmoothTransformation))
        self.questionLabel.setPixmap(self.question_icon.scaledToHeight(15, Qt.SmoothTransformation))
        self.loadCacheData()
        
        
    def initLayout(self):
        layout = QVBoxLayout()
        #layout.setContentsMargins(10, 10, 10, 10)
        #layout.setSpacing(13)
        #layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        ## -- ROW 1
        row = QHBoxLayout()
        self.budgetProjection_btn = QPushButton()
        self.budgetProjection_btn.setToolTip("Check Budget Projection...")
        row.addWidget(self.budgetProjection_btn)
        self.selectMN_btn = QPushButton("Select Masternodes...")
        row.addWidget(self.selectMN_btn)
        self.selectedMNlabel = QLabel("<em>0 masternodes selected for voting</em")
        row.addWidget(self.selectedMNlabel)
        self.refreshingLabel = QLabel("<em><b style='color:red'>Refreshing proposals...</b></em>")
        self.refreshingLabel.hide()
        row.addWidget(self.refreshingLabel)
        row.addStretch(1)
        self.mnCountLabel = QLabel()
        row.addWidget(self.mnCountLabel)
        self.refreshProposals_btn = QPushButton()
        self.refreshProposals_btn.setToolTip("Refresh Proposal List")
        row.addWidget(self.refreshProposals_btn)
        layout.addLayout(row)
        
        ## -- ROW 2
        self.proposalBox = QTableWidget()
        self.proposalBox.setMinimumHeight(280)
        self.proposalBox.setSelectionMode(QAbstractItemView.MultiSelection)
        self.proposalBox.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.proposalBox.setShowGrid(True)
        self.proposalBox.setColumnCount(8)
        self.proposalBox.setRowCount(0)
        self.proposalBox.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.proposalBox.setSortingEnabled(True)
        #self.proposalBox.verticalHeader().hide
        self.setProposalBoxHeader()
        self.proposalBox.setColumnWidth(1, 50)
        self.proposalBox.setColumnWidth(2, 50)
        self.proposalBox.setColumnWidth(3, 100)
        self.proposalBox.setColumnWidth(4, 100)
        self.proposalBox.setColumnWidth(5, 150)
        self.proposalBox.setColumnWidth(6, 120)
        self.proposalBox.setColumnWidth(7, 50)
        layout.addWidget(self.proposalBox)
        
        ## -- ROW 3
        row = QHBoxLayout()      
        self.timeIconLabel = QLabel()
        self.timeIconLabel.setToolTip("Check to add a randomized time offset (positive or negative) to enhance privacy")
        row.addWidget(self.timeIconLabel)
        self.randomDelayCheck = QCheckBox()
        self.randomDelayCheck.setToolTip("Check to add a randomized time offset when voting (max +5/-5 hrs)")
        row.addWidget(self.randomDelayCheck)
        self.randomDelayNeg_edt = QSpinBox()
        self.randomDelayNeg_edt.setPrefix('- ')
        self.randomDelayNeg_edt.setSuffix(" secs")
        self.randomDelayNeg_edt.setToolTip("Maximum random time (in seconds) subtracted from each vote timestamp")
        self.randomDelayNeg_edt.setFixedWidth(100)
        self.randomDelayNeg_edt.setMaximum(18000)
        self.randomDelayNeg_edt.setValue(0)
        row.addWidget(self.randomDelayNeg_edt)
        self.randomDelayPos_edt = QSpinBox()
        self.randomDelayPos_edt.setPrefix("+ ")
        self.randomDelayPos_edt.setSuffix(" secs")
        self.randomDelayPos_edt.setToolTip("Maximum random time (in seconds) added to each vote timestamp")
        self.randomDelayPos_edt.setFixedWidth(100)
        self.randomDelayPos_edt.setMaximum(18000)
        self.randomDelayPos_edt.setValue(300)
        row.addWidget(self.randomDelayPos_edt)
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
        self.questionLabel = QLabel()
        message = "Refresh proposals.\n"
        message += "GREEN: proposal passing\n"
        message += "WHITE: missing votes in order to pass\n"
        message += "RED: proposal not passing\n"
        message += "YELLOW: proposal expiring (last payment block)\n"
        self.questionLabel.setToolTip(message)
        row.addWidget(self.questionLabel)
        layout.addLayout(row)
        
        ## -- ROW 4
        row = QHBoxLayout()
        self.voteYes_btn = QPushButton("Vote YES")
        self.voteYes_btn.setToolTip("Vote YES on selected proposals")
        row.addWidget(self.voteYes_btn)
        self.voteAbstain_btn = QPushButton("Vote ABSTAIN")
        self.voteAbstain_btn.setToolTip("Vote ABSTAIN on selected proposals [currently disabled]")
        row.addWidget(self.voteAbstain_btn)
        self.voteNo_btn = QPushButton("Vote NO")
        self.voteNo_btn.setToolTip("Vote NO on selected proposals")
        row.addWidget(self.voteNo_btn)
        layout.addLayout(row)

        self.setLayout(layout)
    
    
    
    def loadCacheData(self):
        if self.caller.parent.cache.get("votingDelayCheck"):
            negative_delay = self.caller.parent.cache.get("votingDelayNeg")
            positive_delay = self.caller.parent.cache.get("votingDelayPos")
            self.randomDelayCheck.setChecked(True)
            self.randomDelayNeg_edt.setValue(negative_delay)
            self.randomDelayPos_edt.setValue(positive_delay)
    
    
    def setProposalBoxHeader(self):
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Name")
        item.setToolTip("Proposal Name")
        self.proposalBox.setHorizontalHeaderItem(0, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Hash")
        item.setToolTip("Proposal Hash")
        self.proposalBox.setHorizontalHeaderItem(1, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Link")
        item.setToolTip("Link to Proposal Thread")
        self.proposalBox.setHorizontalHeaderItem(2, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("PIV/month")
        item.setToolTip("Monthly PIV Payment requested")
        self.proposalBox.setHorizontalHeaderItem(3, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Payments")
        item.setToolTip("Remaining Payment Count / Total Payment Count")
        self.proposalBox.setHorizontalHeaderItem(4, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Network Votes")
        item.setToolTip("Network Votes: YEAS/ABSTAINS/NAYS")
        self.proposalBox.setHorizontalHeaderItem(5, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("My Votes")
        item.setToolTip("My Votes: YEAS/ABSTAINS/NAYS")
        self.proposalBox.setHorizontalHeaderItem(6, item)
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setText("Details")
        item.setToolTip("Check Proposal Details")
        self.proposalBox.setHorizontalHeaderItem(7, item)
        
        
    def loadIcons(self):
        self.refresh_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_refresh.png'))
        self.time_icon = QPixmap(os.path.join(self.caller.imgDir, 'icon_clock.png'))
        self.link_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_link.png'))
        self.search_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_search.png'))
        self.list_icon = QIcon(os.path.join(self.caller.imgDir, 'icon_list.png'))
        self.question_icon = QPixmap(os.path.join(self.caller.imgDir, 'icon_question.png'))
        
        
        
        
class ScrollMessageBox(QDialog):
    def __init__(self, main_wnd, message):
        QDialog.__init__(self, parent=main_wnd)
        self.setWindowTitle("Confirm Votes")
        scroll = QScrollArea()
        scroll.setMinimumHeight(280)
        scroll.setMaximumHeight(280)
        scroll.setMinimumWidth(500)
        scroll.setWidget(QLabel(message))
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        lay = QVBoxLayout()
        lay.addWidget(scroll)
        row = QHBoxLayout()
        self.yes_btn = QPushButton("Yes")
        self.no_btn = QPushButton("No")
        self.yes_btn.clicked.connect(lambda: self.accept())
        self.no_btn.clicked.connect(lambda: self.reject())
        row.addWidget(self.yes_btn)
        row.addWidget(self.no_btn)
        lay.addLayout(row)
        self.setLayout(lay)
        
        