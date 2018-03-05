#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from masternode import Masternode
from rpcClient import RpcClient
from PyQt5.QtCore import pyqtSlot
import simplejson as json
from time import sleep
from bitcoin import privkey_to_pubkey
from pivx_hashlib import pubkey_to_address
from utils import b64encode
import time

class TestMasternodeMethods(unittest.TestCase):
    def setUp(self):
        self.rpcClient = RpcClient()
        rpcStatus, _ = self.rpcClient.getStatus()
        if not rpcStatus:
            self.skipTest("RPC not connected")
            
        # read masternode data from file    
        with open('test_masternode.data.json') as data_file:
            input_data_list = json.load(data_file)
        
        self.mnode_list = []
        for input_data in input_data_list:
            # Rename input data
            name = input_data['name']
            ip = input_data['ip']
            port = input_data['port']
            mnPrivKey = input_data['mnPrivKey']
            hwAcc = input_data['hwAcc']
            collateral = input_data['collateral']
            # Create masternode object
            mnode = Masternode(self, name, ip, port, mnPrivKey, hwAcc, collateral)
            mnode.sig1 = input_data['sig1']
            mnode.rpcClient = self.rpcClient
            mnode.sig_time = int(time.time())
            mnode.protocol_version = self.rpcClient.getProtocolVersion()
            # Add it to list
            self.mnode_list.append(mnode)
        
        
        
    def tearDown(self):
        if hasattr(self.rpcClient, 'conn'):
            self.rpcClient.parent = None
            
            
    
    def test_finalizeStartMessage(self):
        for mnode in self.mnode_list:
            # Test message construction
            mnode.finalizeStartMessage(mnode.sig1)
            sleep(3)
        
        
        
        
    # Activated by signal from masternode       
    @pyqtSlot(str)    
    def finalizeStartMessage_end(self, text):
        # decode message
        ret = self.caller.rpcClient.decodemasternodebroadcast(text)
        # find masternode in list and check
        for mnode in self.mnode_list:
            ip_addr = mnode.ip + ":" + mnode.port
            if ret['addr'] == ip_addr:
                # check ping signature
                ping_sig = b64encode(text[638:768])
                self.assertEqual(ret['lastPing'].get('vchSig'), ping_sig)
                # check nLastDsq
                self.assertEqual(ret['nLastDsq'], 0)
                # check protocol version
                pv = self.rpcClient.getProtocolVersion()
                self.assertEqual(ret['protocolVersion'], pv)
                # check masternode pubkey1
                self.assertEqual(ret['pubkey'], mnode['collateral'].get('address'))
                # check masternode pubkey2
                pk2 = pubkey_to_address(privkey_to_pubkey(mnode.mnPrivKey))
                self.assertEqual(ret['pubkey2'], pk2)
                # check masternode signature
                node_sig = b64encode(text[320:450])
                self.assertEqual(ret['vchSig'], node_sig)
                
                
    if __name__ == '__main__':
        unittest.main(verbosity=2)    