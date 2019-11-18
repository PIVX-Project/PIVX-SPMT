#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLabel,\
    QListWidget, QFrame, QFormLayout, QComboBox, QLineEdit, QListWidgetItem,\
    QWidget, QPushButton, QMessageBox

from misc import myPopUp, checkRPCstring
from threads import ThreadFuns

class ConfigureRPCservers_dlg(QDialog):
    def __init__(self, main_wnd):
        QDialog.__init__(self, parent=main_wnd)
        self.main_wnd = main_wnd
        self.setWindowTitle('RPC Servers Configuration')
        self.changing_index = None
        self.initUI()
        self.loadServers()
        self.main_wnd.mainWindow.sig_RPClistReloaded.connect(self.loadServers)
            
            
            
    def clearEditFrame(self):
        self.ui.user_edt.clear()
        self.ui.passwd_edt.clear()
        self.ui.protocol_select.setCurrentIndex(0)
        self.ui.host_edt.clear()


    def initUI(self):
        self.ui = Ui_ConfigureRPCserversDlg()
        self.ui.setupUi(self)
        
        
    def insert_server_list(self, server):
        id = server['id']
        index = self.main_wnd.mainWindow.getServerListIndex(server)
        server_line = QWidget()
        server_row = QHBoxLayout()
        server_text = "%s://%s" % (server['protocol'], server['host'])
        if server['id'] == 0 and server['isCustom']:
            # Local Wallet
            server_text = server_text + "&nbsp;&nbsp;<b>Local Wallet</b>"
        elif not server['isCustom']:
            server_text = "<em style='color: purple'>%s</em>" % server_text
        server_row.addWidget(QLabel(server_text))
        server_row.addStretch(1)
        ## -- Edit button
        editBtn = QPushButton()
        editBtn.setIcon(self.main_wnd.mainWindow.tabMain.editMN_icon)
        editBtn.setToolTip("Edit server configuration")
        if not server['isCustom']:
            editBtn.setDisabled(True)
            editBtn.setToolTip('Default servers are not editable')
        editBtn.clicked.connect(lambda: self.onAddServer(index))
        server_row.addWidget(editBtn)
        ## -- Remove button
        removeBtn = QPushButton()
        removeBtn.setIcon(self.main_wnd.mainWindow.tabMain.removeMN_icon)
        removeBtn.setToolTip("Remove server configuration")
        if id == 0:
            removeBtn.setDisabled(True)
            removeBtn.setToolTip('Cannot remove local wallet')
        if not server['isCustom']:
            removeBtn.setDisabled(True)
            removeBtn.setToolTip('Cannot remove default servers')
        removeBtn.clicked.connect(lambda: self.onRemoveServer(index))
        server_row.addWidget(removeBtn)
        ## --
        server_line.setLayout(server_row)
        self.serverItems[id] = QListWidgetItem()
        self.serverItems[id].setSizeHint(server_line.sizeHint())
        self.ui.serversBox.addItem(self.serverItems[id])
        self.ui.serversBox.setItemWidget(self.serverItems[id], server_line)
        
        
    def loadServers(self):
        # Clear serversBox
        self.ui.serversBox.clear()
        # Fill serversBox
        self.serverItems = {}
        for server in self.main_wnd.mainWindow.rpcServersList:
            self.insert_server_list(server)
        
        
    def loadEditFrame(self, index):
        server = self.main_wnd.mainWindow.rpcServersList[index]
        self.ui.user_edt.setText(server['user'])
        self.ui.passwd_edt.setText(server['password'])
        if server['protocol']  == 'https':
            self.ui.protocol_select.setCurrentIndex(1)
        else:
            self.ui.protocol_select.setCurrentIndex(0)
        self.ui.host_edt.setText(server['host'])
        
    

    def onAddServer(self, index=None):
        # Save current index (None for new entry)
        self.changing_index = index
        # Hide 'Add' and 'Close' buttons and disable serversBox
        self.ui.addServer_btn.hide()
        self.ui.close_btn.hide()
        self.ui.serversBox.setEnabled(False)
        # Show edit-frame
        self.ui.editFrame.setHidden(False)
        # If we are adding a new server, clear edit-frame
        if index is None:
            self.clearEditFrame()
        # else pre-load data
        else:
            self.loadEditFrame(index)
        
    

    def onCancel(self):
        # Show 'Add' and 'Close' buttons and enable serversBox
        self.ui.addServer_btn.show()
        self.ui.close_btn.show()
        self.ui.serversBox.setEnabled(True)
        # Hide edit-frame
        self.ui.editFrame.setHidden(True)
        # Clear edit-frame
        self.clearEditFrame()
    
    

    def onClose(self):
        # close dialog
        self.close()
        
        

    def onRemoveServer(self, index):
        mess = "Are you sure you want to remove server with index %d (%s) from list?" % (
            index, self.main_wnd.mainWindow.rpcServersList[index].get('host'))
        ans = myPopUp(self, QMessageBox.Question, 'SPMT - remove server', mess)
        if ans == QMessageBox.Yes:
            # Remove entry from database
            id = self.main_wnd.mainWindow.rpcServersList[index].get('id')
            self.main_wnd.db.removeRPCServer(id)

    

    def onSave(self):
        # Get new config data
        protocol = "http" if self.ui.protocol_select.currentIndex() == 0 else "https"
        host = self.ui.host_edt.text()
        user = self.ui.user_edt.text()
        passwd = self.ui.passwd_edt.text()
        # Check malformed URL
        url_string = "%s://%s:%s@%s" % (protocol, user, passwd, host)
        if checkRPCstring(url_string):            
            if self.changing_index is None:
                # Save new entry in DB.
                self.main_wnd.db.addRPCServer(protocol, host, user, passwd)
            else:
                # Edit existing entry to DB.
                id = self.main_wnd.mainWindow.rpcServersList[self.changing_index].get('id')
                self.main_wnd.db.editRPCServer(protocol, host, user, passwd, id)
                # If this was previously selected in mainWindow, update status
                clients = self.main_wnd.mainWindow.header.rpcClientsBox
                data = clients.itemData(clients.currentIndex())
                if data.get('id') == id and data.get('isCustom'):
                    ThreadFuns.runInThread(self.main_wnd.mainWindow.updateRPCstatus, (True,),)
     
            # call onCancel
            self.onCancel()
    
        
        
        
