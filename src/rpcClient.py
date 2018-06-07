#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from misc import getCallerName, getFunctionName, printException, printDbg, readRPCfile, now
from constants import DEFAULT_PROTOCOL_VERSION, MINIMUM_FEE
import threading

class RpcClient:
        
    def __init__(self):
        # Lock for threads
        self.lock = threading.Lock()
        self.rpc_ip, self.rpc_port, self.rpc_user, self.rpc_passwd = readRPCfile()
        rpc_url = "http://%s:%s@%s:%d" % (self.rpc_user, self.rpc_passwd, self.rpc_ip, self.rpc_port)
        try:
            self.lock.acquire()
            self.conn = AuthServiceProxy(rpc_url, timeout=120)     
        except JSONRPCException as e:
            err_msg = 'remote or local PIVX-cli running?'
            printException(getCallerName(), getFunctionName(), err_msg, e)
        except Exception as e:
            err_msg = 'remote or local PIVX-cli running?'
            printException(getCallerName(), getFunctionName(), err_msg, e)
        finally:
            self.lock.release()
    
    
    
    def decodeRawTransaction(self, rawTx):
        try:
            self.lock.acquire()
            res = self.conn.decoderawtransaction(rawTx)    
        except Exception as e:
            err_msg = 'error in decodeRawTransaction'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            res = None
        finally:
            self.lock.release()
        
        return res
    
    
    
    def getAddressUtxos(self, addresses):
        try:
            self.lock.acquire()
            res = self.conn.getaddressutxos({'addresses': addresses})    
        except Exception as e:
            err_msg = "error in getAddressUtxos"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            res = None
        finally:
            self.lock.release()
        
        return res
    
    
    
    
    def getBlockCount(self):
        try:
            self.lock.acquire()
            n = self.conn.getblockcount()
        except Exception as e:
            err_msg = 'remote or local PIVX-cli running?'
            if str(e.args[0]) != "Request-sent":
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            n = 0
        finally:
            self.lock.release()
            
        return n
    
    
    
    
    def getBlockHash(self, blockNum):
        try:
            self.lock.acquire()
            h = self.conn.getblockhash(blockNum)
        except Exception as e:
            err_msg = 'remote or local PIVX-cli running?'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            h = None
        finally:
            self.lock.release()
            
        return h
    
    
    def getFeePerKb(self):
        try:
            self.lock.acquire()
            # get transaction data from last 120 blocks
            feePerKb = float(self.conn.getfeeinfo(200)['feeperkb'])
            res = (feePerKb if feePerKb > MINIMUM_FEE else MINIMUM_FEE)
        except Exception as e:
            err_msg = 'error in getFeePerKb'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            res = MINIMUM_FEE
        finally:
            self.lock.release()
            
        return res
    
    
    
    def getMNStatus(self, address):
        try:
            self.lock.acquire()
            mnStatusList = self.conn.listmasternodes(address)
            if not mnStatusList:
                return None
            mnStatus = mnStatusList[0]
            mnStatus['mnCount'] = self.conn.getmasternodecount()['enabled']
        except Exception as e:
            err_msg = "error in getMNStatus"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            mnStatus = None
        finally:
            self.lock.release()
            
        return mnStatus
                
                
                
    def getMasternodes(self):
        mnList = {}
        mnList['last_update'] = now()
        score = []
        try:
            self.lock.acquire()
            masternodes = self.conn.listmasternodes()
        except Exception as e:
            err_msg = "error in getMasternodes"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            masternodes = []
        finally:
            self.lock.release()
        
        for mn in masternodes:
            
            if mn.get('status') == 'ENABLED':
                if mn.get('lastpaid') == 0:
                    mn['score'] = mn.get('activetime')
                else:
                    lastpaid_ago = now() - mn.get('lastpaid')
                    mn['score'] = min(lastpaid_ago, mn.get('activetime'))
                
            else:
                mn['score'] = 0
                
            score.append(mn)
        
        score.sort(key=lambda x: x['score'], reverse=True)
        
        for mn in masternodes:
            mn['queue_pos'] = score.index(mn)
                
        mnList['masternodes'] = masternodes
                
        return mnList
    
    
    
    
    def getProtocolVersion(self):
        try:
            self.lock.acquire()
            prot_version = self.conn.getinfo().get('protocolversion')
            res = int(prot_version)      
        except Exception as e:
            err_msg = 'error in getProtocolVersion'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            res = DEFAULT_PROTOCOL_VERSION
        finally:
            self.lock.release()
        
        return res    
     
            
    
    
    def getRawTransaction(self, txid):
        try:
            self.lock.acquire()
            res = self.conn.getrawtransaction(txid)
        except Exception as e:
            err_msg = "is Blockchain synced?"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            res = None
        finally:
            self.lock.release()
            
        return res
    
    
    
    
    def getStatus(self):
        status = False
        statusMess = "Unable to connect to a PIVX RPC server.\n" 
        statusMess += "Either the local PIVX wallet is not open, or the remote RPC server is not responding."
        n = 0
        try:
            self.lock.acquire()
            n = self.conn.getblockcount()
            if n > 0:
                status = True
                statusMess = "Connected to PIVX RPC client"
                
        except Exception as e:
            # If loading block index set lastBlock=1
            if str(e.args[0]) == "Loading block index..." or str(e.args[0]) == "Verifying blocks...":
                printDbg(str(e.args[0]))
                statusMess = "PIVX wallet is connected but still synchronizing / verifying blocks"
                n = 1
            elif str(e.args[0]) != "Request-sent" and str(e.args[0]) != "10061":
                err_msg = "Error while contacting RPC server"
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
                
        finally:
            self.lock.release()
                
        return status, statusMess, n
     
    
    
    
    def isBlockchainSynced(self):
        try:
            self.lock.acquire()
            res = self.conn.mnsync('status').get("IsBlockchainSynced")
        except Exception as e:
            if str(e.args[0]) != "Request-sent":
                err_msg = "error in isBlockchainSynced"
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            res = False
        finally:
            self.lock.release()
        
        return res
            
            
            
    def decodemasternodebroadcast(self, work):
        try:
            self.lock.acquire()
            res = self.conn.decodemasternodebroadcast(work.strip())
        except Exception as e:
            err_msg = "error in decodemasternodebroadcast"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            res = ""
        finally:
            self.lock.release()
        
        return res
    
            
    
    def relaymasternodebroadcast(self, work):
        try:
            self.lock.acquire()
            res = self.conn.relaymasternodebroadcast(work.strip())
        except Exception as e:
            err_msg = "error in relaymasternodebroadcast"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)    
            res = ""
        finally:
            self.lock.release()
        
        return res
    


    def sendRawTransaction(self, tx_hex):
        try:
            self.lock.acquire()
            tx_id = self.conn.sendrawtransaction(tx_hex)
        except Exception as e:
            err_msg = 'error in rpcClient.sendRawTransaction'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            tx_id = None
        finally:
            self.lock.release()
        
        return tx_id
    
    
    
    
    def verifyMessage(self, pivxaddress, signature, message):
        try:
            self.lock.acquire()
            res = self.conn.verifymessage(pivxaddress, signature, message)
        except Exception as e:
            err_msg = "error in verifyMessage"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            res = False
        finally:
            self.lock.release()
            
        return res
            