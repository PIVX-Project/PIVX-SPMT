#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017 chaeplin
# Copyright (c) 2017 Bertrand256
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from base64 import b64decode
import binascii
import bitcoin
import time

from PyQt5.Qt import QObject
from PyQt5.QtCore import pyqtSignal

from constants import NewSigsActive
from misc import printOK, printDbg, printException, getCallerName, getFunctionName, ipport
from pivx_hashlib import wif_to_privkey
from utils import ecdsa_sign, ecdsa_sign_bin, num_to_varint, ipmap, serialize_input_str


class Masternode(QObject):
    """
    Base class for all masternodes
    """
    mnCount = 0
    # signal: sig (thread) is done - emitted by finalizeStartMessage
    sigdone = pyqtSignal(str)

    def __init__(self, tab_main, name, ip, port, mnPrivKey, hwAcc, collateral=None, isTestnet=False, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        if collateral is None:
            collateral = {}
        self.tab_main = tab_main
        self.name = name
        self.ip = ip
        self.port = str(port)
        self.mnPrivKey = wif_to_privkey(mnPrivKey)
        self.mnWIF = mnPrivKey
        self.mnPubKey = bitcoin.privkey_to_pubkey(self.mnPrivKey)
        self.hwAcc = hwAcc
        self.spath = collateral['spath']
        self.nodePath = f"{self.hwAcc}'/0/{self.spath}"
        self.collateral = collateral
        self.isTestnet = isTestnet
        self.currHeight = 0
        Masternode.mnCount += 1
        printOK(f"Initializing MNode with collateral: {self.nodePath}")

    def getOldBroadcastMessage(self):
        self.sig_time = int(time.time())
        serializedData = ipport(self.ip, self.port)
        serializedData += str(self.sig_time)
        serializedData += binascii.unhexlify(bitcoin.hash160(bytes.fromhex(self.collateral['pubKey'])))[::-1].hex()
        serializedData += binascii.unhexlify(bitcoin.hash160(bytes.fromhex(self.mnPubKey)))[::-1].hex()
        serializedData += str(self.protocol_version)
        return serializedData

    def getNewBroadcastMessage(self):
        self.sig_time = int(time.time())
        pk1 = bytes.fromhex(self.collateral['pubKey'])
        pk2 = bytes.fromhex(self.mnPubKey)
        ss = (1).to_bytes(4, byteorder='little')
        ss += bytes.fromhex(ipmap(self.ip, self.port))
        ss += (self.sig_time).to_bytes(8, byteorder='little')
        ss += (len(pk1).to_bytes(1, byteorder='little') + pk1)
        ss += (len(pk2).to_bytes(1, byteorder='little') + pk2)
        ss += (self.protocol_version).to_bytes(4, byteorder='little')
        res = bitcoin.bin_dbl_sha256(ss)[::-1]
        return res.hex()

    def signature1(self, device):
        try:
            fNewSigs = NewSigsActive(self.currHeight, self.isTestnet)
            if fNewSigs:
                serializedData = self.getNewBroadcastMessage()
            else:
                serializedData = self.getOldBroadcastMessage()
            printDbg(f"SerializedData: {serializedData}")
            # HW wallet signature
            device.signMess(self.tab_main.caller, self.nodePath, serializedData, self.isTestnet)
            # wait for signal when device.sig1 is ready then --> finalizeStartMessage
        except Exception as e:
            err_msg = "error in signature1"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        except KeyboardInterrupt:
            err_msg = "Keyboard Interrupt"
            printException(getCallerName(), getFunctionName(), err_msg, '')
        return None

    def getPingMessage(self, fNewSigs, block_hash):
        if fNewSigs:
            ss = bytes.fromhex(self.collateral["txid"])[::-1]
            ss += (self.collateral["txidn"]).to_bytes(4, byteorder='little')
            ss += bytes([0, 255, 255, 255, 255])
            ss += bytes.fromhex(block_hash)[::-1]
            ss += (self.sig_time).to_bytes(8, byteorder='little')
            return bitcoin.bin_dbl_sha256(ss)
        else:
            scriptSig = ''
            sequence = 0xffffffff
            return serialize_input_str(self.collateral['txid'], self.collateral['txidn'], sequence, scriptSig) + \
                   block_hash + str(self.sig_time)

    def signature2(self, block_hash):
        try:
            fNewSigs = NewSigsActive(self.currHeight, self.isTestnet)
            mnping = self.getPingMessage(fNewSigs, block_hash)
            if fNewSigs:
                printDbg(f"mnping: {mnping.hex()}")
                sig2 = ecdsa_sign_bin(mnping, self.mnWIF)  # local
            else:
                printDbg(f"mnping: {mnping}")
                sig2 = ecdsa_sign(mnping, self.mnWIF)

            return (b64decode(sig2).hex()), fNewSigs

        except Exception as e:
            err_msg = "error in signature2"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)

    def finalizeStartMessage(self, text):
        sig1 = text
        if sig1 == "None":
            # Signature refused by the user
            self.sigdone.emit("None")
            return

        printOK(f"first signature: {sig1}")
        # ------ some default config
        scriptSig = ''
        sequence = 0xffffffff

        try:
            block_hash = self.rpcClient.getBlockHash(self.currHeight - 12)
            if block_hash is None:
                raise Exception(f'Unable to get blockhash for block {self.currHeight-12}')

            printDbg(f"Current block from PIVX client: {self.currHeight}")
            printDbg(f"Hash of 12 blocks ago: {block_hash}")

            vintx = bytes.fromhex(self.collateral['txid'])[::-1].hex()
            vinno = self.collateral['txidn'].to_bytes(4, byteorder='big')[::-1].hex()
            vinsig = num_to_varint(len(scriptSig) / 2).hex() + bytes.fromhex(scriptSig)[::-1].hex()
            vinseq = sequence.to_bytes(4, byteorder='big')[::-1].hex()
            ipv6map = ipmap(self.ip, self.port)
            collateral_in = num_to_varint(len(self.collateral['pubKey']) / 2).hex() + self.collateral['pubKey']
            delegate_in = num_to_varint(len(self.mnPubKey) / 2).hex() + self.mnPubKey

        except Exception as e:
            err_msg = "error in startMessage"
            printException(getCallerName(), getFunctionName(), err_msg, e)
            return

        work_sig_time = self.sig_time.to_bytes(8, byteorder='big')[::-1].hex()
        work_protoversion = self.protocol_version.to_bytes(4, byteorder='big')[::-1].hex()
        last_ping_block_hash = bytes.fromhex(block_hash)[::-1].hex()

        sig2, fNewSigs = self.signature2(block_hash)
        printOK(f"second signature: {sig2}")

        work = vintx + vinno + vinsig + vinseq
        work += ipv6map + collateral_in + delegate_in
        work += num_to_varint(len(sig1) / 2).hex() + sig1
        work += work_sig_time + work_protoversion
        work += vintx + vinno + vinsig + vinseq
        work += last_ping_block_hash + work_sig_time
        work += num_to_varint(len(sig2) / 2).hex() + sig2
        if fNewSigs:
            work += (1).to_bytes(4, byteorder='little').hex()
            work += (1).to_bytes(4, byteorder='little').hex()
        else:
            # nnLastDsq to zero
            work += "0" * 16

        # Emit signal
        printDbg(f"EMITTING: {work}")
        self.sigdone.emit(work)

    def startMessage(self, device, rpcClient):
        # setup rpc connection
        self.rpcClient = rpcClient
        try:
            # update protocol version
            self.protocol_version = self.rpcClient.getProtocolVersion()

            # set current height
            self.currHeight = self.rpcClient.getBlockCount()
        except Exception as e:
            err_msg = "error in startMessage"
            printException(getCallerName(), getFunctionName(), err_msg, e)
            return
        # done signal from hwdevice thread
        try:
            device.sig1done.disconnect()
        except:
            pass
        device.sig1done.connect(self.finalizeStartMessage)
        # prepare sig1 (the one done on the hw device)
        self.signature1(device)