class Ui_ConfigureRPCserversDlg(object):
    def setupUi(self, ConfigureRPCserversDlg):
        ConfigureRPCserversDlg.setModal(True)
        ## -- Layout
        self.layout  = QVBoxLayout(ConfigureRPCserversDlg)
        self.layout.setSpacing(10)
        ## -- Servers List
        self.serversBox = QListWidget()
        self.layout.addWidget(self.serversBox)
        ## -- 'Add Server' button
        self.addServer_btn  = QPushButton("Add RPC Server")
        self.layout.addWidget(self.addServer_btn)
        ## -- 'Close' button
        hBox = QHBoxLayout()
        hBox.addStretch(1)
        self.close_btn  = QPushButton("Close")
        hBox.addWidget(self.close_btn)
        self.layout.addLayout(hBox)
        ## -- Edit section
        self.editFrame = QFrame()
        frameLayout = QFormLayout()
        frameLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        frameLayout.setContentsMargins(5, 10, 5, 5)
        frameLayout.setSpacing(7)
        self.user_edt = QLineEdit()
        frameLayout.addRow(QLabel("Username"), self.user_edt)
        self.passwd_edt = QLineEdit()
        frameLayout.addRow(QLabel("Password"), self.passwd_edt)
        hBox = QHBoxLayout()
        self.protocol_select = QComboBox()
        self.protocol_select.addItems(['http', 'https'])
        hBox.addWidget(self.protocol_select)
        hBox.addWidget(QLabel("://"))
        self.host_edt = QLineEdit()
        self.host_edt.setPlaceholderText('myserver.net:8080')
        hBox.addWidget(self.host_edt)
        frameLayout.addRow(QLabel("URL"), hBox)
        hBox2 = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.save_btn = QPushButton("Save")
        hBox2.addWidget(self.cancel_btn)
        hBox2.addWidget(self.save_btn)
        frameLayout.addRow(hBox2)
        self.editFrame.setLayout(frameLayout)
        self.layout.addWidget(self.editFrame)
        self.editFrame.setHidden(True)
        ConfigureRPCserversDlg.setMinimumWidth(500)
        ConfigureRPCserversDlg.setMinimumHeight(500)
        # Connect main buttons
        self.addServer_btn.clicked.connect(lambda: ConfigureRPCserversDlg.onAddServer())
        self.close_btn.clicked.connect(lambda: ConfigureRPCserversDlg.onClose())
        self.cancel_btn.clicked.connect(lambda: ConfigureRPCserversDlg.onCancel())
        self.save_btn.clicked.connect(lambda: ConfigureRPCserversDlg.onSave())
        
        