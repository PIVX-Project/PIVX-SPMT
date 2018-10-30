#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import time

from PyQt5.Qt import QFont, QDesktopServices, QUrl
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QTableWidgetItem, QPushButton, QWidget, QHBoxLayout,\
    QMessageBox, QScrollArea, QLabel

from misc import printException, getCallerName, getFunctionName, \
    printDbg, printOK, persistCacheSetting, myPopUp_sb
from qt.gui_tabGovernance import TabGovernance_gui, ScrollMessageBox
from qt.dlg_proposalDetails import ProposalDetails_dlg
from qt.dlg_selectMNs import SelectMNs_dlg
from qt.dlg_budgetProjection import BudgetProjection_dlg
from threads import ThreadFuns
from utils import ecdsa_sign



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
        self.votingMasternodes = self.caller.parent.cache.get("votingMasternodes")
        self.successVotes = 0
        self.failedVotes = 0
        ##--- Initialize GUI
        self.ui = TabGovernance_gui(caller)
        self.updateSelectedMNlabel()
        self.caller.tabGovernance = self.ui
        # Connect GUI buttons
        self.vote_codes = ["abstains", "yes", "no"]
        self.ui.refreshProposals_btn.clicked.connect(lambda: self.onRefreshProposals())
        self.ui.toggleExpiring_btn.clicked.connect(lambda: self.onToggleExpiring())
        self.ui.selectMN_btn.clicked.connect(lambda:  SelectMNs_dlg(self).exec_())
        self.ui.budgetProjection_btn.clicked.connect(lambda:  BudgetProjection_dlg(self).exec_())
        self.ui.proposalBox.itemClicked.connect(lambda: self.updateSelection())
        self.ui.voteYes_btn.clicked.connect(lambda: self.onVote(1))
        self.ui.voteAbstain_btn.clicked.connect(lambda: self.onVote(0))
        self.ui.voteNo_btn.clicked.connect(lambda: self.onVote(2))
        
    
    def clear(self):
        # Clear voting masternodes and update cache
        self.votingMasternodes = []
        self.caller.parent.cache['votingMasternodes'] = persistCacheSetting('cache_votingMNs', self.votingMasternodes)
        
                
    def countMyVotes(self):
        for prop in self.proposals:
            mnList = self.caller.masternode_list
            budgetVotes = self.caller.rpcClient.getBudgetVotes(prop.name)
            budgetYeas = [[x['mnId'], x['nTime']] for x in budgetVotes if x['Vote'] == "YES"]
            budgetAbstains = [[x['mnId'], x['nTime']] for x in budgetVotes if x['Vote'] == "ABSTAIN"]
            budgetNays = [[x['mnId'], x['nTime']] for x in budgetVotes if x['Vote'] == "NO"]
            prop.MyYeas = [[mn['name'], vote] for mn in mnList for vote in budgetYeas if mn['collateral'].get('txid') == vote[0]]
            prop.MyAbstains = [[mn['name'], vote] for mn in mnList for vote in budgetAbstains if mn['collateral'].get('txid') == vote[0]]
            prop.MyNays = [[mn['name'], vote] for mn in mnList for vote in budgetNays if mn['collateral'].get('txid') == vote[0]]
    
    
    def countMyVotes_thread(self, ctrl):
        self.countMyVotes()
    
    
        
    def displayProposals(self):
        if len(self.proposals) == 0:
            if not self.caller.rpcConnected:
                self.ui.resetStatusLabel('<b style="color:red">PIVX wallet not connected</b>')
            else:
                self.ui.resetStatusLabel('<b style="color:red">No proposal found</b>')
            return
        
        self.ui.statusLabel.setVisible(False)
        
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
            # Make proposal name Bold
            self.ui.proposalBox.setItem(row, 0, item(prop.name))
            font = self.ui.proposalBox.item(row, 0).font()
            font.setBold(True)
            self.ui.proposalBox.item(row, 0).setFont(font)
            
            hash = item(prop.Hash)
            hash.setToolTip(prop.Hash)
            self.ui.proposalBox.setItem(row, 1, hash)
            
            self.ui.proposalBox.setCellWidget(row, 2, itemButton(prop.URL, 0))
            
            monthlyPay = item(prop.MonthlyPayment)
            monthlyPay.setData(Qt.EditRole, int(round(prop.MonthlyPayment)))
            self.ui.proposalBox.setItem(row, 3, monthlyPay)
            
            payments = "%d / %d" % (prop.RemainingPayCount, prop.TotalPayCount)
            self.ui.proposalBox.setItem(row, 4, item(payments))
            
            net_votes = "%d / %d / %d" % (prop.Yeas, prop.Abstains, prop.Nays)
            votes = item(net_votes)
            if (prop.Yeas - prop.Nays) > 0.1 * self.mnCount:
                votes.setBackground(Qt.green)
            if (prop.Yeas - prop.Nays) < 0:
                votes.setBackground(Qt.red)
            if prop.RemainingPayCount == 0:
                votes.setBackground(Qt.yellow)
            self.ui.proposalBox.setItem(row, 5, votes)
            
            my_votes = "%d / %d / %d" % (len(prop.MyYeas), len(prop.MyAbstains), len(prop.MyNays))
            self.ui.proposalBox.setItem(row, 6, item(my_votes))
            self.ui.proposalBox.setCellWidget(row, 7, itemButton(prop, 1))
            
            # hide row if toggleExpiring_btn set
            if prop.RemainingPayCount == 0 and self.ui.toggleExpiring_btn.text() == "Show Expiring":
                self.ui.proposalBox.hideRow(row)
            
        # Sort by Monthly Price descending
        self.ui.proposalBox.setSortingEnabled(True)
        self.ui.proposalBox.sortByColumn(3, Qt.DescendingOrder)
        
            
    
    
    def getSelection(self):
        items = self.ui.proposalBox.selectedItems()
        # Save row indexes to a set to avoid repetition
        rows = set()
        for i in range(0, len(items)):
            row = items[i].row()
            rows.add(row)
        rowsList = list(rows)
        hashesList = [self.ui.proposalBox.item(row,1).text() for row in rowsList]
        #print("Selected: " + str([p.name for p in self.proposals if p.name in namesList]))
        return [p for p in self.proposals if p.Hash in hashesList]
            
     
            
    @pyqtSlot()
    def onRefreshProposals(self):
        self.ui.resetStatusLabel()
        self.ui.proposalBox.setRowCount(0)
        self.proposals = []
        self.selectedProposals = []
        self.ui.proposalBox.setSortingEnabled(False)
        ThreadFuns.runInThread(self.loadProposals_thread, (), self.displayProposals)
        
    
    
    @pyqtSlot()
    def onToggleExpiring(self):
        if self.ui.toggleExpiring_btn.text() == "Hide Expiring":
            # Hide expiring proposals
            for row in range(0, self.ui.proposalBox.rowCount()):
                if self.ui.proposalBox.item(row,5).background() == Qt.yellow:
                    self.ui.proposalBox.hideRow(row)
            # Update button
            self.ui.toggleExpiring_btn.setToolTip("Show expiring proposals (yellow background) in list")
            self.ui.toggleExpiring_btn.setText("Show Expiring")

        else:
            # Show expiring proposals
            for row in range(0, self.ui.proposalBox.rowCount()):
                if self.ui.proposalBox.item(row,5).background() == Qt.yellow:
                    self.ui.proposalBox.showRow(row)       
            # Update button
            self.ui.toggleExpiring_btn.setToolTip("Hide expiring proposals (yellow background) from list")
            self.ui.toggleExpiring_btn.setText("Hide Expiring")
        
        
    @pyqtSlot(str)
    def onVote(self, vote_code):
        if len(self.selectedProposals) == 0:
            message = "NO PROPOSAL SELECTED. Select proposals from the list."
            myPopUp_sb(self.caller, "crit", 'Vote on proposals', message)
            return
        if len(self.votingMasternodes) == 0:
            message = "NO MASTERNODE SELECTED FOR VOTING. Click on 'Select Masternodes...'"
            myPopUp_sb(self.caller, "crit", 'Vote on proposals', message)
            return
        
        reply = self.summaryDlg(vote_code)
        
        if reply == 1:
            ThreadFuns.runInThread(self.vote_thread, ([vote_code]), self.vote_thread_end)
    
    
    def summaryDlg(self, vote_code):
        message = "Voting <b>%s</b> on the following proposal(s):<br><br>" % str(self.vote_codes[vote_code]).upper()
        for prop in self.selectedProposals:
            message += "&nbsp; - <b>%s</b><br>&nbsp; &nbsp; (<em>%s</em>)<br><br>" % (prop.name, prop.Hash)
        message += "<br>with following masternode(s):<br><br>"
        
        for mn in self.votingMasternodes:
            message += "&nbsp; - <b>%s</b><br>" % mn[1]
            
        dlg = ScrollMessageBox(self.caller, message)
        
        return dlg.exec_() 

    
    
    @pyqtSlot(object) 
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
        
        
    
    
    def updateSelectedMNlabel(self):
        selected_MN = len(self.votingMasternodes)
        if selected_MN == 1:
            label = "<em><b>1</b> masternode selected for voting</em>"
        else:
            label = "<em><b>%d</b> masternodes selected for voting</em>" % selected_MN
        self.ui.selectedMNlabel.setText(label)
        
        
    
    
    def updateSelection(self):
        self.selectedProposals = self.getSelection()
        if len(self.selectedProposals) == 1:
            self.ui.selectedPropLabel.setText("<em><b>1</b> proposal selected")
        else:
            self.ui.selectedPropLabel.setText("<em><b>%d</b> proposals selected" % len(self.selectedProposals))
            
            
    
    
    
    @pyqtSlot(object, str)
    def vote_thread(self, ctrl, vote_code):
        # vote_code index for ["yes", "abstain", "no"]
        if not isinstance(vote_code, int) or vote_code not in range(3):
            raise Exception("Wrong vote_code %s" % str(vote_code))
        self.successVotes = 0
        self.failedVotes = 0
        
        # save delay check data to cache and persist settings
        self.caller.parent.cache["votingDelayCheck"] = persistCacheSetting('cache_vdCheck', self.ui.randomDelayCheck.isChecked())
        self.caller.parent.cache["votingDelayNeg"] = persistCacheSetting('cache_vdNeg', self.ui.randomDelayNeg_edt.value())
        self.caller.parent.cache["votingDelayPos"] = persistCacheSetting('cache_vdPos', self.ui.randomDelayPos_edt.value())
        
        for prop in self.selectedProposals:
            for mn in self.votingMasternodes:               
                vote_sig = ''
                serialize_for_sig = ''
                sig_time = int(time.time())

                try:
                    # Get mnPrivKey
                    currNode = next(x for x in self.caller.masternode_list if x['name']==mn[1])
                    if currNode is None:
                        raise Exception("currNode not found for current voting masternode %s" % mn[1])
                    mnPrivKey = currNode['mnPrivKey']
                    
                    # Add random delay offset
                    if self.ui.randomDelayCheck.isChecked():
                        minuns_max = int(self.ui.randomDelayNeg_edt.value())
                        plus_max = int(self.ui.randomDelayPos_edt.value())
                        delay_secs = random.randint(-minuns_max, plus_max)
                        sig_time +=  delay_secs
                        
                    # Print Debug line to console
                    mess = "Processing '%s' vote on behalf of masternode [%s]" % (self.vote_codes[vote_code], mn[1])
                    mess += " for the proposal {%s}" % prop.name
                    if self.ui.randomDelayCheck.isChecked():
                        mess += " with offset of %d seconds" % delay_secs
                    printDbg(mess)
                    
                    # Serialize vote
                    serialize_for_sig = mn[0][:64] + '-' + str(currNode['collateral'].get('txidn'))
                    serialize_for_sig += prop.Hash + str(vote_code) + str(sig_time)                  
                    
                    # Sign vote
                    vote_sig = ecdsa_sign(serialize_for_sig, mnPrivKey)
                    
                    # Broadcast the vote
                    v_res = self.caller.rpcClient.mnBudgetRawVote(
                        mn_tx_hash=currNode['collateral'].get('txid'),
                        mn_tx_index=int(currNode['collateral'].get('txidn')),
                        proposal_hash=prop.Hash,
                        vote=self.vote_codes[vote_code],
                        time=sig_time,
                        vote_sig=vote_sig)
                    
                    printOK(v_res)
                    
                    if v_res == 'Voted successfully':
                        self.successVotes += 1
                    else:
                        self.failedVotes += 1
                    
                except Exception as e:
                    err_msg = "Exception in vote_thread - check MN privKey"
                    printException(getCallerName(), getFunctionName(), err_msg, e.args)



    def vote_thread_end(self):
        message = '<p>Votes sent</p>'
        if self.successVotes > 0:
            message += '<p>Successful Votes: <b>%d</b></p>' % self.successVotes
        if self.failedVotes > 0:
            message += '<p>Failed Votes: <b>%d</b>' % self.failedVotes
        myPopUp_sb(self.caller, "info", 'Vote Finished', message)
        # refresh my votes on proposals
        self.ui.proposalBox.setRowCount(0)
        self.ui.proposalBox.setSortingEnabled(False)
        self.ui.selectedPropLabel.setText("<em><b>0</b> proposals selected")
        self.ui.resetStatusLabel()
        ThreadFuns.runInThread(self.countMyVotes_thread, (), self.displayProposals)
                                        
                    