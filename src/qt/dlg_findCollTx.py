#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLineEdit 
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSpacerItem, QSizePolicy, QTableWidget, QAbstractScrollArea, QAbstractItemView, QTableWidgetItem
from PyQt5.Qt import QHBoxLayout, QHeaderView
from threads import ThreadFuns
from misc import printDbg

class FindCollTx_dlg(QDialog):
    def __init__(self, mainTab):
        QDialog.__init__(self, parent=mainTab.ui)
        self.mainTab = mainTab
        self.utxos = []
        self.blockCount = 0
        self.setupUI()
        
       
       
        
    def setupUI(self):
        Ui_FindCollateralTxDlg.setupUi(self, self)
        self.setWindowTitle('Find Collateral Tx')
        ##--- feedback
        self.lblMessage.setVisible(False)
        self.lblMessage.setVisible(True)
        self.lblMessage.setText('Checking explorer...')
        
        
        
    def load_data(self, pivx_addr):
        self.pivx_addr = pivx_addr
        ##--- PIVX Address
        self.edtAddress.setText(self.pivx_addr)
        ##--- Load utxos
        ThreadFuns.runInThread(self.load_utxos_thread, (), self.display_utxos)



    
    def display_utxos(self):
        def item(value):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            return item

        self.tableW.setRowCount(len(self.utxos))
        for row, utxo in enumerate(self.utxos):
            pivxAmount = round(int(utxo.get('value', 0))/1e8, 8)
            self.tableW.setItem(row, 0, item(str(pivxAmount)))
            self.tableW.setItem(row, 1, item(str(utxo['confirmations'])))
            self.tableW.setItem(row, 2, item(utxo.get('tx_hash', None)))
            self.tableW.setItem(row, 3, item(str(utxo.get('tx_ouput_n', None))))

        if len(self.utxos):
            self.tableW.resizeColumnsToContents()
            self.lblMessage.setVisible(False)
            self.tableW.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            
        else:
            if self.apiConnected:
                self.lblMessage.setText('<b style="color:red">Found no unspent transactions with 10000 PIVs '
                                        'amount sent to address %s.</b> (or explorer offline - try manually)' %
                                        self.pivx_addr)
            else:
                self.lblMessage.setText('<b style="color:purple">Unable to connect to API provider or RPC server.\nEnter tx manually</b>')
            self.lblMessage.setVisible(True)
        
        
    
    
    def load_utxos_thread(self, ctrl):
        self.apiConnected = False
        try:
            if not self.mainTab.caller.rpcClient.getStatus():
                printDbg('PIVX daemon not connected')
            else:
                try:
                    if self.mainTab.caller.apiClient.getStatus() != 200:
                        return
                    self.apiConnected = True
                    self.blockCount = self.mainTab.caller.rpcClient.getBlockCount()
                    utxos = self.mainTab.caller.apiClient.getAddressUtxos(self.pivx_addr)['unspent_outputs']
                    printDbg("loading utxos\nblockCount=%s\n%s" % (str(self.blockCount), str(self.utxos)))
                    self.utxos = [utxo for utxo in utxos if round(int(utxo.get('value', 0))/1e8, 8) == 10000.00000000 ]

                except Exception as e:
                    self.errorMsg = 'Error occurred while calling getaddressutxos method: ' + str(e)
                    print(self.errorMsg)
                    
        except Exception as e:
            pass
        
        
        

    def getSelection(self):
        items = self.tableW.selectedItems()
        if len(items):
            row = items[0].row()
            return self.utxos[row]['tx_hash'], self.utxos[row]['tx_ouput_n']
        else:
            return None, 0





class Ui_FindCollateralTxDlg(object):
    def setupUi(self, FindCollateralTxDlg):
        self.dlg = FindCollateralTxDlg
        FindCollateralTxDlg.resize(658, 257)
        FindCollateralTxDlg.setModal(True)
        self.vBox = QVBoxLayout(FindCollateralTxDlg)
        self.vBox.setContentsMargins(8, 8, 8, 8)
        self.vBox.setSpacing(8)
        self.hBox = QHBoxLayout()
        self.hBox.setContentsMargins(-1, 8, -1, 6)
        self.addrLabel = QLabel(FindCollateralTxDlg)
        self.hBox.addWidget(self.addrLabel)
        self.edtAddress = QLineEdit(FindCollateralTxDlg)
        self.edtAddress.setReadOnly(True)
        self.hBox.addWidget(self.edtAddress)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.hBox.addItem(spacerItem)
        self.hBox.setStretch(1, 1)
        self.vBox.addLayout(self.hBox)
        self.lblMessage = QLabel(FindCollateralTxDlg)
        self.lblMessage.setText("")
        self.lblMessage.setWordWrap(True)
        self.vBox.addWidget(self.lblMessage)
        self.tableW = QTableWidget(FindCollateralTxDlg)
        self.tableW.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableW.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableW.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableW.setShowGrid(True)
        self.tableW.setColumnCount(4)
        self.tableW.setRowCount(0)
        self.tableW.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tableW.verticalHeader().hide()
        item = QTableWidgetItem()
        item.setText("PIVs")
        item.setTextAlignment(Qt.AlignCenter)
        self.tableW.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem()
        item.setText("Confirmations")
        item.setTextAlignment(Qt.AlignCenter)
        self.tableW.setHorizontalHeaderItem(1, item)
        item = QTableWidgetItem()
        item.setText("TX Hash")
        item.setTextAlignment(Qt.AlignCenter)
        self.tableW.setHorizontalHeaderItem(2, item)
        item = QTableWidgetItem()
        item.setText("TX Output N")
        item.setTextAlignment(Qt.AlignCenter)
        self.tableW.setHorizontalHeaderItem(3, item)
        self.vBox.addWidget(self.tableW)
        self.buttonBox = QDialogButtonBox(FindCollateralTxDlg)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.vBox.addWidget(self.buttonBox)
        btnCancel = self.buttonBox.button(QDialogButtonBox.Cancel)
        btnCancel.clicked.connect(self.reject)
        btnOk = self.buttonBox.button(QDialogButtonBox.Ok)
        btnOk.clicked.connect(self.accept)