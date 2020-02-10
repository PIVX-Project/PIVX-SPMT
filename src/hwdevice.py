#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import logging

from PyQt5.QtCore import QObject, pyqtSignal

from constants import HW_devices
from ledgerClient import LedgerApi
from misc import printOK, printDbg
from time import sleep
from trezorClient import TrezorApi


def check_api_init(func):
    def func_int(*args, **kwargs):
        hwDevice = args[0]
        if hwDevice.api is None:
            logging.warning("%s: hwDevice.api is None" % func.__name__)
            raise Exception("HW device: client not initialized")
        return func(*args, **kwargs)

    return func_int



class HWdevice(QObject):
    # signal: sig1 (thread) is done - emitted by signMessageFinish
    sig1done = pyqtSignal(str)

    def __init__(self, main_wnd, *args, **kwargs):
        printDbg("HW: Initializing Class...")
        QObject.__init__(self, *args, **kwargs)
        self.main_wnd = main_wnd
        self.api = None
        printOK("HW: Class initialized")


    def initDevice(self, hw_index):
        printDbg("HW: initializing hw device with index %d" % hw_index)
        if hw_index >= len(HW_devices):
            raise Exception("Invalid HW index")

        # Select API
        api_index = HW_devices[hw_index][1]
        if api_index == 0:
            self.api = LedgerApi(self.main_wnd)
        else:
            self.api = TrezorApi(hw_index, self.main_wnd)

        # Init device & connect signals
        self.api.initDevice()
        self.sig1done = self.api.sig1done
        self.api.sig_disconnected.connect(self.main_wnd.clearHWstatus)
        printOK("HW: hw device with index %d initialized" % hw_index)


    @check_api_init
    def clearDevice(self):
        printDbg("HW: Clearing HW device...")
        self.api.closeDevice('')
        printOK("HW: device cleared")


    # Status codes:
    # 0 - not connected
    # 1 - not initialized
    # 2 - fine
    @check_api_init
    def getStatus(self):
        printDbg("HW: checking device status...")
        printOK("Status: %d" % self.api.status)
        return self.api.model, self.api.status, self.api.messages[self.api.status]


    def prepare_transfer_tx(self, caller, bip32_path,  utxos_to_spend, dest_address, tx_fee, useSwiftX=False, isTestnet=False):
        rewardsArray = []
        mnode = {}
        mnode['path'] = bip32_path
        mnode['utxos'] = utxos_to_spend
        rewardsArray.append(mnode)
        self.prepare_transfer_tx_bulk(caller, rewardsArray, dest_address, tx_fee, useSwiftX, isTestnet)


    @check_api_init
    def prepare_transfer_tx_bulk(self, caller, rewardsArray, dest_address, tx_fee, useSwiftX=False, isTestnet=False):
        printDbg("HW: Preparing transfer TX")
        self.api.prepare_transfer_tx_bulk(caller, rewardsArray, dest_address, tx_fee, useSwiftX, isTestnet)


    @check_api_init
    def scanForAddress(self, account, spath, isTestnet=False):
        printOK("HW: Scanning for Address n. %d on account n. %d" % (spath, account))
        return self.api.scanForAddress(account, spath, isTestnet)


    @check_api_init
    def scanForBip32(self, account, address, starting_spath=0, spath_count=10, isTestnet=False):
        printOK("HW: Scanning for Bip32 path of address: %s" % address)
        found = False
        spath = -1

        for i in range(starting_spath, starting_spath + spath_count):
            printDbg("HW: checking path... %d'/0/%d" % (account, i))
            curr_addr = self.api.scanForAddress(account, i, isTestnet)

            if curr_addr == address:
                found = True
                spath = i
                break

            sleep(0.01)

        return (found, spath)


    @check_api_init
    def scanForPubKey(self, account, spath, isTestnet=False):
        printOK("HW: Scanning for PubKey of address n. %d on account n. %d" % (spath, account))
        return self.api.scanForPubKey(account, spath, isTestnet)


    @check_api_init
    def signMess(self, caller, path, message, isTestnet=False):
        printDbg("HW: Signing message...")
        self.api.signMess(caller, path, message, isTestnet)
        printOK("HW: Message signed")
