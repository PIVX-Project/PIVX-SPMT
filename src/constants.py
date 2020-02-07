#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import os
from queue import Queue

wqueue = Queue()

MPATH_LEDGER = "44'/77'/"
MPATH_TREZOR = "44'/119'/"
MPATH_TESTNET = "44'/1'/"
WIF_PREFIX = 212 # 212 = d4
MAGIC_BYTE = 30
STAKE_MAGIC_BYTE = 63
TESTNET_WIF_PREFIX = 239
TESTNET_MAGIC_BYTE = 139
TESTNET_STAKE_MAGIC_BYTE = 73
DEFAULT_PROTOCOL_VERSION = 70915
MINIMUM_FEE = 0.0001    # minimum PIV/kB
starting_width = 933
starting_height = 666
APPDATA_DIRNAME = ".SecurePivxMasternodeTool"
home_dir = os.path.expanduser('~')
user_dir = os.path.join(home_dir, APPDATA_DIRNAME)
log_File = os.path.join(user_dir, 'debug.log')
database_File = os.path.join(user_dir, 'application.db')
NEW_SIGS_HEIGHT_MAINNET = 2153200
NEW_SIGS_HEIGHT_TESTNET = 1347000
SECONDS_IN_2_MONTHS = 60 * 24 * 60 * 60
MAX_INPUTS_NO_WARNING = 75

def NewSigsActive(nHeight, fTestnet=False):
    if fTestnet:
        return (nHeight >= NEW_SIGS_HEIGHT_TESTNET)
    return (nHeight >= NEW_SIGS_HEIGHT_MAINNET)

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
    "MN_count": 1,
    "isTestnetRPC": False
    }


trusted_RPC_Servers = [
    ["https", "amsterdam.randomzebra.party:8080", "spmtUser_ams", "WUss6sr8956S5Paex254"],
    ["https", "losangeles.randomzebra.party:8080", "spmtUser_la", "8X88u7TuefPm7mQaJY52"],
    ["https", "singapore.randomzebra.party:8080", "spmtUser_sing", "ZyD936tm9dvqmMP8A777"]]


HW_devices = [
    # (model name, api index)
    ("LEDGER Nano", 0),
    ("TREZOR One", 1),
    ("TREZOR Model T", 1)
]
