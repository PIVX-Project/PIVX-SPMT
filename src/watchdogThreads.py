#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from time import sleep
from threading import Event

from PyQt5.Qt import QApplication, QObject

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
            self.control_tab.updateRPCstatus(self.ctrl_obj, self.firstLoop)
            
            if not self.control_tab.rpcConnected:
                sleep(self.timer_off)
            else:
                # first time we get connection reload UTXOs and Proposals
                if not self.control_tab.t_rewards.utxoLoaded:
                    self.control_tab.t_rewards.load_utxos_thread(None)

                if not self.control_tab.t_governance.proposalsLoaded:
                    self.control_tab.t_governance.loadProposals_thread(None)
                    
                sleep(self.timer_on)
                
            if self.firstLoop:
                self.firstLoop = False
            
        printOK("Exiting Rpc Watchdog Thread")
        
        
            
            
