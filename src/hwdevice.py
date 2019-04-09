#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.Qt import QObject
from PyQt5.QtCore import pyqtSignal

from constants import HW_devices
from ledgerClient import LedgerApi
from misc import printOK
from trezorClient import TrezorApi

class HWdevice(QObject):
    # signal: sig1 (thread) is done - emitted by signMessageFinish
    sig1done = pyqtSignal(str)
    # signal: sig_disconnected -emitted with DisconnectedException
    sig_disconnected = pyqtSignal(str)

    def __init__(self, main_wnd, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.main_wnd = main_wnd
        self.status = 0

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
        self.sig_disconnected = self.api.sig_disconnected
        self.sig_disconnected.connect(self.main_wnd.clearHWstatus)



    def clearDevice(self, message=''):
        self.status = 0
        self.api.clearDevice(message)



    def getStatus(self):
        return self.api.getStatus()



    def prepare_transfer_tx(self, caller, bip32_path,  utxos_to_spend, dest_address, tx_fee, useSwiftX=False, isTestnet=False):
        self.api.prepare_transfer_tx(caller, bip32_path,  utxos_to_spend, dest_address, tx_fee, useSwiftX, isTestnet)



    def prepare_transfer_tx_bulk(self, caller, rewardsArray, dest_address, tx_fee, useSwiftX=False, isTestnet=False):
        self.api.prepare_transfer_tx_bulk(caller, rewardsArray, dest_address, tx_fee, useSwiftX, isTestnet)



    def scanForAddress(self, account, spath, isTestnet=False):
        printOK("Scanning for Address n. %d on account n. %d" % (spath, account))
        return self.api.scanForAddress(account, spath, isTestnet)



    def scanForBip32(self, account, address, starting_spath=0, spath_count=10, isTestnet=False):
        printOK("Scanning for Bip32 path of address: %s" % address)
        return self.api.scanForBip32(account, address, starting_spath, spath_count, isTestnet)



    def scanForPubKey(self, account, spath, isTestnet=False):
        printOK("Scanning for PubKey of address n. %d on account n. %d" % (spath, account))
        return self.api.scanForPubKey(account, spath, isTestnet)



    def signMess(self, caller, path, message, isTestnet=False):
        self.api.signMess(caller, path, message, isTestnet)



    def signTxSign(self, ctrl):
        self.api.signTxSign(ctrl)



    def signTxFinish(self):
        self.api.signTxFinish()

