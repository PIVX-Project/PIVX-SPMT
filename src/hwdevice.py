#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    # signal: sig_disconnected -emitted with DisconnectedException
    sig_disconnected = pyqtSignal(str)

    def __init__(self, main_wnd, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.main_wnd = main_wnd
        self.api = None


    def initDevice(self, hw_index):
        if hw_index >= len(HW_devices):
            raise Exception("Invalid HW index")

        # Select API
        if hw_index == 0:
            self.api = LedgerApi()
        else:
            self.api = TrezorApi()

        # Init device & connect signals
        self.api.initDevice()
        self.sig1done = self.api.sig1done
        self.sig_disconnected.connect(self.main_wnd.clearHWstatus)


    @check_api_init
    def clearDevice(self, message=''):
        printDbg("Clearing HW device...")
        self.api.closeDevice()
        self.sig_disconnected.emit(message)


    # Status codes:
    # 0 - not connected
    # 1 - not initialized
    # 2 - fine
    @check_api_init
    def getStatus(self):
        messages = self.api.messages
        return self.api.model, self.api.status, messages[self.api.status]


    def prepare_transfer_tx(self, caller, bip32_path,  utxos_to_spend, dest_address, tx_fee, useSwiftX=False, isTestnet=False):
        rewardsArray = []
        mnode = {}
        mnode['path'] = bip32_path
        mnode['utxos'] = utxos_to_spend
        rewardsArray.append(mnode)
        self.prepare_transfer_tx_bulk(caller, rewardsArray, dest_address, tx_fee, useSwiftX, isTestnet)


    @check_api_init
    def prepare_transfer_tx_bulk(self, caller, rewardsArray, dest_address, tx_fee, useSwiftX=False, isTestnet=False):
        self.api.prepare_transfer_tx_bulk(caller, rewardsArray, dest_address, tx_fee, useSwiftX, isTestnet)


    @check_api_init
    def scanForAddress(self, account, spath, isTestnet=False):
        printOK("Scanning for Address n. %d on account n. %d" % (spath, account))
        return self.api.scanForAddress(account, spath, isTestnet)


    @check_api_init
    def scanForBip32(self, account, address, starting_spath=0, spath_count=10, isTestnet=False):
        printOK("Scanning for Bip32 path of address: %s" % address)
        found = False
        spath = -1

        for i in range(starting_spath, starting_spath + spath_count):
            printDbg("checking path... %d'/0/%d" % (account, i))
            curr_addr = self.api.scanForAddress(account, i, isTestnet)

            if curr_addr == address:
                found = True
                spath = i
                break

            sleep(0.01)

        return (found, spath)


    @check_api_init
    def scanForPubKey(self, account, spath, isTestnet=False):
        printOK("Scanning for PubKey of address n. %d on account n. %d" % (spath, account))
        return self.api.scanForPubKey(account, spath, isTestnet)


    @check_api_init
    def signMess(self, caller, path, message, isTestnet=False):
        self.api.signMess(caller, path, message, isTestnet)


    @check_api_init
    def signTxSign(self, ctrl):
        self.api.signTxSign(ctrl)


    @check_api_init
    def signTxFinish(self):
        self.api.signTxFinish()
