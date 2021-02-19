#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017 chaeplin
# Copyright (c) 2017 Bertrand256
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from bitcoin import bin_hash160
from btchip.btchip import btchip, getDongle, BTChipException
from btchip.btchipUtils import compress_public_key, bitcoinTransaction, bitcoinInput, bitcoinOutput

import threading

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QApplication

from constants import MPATH_LEDGER as MPATH, MPATH_TESTNET, HW_devices
from misc import printDbg, printException, printOK, getCallerName, getFunctionName, splitString, DisconnectedException
from pivx_hashlib import pubkey_to_address, single_sha256
from threads import ThreadFuns
from txCache import TxCache
from utils import extract_pkh_from_locking_script, compose_tx_locking_script


def process_ledger_exceptions(func):
    def process_ledger_exceptions_int(*args, **kwargs):
        hwDevice = args[0]
        try:
            return func(*args, **kwargs)

        except BTChipException as e:
            printDbg('Error while communicating with Ledger hardware wallet.')
            e.message = 'Error while communicating with Ledger hardware wallet.'
            if (e.sw in (0x6f01, 0x6d00, 0x6700, 0x6faa)):
                e.message = 'Make sure the PIVX app is open on your Ledger device.'
                e.message += '<br>If there is a program (such as Ledger Bitcoin Wallet) interfering with the USB communication, close it first.'
            elif (e.sw == 0x6982):
                e.message = 'Enter the PIN on your Ledger device.'
            printException(getCallerName(True), getFunctionName(True), e.message, e.args)
            raise DisconnectedException(e.message, hwDevice)

        except Exception as e:
            e.message = "Ledger - generic exception"
            if str(e.args[0]) == 'read error':
                e.message = 'Read Error. Click "Connect" to reconnect HW device'
            printException(getCallerName(True), getFunctionName(True), e.message, str(e))
            raise DisconnectedException(e.message, hwDevice)

    return process_ledger_exceptions_int


