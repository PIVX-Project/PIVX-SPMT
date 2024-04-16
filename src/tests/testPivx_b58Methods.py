#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import unittest
from pivx_b58 import b58chars, b58encode, b58decode
from random import randint


class TestPivx_b58Methods(unittest.TestCase):

    def test_encodeDecode(self):
        # get 32 random bytes
        text = self.randomBytesString(32)
        print(f"\nRandom Bytes: {text.hex()}")
        # encode base58
        encoded_text = b58encode(text)
        print(f"\nEncoded Text: {encoded_text}\n")
        # verify
        self.assertEqual(b58decode(encoded_text), text)

    def test_decodeEncode(self):
        # get 10 random base58 chars
        text = self.randomB58String(10)
        print(f"\nRandom Text: {text}")
        # decode base58
        decoded_text = b58decode(text)
        print(f"\nDecoded Text: {decoded_text}\n")
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
