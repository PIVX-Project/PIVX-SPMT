#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import logging
import os
import signal
from time import time

from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog

from database import Database
from misc import getSPMTVersion, printDbg, initLogs, \
    clean_v4_migration, saveCacheSettings, readCacheSettings
from mainWindow import MainWindow
from constants import user_dir, SECONDS_IN_2_MONTHS
from qt.dlg_configureRPCservers import ConfigureRPCservers_dlg
from qt.dlg_signmessage import SignMessage_dlg

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass



def service_shutdown(signum, frame):
    print('Caught signal %d' % signum)
    raise ServiceExit



class App(QMainWindow):
    # Signal emitted from database
    sig_changed_rpcServers = pyqtSignal()

    def __init__(self, imgDir, app, start_args):
        # Create the userdir if it doesn't exist
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        # Initialize Logs
        initLogs()
        super().__init__()
        self.app = app
        # Register the signal handlers
        signal.signal(signal.SIGTERM, service_shutdown)
        signal.signal(signal.SIGINT, service_shutdown)

        # Get version and title
        self.version = getSPMTVersion()
        self.title = 'SPMT - Secure PIVX Masternode Tool - v.%s-%s' % (self.version['number'], self.version['tag'])

        # Open database
        self.db = Database(self)
        self.db.open()

        # Clean v4 migration (read data from old files and delete them)
        clean_v4_migration(self)

        # Check for startup args (clear data)
        if start_args.clearAppData:
            settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
            settings.clear()
        if start_args.clearRpcData:
            self.db.clearTable('CUSTOM_RPC_SERVERS')
        if start_args.clearMnData:
            self.db.clearTable('MASTERNODES')
        if start_args.clearTxCache:
            self.db.clearTable('RAWTXES')

        # Clear Rewards and Governance DB (in case of forced shutdown)
        self.db.clearTable('REWARDS')
        self.db.clearTable('PROPOSALS')
        self.db.clearTable('MY_VOTES')

        # Remove raw txes updated earlier than two months ago (if not already cleared)
        if not start_args.clearTxCache:
            self.db.clearRawTxes(time() - SECONDS_IN_2_MONTHS)

        # Read Masternode List
        masternode_list = self.db.getMasternodeList()
        # Read cached app data
        self.cache = readCacheSettings()
        # Initialize user interface
        self.initUI(masternode_list, imgDir)



    def initUI(self, masternode_list, imgDir):
        # Set title and geometry
        self.setWindowTitle(self.title)
        self.resize(self.cache.get("window_width"), self.cache.get("window_height"))
        # Set Icons
        self.spmtIcon = QIcon(os.path.join(imgDir, 'spmtLogo_shield.png'))
        self.pivx_icon = QIcon(os.path.join(imgDir, 'icon_pivx.png'))
        self.script_icon = QIcon(os.path.join(imgDir, 'icon_script.png'))
        self.setWindowIcon(self.spmtIcon)

        # Sort masternode list (by alias if no previous order set)
        if self.cache.get('mnList_order') != {} and (
            len(self.cache.get('mnList_order')) == len(masternode_list)):
            try:
                masternode_list.sort(key=self.extract_order)
            except Exception as e:
                print(e)
                masternode_list.sort(key=self.extract_name)

        else:
            masternode_list.sort(key=self.extract_name)

        # Create main window
        self.mainWindow = MainWindow(self, masternode_list, imgDir)
        self.setCentralWidget(self.mainWindow)

        # Add RPC server menu
        mainMenu = self.menuBar()
        confMenu = mainMenu.addMenu('Setup')
        self.rpcConfMenu = QAction(self.pivx_icon, 'RPC Servers config...', self)
        self.rpcConfMenu.triggered.connect(self.onEditRPCServer)
        confMenu.addAction(self.rpcConfMenu)
        self.loadMNConfAction = QAction(self.script_icon, 'Import "masternode.conf" file', self)
        self.loadMNConfAction.triggered.connect(self.loadMNConf)
        confMenu.addAction(self.loadMNConfAction)
        toolsMenu = mainMenu.addMenu('Tools')
        self.signVerifyAction = QAction('Sign/Verify message', self)
        self.signVerifyAction.triggered.connect(self.onSignVerifyMessage)
        toolsMenu.addAction(self.signVerifyAction)

        # Show
        self.show()
        self.activateWindow()



    def extract_name(self, json):
        try:
            return json['name'].lower()
        except KeyError:
            return 0



    def extract_order(self, json):
        try:
            name = json['name']
            if name in self.cache.get('mnList_order'):
                return self.cache.get('mnList_order').get(name)
            return 0

        except KeyError:
            return 0



    def closeEvent(self, *args, **kwargs):
        # Terminate the running threads.
        # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
        self.mainWindow.myRpcWd.shutdown_flag.set()
        logging.debug("Saving stuff & closing...")
        try:
            self.mainWindow.hwdevice.clearDevice()
        except Exception as e:
            logging.warning(str(e))

        # Update window/splitter size
        self.cache['window_width'] = self.width()
        self.cache['window_height'] = self.height()
        self.cache['splitter_x'] = self.mainWindow.splitter.sizes()[0]
        self.cache['splitter_y'] = self.mainWindow.splitter.sizes()[1]
        self.cache['console_hidden'] = (self.mainWindow.btn_consoleToggle.text() == 'Show')

        # Update mnList order to cache settings
        mnOrder = {}
        mnList = self.mainWindow.tabMain.myList
        for i in range(mnList.count()):
            mnName = mnList.itemWidget(mnList.item(i)).alias
            mnOrder[mnName] = i
        self.cache['mnList_order'] = mnOrder

        # persist cache
        saveCacheSettings(self.cache)

        # Clear Rewards and Governance DB
        try:
            self.db.open()
        except Exception:
            pass
        self.db.removeTable('REWARDS')
        self.db.removeTable('PROPOSALS')
        self.db.removeTable('MY_VOTES')

        # close database
        self.db.close()

        # Adios
        print("Bye Bye.")

        # Return
        return QMainWindow.closeEvent(self, *args, **kwargs)



    def loadMNConf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open masternode.conf', 'masternode.conf', 'Text Files (*.conf)', options=options)

        if fileName:
            self.mainWindow.loadMNConf(fileName)



    def onEditRPCServer(self):
        # Create Dialog
        ui = ConfigureRPCservers_dlg(self)
        if ui.exec():
            printDbg("Configuring RPC Servers...")



    def onSignVerifyMessage(self):
        # Create Dialog
        ui = SignMessage_dlg(self.mainWindow)
        if ui.exec():
            printDbg("Sign/Verify message...")
