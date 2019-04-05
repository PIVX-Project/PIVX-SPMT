#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

MPATH_LEDGER = "44'/77'/"
MPATH_TREZOR = "44'/119'/"
MPATH_TESTNET = "44'/1'/"
WIF_PREFIX = 212 # 212 = d4
MAGIC_BYTE = 30
TESTNET_WIF_PREFIX = 239
TESTNET_MAGIC_BYTE = 139
DEFAULT_PROTOCOL_VERSION = 70915
MINIMUM_FEE = 0.0001    # minimum PIV/kB
starting_width = 933
starting_height = 666
APPDATA_DIRNAME = ".SecurePivxMasternodeTool"
home_dir = os.path.expanduser('~')
user_dir = os.path.join(home_dir, APPDATA_DIRNAME)
log_File = os.path.join(user_dir, 'lastLogs.html')
database_File = os.path.join(user_dir, 'application.db')


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

DefaultCache = {
    "lastAddress": "",
    "window_width": starting_width,
    "window_height": starting_height,
    "splitter_x": 342,
    "splitter_y": 133,
    "mnList_order": {},
    "console_hidden": False,
    "useSwiftX": False,
    "votingMasternodes": [],
    "votingDelayCheck": False,
    "votingDelayNeg": 0,
    "votingDelayPos": 300,
    "selectedHW_index": 0,
    "selectedRPC_index": 0,
    "MN_count": 1
    }


trusted_RPC_Servers = [
    ["https", "amsterdam.randomzebra.party:8080", "spmtUser_ams", "WUss6sr8956S5Paex254"],
    ["https", "losangeles.randomzebra.party:8080", "spmtUser_la", "8X88u7TuefPm7mQaJY52"],
    ["https", "singapore.randomzebra.party:8080", "spmtUser_sing", "ZyD936tm9dvqmMP8A777"]]


HW_devices = [
    "LEDGER Nano S",
    "TREZOR Model T"
]
