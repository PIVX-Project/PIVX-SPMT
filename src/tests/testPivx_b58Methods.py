#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from pivx_b58 import b58chars, b58encode, b58decode
from random import randint

class TestPivx_b58Methods(unittest.TestCase):
    
    def test_encodeDecode(self):
        # get 32 random bytes
        text = self.randomBytesString(32)
        print("\nRandom Bytes: %s" % text.hex())
        # encode base58
        encoded_text = b58encode(text)
        print("\nEncoded Text: %s\n" % encoded_text)
        # verify
        self.assertEqual(b58decode(encoded_text), text)
        
        
    
    def test_decodeEncode(self):
        # get 10 random base58 chars
        text = self.randomB58String(10)
        print("\nRandom Text: %s" % text)
        # decode base58
        decoded_text = b58decode(text)
        print("\nDecoded Text: %s\n" % decoded_text)
        # verify
        self.assertEqual(b58encode(decoded_text), text)  
        
    
    
    
    def randomBytesString(self, length):
        randomString = bytes()
        for _ in range(length):
            randomString += bytes([randint(0, 256)])
            
        return randomString
    
    
    
    def randomB58String(self, length):
        randomString = ''
        for _ in range(length):
            randomString += b58chars[randint(0, len(b58chars))]
            
        return randomString
    
    
    
    
    if __name__ == '__main__':
        unittest.main(verbosity=2)