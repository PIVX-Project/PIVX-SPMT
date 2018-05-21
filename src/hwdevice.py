#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from btchip.btchip import btchip, getDongle, BTChipException
from btchip.btchipUtils import compress_public_key, bitcoinTransaction, bitcoinInput, bitcoinOutput
from bitcoin import bin_hash160
from time import sleep
from misc import printDbg, printException, printOK, getCallerName, getFunctionName, splitString
from constants import MPATH
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.Qt import QObject
from threads import ThreadFuns
from utils import extract_pkh_from_locking_script, compose_tx_locking_script
from pivx_hashlib import pubkey_to_address, single_sha256


def process_ledger_exceptions(func):

    def process_ledger_exceptions_int(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BTChipException as e:
            printDbg('Error while communicating with Ledger hardware wallet.')
            if (e.sw in (0x6d00, 0x6700)):
                e.message += '\n\nMake sure the PIVX app is running on your Ledger device.'
            elif (e.sw == 0x6982):
                e.message += '\n\nMake sure you have entered the PIN on your Ledger device.'
            raise
    return process_ledger_exceptions_int




class HWdevice(QObject):
    # signal: sig1 (thread) is done - emitted by signMessageFinish
    sig1done = pyqtSignal(str)
    # signal: sigtx (thread) is done - emitted by signTxFinish
    sigTxdone = pyqtSignal(bytearray, str)
    
    def __init__(self, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        # Device Lock for threads
        printDbg("Creating HW device class")
        self.initDevice()
        
    @process_ledger_exceptions
    def initDevice(self):
        try:
            if hasattr(self, 'dongle'):
                self.dongle.close()
            self.dongle = getDongle(False)
            printOK('Ledger Nano S drivers found')
            self.chip = btchip(self.dongle)
            printDbg("Ledger Initialized")
            self.initialized = True
            ver = self.chip.getFirmwareVersion()
            printOK("Ledger HW device connected [v. %s]" % str(ver.get('version')))
            
        except Exception as e:
            err_msg = 'error Initializing Ledger'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            self.initialized = False
            if hasattr(self, 'dongle'):
                self.dongle.close()
            
        
    
    # Status codes:
    # 0 - not connected
    # 1 - not in pivx app
    # 2 - fine
    @process_ledger_exceptions
    def getStatusCode(self):
        try:
            if self.initialized:
                if not self.checkApp():
                    statusCode = 1     
                else:
                    statusCode = 2
            else:
                statusCode = 0          
        except Exception as e:
            err_msg = 'error in getStatusCode'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            statusCode = 0
        return statusCode
    
    
    
        
    @process_ledger_exceptions
    def getStatusMess(self, statusCode = None):
        if statusCode == None or not statusCode in [0, 1, 2]:
            statusCode = self.getStatusCode()
        messages = {
            0: 'Unable to connect to the device',
            1: 'Open PIVX app on Ledger device',
            2: 'HW DEVICE CONNECTED!'}
        return messages[statusCode]
    
    
        
    
    @process_ledger_exceptions
    def checkApp(self):
        printDbg("Checking app")
        try:
            firstAddress = self.chip.getWalletPublicKey(MPATH + "0'/0/0").get('address')[12:-2]
            if firstAddress[0] == 'D':
                printOK("found PIVX app on ledger device")
                return True       
        except Exception as e:
            err_msg = 'error in checkApp'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        return False 
    
    
    
    
    @process_ledger_exceptions
    def prepare_transfer_tx(self, caller, bip32_path,  utxos_to_spend, dest_address, tx_fee, rawtransactions):
        # For each UTXO create a Ledger 'trusted input'
        self.trusted_inputs = []
        #    https://klmoney.wordpress.com/bitcoin-dissecting-transactions-part-2-building-a-transaction-by-hand)
        self.arg_inputs = []
        self.amount = 0
        for idx, utxo in enumerate(utxos_to_spend):
            
            self.amount += int(utxo['value'])
            raw_tx = bytearray.fromhex(rawtransactions[utxo['tx_hash']])

            if not raw_tx:
                raise Exception("Can't find raw transaction for txid: " + rawtransactions[utxo['tx_hash']])
            
            # parse the raw transaction, so that we can extract the UTXO locking script we refer to
            prev_transaction = bitcoinTransaction(raw_tx)

            utxo_tx_index = utxo['tx_ouput_n']
            if utxo_tx_index < 0 or utxo_tx_index > len(prev_transaction.outputs):
                raise Exception('Incorrect value of outputIndex for UTXO %s' % str(idx))

            trusted_input = self.chip.getTrustedInput(prev_transaction, utxo_tx_index)
            self.trusted_inputs.append(trusted_input)
           
            # Hash check
            curr_pubkey = compress_public_key(self.chip.getWalletPublicKey(bip32_path)['publicKey'])
            pubkey_hash = bin_hash160(curr_pubkey)
            pubkey_hash_from_script = extract_pkh_from_locking_script(prev_transaction.outputs[utxo_tx_index].script)
            if pubkey_hash != pubkey_hash_from_script:
                text = "Error: different public key hashes for the BIP32 path and the UTXO"
                text += "locking script. Your signed transaction will not be validated by the network.\n"
                text += "pubkey_hash: %s\n" % str(pubkey_hash)
                text += "pubkey_hash_from_script: %s\n" % str(pubkey_hash_from_script)
                printDbg(text)

            self.arg_inputs.append({
                'locking_script': prev_transaction.outputs[utxo['tx_ouput_n']].script,
                'pubkey': curr_pubkey,
                'bip32_path': bip32_path,
                'outputIndex': utxo['tx_ouput_n'],
                'txid': utxo['tx_hash']
            })

        self.amount -= int(tx_fee)
        self.amount = int(self.amount)
        arg_outputs = [{'address': dest_address, 'valueSat': self.amount}] # there will be multiple outputs soon
        self.new_transaction = bitcoinTransaction()  # new transaction object to be used for serialization at the last stage
        self.new_transaction.version = bytearray([0x01, 0x00, 0x00, 0x00])
        
        try:
            for o in arg_outputs:
                output = bitcoinOutput()
                output.script = compose_tx_locking_script(o['address'])
                output.amount = int.to_bytes(o['valueSat'], 8, byteorder='little')
                self.new_transaction.outputs.append(output)
        except Exception:
            raise
        
        # join all outputs - will be used by Ledger for signing transaction
        self.all_outputs_raw = self.new_transaction.serializeOutputs()

        self.mBox2 = QMessageBox(caller)
        messageText = "Check display of your hardware device<br><br><br>"
        messageText += "From bip32_path: <b>%s</b><br><br>" % str(bip32_path)
        messageText += "To PIVX Address: <b>%s</b><br><br>" % dest_address
        messageText += "PIV amount: <b>%s</b><br>" % str(round(self.amount / 1e8, 8))
        messageText += "plus PIV for fee: <b>%s</b><br><br>" % str(round(int(tx_fee) / 1e8, 8))
        self.mBox2.setText(messageText)
        self.mBox2.setIconPixmap(caller.tabMain.ledgerImg.scaledToHeight(200, Qt.SmoothTransformation))
        self.mBox2.setWindowTitle("CHECK YOUR LEDGER")
        self.mBox2.setStandardButtons(QMessageBox.NoButton)
        self.mBox2.setMaximumWidth(500)
        self.mBox2.show()
        
        ThreadFuns.runInThread(self.signTxSign, (), self.signTxFinish)
        
    
    
    @process_ledger_exceptions
    def scanForAddress(self, account, spath, isTestnet=False):
        printOK("Scanning for Address of path_id %s on account n° %s" % (str(spath), str(account)))
        curr_path = MPATH + "%d'/0/%d" % (account, spath) 
        try:
            if not isTestnet:
                curr_addr = self.chip.getWalletPublicKey(curr_path).get('address')[12:-2]
            else:
                pubkey = compress_public_key(self.chip.getWalletPublicKey(curr_path).get('publicKey')).hex()
                curr_addr = pubkey_to_address(pubkey, isTestnet) 
                                         
        except Exception as e:
            err_msg = 'error in scanForAddress'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            return None
        return curr_addr
    
    
    
    
    @process_ledger_exceptions
    def scanForBip32(self, account, address, starting_spath=0, spath_count=10, isTestnet=False):
        found = False
        spath = -1
         
        printOK("Scanning for Bip32 path of address: %s" % address)
        for i in range(starting_spath, starting_spath+spath_count):
            curr_path = MPATH + "%d'/0/%d" % (account, i)
            printDbg("checking path... %s" % curr_path)
            try:
                if not isTestnet:
                    curr_addr = self.chip.getWalletPublicKey(curr_path).get('address')[12:-2]
                else:
                    pubkey = compress_public_key(self.chip.getWalletPublicKey(curr_path).get('publicKey')).hex()          
                    curr_addr = pubkey_to_address(pubkey, isTestnet)     
                             
                if curr_addr == address:
                    found = True
                    spath = i
                    break
                
                sleep(0.01)
            
            except Exception as e:
                err_msg = 'error in scanForBip32'
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
                
        return (found, spath)
            
            
            
    
    @process_ledger_exceptions
    def scanForPubKey(self, account, spath):
        printOK("Scanning for Address of path_id %s on account n° %s" % (str(spath), str(account)))
        curr_path = MPATH + "%d'/0/%d" % (account, spath)
        try:
            nodeData = self.chip.getWalletPublicKey(curr_path)          
                
        except Exception as e:
            err_msg = 'error in scanForPubKey'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            return None
        
        return compress_public_key(nodeData.get('publicKey')).hex()
    
    
    
    
    @process_ledger_exceptions        
    def signMess(self, caller, path, message):
        # Ledger doesn't accept characters other that ascii printable:
        # https://ledgerhq.github.io/btchip-doc/bitcoin-technical.html#_sign_message
        message = message.encode('ascii', 'ignore')
        message_sha = splitString(single_sha256(message).hex(),32);
        
        # Connection pop-up
        mBox  = QMessageBox(caller.ui)
        warningText = "Another application (such as Ledger Wallet app) has probably taken over "
        warningText += "the communication with the Ledger device.<br><br>To continue, close that application and "
        warningText += "click the <b>Retry</b> button.\nTo cancel, click the <b>Abort</b> button"
        mBox.setText(warningText)
        mBox.setWindowTitle("WARNING")
        mBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Abort);
        
        # Ask confirmation
        info = self.chip.signMessagePrepare(path, message)
        while info['confirmationNeeded'] and info['confirmationType'] == 34:
            ans = mBox.exec_()        
            # we need to reconnect the device
            self.dongle.close()
            self.initialized = False
            self.initDevice()
            
            if ans == QMessageBox.Abort:
                raise Exception('Message Signature failed')
            
            info = self.chip.signMessagePrepare(path, message)
            

        printOK('Signing Message')
        self.mBox = QMessageBox(caller.ui)
        messageText = "Check display of your hardware device\n\n" + "- masternode message hash:\n\n%s\n\n-path:\t%s\n" % (message_sha, path)
        self.mBox.setText(messageText)
        self.mBox.setIconPixmap(caller.ui.ledgerImg.scaledToHeight(200, Qt.SmoothTransformation))
        self.mBox.setWindowTitle("CHECK YOUR LEDGER")
        self.mBox.setStandardButtons(QMessageBox.NoButton)
        
        self.mBox.show()
        # Sign message
        ThreadFuns.runInThread(self.signMessageSign, (), self.signMessageFinish)



    
    @process_ledger_exceptions
    def signMessageSign(self, ctrl):
        try:
            self.signature = self.chip.signMessageSign()
            
        except:
            self.signature = None
    
    
    
    
    @process_ledger_exceptions        
    def signMessageFinish(self):
        self.mBox.accept()
        if self.signature != None:
            if len(self.signature) > 4:
                rLength = self.signature[3]
                r = self.signature[4 : 4 + rLength]
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
        try:
            starting = True
            # sign all inputs on Ledger and add inputs in the self.new_transaction object for serialization
            for idx, new_input in enumerate(self.arg_inputs):
                self.chip.startUntrustedTransaction(starting, idx, self.trusted_inputs, new_input['locking_script'])
                
                self.chip.finalizeInputFull(self.all_outputs_raw)

                sig = self.chip.untrustedHashSign(new_input['bip32_path'], lockTime=0)
                
                new_input['signature'] = sig
                inputTx = bitcoinInput()
                inputTx.prevOut = bytearray.fromhex(new_input['txid'])[::-1] + int.to_bytes(new_input['outputIndex'], 4, byteorder='little')
                
                inputTx.script = bytearray([len(sig)]) + sig + bytearray([0x21]) + new_input['pubkey']

                inputTx.sequence = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

                self.new_transaction.inputs.append(inputTx)

                starting = False
    
            self.new_transaction.lockTime = bytearray([0, 0, 0, 0])
            self.tx_raw = bytearray(self.new_transaction.serialize())
            
        except Exception as e:
            printException(getCallerName(), getFunctionName(), "Signature Exception", e.args)
            self.tx_raw = None
    
    
    
    
    @process_ledger_exceptions        
    def signTxFinish(self):
        self.mBox2.accept()
        try:
            if self.tx_raw is not None:
                # Signal to be catched by FinishSend on TabRewards
                self.sigTxdone.emit(self.tx_raw, str(round(self.amount / 1e8, 8)))
            else:
                printOK("Transaction refused by the user")
                
        except Exception as e:    
            printDbg(e) 
                    