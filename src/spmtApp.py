#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import signal
import simplejson as json
import sys

from PyQt5.Qt import QMainWindow, QIcon, QAction, QFileDialog
from PyQt5.QtCore import QSettings

from misc import getSPMTVersion, printDbg, readMNfile, writeToFile, printOK, clean_v4_migration
from mainWindow import MainWindow
from constants import user_dir, DefaultCache
from qt.dlg_configureRPCserver import ConfigureRPCserver_dlg


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
 
    def __init__(self, imgDir, app):
        super().__init__()
        self.app = app
        # Register the signal handlers
        signal.signal(signal.SIGTERM, service_shutdown)
        signal.signal(signal.SIGINT, service_shutdown)
        # Get version and title
        self.version = getSPMTVersion()
        self.title = 'SPMT - Secure PIVX Masternode Tool - v.%s-%s' % (self.version['number'], self.version['tag'])
        # Create the userdir if it doesn't exist
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        # Clean v4 migration (read data from old files and delete them)
        clean_v4_migration()
        # Read cached app data
        self.cache = self.readCache()
        # Read Masternode List
        masternode_list = readMNfile()
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
        # Add RPC server menu
        mainMenu = self.menuBar()
        confMenu = mainMenu.addMenu('Setup')
        self.rpcConfMenu = QAction(self.pivx_icon, 'Local RPC Server...', self)
        self.rpcConfMenu.triggered.connect(self.onEditRPCServer)
        confMenu.addAction(self.rpcConfMenu)
        self.loadMNConfAction = QAction(self.script_icon, 'Import "masternode.conf" file', self)
        self.loadMNConfAction.triggered.connect(self.loadMNConf)
        confMenu.addAction(self.loadMNConfAction)
        
        # Sort masternode list (by alias if no previous order set)
        if self.cache.get('mnList_order') != {}:
            masternode_list.sort(key=self.extract_order)
        else:
            masternode_list.sort(key=self.extract_name)
        
        # Create main window
        self.mainWindow = MainWindow(self, masternode_list, imgDir)
        self.setCentralWidget(self.mainWindow)
        
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
            return self.cache.get('mnList_order').get(name)
        
        except KeyError:
            return 0
        
        
        
    def closeEvent(self, *args, **kwargs):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        # Terminate the running threads.
        # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
        self.mainWindow.myRpcWd.shutdown_flag.set()
        print("Saving stuff & closing...")
        if getattr(self.mainWindow.hwdevice, 'dongle', None) is not None:
            self.mainWindow.hwdevice.dongle.close()
            print("Dongle closed")
            
        # Persist window/splitter size to cache settings
        settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
        settings.setValue('cache_winWidth', self.width())
        settings.setValue('cache_winHeight', self.height())
        settings.setValue('cache_splitterX', self.mainWindow.splitter.sizes()[0])
        settings.setValue('cache_splitterY', self.mainWindow.splitter.sizes()[1])
        settings.setValue('cache_consoleHidden', (self.mainWindow.btn_consoleToggle.text() == 'Show'))
        
        # Persist mnList order to cache settings
        mnOrder = {}
        mnList = self.mainWindow.tabMain.myList
        for i in range(mnList.count()):
            mnName = mnList.itemWidget(mnList.item(i)).alias
            mnOrder[mnName] = i
        settings.setValue('cache_mnOrder', json.dumps(mnOrder))
        
        # Adios
        print("Bye Bye.")
        return QMainWindow.closeEvent(self, *args, **kwargs)
    
    
    
    def loadMNConf(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, 'Open masternode.conf', 'masternode.conf', 'Text Files (*.conf)', options=options)
            
        if fileName:
            self.mainWindow.loadMNConf(fileName)     
    
    
    def onEditRPCServer(self):
        # Create Dialog
        ui = ConfigureRPCserver_dlg(self)
        if ui.exec():
            printDbg("Configuring RPC Server...")
            
            
    def readCache(self):
        settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
        defaultcache = DefaultCache()
        cache = {}
        cache["lastAddress"] = settings.value('cache_lastAddress', defaultcache.lastAddress, type=str)
        cache["window_width"] = settings.value('cache_winWidth', defaultcache.winWidth, type=int)
        cache["window_height"] = settings.value('cache_winHeight', defaultcache.winHeight, type=int)
        cache["splitter_x"] = settings.value('cache_splitterX', defaultcache.splitterX, type=int)
        cache["splitter_y"] = settings.value('cache_splitterY', defaultcache.splitterY, type=int)
        cache["mnList_order"] = json.loads(settings.value('cache_mnOrder', json.dumps(defaultcache.mnOrder), type=str))
        cache["console_hidden"] = settings.value('cache_consoleHidden', defaultcache.consoleHidden, type=bool)
        cache["useSwiftX"] = settings.value('cache_useSwiftX', defaultcache.useSwiftX, type=bool)
        cache["votingMasternodes"] = json.loads(settings.value('cache_votingMNs', json.dumps(defaultcache.votingMNs), type=str))
        cache["votingDelayCheck"] = settings.value('cache_vdCheck', defaultcache.vdCheck, type=bool)
        cache["votingDelayNeg"] = settings.value('cache_vdNeg', defaultcache.vdNeg, type=int)
        cache["votingDelayPos"] = settings.value('cache_vdPos', defaultcache.vdPos, type=int)
        return cache
        
        
