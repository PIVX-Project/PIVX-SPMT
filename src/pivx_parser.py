#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from misc import getCallerName, getFunctionName, printException
from utils import extract_pkh_from_locking_script
from pivx_hashlib import pubkeyhash_to_address

class HexParser():
    def __init__(self, hex_str):
        self.cursor = 0
        self.hex_str = hex_str

    def readInt(self, nbytes, byteorder="big", signed=False):
        if self.cursor + nbytes * 2 > len(self.hex_str):
            raise Exception("HexParser range error")
        b = bytes.fromhex(self.hex_str[self.cursor:self.cursor + nbytes * 2])
        res = int.from_bytes(b, byteorder=byteorder, signed=signed)
        self.cursor += nbytes * 2
        return res

    def readString(self, nbytes, byteorder="big"):
        if self.cursor + nbytes * 2 > len(self.hex_str):
            raise Exception("HexParser range error")
        res = self.hex_str[self.cursor:self.cursor + nbytes * 2]
        self.cursor += nbytes * 2
        if byteorder == "little":
            splits = [res[i:i + 2] for i in range(0, len(res), 2)]
            return ''.join(splits[::-1])
        return res


def IsCoinBase(vin):
    return vin["txid"] == "0" * 64 and vin["vout"] == 4294967295 and vin["scriptSig"]["hex"][:2] != "c2"


def ParseTxInput(p):
    vin = {}
    vin["txid"] = p.readString(32, "little")
    vin["vout"] = p.readInt(4, "little")
    script_len = p.readInt(1, "little")
    vin["scriptSig"] = {}
    vin["scriptSig"]["hex"] = p.readString(script_len, "big")
    vin["sequence"] = p.readInt(4, "little")
    if IsCoinBase(vin):
        del vin["txid"]
        del vin["vout"]
        vin["coinbase"] = vin["scriptSig"]["hex"]
        del vin["scriptSig"]

    return vin


def ParseTxOutput(p, isTestnet=False):
    vout = {}
    vout["value"] = p.readInt(8, "little")
    script_len = p.readInt(1, "little")
    vout["scriptPubKey"] = {}
    vout["scriptPubKey"]["hex"] = p.readString(script_len, "big")
    vout["scriptPubKey"]["addresses"] = []
    try:
        add_bytes = extract_pkh_from_locking_script(bytes.fromhex(vout["scriptPubKey"]["hex"]))
        address = pubkeyhash_to_address(add_bytes, isTestnet)
        vout["scriptPubKey"]["addresses"].append(address)
    except Exception as e:
        printException(getCallerName(True), getFunctionName(True), "error parsing output", str(e))
    return vout


def ParseTx(hex_string, isTestnet=False):
    p = HexParser(hex_string)
    tx = {}

    tx["version"] = p.readInt(4, "little")

    num_of_inputs = p.readInt(1, "little")
    tx["vin"] = []
    for i in range(num_of_inputs):
        tx["vin"].append(ParseTxInput(p))

    num_of_outputs = p.readInt(1, "little")
    tx["vout"] = []
    for i in range(num_of_outputs):
        tx["vout"].append(ParseTxOutput(p, isTestnet))

    tx["locktime"] = p.readInt(4, "little")
    return tx
