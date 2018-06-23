#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
from PyQt5.Qt import QFont, QDesktopServices, QUrl
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QTableWidgetItem, QPushButton, QWidget, QHBoxLayout

from qt.gui_tabGovernance import TabGovernance_gui
from qt.dlg_proposalDetails import ProposalDetails_dlg
from qt.dlg_selectMNs import SelectMNs_dlg
from misc import printException, getCallerName, getFunctionName
from threads import ThreadFuns


class Proposal():
    def __init__(self, name, URL, Hash, FeeHash, BlockStart, BlockEnd, TotalPayCount, RemainingPayCount, 
                 PayMentAddress, Yeas, Nays, Abstains, TotalPayment, MonthlyPayment):
        self.name = name
        self.URL = URL if URL.startswith('http') or URL.startswith('https') else 'http://'+URL
        self.Hash = Hash
        self.FeeHash = FeeHash
        self.BlockStart = int(BlockStart)
        self.BlockEnd = int(BlockEnd)
        self.TotalPayCount = int(TotalPayCount)
        self.RemainingPayCount = int(RemainingPayCount)
        self.PaymentAddress = PayMentAddress        
        self.Yeas = int(Yeas)
        self.Nays = int(Nays)
        self.Abstains = int(Abstains)
        self.ToalPayment = TotalPayment
        self.MonthlyPayment = MonthlyPayment
        ## list of personal masternodes voting
        self.MyYeas = []
        self.MyAbstains = []
        self.MyNays = []
        

class TabGovernance():
    def __init__(self, caller):
        self.caller = caller
        self.proposals = []  # list of Proposal Objects
        self.selectedProposals = []
        self.votingMasternodes = []
        ##--- Initialize GUI
        self.ui = TabGovernance_gui(caller)
        self.caller.tabGovernance = self.ui
        # Connect GUI buttons
        self.ui.refreshProposals_btn.clicked.connect(lambda: self.onRefreshProposals())
        self.ui.selectMN_btn.clicked.connect(lambda:  SelectMNs_dlg(self).exec_())
        self.ui.proposalBox.itemClicked.connect(lambda: self.updateSelection())
        
            
    def countMyVotes(self):
        for prop in self.proposals:
            budgetVotes = self.caller.rpcClient.getBudgetVotes(prop.name)
            budgetYeas = [x['mnId'] for x in budgetVotes if x['Vote'] == "YES"]
            budgetAbstains = [x['mnId'] for x in budgetVotes if x['Vote'] == "ABSTAIN"]
            budgetNays = [x['mnId'] for x in budgetVotes if x['Vote'] == "NO"]
            prop.myYeas = [x[1] for x in self.votingMasternodes if x[0] in budgetYeas]
            prop.myAbstains = [x[1] for x in self.votingMasternodes if x[0] in budgetAbstains]
            prop.myNays = [x[1] for x in self.votingMasternodes if x[0] in budgetNays]
    
        
    def displayProposals(self):
        if len(self.proposals) == 0:
            return
        
        def item(value):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            return item
        
        def itemButton(value, icon_num):
            pwidget = QWidget()
            btn = QPushButton()
            if icon_num == 0:
                btn.setIcon(self.ui.link_icon)
                btn.setToolTip("Open WebPage: %s" % str(value))
                btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(str(value))))
            else:
                btn.setIcon(self.ui.search_icon)
                btn.setToolTip("Check proposal details...")
                btn.clicked.connect(lambda: ProposalDetails_dlg(self.ui, value).exec_())
            
            pLayout = QHBoxLayout()
            pLayout.addWidget(btn)
            pLayout.setContentsMargins(0, 0, 0, 0)
            pwidget.setLayout(pLayout)
            return pwidget
        
        self.ui.mnCountLabel.setText("Total MN Count: <em>%d</em>" % self.mnCount)
        self.ui.proposalBox.setRowCount(len(self.proposals))
        
        for row, prop in enumerate(self.proposals):
            self.ui.proposalBox.setItem(row, 0, item(prop.name))
            self.ui.proposalBox.item(row, 0).setFont(QFont("Arial", 9, QFont.Bold))
            
            self.ui.proposalBox.setCellWidget(row, 1, itemButton(prop.URL, 0))
            
            monthlyPay = item(prop.MonthlyPayment)
            monthlyPay.setData(Qt.EditRole, float(prop.MonthlyPayment))
            self.ui.proposalBox.setItem(row, 2, monthlyPay)
            
            payments = "%d / %d" % (prop.RemainingPayCount, prop.TotalPayCount)
            self.ui.proposalBox.setItem(row, 3, item(payments))
            
            net_votes = "%d / %d / %d" % (prop.Yeas, prop.Abstains, prop.Nays)
            votes = item(net_votes)
            if (prop.Yeas - prop.Nays) > 0.1 * self.mnCount:
                votes.setBackground(Qt.green)
            if (prop.Yeas - prop.Nays) < 0:
                votes.setBackground(Qt.red)
            self.ui.proposalBox.setItem(row, 4, votes)
            
            my_votes = "%d / %d / %d" % (len(prop.MyYeas), len(prop.MyAbstains), len(prop.MyNays))
            self.ui.proposalBox.setItem(row, 5, item(my_votes))
            self.ui.proposalBox.setCellWidget(row, 6, itemButton(prop, 1))
            
        # Sort by Monthly Price descending
        self.ui.proposalBox.sortByColumn(2, Qt.DescendingOrder)
            
    
    
    def getSelection(self):
        items = self.ui.proposalBox.selectedItems()
        # Save row indexes to a set to avoid repetition
        rows = set()
        for i in range(0, len(items)):
            row = items[i].row()
            rows.add(row)
        rowList = list(rows)  
        return [self.proposals[row] for row in rowList]
            
     
            
    @pyqtSlot()
    def onRefreshProposals(self):
        ThreadFuns.runInThread(self.loadProposals_thread, (), self.displayProposals)
    
    
    
    def loadProposals_thread(self, ctrl):
        if not self.caller.rpcConnected:
            printException(getCallerName(), getFunctionName(), "RPC server not connected", "")
            return
        
        self.proposals = self.caller.rpcClient.getProposals()
        num_of_masternodes = self.caller.rpcClient.getMasternodeCount()

        if num_of_masternodes is None:
            printDbg("Total number of masternodes not available. Background coloring not accurate")
            self.mnCount = 1
        else:
            self.mnCount = num_of_masternodes.get("total")  
                
        self.countMyVotes()
        
        
    def updateSelection(self):
        self.selectedProposals = self.getSelection()
        self.ui.selectedPropLabel.setText("<em><b>%d</b> proposals selected</em>" % len(self.selectedProposals))
            
        