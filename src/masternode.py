#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import bitcoin 
from PyQt5.Qt import QObject
from base64 import b64decode
from utils import ecdsa_sign
import time
from pivx_hashlib import wif_to_privkey
import binascii
from constants import MPATH
from misc import printOK, printDbg, printException, getCallerName, getFunctionName
from utils import num_to_varint, ipmap, serialize_input_str
from misc import ipport
from PyQt5.QtCore import pyqtSlot, pyqtSignal


class Masternode(QObject):
    # Base class for all masternodes
    mnCount = 0
    # signal: sig (thread) is done
    sigdone = pyqtSignal(str)
    
    def __init__(self, caller, name, ip, port, mnPrivKey, hwAcc, collateral = {}, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.caller = caller
        self.name = name
        self.ip = ip
        self.port = str(port)
        self.mnPrivKey = wif_to_privkey(mnPrivKey)
        self.mnWIF = mnPrivKey
        self.mnPubKey = bitcoin.privkey_to_pubkey(self.mnPrivKey)
        self.hwAcc = hwAcc
        self.spath = collateral['spath']

        self.nodePath = MPATH + "%d'/0/%d" % (self.hwAcc, self.spath)
        self.collateral = collateral
        Masternode.mnCount += 1
        printOK("Initializing MNode with collateral: %s" % self.nodePath)

    
    
    
    def signature1(self, device):
        self.sig_time = int(time.time())
              
        serializedData = ipport(self.ip, self.port)
        serializedData += str(self.sig_time)
        serializedData += binascii.unhexlify(bitcoin.hash160(bytes.fromhex(self.collateral['pubKey'])))[::-1].hex()
        serializedData += binascii.unhexlify(bitcoin.hash160(bytes.fromhex(self.mnPubKey)))[::-1].hex()
        serializedData += str(self.protocol_version)
        
        printDbg("Masternode PubKey: %s" % self.mnPubKey)
        printDbg("SerializedData: %s" % serializedData)
        
        try:
            device.signMess(self.caller, self.nodePath, serializedData)
            #wait for signal when device.sig1 is ready then --> finalizeStartMessage
        
        except Exception as e:
            err_msg = "error in signature1"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)

        except KeyboardInterrupt:
            err_msg = "Keyboard Interrupt"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
        return None
    
    
    def signature2(self, serializedData):
        try:
            # local
            sig2 = ecdsa_sign(serializedData, self.mnWIF)

            return (b64decode(sig2).hex())
    
        except Exception as e:
            err_msg = "error in signature2"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
    
    @pyqtSlot(str)        
    def finalizeStartMessage(self, text):
        sig1 = text
        if sig1=="None":
            # Signature refused by the user
            self.sigdone.emit("None")
            return
        
        printOK("first signature: %s" % sig1)
        # ------ some default config
        scriptSig = ''
        sequence = 0xffffffff
        
        # block_hash = hash(currBlock-12)
        currBlock = self.rpcClient.getBlockCount()
        block_hash = self.rpcClient.getBlockHash(currBlock - 12)
        
        printDbg("Current block from PIVX client: %s" % str(currBlock))
        printDbg("Hash of 12 blocks ago: %s" % block_hash)
        
        try:
            vintx = bytes.fromhex(self.collateral['txid'])[::-1].hex()
            vinno = self.collateral['txidn'].to_bytes(4, byteorder='big')[::-1].hex()
            vinsig = num_to_varint(len(scriptSig) / 2).hex() + bytes.fromhex(scriptSig)[::-1].hex()
            vinseq = sequence.to_bytes(4, byteorder='big')[::-1].hex()
            
            ipv6map = ipmap(self.ip, self.port)
            printDbg("ipv6map: %s" % ipv6map)
        
            collateral_in = num_to_varint(len(self.collateral['pubKey'])/2).hex() + self.collateral['pubKey']
            delegate_in = num_to_varint(len(self.mnPubKey)/2).hex() + self.mnPubKey
            
        except Exception as e:
            err_msg = "error in startMessage"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        
        
                
        work_sig_time = self.sig_time.to_bytes(8, byteorder='big')[::-1].hex()
        work_protoversion = self.protocol_version.to_bytes(4, byteorder='big')[::-1].hex()
        
        last_ping_block_hash = bytes.fromhex(block_hash)[::-1].hex()
        
        serializedData = serialize_input_str(self.collateral['txid'], self.collateral['txidn'], sequence, scriptSig) + block_hash + str(self.sig_time)
        
        
        printDbg("serializedData: %s" % serializedData)
        sig2 = self.signature2(serializedData)
        printOK("second signature: %s" % sig2)
        
        work = vintx + vinno + vinsig + vinseq
        work += ipv6map + collateral_in + delegate_in
        work += num_to_varint(len(sig1) / 2).hex() + sig1
        work += work_sig_time + work_protoversion
        work += vintx + vinno + vinsig + vinseq
        work += last_ping_block_hash + work_sig_time
        work += num_to_varint(len(sig2) / 2).hex() + sig2
        
        # nnLastDsq to zero
        work += "0"*16
        
        self.sigdone.emit(work)  
    
    
    def startMessage(self, device, rpcClient):
        # setuo rpc connection
        self.rpcClient = rpcClient
        # update protocol version
        self.protocol_version = self.rpcClient.getProtocolVersion()
        # done signal from hwdevice thread
        device.sig1done.connect(self.finalizeStartMessage)
        # prepare sig1 (the one done on the hw device)
        self.signature1(device)
        
        
        
                
