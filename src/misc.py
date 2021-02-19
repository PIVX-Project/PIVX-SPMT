#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import logging
import os
import sys
import time
from contextlib import redirect_stdout
from ipaddress import ip_address
from urllib.parse import urlparse

import simplejson as json
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from PyQt5.QtWidgets import QMessageBox

from constants import user_dir, log_File, DEFAULT_MN_CONF, DefaultCache, wqueue, MAX_INPUTS_NO_WARNING

QT_MESSAGE_TYPE = {
    "info": QMessageBox.Information,
    "warn": QMessageBox.Warning,
    "crit": QMessageBox.Critical,
    "quest": QMessageBox.Question
}


def add_defaultKeys_to_dict(dictObj, defaultObj):
    for key in defaultObj:
        if key not in dictObj:
            dictObj[key] = defaultObj[key]


def appendMasternode(mainWnd, mn):
    printDbg("saving MN configuration for %s" % mn['name'])

    # If we are changing a MN, remove previous entry:
    if mainWnd.mnode_to_change is not None:
        # remove from cache and QListWidget only
        removeMNfromList(mainWnd, mainWnd.mnode_to_change, removeFromDB=False)

    # Append new mn to list
    mainWnd.masternode_list.append(mn)

    # Save/edit DB
    mainWnd.parent.db.addMasternode(mn, mainWnd.mnode_to_change)
    mainWnd.mnode_to_change = None

    # update list in rewards tab
    mainWnd.t_rewards.onChangedMNlist()

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
            raise Exception("Wrong protocol. Set either http or https.")
        if o.netloc is None or o.netloc == '':
            raise Exception("Malformed host network location part.")
        if o.port is None or o.port == '':
            raise Exception("Wrong IP port number")
        if o.username is None:
            raise Exception("Malformed username")
        if o.password is None:
            raise Exception("Malformed password")
        return True

    except Exception as e:
        error_msg = "Unable to parse URL"
        printException(getCallerName(), getFunctionName(), error_msg, e)
        return False


def checkTxInputs(parentWindow, num_of_inputs):
    if num_of_inputs == 0:
        myPopUp_sb(parentWindow, "warn", 'Transaction NOT sent', "No UTXO to send")
        return None

    if num_of_inputs > MAX_INPUTS_NO_WARNING:
        warning = "Warning: Trying to spend %d inputs.\nA few minutes could be required " \
                  "for the transaction to be prepared and signed.\n\nThe hardware device must remain unlocked " \
                  "during the whole time (it's advised to disable the auto-lock feature)\n\n" \
                  "Do you wish to proceed?" % num_of_inputs
        title = "SPMT - spending more than %d inputs" % MAX_INPUTS_NO_WARNING
        return myPopUp(parentWindow, "warn", title, warning)

    return QMessageBox.Yes


def clean_v4_migration(wnd):
    rpc_file = os.path.join(user_dir, 'rpcServer.json')
    cache_file = os.path.join(user_dir, 'cache.json')
    mn_file = os.path.join(user_dir, 'masternodes.json')
    log_file = os.path.join(user_dir, 'lastLogs.html')

    messTitle = "Clean migration to v0.4.0 data storage"

    if os.path.exists(rpc_file) or os.path.exists(cache_file) or os.path.exists(mn_file):
        printDbg(messTitle)

    if os.path.exists(rpc_file):
        # If RPC file exists
        try:
            with open(rpc_file) as data_file:
                rpc_config = json.load(data_file)
            # copy to database
            rpc_host = "%s:%d" % (rpc_config['rpc_ip'], rpc_config['rpc_port'])
            wnd.db.editRPCServer("http", rpc_host, rpc_config['rpc_user'], rpc_config['rpc_password'], 0)
            printDbg("...saved to Database")
            # and delete old file
            os.remove(rpc_file)
            printDbg("old rpcServer.json file deleted")
        except Exception as e:
            mess = "Error importing old rpc_config file"
            printException(getCallerName(), getFunctionName(), mess, e)

    if os.path.exists(cache_file):
        # If cache file exists, delete it
        try:
            os.remove(cache_file)
            printDbg("old cache.json file deleted")
        except Exception as e:
            mess = "Error deleting old cache file"
            printException(getCallerName(), getFunctionName(), mess, e)

    if os.path.exists(mn_file):
        # If mn file exists
        try:
            with open(mn_file) as data_file:
                mnList = json.load(data_file)
            # add to database
            for mn in mnList:
                wnd.db.addMasternode(mn)
            printDbg("...saved to Database")
            # and delete old file
            os.remove(mn_file)
            printDbg("old masternodes.json file deleted")
        except Exception as e:
            mess = "Error importing old masternodes_config file"
            printException(getCallerName(), getFunctionName(), mess, e)

    # Remove old logs
    if os.path.exists(log_file):
        os.remove(log_file)
        printDbg("old lastLogs.html file deleted")


