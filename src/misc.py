#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from ipaddress import ip_address
import simplejson as json
import time
from urllib.parse import urlparse

from PyQt5.QtCore import QObject, pyqtSignal, QSettings

from constants import user_dir, log_File, DEFAULT_MN_CONF, DefaultCache
from PyQt5.QtWidgets import QMessageBox
from sympy.physics.units.dimensions import action


def add_defaultKeys_to_dict(dictObj, defaultObj):
    for key in defaultObj:
        if key not in dictObj:
            dictObj[key] = defaultObj[key]


def append_to_logfile(text):
    try:
        logFile = open(log_File, 'a+')
        logFile.write(text)
        logFile.close()
    except Exception as e:
        print(e)

    
    
        
def appendMasternode(mainWnd, mn):
    printDbg("saving MN configuration for %s" % mn['name'])
    
    # If we are changing a MN, remove previous entry:
    if not mainWnd.mnode_to_change is None:
        # remove from cache and QListWidget only
        removeMNfromList(mainWnd, mainWnd.mnode_to_change, removeFromDB=False)
        
    # Append new mn to list
    mainWnd.masternode_list.append(mn)
    
    # Save/edit DB
    mainWnd.parent.db.addMasternode(mn, mainWnd.mnode_to_change)
    mainWnd.mnode_to_change = None
    
    # Insert item in list of Main tab
    name = mn['name']
    namelist = [x['name'] for x in mainWnd.masternode_list]
    row = namelist.index(name)
    if row == -1:
        row = None
    mainWnd.tabMain.insert_mn_list(name, mn['ip'], mn['port'], row, isHardware=mn['isHardware'])
    
    # Connect buttons
    mainWnd.tabMain.btn_remove[name].clicked.connect(lambda: mainWnd.t_main.onRemoveMN())
    mainWnd.tabMain.btn_edit[name].clicked.connect(lambda: mainWnd.t_main.onEditMN())
    mainWnd.tabMain.btn_start[name].clicked.connect(lambda: mainWnd.t_main.onStartMN())
    mainWnd.tabMain.btn_rewards[name].clicked.connect(lambda: mainWnd.t_main.onRewardsMN())   
    printDbg("saved")




def checkRPCstring(urlstring, action_msg="Malformed credentials"):
    try:
        o = urlparse(urlstring)
        if o.scheme is None or o.scheme == '':
            action_msg = "Wrong protocol. Set either http or https."
            raise
        if o.netloc is None or o.netloc == '':
            action_msg = "Malformed host network location part"
            raise
        if o.port is None or o.port == '':
            action_msg = "Wrong IP port number"
            raise
        if o.username is None:
            action_msg = "Malformed username"
            raise
        if  o.password is None:
            action_msg = "Malformed password"
            raise
        return True
    
    except Exception as e:
        print(e)
        error_msg = "Unable to parse URL"
        printException(getCallerName(), getFunctionName(), action_msg, error_msg)
        return False
        
        
        
        
def clean_v4_migration(db):
    try:
        rpc_file = os.path.join(user_dir, 'rpcServer.json')
        cache_file = os.path.join(user_dir, 'cache.json')
        mn_file = os.path.join(user_dir, 'masternodes.json')
        
        if os.path.exists(rpc_file) or os.path.exists(cache_file) or os.path.exists(mn_file):
            printDbg("Clean migration to v0.4.0 data storage")
        
        if os.path.exists(rpc_file):
            # If RPC file exists
            printDbg("found old rpcServer.json file")
            with open(rpc_file) as data_file:
                rpc_config = json.load(data_file)
            # copy to database
            rpc_host = "%s:%d" % (rpc_config['rpc_ip'], rpc_config['rpc_port'])
            db.editRPCServer("http", rpc_host, rpc_config['rpc_user'], rpc_config['rpc_password'], 0)
            printDbg("...saved to Database")
            # and delete old file
            os.remove(rpc_file)
            printDbg("old rpcServer.json file deleted")
        
        if os.path.exists(cache_file):
            # If cache file exists
            printDbg("found old cache.json file")
            with open(cache_file) as data_file:
                cache = json.load(data_file)
            # copy to Settings
            saveCacheSettings(cache, True)
            printDbg("...saved to Settings")
            # and delete old file
            os.remove(cache_file)
            printDbg("old cache.json file deleted")
        
        if os.path.exists(mn_file):
            # If mn file exists
            printDbg("found old masternodes.json file")
            with open(mn_file) as data_file:
                mnList = json.load(data_file)
            # add to database
            for mn in mnList:
                db.addMasternode(mn)
            printDbg("...saved to Database")
            # and delete old file
            os.remove(mn_file)
            printDbg("old masternodes.json file deleted")    
        
    except Exception as e:
        printDbg(e)
        
        
        
        


def clean_for_html(text):
    if text is None:
        return ""
    return text.replace("<", "{").replace(">","}")



def clear_screen():
    os.system('clear')



def getCallerName():
    try:
        return sys._getframe(2).f_code.co_name
    except Exception:
        return None



