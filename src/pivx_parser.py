#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from misc import getCallerName, getFunctionName, printException
import utils
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

    def readVarInt(self):
        r = self.readInt(1)
        if r == 253:
            return self.readInt(2, "little")
        elif r == 254:
            return self.readInt(4, "little")
        elif r == 255:
            return self.readInt(8, "little")
        return r

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
    script_len = p.readVarInt()
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
    script_len = p.readVarInt()
    vout["scriptPubKey"] = {}
    vout["scriptPubKey"]["hex"] = p.readString(script_len, "big")
    vout["scriptPubKey"]["addresses"] = []
    try:
        locking_script = bytes.fromhex(vout["scriptPubKey"]["hex"])

        # add addresses only if P2PKH, P2PK or P2CS
        if len(locking_script) in [25, 35, 51]:
            add_bytes = utils.extract_pkh_from_locking_script(locking_script)

            address = pubkeyhash_to_address(add_bytes, isTestnet)
            vout["scriptPubKey"]["addresses"].append(address)
    except Exception as e:
        printException(getCallerName(True), getFunctionName(True), "error parsing output", str(e))
    return vout


def ParseTx(hex_string, isTestnet=False):
    p = HexParser(hex_string)
    tx = {}

    tx["version"] = p.readInt(4, "little")

    num_of_inputs = p.readVarInt()
    tx["vin"] = []
    for i in range(num_of_inputs):
        tx["vin"].append(ParseTxInput(p))

    num_of_outputs = p.readVarInt()
    tx["vout"] = []
    for i in range(num_of_outputs):
        tx["vout"].append(ParseTxOutput(p, isTestnet))

    tx["locktime"] = p.readInt(4, "little")
    return tx


def IsCoinStake(tx):
    return tx['vout'][0]["scriptPubKey"]["hex"] == ""


def IsPayToColdStaking(rawtx, out_n):
    tx = ParseTx(rawtx)
    script = tx['vout'][out_n]["scriptPubKey"]["hex"]
    return utils.IsPayToColdStaking(bytes.fromhex(script)), IsCoinStake(tx)


def GetDelegatedStaker(rawtx, out_n, isTestnet):
    tx = ParseTx(rawtx)
    script = tx['vout'][out_n]["scriptPubKey"]["hex"]
    if not utils.IsPayToColdStaking(bytes.fromhex(script)):
        return ""
    pkh = utils.GetDelegatedStaker(bytes.fromhex(script))
    return pubkeyhash_to_address(pkh, isTestnet, isCold=True)
