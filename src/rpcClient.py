#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from misc import getCallerName, getFunctionName, printException, printDbg, readRPCfile
from constants import DEFAULT_PROTOCOL_VERSION, MINIMUM_FEE

class RpcClient:
        
    def __init__(self):
        self.rpc_ip, self.rpc_port, self.rpc_user, self.rpc_passwd = readRPCfile()
        rpc_url = "http://%s:%s@%s:%d" % (self.rpc_user, self.rpc_passwd, self.rpc_ip, self.rpc_port)
        try:    
            self.conn = AuthServiceProxy(rpc_url, timeout=8)     
        except JSONRPCException as e:
            err_msg = 'remote or local PIVX-cli running?'
            printException(getCallerName(), getFunctionName(), err_msg, e)
        except Exception as e:
            err_msg = 'remote or local PIVX-cli running?'
            printException(getCallerName(), getFunctionName(), err_msg, e)
            
    
    
    
    def decodeRawTransaction(self, rawTx):
        try:
            return self.conn.decoderawtransaction(rawTx)    
        except Exception as e:
            err_msg = 'error in decodeRawTransaction'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            
    
    
    
    def getAddressUtxos(self, addresses):
        try:
            return self.conn.getaddressutxos({'addresses': addresses})    
        except Exception as e:
            err_msg = "error in getAddressUtxos"
            if str(e.args[0]) != "Request-sent":
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            else:
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            raise e
    
    
    
    
    def getBlockCount(self):
        try:
            n = self.conn.getblockcount()
            return n
        except Exception as e:
            err_msg = 'remote or local PIVX-cli running?'
            if str(e.args[0]) != "Request-sent":
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            else:
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
    
    
    
    def getBlockHash(self, blockNum):
        try:
            h = self.conn.getblockhash(blockNum)
            return h
        except Exception as e:
            err_msg = 'remote or local PIVX-cli running?'
            if str(e.args[0]) != "Request-sent":
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            else:
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
    
    def getFeePerKb(self):
        try:
            # get transaction data from last 10 blocks
            feePerKb = float(self.conn.getfeeinfo(10)['feeperkb'])
            return (feePerKb if feePerKb > MINIMUM_FEE else MINIMUM_FEE)
        except Exception as e:
            err_msg = 'error in getFeePerKb'
            if str(e.args[0]) != "Request-sent":
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            else:
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
    
    
    def getMNStatus(self, address):
        try:
            mnStatusList = self.conn.listmasternodes(address)
            if not mnStatusList:
                return None
            mnStatus = mnStatusList[0]
            mnStatus['mnCount'] = self.conn.getmasternodecount()['enabled']
            return mnStatus
        
        except Exception as e:
            err_msg = "error in getMNStatus"
            if str(e.args[0]) != "Request-sent":
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            else:
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
    
    
    
    def getProtocolVersion(self):
        try:
            prot_version = self.conn.getinfo().get('protocolversion')
            return int(prot_version)
        
        except Exception as e:
            err_msg = 'error in getProtocolVersion'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            return DEFAULT_PROTOCOL_VERSION    
     
            
    
    
    def getRawTransaction(self, txid):
        try:
            return self.conn.getrawtransaction(txid)
        except Exception as e:
            err_msg = "is Blockchain synced?"
            if str(e.args[0]) != "Request-sent":
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            return None
    
    
    
    
    def getStatus(self):
        status = False
        n = 0
        try:
            n = self.conn.getblockcount()
            if n > 0:
                status = True
                
        except Exception as e:
            # If loading block index set lastBlock=1
            if str(e.args[0]) == "Loading block index..." or str(e.args[0]) == "Verifying blocks...":
                printDbg(str(e.args[0]))
                n = 1
            #else:
                #err_msg = "Error while contacting RPC server"
                #printException(getCallerName(), getFunctionName(), err_msg, e.args)    
        return status, n
    
    
    
    
    def getStatusMess(self, status=None):
        if status == None:
            status = self.getStatus()    
        if status: 
            return "RPC status: Connected"
        else:
            return "RPC status: Not connected. Is the remote or local PIVX-cli running?"
    
    
    
    def isBlockchainSynced(self):
        try:
            return self.conn.mnsync('status').get("IsBlockchainSynced")
        
        except Exception as e:
            err_msg = "error in isBlockchainSynced"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            return False
            
            
            
    def decodemasternodebroadcast(self, work):
        try:
            return self.conn.decodemasternodebroadcast(work.strip())
        
        except Exception as e:
            err_msg = "error in decodemasternodebroadcast"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            return ""
            
            
    
    def relaymasternodebroadcast(self, work):
        try:
            return self.conn.relaymasternodebroadcast(work.strip())
        
        except Exception as e:
            err_msg = "error in relaymasternodebroadcast"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)    
            return ""


    def sendRawTransaction(self, tx_hex):
        try:
            tx_id = self.conn.sendrawtransaction(tx_hex)
            return tx_id
        except Exception as e:
            err_msg = 'error in rpcClient.sendRawTransaction'
            if str(e.args[0]) != "Request-sent":
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
            else:
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
    
    
    
    def verifyMessage(self, pivxaddress, signature, message):
        try:
            return self.conn.verifymessage(pivxaddress, signature, message)
        
        except Exception as e:
            err_msg = "error in verifyMessage"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            