def getFunctionName():
    try:
        return sys._getframe(1).f_code.co_name
    except Exception:
        return None
    
    
def getRemoteSPMTversion():
    import requests
    resp = requests.get("https://raw.githubusercontent.com/PIVX-Project/PIVX-SPMT/master/src/version.txt")
    if resp.status_code == 200:
        data = resp.json()
        return data['number']
    else:
        print("Invalid response getting version from GitHub\n")
        return "0.0.0"



def getSPMTVersion():
    version_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'version.txt')
    with open(version_file) as data_file:
        data = json.load(data_file)       

    return data



def getTxidTxidn(txid, txidn):
    if txid is None or txidn is None:
        return None
    else:
        return txid + '-' + str(txidn)



def ipport(ip, port):
    if ip is None or port is None:
        return None
    elif ip.endswith('.onion'):
        return ip + ':' + port
    else:
        ipAddr = ip_address(ip)
        if ipAddr.version == 4:
            return ip + ':' + port
        elif ipAddr.version == 6:
            return "[" + ip + "]:" + port
        else:
            raise Exception("invalid IP version number")
        
        
        
def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False



def loadMNConfFile(fileName):
    
    hot_masternodes = []
    try:
        with open(fileName) as f:
            for line in f:
                confline = line.strip()
                
                # skip blank lines
                if len(confline) == 0:
                    continue
                
                # skip comments
                if confline[0] == '#':
                    continue
                
                configs = confline.split(' ')
                # check number of keys
                if len(configs) != 5:
                    printDbg("wrong number of parameters in masternode.conf")
                    return None
                
                new_mn = {}
                new_mn['name'] = configs[0]
                
                ipaddr = configs[1].split(':')
                if len(ipaddr) != 2:
                    printDbg("wrong ip:address in masternode.conf")
                    return None
                
                new_mn['ip'] = ipaddr[0]
                new_mn['port'] = int(ipaddr[1])
                new_mn['mnPrivKey'] = configs[2]
                new_mn['isTestnet'] = DEFAULT_MN_CONF['isTestnet']
                new_mn['isHardware'] = False
                new_mn['hwAcc'] = DEFAULT_MN_CONF['hwAcc']
                collateral = {}
                collateral['address'] = ""
                collateral['pubkey'] = ""
                collateral['txid'] = configs[3]
                collateral['txidn'] = int(configs[4])
                new_mn['collateral'] = collateral
                
                hot_masternodes.append(new_mn)
        
        return hot_masternodes
                
    except Exception as e:
        errorMsg = "error loading MN file"
        printException(getCallerName(), getFunctionName(), errorMsg, e.args)
            
            
            
def myPopUp(p, messType, messTitle, messText, defaultButton=QMessageBox.No):
    mess = QMessageBox(messType, messTitle, messText, defaultButton, parent=p)
    mess.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    mess.setDefaultButton(defaultButton)
    return mess.exec_()
    
    
def now():
    return int(time.time())




def persistCacheSetting(cache_key, cache_value):
    settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
    if not settings.contains(cache_key):
        errorMsg = "Adding new cache key to settings..."
        causeMsg = "Cache key %s not found" % str(cache_key)
        printException(getCallerName(), getFunctionName(), errorMsg, causeMsg)
        
    if type(cache_value) in [list, dict]:    
        settings.setValue(cache_key, json.dumps(cache_value))
    else:
        settings.setValue(cache_key, cache_value)

    return cache_value




def printDbg_msg(what):
    what = clean_for_html(what)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(now()))
    log_line = '<b style="color: yellow">{}</b> : {}<br>'.format(timestamp, what)
    return log_line



def printDbg(what):
    log_line = printDbg_msg(what)
    append_to_logfile(log_line)
    print(log_line)
    
    
    
    
def printException_msg(
        caller_name,
        function_name,
        err_msg,
        errargs=None):
    VERSION = getSPMTVersion()
    msg = '<b style="color: red">EXCEPTION</b><br>'
    msg += '<span style="color:white">version</span> : %s-%s<br>' % (VERSION['number'], VERSION['tag'])
    msg += '<span style="color:white">caller</span>   : %s<br>' % caller_name
    msg += '<span style="color:white">function</span> : %s<br>' % function_name
    msg += '<span style="color:red">'
    if errargs:
        msg += 'err: %s<br>' % str(errargs)
        
    msg += '===> %s</span><br>' % err_msg 
    return msg



def printException(caller_name,
        function_name,
        err_msg,
        errargs=None):
    text = printException_msg(caller_name, function_name, err_msg, errargs)
    append_to_logfile(text)
    print(text)
    
    

def printOK(what):
    msg = '<b style="color: #cc33ff">===> ' + what + '</b><br>'
    append_to_logfile(msg)
    print(msg)
    



