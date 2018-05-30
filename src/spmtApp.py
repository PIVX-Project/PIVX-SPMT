#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import signal
from misc import getSPMTVersion, printDbg, readCacheFile, writeToFile
from constants import starting_height, starting_width, user_dir, cache_File
from PyQt5.Qt import QMainWindow, QIcon, QAction
from mainWindow import MainWindow
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
 
    def __init__(self, masternode_list, imgDir, app):
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
        # Read cache
        self.cache = readCacheFile()
        # Initialize user interface
        self.initUI(masternode_list, imgDir)
 
    def initUI(self, masternode_list, imgDir):
        # Set title and geometry
        self.setWindowTitle(self.title)
        self.resize(self.cache.get("window_width"), self.cache.get("window_height"))
        # Set Icon
        spmtIcon_file = os.path.join(imgDir, 'spmtLogo_shield.png')
        self.spmtIcon = QIcon(spmtIcon_file)
        self.setWindowIcon(self.spmtIcon)
        # Add RPC server menu
        mainMenu = self.menuBar()
        confMenu = mainMenu.addMenu('Setup')
        self.rpcConfMenu = QAction(self.spmtIcon, 'Local RPC Server...', self)
        self.rpcConfMenu.triggered.connect(self.onEditRPCServer)
        confMenu.addAction(self.rpcConfMenu)
        
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
            
        # Save window/splitter size to cache file
        self.cache["window_width"] = self.width()
        self.cache["window_height"] = self.height()
        self.cache["splitter_sizes"] = self.mainWindow.splitter.sizes()
        self.cache["console_hidden"] = (self.mainWindow.btn_consoleToggle.text() == 'Show')
        
        # Save mnList order to cache file
        mnOrder = {}
        mnList = self.mainWindow.tabMain.myList
        for i in range(mnList.count()):
            mnName = mnList.itemWidget(mnList.item(i)).alias
            mnOrder[mnName] = i
        self.cache['mnList_order'] = mnOrder
        
        # Write cache file
        writeToFile(self.cache, cache_File)
        print("Bye Bye.")
        return QMainWindow.closeEvent(self, *args, **kwargs)
    
    
    
    def onEditRPCServer(self):
        # Create Dialog
        try:
            ui = ConfigureRPCserver_dlg(self)
            if ui.exec():
                printDbg("Configuring RPC Server...")
        except Exception as e:
            print(e)
