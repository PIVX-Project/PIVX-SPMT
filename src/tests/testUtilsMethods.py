#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from utils import checkPivxAddr, compose_tx_locking_script
from pivx_hashlib import generate_privkey, pubkey_to_address
from bitcoin import privkey_to_pubkey
from bitcoin.main import b58check_to_hex

class TestUtilsMethods(unittest.TestCase):
    
    def test_checkPivxAddr(self):
        # Generate Valid PIVX address
        pK = privkey_to_pubkey(generate_privkey())
        pivxAddr = pubkey_to_address(pK)
        # Check valid address
        self.assertTrue(checkPivxAddr(pivxAddr))
        # Check malformed address 1: change leading char
        pivxAddr2 = self.getRandomChar() + pivxAddr[1:]
        while pivxAddr2[0] == 'D':
            pivxAddr2 = self.getRandomChar() + pivxAddr[1:]
        self.assertFalse(checkPivxAddr(pivxAddr2))
        # Check malformed address 1: add random chars
        pivxAddr3 = pivxAddr
        for _ in range(10):
            pivxAddr3 += self.getRandomChar()
        self.assertFalse(checkPivxAddr(pivxAddr3))
        
        
        
    def test_compose_tx_locking_script(self):
        # check with P2PKH addresses
        # Generate Valid PIVX address
        pK = privkey_to_pubkey(generate_privkey())
        pivxAddr = pubkey_to_address(pK)
        # compose TX script
        result = compose_tx_locking_script(pivxAddr)
        print(result)
        # check OP_DUP
        self.assertEqual(result[0], int('76', 16))
        # check OP_HASH160
        self.assertEqual(result[1], int('A9', 16))
        pubkey_hash = bytearray.fromhex(b58check_to_hex(pivxAddr))
        self.assertEqual(result[2], len(pubkey_hash))
        self.assertEqual(result[3:23], pubkey_hash)
        # check OP_QEUALVERIFY
        self.assertEqual(result[23], int('88', 16))
        # check OP_CHECKSIG
        self.assertEqual(result[24], int('AC', 16))
        
        
        
        
    
    def getRandomChar(self):
        import string
        import random
        return random.choice(string.ascii_letters)
    
    
    
    if __name__ == '__main__':
        unittest.main(verbosity=2)