def readCacheSettings():
    settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
    try:
        cache = {}
        cache["lastAddress"] = settings.value('cache_lastAddress', DefaultCache["lastAddress"], type=str)
        cache["window_width"] = settings.value('cache_winWidth', DefaultCache["window_width"], type=int)
        cache["window_height"] = settings.value('cache_winHeight', DefaultCache["window_height"], type=int)
        cache["splitter_x"] = settings.value('cache_splitterX', DefaultCache["splitter_x"], type=int)
        cache["splitter_y"] = settings.value('cache_splitterY', DefaultCache["splitter_y"], type=int)
        cache["mnList_order"] = json.loads(settings.value('cache_mnOrder', json.dumps(DefaultCache["mnList_order"]), type=str))
        cache["console_hidden"] = settings.value('cache_consoleHidden', DefaultCache["console_hidden"], type=bool)
        cache["useSwiftX"] = settings.value('cache_useSwiftX', DefaultCache["useSwiftX"], type=bool)
        cache["votingMasternodes"] = json.loads(settings.value('cache_votingMNs', json.dumps(DefaultCache["votingMasternodes"]), type=str))
        cache["votingDelayCheck"] = settings.value('cache_vdCheck', DefaultCache["votingDelayCheck"], type=bool)
        cache["votingDelayNeg"] = settings.value('cache_vdNeg', DefaultCache["votingDelayNeg"], type=int)
        cache["votingDelayPos"] = settings.value('cache_vdPos', DefaultCache["votingDelayPos"], type=int)
        cache["selectedRPC_index"] = settings.value('cache_RPCindex', DefaultCache["selectedRPC_index"], type=int)
        add_defaultKeys_to_dict(cache, DefaultCache)
        return cache
    except:
        return DefaultCache
        
      
        
def removeMNfromList(mainWnd, mn, removeFromDB=True):
    # remove from cache list
    mainWnd.masternode_list.remove(mn)
    # remove from tabMain widget
    row = mainWnd.tabMain.myList.row
    item = mainWnd.tabMain.current_mn[mn['name']]
    mainWnd.tabMain.myList.takeItem(row(item))
    # remove from database
    if removeFromDB:
        mainWnd.parent.db.deleteMasternode(mn['name'])
    # Clear voting masternodes configuration and update cache
    # if we are removing an already selected masternode
    if mn['name'] in [x[1] for x in mainWnd.t_governance.votingMasternodes]:
        mainWnd.t_governance.clear()
    

    

def saveCacheSettings(cache, old_version=False):
    settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
    settings.setValue('cache_lastAddress', cache.get('lastAddress'))
    settings.setValue('cache_winWidth', cache.get('window_width'))
    settings.setValue('cache_winHeight', cache.get('window_height'))
    if old_version:
        settings.setValue('cache_splitterX', cache.get('splitter_sizes')[0])
        settings.setValue('cache_splitterY', cache.get('splitter_sizes')[1])
    else:
        settings.setValue('cache_splitterX', cache.get('splitter_x'))
        settings.setValue('cache_splitterY', cache.get('splitter_y'))
    settings.setValue('cache_mnOrder', json.dumps(cache.get('mnList_order')))
    settings.setValue('cache_consoleHidden', cache.get('console_hidden'))   
    settings.setValue('cache_useSwiftX', cache.get('useSwiftX'))
    settings.setValue('cache_votingMNs', json.dumps(cache.get('votingMasternodes')))
    settings.setValue('cache_vdCheck', cache.get('votingDelayCheck'))
    settings.setValue('cache_vdNeg', cache.get('votingDelayNeg'))
    settings.setValue('cache_vdPos', cache.get('votingDelayPos'))
    if not old_version:
        settings.setValue('cache_RPCindex', cache.get('selectedRPC_index'))
        
    
    
    
def sec_to_time(seconds):
    days = seconds//86400
    seconds -= days*86400
    hrs = seconds//3600
    seconds -= hrs*3600
    mins = seconds//60
    seconds -= mins*60   
    return "{} days, {} hrs, {} mins, {} secs".format(days, hrs, mins, seconds)


      
    
def splitString(text, n):
    arr = [text[i:i+n] for i in range(0, len(text), n)]
    return '\n'.join(arr)




def timeThis(function, *args):
    start = time.clock()
    val = function(*args)
    end = time.clock()
    return val, (end-start)
    



def updateSplash(label, i):
    if i==10:
        progressText = "Loading configuration data..."
        label.setText(progressText)
    elif i==40:
        progressText = "Opening database..."
        label.setText(progressText)
    elif i==50:
        progressText = "Creating user interface..."
        label.setText(progressText)
    elif i==70:
        progressText = "Releasing the watchdogs..."
        label.setText(progressText)
    elif i==90:
        progressText = "SPMT ready"
        label.setText(progressText)   
    elif i==99:
        time.sleep(0.1)

    
    
    
# Stream object to redirect sys.stdout and sys.stderr to a queue
class WriteStream(object):
    def __init__(self, queue):
        self.queue = queue
    
    def write(self, text):
        self.queue.put(text)
        
    def flush(self):
        pass
        


# QObject (to be run in QThread) that blocks until data is available
# and then emits a QtSignal to the main thread.
class WriteStreamReceiver(QObject):
    mysignal = pyqtSignal(str)
    
    def __init__(self, queue, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.queue = queue
          
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)
