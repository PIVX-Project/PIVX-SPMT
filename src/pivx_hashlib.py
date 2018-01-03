#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
import hashlib
import bitcoin
from constants import WIF_PREFIX, MAGIC_BYTE
from pivx_b58 import b58encode, b58decode

def double_sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()



def generate_privkey():
    """
    Based on Andreas Antonopolous work from 'Mastering Bitcoin'.
    """
    valid = False
    privkey = 0
    while not valid:
        privkey = bitcoin.random_key()
        decoded_private_key = bitcoin.decode_privkey(privkey, 'hex')
        valid = 0 < decoded_private_key < bitcoin.N
    data = bytes([WIF_PREFIX]) + bytes.fromhex(privkey)
    checksum = bitcoin.bin_dbl_sha256(data)[0:4]
    return b58encode(data + checksum)



def pubkey_to_address(pubkey):
    pubkey_bin = bytes.fromhex(pubkey)
    pub_hash = bitcoin.bin_hash160(pubkey_bin)
    data = bytes([MAGIC_BYTE]) + pub_hash
    checksum = bitcoin.bin_dbl_sha256(data)[0:4]
    return b58encode(data + checksum)



def num_to_varint(a):
    """
    Based on project: https://github.com/chaeplin/dashmnb
    """
    x = int(a)
    if x < 253:
        return x.to_bytes(1, byteorder='big')
    elif x < 65536:
        return int(253).to_bytes(1, byteorder='big') +  x.to_bytes(2, byteorder='little')
    elif x < 4294967296:
        return int(254).to_bytes(1, byteorder='big') + x.to_bytes(4, byteorder='little')
    else:
        return int(255).to_bytes(1, byteorder='big') + x.to_bytes(8, byteorder='little')



def wif_to_privkey(string):
    wif_compressed = 52 == len(string)
    pvkeyencoded = b58decode(string).hex()
    wifversion = pvkeyencoded[:2]
    checksum = pvkeyencoded[-8:]
    vs = bytes.fromhex(pvkeyencoded[:-8])
    check = double_sha256(vs)[0:4]

    if wifversion == WIF_PREFIX.to_bytes(1, byteorder='big').hex() and checksum == check.hex():

        if wif_compressed:
            privkey = pvkeyencoded[2:-10]

        else:
            privkey = pvkeyencoded[2:-8]

        return privkey

    else:
        return None
    