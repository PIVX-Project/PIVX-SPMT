#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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


def ParseTxOutput(p):
    vout = {}
    vout["value"] = p.readInt(8, "little")/1e8
    script_len = p.readInt(1, "little")
    vout["scriptPubKey"] = {}
    vout["scriptPubKey"]["hex"] = p.readString(script_len, "big")
    return vout


def ParseTx(rawhex):
    p = HexParser(rawhex)
    tx = {}

    tx["version"] = p.readInt(4, "little")

    num_of_inputs = p.readInt(1, "little")
    tx["vin"] = []
    for i in range(num_of_inputs):
        tx["vin"].append(ParseTxInput(p))

    num_of_outputs = p.readInt(1, "little")
    tx["vout"] = []
    for i in range(num_of_outputs):
        tx["vout"].append(ParseTxOutput(p))

    tx["locktime"] = p.readInt(4, "little")
    return tx
