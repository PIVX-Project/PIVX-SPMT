from time import sleep
from PyQt5.Qt import QApplication, QObject
from misc import printOK
from threading import Event

class CtrlObject(object):
    pass

class RpcWatchdog(QObject):
    def __init__(self, control_tab, timer_off=3, timer_on=7, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.shutdown_flag = Event()
        self.control_tab = control_tab
        self.timer_off = timer_off  #delay when not connected
        self.timer_on = timer_on    #delay when connected
        self.ctrl_obj = CtrlObject()
        self.ctrl_obj.finish = False
        
     
    def run(self):    
        while not self.shutdown_flag.is_set():
            self.control_tab.updateRPCstatus(self.ctrl_obj)
            QApplication.processEvents()
            self.control_tab.updateRPCled()
            
            if not self.control_tab.rpcConnected:
                sleep(self.timer_off)
            else:
                sleep(self.timer_on)
            
        printOK("Exiting Rpc Watchdog Thread")
            
            