class LedgerApi(QObject):
    # signal: sig1 (thread) is done - emitted by signMessageFinish
    sig1done = pyqtSignal(str)
    # signal: sigtx (thread) is done - emitted by signTxFinish
    sigTxdone = pyqtSignal(bytearray, str)
    # signal: sigtx (thread) is done (aborted) - emitted by signTxFinish
    sigTxabort = pyqtSignal()
    # signal: tx_progress percent - emitted by perepare_transfer_tx_bulk
    tx_progress = pyqtSignal(int)
    # signal: sig_progress percent - emitted by signTxSign
    sig_progress = pyqtSignal(int)
    # signal: sig_disconnected -emitted with DisconnectedException
    sig_disconnected = pyqtSignal(str)

    def __init__(self, main_wnd, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.main_wnd = main_wnd
        self.model = [x[0] for x in HW_devices].index("LEDGER Nano")
        self.messages = [
            'Device not initialized.',
            'Unable to connect to the device. Please check that the PIVX app on the device is open, and try again.',
            'Hardware device connected.'
        ]
        # Device Lock for threads
        self.lock = threading.RLock()
        self.status = 0
        self.dongle = None
        printDbg("Creating HW device class")

    @process_ledger_exceptions
    def initDevice(self):
        printDbg("Initializing Ledger")
        with self.lock:
            self.status = 0
            self.dongle = getDongle(False)
            printOK('Ledger Nano drivers found')
            self.chip = btchip(self.dongle)
            printDbg("Ledger Initialized")
            self.status = 1
            ver = self.chip.getFirmwareVersion()
            printOK("Ledger HW device connected [v. %s]" % str(ver.get('version')))
            # Check device is unlocked
            bip32_path = MPATH + "%d'/0/%d" % (0, 0)
            _ = self.chip.getWalletPublicKey(bip32_path)
            self.status = 2
        self.sig_progress.connect(self.updateSigProgress)

    def closeDevice(self, message=''):
        printDbg("Closing LEDGER client")
        self.sig_disconnected.emit(message)
        self.status = 0
        with self.lock:
            if self.dongle is not None:
                try:
                    self.dongle.close()
                except:
                    pass
                self.dongle = None

    @process_ledger_exceptions
    def append_inputs_to_TX(self, utxo, bip32_path):
        self.amount += int(utxo['satoshis'])
        raw_tx = TxCache(self.main_wnd)[utxo['txid']]

        # parse the raw transaction, so that we can extract the UTXO locking script we refer to
        prev_transaction = bitcoinTransaction(bytearray.fromhex(raw_tx))

        utxo_tx_index = utxo['vout']
        if utxo_tx_index < 0 or utxo_tx_index > len(prev_transaction.outputs):
            raise Exception('Incorrect value of outputIndex for UTXO %s-%d' %
                            (utxo['txid'], utxo['vout']))

        trusted_input = self.chip.getTrustedInput(prev_transaction, utxo_tx_index)
        self.trusted_inputs.append(trusted_input)

        # Hash check
        curr_pubkey = compress_public_key(self.chip.getWalletPublicKey(bip32_path)['publicKey'])
        pubkey_hash = bin_hash160(curr_pubkey)
        pubkey_hash_from_script = extract_pkh_from_locking_script(prev_transaction.outputs[utxo_tx_index].script)
        if pubkey_hash != pubkey_hash_from_script:
            text = "Error: The hashes for the public key for the BIP32 path, and the UTXO locking script do not match."
            text += "Your signed transaction will not be validated by the network.\n"
            text += "pubkey_hash: %s\n" % pubkey_hash.hex()
            text += "pubkey_hash_from_script: %s\n" % pubkey_hash_from_script.hex()
            printDbg(text)

        self.arg_inputs.append({
            'locking_script': prev_transaction.outputs[utxo['vout']].script,
            'pubkey': curr_pubkey,
            'bip32_path': bip32_path,
            'outputIndex': utxo['vout'],
            'txid': utxo['txid'],
            'p2cs': (utxo['staker'] != "")
        })

    @process_ledger_exceptions
    def prepare_transfer_tx_bulk(self, caller, rewardsArray, dest_address, tx_fee, isTestnet=False):
        with self.lock:
            # For each UTXO create a Ledger 'trusted input'
            self.trusted_inputs = []
            #    https://klmoney.wordpress.com/bitcoin-dissecting-transactions-part-2-building-a-transaction-by-hand)
            self.arg_inputs = []
            self.amount = 0
            num_of_sigs = sum([len(mnode['utxos']) for mnode in rewardsArray])
            curr_utxo_checked = 0

            for mnode in rewardsArray:
                # Add proper HW path (for current device) on each utxo
                if isTestnet:
                    mnode['path'] = MPATH_TESTNET + mnode['path']
                else:
                    mnode['path'] = MPATH + mnode['path']

                # Create a TX input with each utxo
                for utxo in mnode['utxos']:
                    self.append_inputs_to_TX(utxo, mnode['path'])
                    # completion percent emitted
                    curr_utxo_checked += 1
                    completion = int(95 * curr_utxo_checked / num_of_sigs)
                    self.tx_progress.emit(completion)

            self.amount -= int(tx_fee)
            self.amount = int(self.amount)
            arg_outputs = [{'address': dest_address, 'valueSat': self.amount}]  # there will be multiple outputs soon
            self.new_transaction = bitcoinTransaction()  # new transaction object to be used for serialization at the last stage
            self.new_transaction.version = bytearray([0x01, 0x00, 0x00, 0x00])

            self.tx_progress.emit(99)

            for o in arg_outputs:
                output = bitcoinOutput()
                output.script = compose_tx_locking_script(o['address'], isTestnet)
                output.amount = int.to_bytes(o['valueSat'], 8, byteorder='little')
                self.new_transaction.outputs.append(output)

            self.tx_progress.emit(100)

            # join all outputs - will be used by Ledger for signing transaction
            self.all_outputs_raw = self.new_transaction.serializeOutputs()

            self.mBox2 = QMessageBox(caller)
            self.messageText = "<p>Confirm transaction on your device, with the following details:</p>"
            # messageText += "From bip32_path: <b>%s</b><br><br>" % str(bip32_path)
            self.messageText += "<p>Payment to:<br><b>%s</b></p>" % dest_address
            self.messageText += "<p>Net amount:<br><b>%s</b> PIV</p>" % str(round(self.amount / 1e8, 8))
            self.messageText += "<p>Fees:<br><b>%s</b> PIV<p>" % str(round(int(tx_fee) / 1e8, 8))
            messageText = self.messageText + "Signature Progress: 0 %"
            self.mBox2.setText(messageText)
            self.mBox2.setIconPixmap(caller.tabMain.ledgerImg.scaledToHeight(200, Qt.SmoothTransformation))
            self.mBox2.setWindowTitle("CHECK YOUR LEDGER")
            self.mBox2.setStandardButtons(QMessageBox.NoButton)
            self.mBox2.setMaximumWidth(500)
            self.mBox2.show()

        ThreadFuns.runInThread(self.signTxSign, (), self.signTxFinish)

    @process_ledger_exceptions
    def scanForAddress(self, account, spath, isTestnet=False):
        with self.lock:
            if not isTestnet:
                curr_path = MPATH + "%d'/0/%d" % (account, spath)
                curr_addr = self.chip.getWalletPublicKey(curr_path).get('address')[12:-2]
            else:
                curr_path = MPATH_TESTNET + "%d'/0/%d" % (account, spath)
                pubkey = compress_public_key(self.chip.getWalletPublicKey(curr_path).get('publicKey')).hex()
                curr_addr = pubkey_to_address(pubkey, isTestnet)

        return curr_addr

    @process_ledger_exceptions
    def scanForPubKey(self, account, spath, isTestnet=False):
        hwpath = "%d'/0/%d" % (account, spath)
        if isTestnet:
            curr_path = MPATH_TESTNET + hwpath
        else:
            curr_path = MPATH + hwpath

        with self.lock:
            nodeData = self.chip.getWalletPublicKey(curr_path)

        return compress_public_key(nodeData.get('publicKey')).hex()

    @process_ledger_exceptions
    def signMess(self, caller, hwpath, message, isTestnet=False):
        if isTestnet:
            path = MPATH_TESTNET + hwpath
        else:
            path = MPATH + hwpath
        # Ledger doesn't accept characters other that ascii printable:
        # https://ledgerhq.github.io/btchip-doc/bitcoin-technical.html#_sign_message
        message = message.encode('ascii', 'ignore')
        message_sha = splitString(single_sha256(message).hex(), 32)

        # Connection pop-up
        mBox = QMessageBox(caller)
        warningText = "Another application (such as Ledger Wallet app) has probably taken over "
        warningText += "the communication with the Ledger device.<br><br>To continue, close that application and "
        warningText += "click the <b>Retry</b> button.\nTo cancel, click the <b>Abort</b> button"
        mBox.setText(warningText)
        mBox.setWindowTitle("WARNING")
        mBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Abort)

        # Ask confirmation
        with self.lock:
            info = self.chip.signMessagePrepare(path, message)

            while info['confirmationNeeded'] and info['confirmationType'] == 34:
                ans = mBox.exec_()

                if ans == QMessageBox.Abort:
                    raise Exception("Reconnect HW device")

                # we need to reconnect the device
                self.initDevice()
                info = self.chip.signMessagePrepare(path, message)

            printOK('Signing Message')
            self.mBox = QMessageBox(caller)
            messageText = "Check display of your hardware device\n\n- message hash:\n\n%s\n\n-path:\t%s\n" % (
                message_sha, path)
            self.mBox.setText(messageText)
            self.mBox.setIconPixmap(caller.tabMain.ledgerImg.scaledToHeight(200, Qt.SmoothTransformation))
            self.mBox.setWindowTitle("CHECK YOUR LEDGER")
            self.mBox.setStandardButtons(QMessageBox.NoButton)
            self.mBox.show()

        # Sign message
        ThreadFuns.runInThread(self.signMessageSign, (), self.signMessageFinish)

    @process_ledger_exceptions
    def signMessageSign(self, ctrl):
        self.signature = None
        with self.lock:
            try:
                self.signature = self.chip.signMessageSign()
            except:
                pass

    def signMessageFinish(self):
        with self.lock:
            self.mBox.accept()
        if self.signature != None:
            if len(self.signature) > 4:
                rLength = self.signature[3]
                r = self.signature[4: 4 + rLength]
                if len(self.signature) > 4 + rLength + 1:
                    sLength = self.signature[4 + rLength + 1]
                    if len(self.signature) > 4 + rLength + 2:
                        s = self.signature[4 + rLength + 2:]
                        if rLength == 33:
                            r = r[1:]
                        if sLength == 33:
                            s = s[1:]

                        work = bytes(chr(27 + 4 + (self.signature[0] & 0x01)), "utf-8") + r + s
                        printOK("Message signed")
                        sig1 = work.hex()
                    else:
                        printDbg('client.signMessageSign() returned invalid response (code 3): ' + self.signature.hex())
                        sig1 = "None"
                else:
                    printDbg('client.signMessageSign() returned invalid response (code 2): ' + self.signature.hex())
                    sig1 = "None"
            else:
                printDbg('client.signMessageSign() returned invalid response (code 1): ' + self.signature.hex())
                sig1 = "None"
        else:
            printOK("Signature refused by the user")
            sig1 = "None"

        self.sig1done.emit(sig1)

    @process_ledger_exceptions
    def signTxSign(self, ctrl):
        self.tx_raw = None
        with self.lock:
            starting = True
            curr_input_signed = 0
            # sign all inputs on Ledger and add inputs in the self.new_transaction object for serialization
            for idx, new_input in enumerate(self.arg_inputs):
                try:
                    self.chip.startUntrustedTransaction(starting, idx, self.trusted_inputs, new_input['locking_script'])

                    self.chip.finalizeInputFull(self.all_outputs_raw)

                    sig = self.chip.untrustedHashSign(new_input['bip32_path'], lockTime=0)
                except BTChipException as e:
                    if e.args[0] != "Invalid status 6985":
                        raise e
                    # Signature refused by the user
                    return

                new_input['signature'] = sig
                inputTx = bitcoinInput()
                inputTx.prevOut = bytearray.fromhex(new_input['txid'])[::-1] + int.to_bytes(new_input['outputIndex'], 4,
                                                                                            byteorder='little')

                inputTx.script = bytearray([len(sig)]) + sig
                if new_input['p2cs']:
                    inputTx.script += bytearray([0x00])
                inputTx.script += bytearray([0x21]) + new_input['pubkey']

                inputTx.sequence = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

                self.new_transaction.inputs.append(inputTx)

                starting = False

                # signature percent emitted
                curr_input_signed += 1
                completion = int(100 * curr_input_signed / len(self.arg_inputs))
                self.sig_progress.emit(completion)

            self.new_transaction.lockTime = bytearray([0, 0, 0, 0])
            self.tx_raw = bytearray(self.new_transaction.serialize())
            self.sig_progress.emit(100)

    def signTxFinish(self):
        self.mBox2.accept()

        if self.tx_raw is not None:
            # Signal to be catched by FinishSend on TabRewards / dlg_sewwpAll
            self.sigTxdone.emit(self.tx_raw, str(round(self.amount / 1e8, 8)))
        else:
            printOK("Transaction refused by the user")
            self.sigTxabort.emit()

    def updateSigProgress(self, percent):
        messageText = self.messageText + "Signature Progress: <b style='color:red'>" + str(percent) + " %</b>"
        self.mBox2.setText(messageText)
        QApplication.processEvents()
