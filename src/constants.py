#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

MPATH = "44'/77'/"
WIF_PREFIX = 212 # 212 = d4
MAGIC_BYTE = 30
TESTNET_WIF_PREFIX = 239
TESTNET_MAGIC_BYTE = 139
DEFAULT_PROTOCOL_VERSION = 70913
MINIMUM_FEE = 0.0001    # minimum PIV/kB
starting_width = 933
starting_height = 666
APPDATA_DIRNAME = ".SecurePivxMasternodeTool"
home_dir = os.path.expanduser('~')
user_dir = os.path.join(home_dir, APPDATA_DIRNAME)
log_File = os.path.join(user_dir, 'lastLogs.html')
database_file = os.path.join(user_dir, 'data.db')
masternodes_File = 'masternodes.json'

DEFAULT_MN_CONF = {
    "name": "",
    "ip": "",
    "port": 51472,
    "mnPrivKey": "",
    "isTestnet": 0,
    "isHardware": True,
    "hwAcc": 0,
    "collateral": {}
    }

class DefaultCache():
    def __init__(self):
        self.lastAddress = ""
        self.winWidth = starting_width
        self.winHeight = starting_height
        self.useSwiftX = False
        self.consoleHidden = False
        self.splitterX = 342
        self.splitterY = 133
        self.mnOrder = {}
        self.votingMNs = []
        self.vdCheck = False
        self.vdNeg = 0
        self.vdPos = 300
        

class DefaultRPCConf():
    def __init__(self):
        self.ip = '127.0.0.1'
        self.port = 51473
        self.user = 'myUsername'
        self.password = 'myPassword'
        