#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import unittest
from pivx_hashlib import generate_privkey, pubkey_to_address
import bitcoin
from pivx_b58 import b58decode


class TestPivx_hashlibMethods(unittest.TestCase):

    def test_generate_privkey(self):
        # generate random private key
        randomKey = generate_privkey()
        # check length
        self.assertEqual(len(randomKey), 51)
        # check leading char '8'
        self.assertEqual(randomKey[0], '8')
        # decode and verify checksum
        randomKey_bin = bytes.fromhex(b58decode(randomKey).hex())
        randomKey_bin_check = bitcoin.bin_dbl_sha256(randomKey_bin[0:-4])[0:4]
        self.assertEqual(randomKey_bin[-4:], randomKey_bin_check)

    def test_pubkey_to_address(self):
        # generate random private key and convert to public
        randomPubKey = bitcoin.privkey_to_pubkey(generate_privkey())
        # compute address
        randomPivxAddr = pubkey_to_address(randomPubKey)
        # check leading char 'D'
        self.assertEqual(randomPivxAddr[0], 'D')
        # decode and verify checksum
        randomPivxAddr_bin = bytes.fromhex(b58decode(randomPivxAddr).hex())
        randomPivxAddr_bin_check = bitcoin.bin_dbl_sha256(randomPivxAddr_bin[0:-4])[0:4]
        self.assertEqual(randomPivxAddr_bin[-4:], randomPivxAddr_bin_check)

    if __name__ == '__main__':
        unittest.main(verbosity=2)
