#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from ipaddress import ip_address
import time
from urllib.parse import urlsplit

from PyQt5.QtCore import QObject, pyqtSignal, QSettings

from constants import user_dir, log_File, masternodes_File, DEFAULT_MN_CONF


def append_to_logfile(text):
    try:
        logFile = open(log_File, 'a+')
        logFile.write(text)
        logFile.close()
    except Exception as e:
        print(e)
        
        
        
def clean_v4_migration():
    try:
        import simplejson as json
        rpc_file = os.path.join(user_dir, 'rpcServer.json')
        cache_file = os.path.join(user_dir, 'cache.json')
        
        if os.path.exists(rpc_file) or os.path.exists(cache_file):
            printDbg("Clean migration to v0.4.0 data storage")
        
        if os.path.exists(rpc_file):
            # If RPC file exists
            printDbg("found old rpcServer.json file")
            with open(rpc_file) as data_file:
                rpc_config = json.load(data_file)
            # copy to Settings
            saveLocalRPCSettingsConf(rpc_config)
            printDbg("...saved to Settings")
            # and delete old file
            os.remove(rpc_file)
            printDbg("old rpcServer.json file deleted")
        
        if os.path.exists(cache_file):
            # If cache file exists
            printDbg("found old cache.json file")
            with open(cache_file) as data_file:
                cache = json.load(data_file)
            # copy to Settings
            saveCacheSettings(cache)
            printDbg("...saved to Settings")
            # and delete old file
            os.remove(cache_file)
            printDbg("old cache.json file deleted")   
        
    except Exception as e:
        if e.args is not None:
            printDbg(e.args[0])
        
        
        
def checkRPCstring(urlstring, action_msg="Resetting default credentials"):
    try:
        if urlsplit(urlstring).netloc != urlstring[7:]:
            raise
        return True
    
    except:
        error_msg = "Unable to parse URL"
        printException(getCallerName(), getFunctionName(), action_msg, [error_msg])
        return False
        


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
    import simplejson as json
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
                new_mn['isHardware'] = False
                collateral = {}
                collateral['txid'] = configs[3]
                collateral['txidn'] = int(configs[4])
                new_mn['collateral'] = collateral
                
                hot_masternodes.append(new_mn)
        
        return hot_masternodes
                
    except Exception as e:
        errorMsg = "error loading MN file"
        printException(getCallerName(), getFunctionName(), errorMsg, e.args)
      
      
    
    
    
def now():
    return int(time.time())



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
    
    
    
def readMNfile():
    try:
        import simplejson as json
        mn_file = os.path.join(user_dir, masternodes_File)
        if os.path.exists(mn_file):
            with open(mn_file) as data_file:
                mnList = json.load(data_file)    
   
        else:
            # save default config (empty list) and return it
            resetMNfile()
        
    except Exception as e:
        if e.args is not None:
            printDbg(e.args[0])
        resetMNfile()
        return []
    
    # Fix missing data
    newKeys = False
    for key in DEFAULT_MN_CONF:
        for node in mnList:
            if key not in node:
                node[key] = DEFAULT_MN_CONF[key]
                newKeys = True   
    if newKeys:
        writeToFile(mnList, masternodes_File)
        
    return mnList



def resetMNfile():
    printDbg("Creating empty masternodes.json")
    writeToFile([], masternodes_File)
    
    
    
def saveLocalRPCSettings(ip, port, user, password):
    settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
    settings.setValue('local_RPC_ip', ip)
    settings.setValue('local_RPC_port', port)
    settings.setValue('local_RPC_user', user)
    settings.setValue('local_RPC_pass', password)
    


def saveLocalRPCSettingsConf(conf):
    saveLocalRPCSettings(conf.get('rpc_ip'), conf.get('rpc_port'), conf.get('rpc_user'), conf.get('rpc_password'))
    
    

def saveCacheSettings(cache):
    import simplejson as json
    settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
    settings.setValue('cache_lastAddress', cache.get('lastAddress'))
    settings.setValue('cache_winWidth', cache.get('window_width'))
    settings.setValue('cache_winHeight', cache.get('window_height'))
    settings.setValue('cache_splitterX', cache.get('splitter_sizes')[0])
    settings.setValue('cache_splitterY', cache.get('splitter_sizes')[1])
    settings.setValue('cache_mnOrder', json.dumps(cache.get('mnList_order')))
    settings.setValue('cache_consoleHidden', cache.get('console_hidden'))   
    settings.setValue('cache_useSwiftX', cache.get('useSwiftX'))
    settings.setValue('cache_votingMNs', json.dumps(cache.get('votingMasternodes')))
    settings.setValue('cache_vdCheck', cache.get('votingDelayCheck'))
    settings.setValue('cache_vdNeg', cache.get('votingDelayNeg'))
    settings.setValue('cache_vdPos', cache.get('votingDelayPos'))

    
    
    
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



def writeToFile(data, filename):
    try:
        import simplejson as json
        datafile_name = os.path.join(user_dir, filename)
        with open(datafile_name, 'w+') as data_file:
            json.dump(data, data_file)        

    except Exception as e:
        errorMsg = "error writing file %s" % filename
        printException(getCallerName(), getFunctionName(), errorMsg, e.args)
    
    
    
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
