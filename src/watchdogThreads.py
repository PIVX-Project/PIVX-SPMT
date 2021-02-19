#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017 chaeplin
# Copyright (c) 2017 Bertrand256
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from time import sleep
from threading import Event

from PyQt5.Qt import QObject

from misc import printOK


class CtrlObject(object):
    pass


class RpcWatchdog(QObject):
    def __init__(self, control_tab, timer_off=10, timer_on=120, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.firstLoop  = True
        self.shutdown_flag = Event()
        self.control_tab = control_tab
        self.timer_off = timer_off      #delay when not connected
        self.timer_on = timer_on        #delay when connected
        self.ctrl_obj = CtrlObject()
        self.ctrl_obj.finish = False

    def run(self):
        while not self.shutdown_flag.is_set():
            # update status without printing on debug
            self.control_tab.updateRPCstatus(self.ctrl_obj, False)
            with self.control_tab.lock:
                connected = self.control_tab.rpcConnected

            if not connected:
                sleep(self.timer_off)
            else:
                sleep(self.timer_on)

        printOK("Exiting Rpc Watchdog Thread")
