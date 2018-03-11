#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import time
from PyQt5.QtCore import QObject, pyqtSignal

from constants import log_File

def clean_for_html(text):
    if text is None:
        return ""
    return text.replace("<", "{").replace(">","}")



def clear_screen():
    os.system('clear')
    


def eprint(*args, **kwargs):
    logFile = open(log_File, 'a+')
    print(*args, file=logFile, **kwargs)
    logFile.close()
    print(*args, file=sys.stderr, **kwargs)
    

    
def eprintDbg(what):
    log_line = printDbg_msg(what)
    eprint(log_line)
    

    
def eprintException(caller_name,
        function_name,
        err_msg,
        errargs=None):
    text = printException_msg(caller_name, function_name, err_msg, errargs)
    eprint(text)



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



def getSPMTVersion():
    import simplejson as json
    version_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'version.txt')
    with open(version_file) as data_file:
        data = json.load(data_file)       
    data_file.close()
    return data



def getTxidTxidn(txid, txidn):
    if txid is None or txidn is None:
        return None
    else:
        return txid + '-' + str(txidn)



def ipport(ip, port):
    if ip is None or port is None:
        return None
    else:
        return ip + ':' + port



def now():
    return int(time.time())



def printDbg_msg(what):
    what = clean_for_html(what)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(now()))
    log_line = '<b style="color: yellow">{}</b> : {}<br>'.format(timestamp, what)
    return log_line



def printDbg(what):
    log_line = printDbg_msg(what)
    logFile = open(log_File, 'a+')
    logFile.write(log_line)
    logFile.close()
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
    logFile = open(log_File, 'a+')
    logFile.write(text)
    logFile.close()
    print(text)
    
    
    

def printOK(what):
    msg = '<b style="color: #cc33ff">===> ' + what + '</b><br>'
    logFile = open(log_File, 'a+')
    logFile.write(msg)
    logFile.close()
    print(msg)
    
  
    
def splitString(text, n):
    arr = [text[i:i+n] for i in range(0, len(text), n)]
    return '\n'.join(arr)
    
 
 
def readMNfile():
    import simplejson as json
    mn_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'masternodes.json')
    with open(mn_file) as data_file:
        mnList = json.load(data_file)    
    data_file.close()
    return mnList



def readRPCfile():
    import simplejson as json
    config_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'rpcServer.json')
    with open(config_file) as data_file:
        rpc_config = json.load(data_file)
    data_file.close()
    
    rpc_ip = rpc_config.get('rpc_ip')
    rpc_port = int(rpc_config.get('rpc_port'))
    rpc_user = rpc_config.get('rpc_user')
    rpc_password = rpc_config.get('rpc_password')
        
    return rpc_ip, rpc_port, rpc_user, rpc_password



def sec_to_time(seconds):
    days = seconds//86400
    seconds -= days*86400
    hrs = seconds//3600
    seconds -= hrs*3600
    mins = seconds//60
    seconds -= mins*60   
    return "{} days, {} hrs, {} mins, {} secs".format(days, hrs, mins, seconds)



def updateSplash(label, i):
    if i==10:
        progressText = "loading masternode conf..."
        label.setText(progressText)
    elif i==30:
        progressText = "drawing GUI..."
        label.setText(progressText)
    elif i==59:
        progressText = "releasing the watchdogs..."
        label.setText(progressText)
    elif i==89:
        progressText = "Enjoy the Purple Power!"
        label.setText(progressText)   
    elif i==99:
        time.sleep(0.4)



def writeMNfile(mnList):
    import simplejson as json
    mn_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'masternodes.json')
    with open(mn_file, 'w+') as data_file:
        json.dump(mnList, data_file)        
    data_file.close()
    

    
def writeRPCfile(configuration):
    import simplejson as json
    rpc_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'rpcServer.json')
    with open(rpc_file, 'w+') as data_file:
        json.dump(configuration, data_file)
            
    data_file.close()
    
    
    
# Stream object to redirect sys.stdout to a queue
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