def clean_for_html(text):
    if text is None:
        return ""
    return text.replace("<", "{").replace(">", "}")


def clear_screen():
    os.system('clear')


def getCallerName(inDecorator=False):
    try:
        if inDecorator:
            return sys._getframe(3).f_code.co_name
        return sys._getframe(2).f_code.co_name
    except Exception:
        return None


def getFunctionName(inDecorator=False):
    try:
        if inDecorator:
            return sys._getframe(2).f_code.co_name
        return sys._getframe(1).f_code.co_name
    except Exception:
        return None


def getRemoteSPMTversion():
    import requests
    try:
        resp = requests.get("https://raw.githubusercontent.com/PIVX-Project/PIVX-SPMT/master/src/version.txt")
        if resp.status_code == 200:
            data = resp.json()
            return data['number']
        else:
            raise Exception

    except Exception:
        redirect_print("Invalid response getting version from GitHub\n")
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


def initLogs():
    filename = log_File
    filemode = 'w'
    format = '%(asctime)s - %(levelname)s - %(threadName)s | %(message)s'
    level = logging.DEBUG
    logging.basicConfig(filename=filename,
                        filemode=filemode,
                        format=format,
                        level=level
                        )


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


def myPopUp(parentWindow, messType, messTitle, messText, defaultButton=QMessageBox.No):
    if messType in QT_MESSAGE_TYPE:
        type = QT_MESSAGE_TYPE[messType]
    else:
        type = QMessageBox.Question
    mess = QMessageBox(type, messTitle, messText, defaultButton, parent=parentWindow)
    mess.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    mess.setDefaultButton(defaultButton)
    return mess.exec_()


def myPopUp_sb(parentWindow, messType, messTitle, messText, singleButton=QMessageBox.Ok):
    if messType in QT_MESSAGE_TYPE:
        type = QT_MESSAGE_TYPE[messType]
    else:
        type = QMessageBox.Information
    mess = QMessageBox(type, messTitle, messText, singleButton, parent=parentWindow)
    mess.setStandardButtons(singleButton | singleButton)
    return mess.exec_()


def now():
    return int(time.time())


def persistCacheSetting(cache_key, cache_value):
    settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
    if not settings.contains(cache_key):
        printDbg("Cache key %s not found" % str(cache_key))
        printOK("Adding new cache key to settings...")

    if type(cache_value) in [list, dict]:
        settings.setValue(cache_key, json.dumps(cache_value))
    else:
        settings.setValue(cache_key, cache_value)

    return cache_value


def printDbg(what):
    logging.info(what)
    log_line = printDbg_msg(what)
    redirect_print(log_line)


def printDbg_msg(what):
    what = clean_for_html(what)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(now()))
    log_line = '<b style="color: yellow">{}</b> : {}<br>'.format(timestamp, what)
    return log_line


def printError(
        caller_name,
        function_name,
        what
):
    logging.error("%s | %s | %s" % (caller_name, function_name, what))
    log_line = printException_msg(caller_name, function_name, what, None, True)
    redirect_print(log_line)


def printException(
        caller_name,
        function_name,
        err_msg,
        errargs=None
):
    what = err_msg
    if errargs is not None:
        what += " ==> %s" % str(errargs)
    logging.warning("%s | %s | %s" % (caller_name, function_name, what))
    text = printException_msg(caller_name, function_name, err_msg, errargs)
    redirect_print(text)


def printException_msg(
        caller_name,
        function_name,
        err_msg,
        errargs=None,
        is_error=False
):
    if is_error:
        msg = '<b style="color: red">ERROR</b><br>'
    else:
        msg = '<b style="color: red">EXCEPTION</b><br>'
    msg += '<span style="color:white">caller</span>   : %s<br>' % caller_name
    msg += '<span style="color:white">function</span> : %s<br>' % function_name
    msg += '<span style="color:red">'
    if errargs:
        msg += 'err: %s<br>' % str(errargs)

    msg += '===> %s</span><br>' % err_msg
    return msg


