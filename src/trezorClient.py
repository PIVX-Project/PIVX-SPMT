#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import binascii
import threading
from time import sleep

from PyQt5.Qt import QObject
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QApplication

from trezorlib import btc, exceptions, messages as trezor_proto, coins
from trezorlib.client import TrezorClient, MINIMUM_FIRMWARE_VERSION
from trezorlib.tools import parse_path
from trezorlib.transport import get_transport
from trezorlib.tx_api import TxApi
from trezorlib.ui import ClickUI

from constants import MPATH_TREZOR as MPATH, MPATH_TESTNET, HW_devices
from misc import getCallerName, getFunctionName, printException, printDbg, \
    DisconnectedException, printOK, splitString
from threads import ThreadFuns



def  process_trezor_exceptions(func):
    def process_trezor_exceptions_int(*args, **kwargs):
        hwDevice = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_mess = "Trezor Exception"
            printException(getCallerName(True), getFunctionName(True), err_mess, e.args)
            raise DisconnectedException(err_mess, hwDevice, str(e))

    return process_trezor_exceptions_int


class TrezorApi(QObject):
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



    def __init__(self, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.model = HW_devices.index("TREZOR Model T")
        self.messages = [
            'Trezor not initialized. Coonect and unlock it',
            'Error setting up Trezor Client',
            'Hardware device connected.'
        ]
        # Device Lock for threads
        self.lock = threading.RLock()
        self.status = 0
        self.client = None
        printDbg("Creating HW device class")
        self.sig_progress.connect(self.updateSigProgress)



    @process_trezor_exceptions
    def append_inputs_to_TX(self, utxo, bip32_path, inputs):
        # Update amount
        self.amount += int(utxo['satoshis'])
        # Add input
        address_n = parse_path(bip32_path)
        prev_hash = binascii.unhexlify(utxo['txid'])
        it = trezor_proto.TxInputType(
            address_n=address_n,
            prev_hash=prev_hash,
            prev_index=int(utxo['vout'])
        )
        inputs.append(it)



    def clearDevice(self, message=''):
        self.status = 1
        if self.client is not None:
            self.client.close()
            self.client = None

        self.sig_disconnected.emit(message)



    @process_trezor_exceptions
    def initDevice(self):
        print("Initializing Trezor")
        with self.lock:
            transport = get_transport()
            ui = ClickUI()
            printOK('Trezor drivers found')
            self.status = 1
            self.client = TrezorClient(transport, ui)
            printOK("Trezor HW device connected [v. %s.%s.%s]" % (
                self.client.features.major_version,
                self.client.features.minor_version,
                self.client.features.patch_version)
            )
            model = self.client.features.model or "1"
            required_version = MINIMUM_FIRMWARE_VERSION[model]
            printDbg("Current version is %s (minimum required: %s)" % (str(self.client.version), str(required_version)))
            self.status = 2



    def load_prev_txes(self, tx_api, rewardsArray, skip_cache: bool = False):
        curr_utxo_checked = 0
        txes = {}
        tx_api.skip_cache = skip_cache
        num_of_txes = sum([len(mnode['utxos']) for mnode in rewardsArray])
        for mn in rewardsArray:
            for utxo in mn['utxos']:
                prev_hash = bytes.fromhex(utxo["txid"])
                if prev_hash not in txes:
                    tx = tx_api[prev_hash]
                    txes[prev_hash] = tx

                # completion percent emitted
                curr_utxo_checked += 1
                completion = int(95 * curr_utxo_checked / num_of_txes)
                self.tx_progress.emit(completion)
        self.tx_progress.emit(100)
        return txes



    def prepare_transfer_tx_bulk(self, caller, rewardsArray, dest_address, tx_fee, useSwiftX=False, isTestnet=False):
        inputs = []
        outputs = []
        c_name = "PIVX"
        if isTestnet:
            c_name += " Testnet"
        coin = coins.by_name[c_name]
        with self.lock:
            self.amount = 0

            for mnode in rewardsArray:
                # Add proper HW path (for current device) on each utxo
                if isTestnet:
                    mnode['path'] = MPATH_TESTNET + mnode['path']
                else:
                    mnode['path'] = MPATH + mnode['path']

                # Create a TX input with each utxo
                for utxo in mnode['utxos']:
                    self.append_inputs_to_TX(utxo, mnode['path'], inputs)

            self.amount = int(self.amount)
            self.amount -= int(tx_fee)
            if self.amount < 0:
                raise Exception('Invalid TX: inputs + fee != outputs')

            outputs.append(trezor_proto.TxOutputType(
                address=dest_address,
                address_n=None,
                amount=self.amount,
                script_type=trezor_proto.OutputScriptType.PAYTOSCRIPTHASH
            ))

            tx_api = TxApi(coin)

            for skip_cache in (False, True):
                try:
                    txes = self.load_prev_txes(tx_api, rewardsArray, skip_cache)
                    break
                except exceptions.Cancelled:
                    return
                except Exception as e:
                    if skip_cache:
                        raise

            self.mBox2 = QMessageBox(caller)
            self.messageText = "<p>Confirm transaction on your device, with the following details:</p>"
            # messageText += "From bip32_path: <b>%s</b><br><br>" % str(bip32_path)
            self.messageText += "<p>Payment to:<br><b>%s</b></p>" % dest_address
            self.messageText += "<p>Net amount:<br><b>%s</b> PIV</p>" % str(round(self.amount / 1e8, 8))
            if useSwiftX:
                self.messageText += "<p>Fees (SwiftX flat rate):<br><b>%s</b> PIV<p>" % str(round(int(tx_fee) / 1e8, 8))
            else:
                self.messageText += "<p>Fees:<br><b>%s</b> PIV<p>" % str(round(int(tx_fee) / 1e8, 8))
            messageText = self.messageText + "Signature Progress: 0 %"
            self.mBox2.setText(messageText)
            self.mBox2.setIconPixmap(caller.tabMain.trezorImg.scaledToHeight(200, Qt.SmoothTransformation))
            self.mBox2.setWindowTitle("CHECK YOUR TREZOR")
            self.mBox2.setStandardButtons(QMessageBox.NoButton)
            self.mBox2.setMaximumWidth(500)
            self.mBox2.show()

        ThreadFuns.runInThread(self.signTxSign, (inputs, outputs, txes, isTestnet), self.signTxFinish)



    def scanForAddress(self, account, spath, isTestnet=False):
        curr_addr = None

        with self.lock:
            if not isTestnet:
                curr_path = parse_path(MPATH + "%d'/0/%d" % (account, spath))
                curr_addr = btc.get_address(self.client, 'PIVX', curr_path, False)
            else:
                curr_path = parse_path(MPATH_TESTNET + "%d'/0/%d" % (account, spath))
                curr_addr = btc.get_address(self.client, 'PIVX Testnet', curr_path, False)

        return curr_addr



    def scanForBip32(self, account, address, starting_spath=0, spath_count=10, isTestnet=False):
        found = False
        spath = -1

        for i in range(starting_spath, starting_spath + spath_count):
            printDbg("checking path... %d'/0/%d" % (account, i))
            curr_addr = self.scanForAddress(account, i, isTestnet)
            if curr_addr == address:
                found = True
                spath = i
                break

            sleep(0.01)

        return (found, spath)



    def scanForPubKey(self, account, spath, isTestnet=False):
        result = None
        hwpath = "%d'/0/%d" % (account, spath)
        if isTestnet:
            path = MPATH_TESTNET + hwpath
        else:
            path = MPATH + hwpath

        curr_path = parse_path(path)
        with self.lock:
            result = btc.get_public_node(self.client, curr_path)

        return result.node.public_key.hex()


    def signMess(self, caller, hwpath, message, isTestnet=False):
        if isTestnet:
            path = MPATH_TESTNET + hwpath
        else:
            path = MPATH + hwpath
        # Connection pop-up
        self.mBox = QMessageBox(caller.ui)
        messageText = "Check display of your hardware device\n\n- masternode message:\n\n%s\n\n-path:\t%s\n" % (
            splitString(message, 32), path)
        self.mBox.setText(messageText)
        self.mBox.setIconPixmap(caller.ui.trezorImg.scaledToHeight(200, Qt.SmoothTransformation))
        self.mBox.setWindowTitle("CHECK YOUR TREZOR")
        self.mBox.setStandardButtons(QMessageBox.NoButton)
        self.mBox.show()

        # Sign message
        ThreadFuns.runInThread(self.signMessageSign, (path, message, isTestnet), self.signMessageFinish)



    @process_trezor_exceptions
    def signMessageSign(self, ctrl, path, mess, isTestnet):
        self.signature = None
        if isTestnet:
            hw_coin = "PIVX Testnet"
        else:
            hw_coin = "PIVX"
        with self.lock:
            try:
                bip32_path = parse_path(path)
                signed_mess = btc.sign_message(self.client, hw_coin, bip32_path, mess)
                self.signature = signed_mess.signature
            except exceptions.Cancelled:
                pass



    def signMessageFinish(self):
        with self.lock:
            self.mBox.accept()
        if self.signature is None:
            printOK("Signature refused by the user")
            self.sig1done.emit("None")
        else:
            self.sig1done.emit(self.signature.hex())



    @process_trezor_exceptions
    def signTxSign(self, ctrl, inputs, outputs, txes, isTestnet=False):
        self.tx_raw = None
        if isTestnet:
            hw_coin = "PIVX Testnet"
        else:
            hw_coin = "PIVX"
        with self.lock:
            try:
                signed = sign_tx(self.sig_progress, self.client, hw_coin, inputs, outputs, prev_txes=txes)
            except exceptions.Cancelled:
                return

        self.tx_raw = bytearray(signed[1])
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
        # -1 simply adds a waiting message to the actual progress
        if percent == -1:
            t = self.mBox2.text()
            messageText = t + "<br>Please confirm action on your Trezor device..."
        else:
            messageText = self.messageText + "Signature Progress: <b style='color:red'>" + str(percent) + " %</b>"
        self.mBox2.setText(messageText)
        QApplication.processEvents()



# From trezorlib.btc
def sign_tx(sig_percent, client, coin_name, inputs, outputs, details=None, prev_txes=None):
    # set up a transactions dict
    txes = {None: trezor_proto.TransactionType(inputs=inputs, outputs=outputs)}
    # preload all relevant transactions ahead of time
    for inp in inputs:
        if inp.script_type not in (
            trezor_proto.InputScriptType.SPENDP2SHWITNESS,
            trezor_proto.InputScriptType.SPENDWITNESS,
            trezor_proto.InputScriptType.EXTERNAL,
        ):
            try:
                prev_tx = prev_txes[inp.prev_hash]
            except Exception as e:
                raise ValueError("Could not retrieve prev_tx") from e
            if not isinstance(prev_tx, trezor_proto.TransactionType):
                raise ValueError("Invalid value for prev_tx") from None
            txes[inp.prev_hash] = prev_tx

    if details is None:
        signtx = trezor_proto.SignTx()
    else:
        signtx = details

    signtx.coin_name = coin_name
    signtx.inputs_count = len(inputs)
    signtx.outputs_count = len(outputs)

    res = client.call(signtx)

    # Prepare structure for signatures
    signatures = [None] * len(inputs)
    serialized_tx = b""

    def copy_tx_meta(tx):
        tx_copy = trezor_proto.TransactionType()
        tx_copy.CopyFrom(tx)
        # clear fields
        tx_copy.inputs_cnt = len(tx.inputs)
        tx_copy.inputs = []
        tx_copy.outputs_cnt = len(tx.bin_outputs or tx.outputs)
        tx_copy.outputs = []
        tx_copy.bin_outputs = []
        tx_copy.extra_data_len = len(tx.extra_data or b"")
        tx_copy.extra_data = None
        return tx_copy

    R = trezor_proto.RequestType

    percent = 0  # Used for signaling progress. 1-10 for inputs/outputs, 10-100 for sigs.
    sig_percent.emit(percent)
    while isinstance(res, trezor_proto.TxRequest):
        # If there's some part of signed transaction, let's add it
        if res.serialized:
            if res.serialized.serialized_tx:
                serialized_tx += res.serialized.serialized_tx

            if res.serialized.signature_index is not None:
                idx = res.serialized.signature_index
                sig = res.serialized.signature
                if signatures[idx] is not None:
                    raise ValueError("Signature for index %d already filled" % idx)
                signatures[idx] = sig
                # emit completion percent
                percent = 10 + int(90 * (idx+1) / len(signatures))
                sig_percent.emit(percent)

        if res.request_type == R.TXFINISHED:
            break

        # Device asked for one more information, let's process it.
        current_tx = txes[res.details.tx_hash]

        if res.request_type == R.TXMETA:
            msg = copy_tx_meta(current_tx)
            res = client.call(trezor_proto.TxAck(tx=msg))

        elif res.request_type == R.TXINPUT:
            if percent == 0 or (res.details.request_index > 0 and percent < 10):
                percent = 1 + int(8 * (res.details.request_index + 1) / len(inputs))
                sig_percent.emit(percent)
            msg = trezor_proto.TransactionType()
            msg.inputs = [current_tx.inputs[res.details.request_index]]
            res = client.call(trezor_proto.TxAck(tx=msg))

        elif res.request_type == R.TXOUTPUT:
            # Update just one percent then display additional waiting message (emitting -1)
            if percent == 9:
                percent += 1
                sig_percent.emit(percent)
                sig_percent.emit(-1)

            msg = trezor_proto.TransactionType()
            if res.details.tx_hash:
                msg.bin_outputs = [current_tx.bin_outputs[res.details.request_index]]
            else:
                msg.outputs = [current_tx.outputs[res.details.request_index]]

            res = client.call(trezor_proto.TxAck(tx=msg))

        elif res.request_type == R.TXEXTRADATA:
            o, l = res.details.extra_data_offset, res.details.extra_data_len
            msg = trezor_proto.TransactionType()
            msg.extra_data = current_tx.extra_data[o : o + l]
            res = client.call(trezor_proto.TxAck(tx=msg))

    if isinstance(res, trezor_proto.Failure):
        raise Exception("Signing failed")

    if not isinstance(res, trezor_proto.TxRequest):
        raise Exception("Unexpected message")

    if None in signatures:
        raise RuntimeError("Some signatures are missing!")

    return signatures, serialized_tx
