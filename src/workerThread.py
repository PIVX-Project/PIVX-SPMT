#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Bertrand256
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

"""
            Based on project:
            https://github.com/Bertrand256/dash-masternode-tool
"""
from PyQt5.QtCore import QThread

from misc import printError

class CtrlObject(object):
    pass

class WorkerThread(QThread):
    """
    Helper class for running function inside a thread.
    """

    def __init__(self, worker_fun, worker_fun_args):
        QThread.__init__(self)
        self.worker_fun = worker_fun
        self.worker_fun_args = worker_fun_args
        # prepare control object passed to external thread function
        self.ctrl_obj = CtrlObject()
        self.ctrl_obj.finish = False
        self.worker_result = None
        self.worker_exception = None

    def stop(self):
        """
        Sets information in control object that thread should finish its work as soon as possible.
        Finish attribute should be checked by a thread periodically.
        """
        self.ctrl_obj.finish = True

    def run(self):
        try:
            self.worker_result = self.worker_fun(self.ctrl_obj, *self.worker_fun_args)
        except Exception as e:
            printError("worker thread", "run", str(e))
            self.stop()