def printOK(what):
    logging.debug(what)
    msg = '<b style="color: #cc33ff">===> ' + what + '</b><br>'
    redirect_print(msg)


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
        cache["votingMasternodes"] = json.loads(settings.value('cache_votingMNs', json.dumps(DefaultCache["votingMasternodes"]), type=str))
        cache["votingDelayCheck"] = settings.value('cache_vdCheck', DefaultCache["votingDelayCheck"], type=bool)
        cache["votingDelayNeg"] = settings.value('cache_vdNeg', DefaultCache["votingDelayNeg"], type=int)
        cache["votingDelayPos"] = settings.value('cache_vdPos', DefaultCache["votingDelayPos"], type=int)
        cache["selectedHW_index"] = settings.value('cache_HWindex', DefaultCache["selectedHW_index"], type=int)
        cache["selectedRPC_index"] = settings.value('cache_RPCindex', DefaultCache["selectedRPC_index"], type=int)
        cache["MN_count"] = settings.value('cache_MNcount', DefaultCache["MN_count"], type=int)
        cache["isTestnetRPC"] = settings.value('cache_isTestnetRPC', DefaultCache["isTestnetRPC"], type=bool)
        add_defaultKeys_to_dict(cache, DefaultCache)
        return cache
    except:
        return DefaultCache


def redirect_print(what):
    with redirect_stdout(WriteStream(wqueue)):
        print(what)


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


def saveCacheSettings(cache):
    settings = QSettings('PIVX', 'SecurePivxMasternodeTool')
    settings.setValue('cache_lastAddress', cache.get('lastAddress'))
    settings.setValue('cache_vdCheck', cache.get('votingDelayCheck'))
    settings.setValue('cache_vdNeg', cache.get('votingDelayNeg'))
    settings.setValue('cache_vdPos', cache.get('votingDelayPos'))
    settings.setValue('cache_winWidth', cache.get('window_width'))
    settings.setValue('cache_winHeight', cache.get('window_height'))
    settings.setValue('cache_splitterX', cache.get('splitter_x'))
    settings.setValue('cache_splitterY', cache.get('splitter_y'))
    settings.setValue('cache_mnOrder', json.dumps(cache.get('mnList_order')))
    settings.setValue('cache_consoleHidden', cache.get('console_hidden'))
    settings.setValue('cache_votingMNs', json.dumps(cache.get('votingMasternodes')))
    settings.setValue('cache_HWindex', cache.get('selectedHW_index'))
    settings.setValue('cache_RPCindex', cache.get('selectedRPC_index'))
    settings.setValue('cache_MNcount', cache.get('MN_count'))
    settings.setValue('cache_isTestnetRPC', cache.get('isTestnetRPC'))


def sec_to_time(seconds):
    days = seconds // 86400
    seconds -= days * 86400
    hrs = seconds // 3600
    seconds -= hrs * 3600
    mins = seconds // 60
    seconds -= mins * 60
    return "{} days, {} hrs, {} mins, {} secs".format(days, hrs, mins, seconds)


def splitString(text, n):
    arr = [text[i:i + n] for i in range(0, len(text), n)]
    return '\n'.join(arr)


def timeThis(function, *args):
    try:
        start = time.clock()
        val = function(*args)
        end = time.clock()
        return val, (end - start)
    except Exception:
        return None, None


def updateSplash(label, i):
    if i == 10:
        progressText = "Loading configuration data..."
        label.setText(progressText)
    elif i == 40:
        progressText = "Opening database..."
        label.setText(progressText)
    elif i == 50:
        progressText = "Creating user interface..."
        label.setText(progressText)
    elif i == 70:
        progressText = "Releasing the watchdogs..."
        label.setText(progressText)
    elif i == 90:
        progressText = "SPMT ready"
        label.setText(progressText)
    elif i == 99:
        time.sleep(0.1)


class DisconnectedException(Exception):
    def __init__(self, message, hwDevice):
        # Call the base class constructor
        super().__init__(message)
        # clear device
        hwDevice.closeDevice(message)


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
