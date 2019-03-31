#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading

from PyQt5.Qt import QObject
from PyQt5.QtCore import pyqtSignal

from trezorlib import btc
from trezorlib.client import TrezorClient
from trezorlib.transport import get_transport
from trezorlib.ui import ClickUI

from misc import getCallerName, getFunctionName, printException, printDbg, \
    DisconnectedException, printOK


def  process_trezor_exceptions(func):
    def process_trezor_exceptions_int(*args, **kwargs):
        hwDevice = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_mess = "Trezor Exception"
            printException(getCallerName(True), getFunctionName(True), err_mess, e.args)
            raise DisconnectedException(err_mess, hwDevice, e.args[0])

    return process_trezor_exceptions_int


class TrezorApi(QObject):
    # signal: sig1 (thread) is done - emitted by signMessageFinish
    sig1done = pyqtSignal(str)
    # signal: sigtx (thread) is done - emitted by signTxFinish
    sigTxdone = pyqtSignal(bytearray, str)
    # signal: sigtx (thread) is done (aborted) - emitted by signTxFinish
    sigTxabort = pyqtSignal()
    # signal: tx_progress percent - emitted by perepare_transfer_tx_bulk
    tx_progress = pyqtSignal(int)
    # signal: sig_progress percent - emitted by signTxSign
    sig_progress = pyqtSignal(int)
    # signal: sig_disconnected -emitted with DisconnectedException
    sig_disconnected = pyqtSignal(str)


    def __init__(self, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        # Device Lock for threads
        self.lock = threading.RLock()
        self.status = 0
        self.client = None
        printDbg("Creating HW device class")
        # Connect signal
        #self.sig_progress.connect(self.updateSigProgress)


    @process_trezor_exceptions
    def initDevice(self):
        print("Initializing Trezor")
        with self.lock:
            transport = get_transport()
            ui = ClickUI()
            printOK('Trezor drivers found')
            self.status = 1
            self.client = TrezorClient(transport, ui)
            printOK("Trezor HW device connected [v. %s.%s.%s]" % (
                self.client.features.major_version,
                self.client.features.minor_version,
                self.client.features.patch_version)
            )
            self.status = 2



    def clearDevice(self, message=''):
        self.status = 1
        if self.client is not None:
            self.client.close()
            self.client = None


    # Status codes:
    # 0 - not connected
    # 1 - not initialized
    # 2 - fine
    def getStatus(self):
        messages = {
            0: 'Trezor not initialized. Coonect and unlock it',
            1: 'Error setting up Trezor Client',
            2: 'Hardware device connected.'}
        return self.status, messages[self.status]
