import unittest
from hwdevice import HWdevice
from btchip.btchipUtils import compress_public_key, bitcoinTransaction, bitcoinInput, bitcoinOutput
from bitcoin import bin_hash160
from utils import extract_pkh_from_locking_script, compose_tx_locking_script

class TestHwDeviceMethods(unittest.TestCase):
    
    def test_transaction(self):
        # Init HW device & Api client
        device = HWdevice()
        try:
            # Read input data from file
            import simplejson as json
            with open('test_transaction.data.json') as data_file:
                input_data = json.load(data_file)
            data_file.close()
            # Parse input data
            path = input_data['path']
            pivx_address_to = input_data['address_from']
            fee = input_data['fee']
            utxos = input_data['unspent_outputs']
            rawtransactions = input_data['raw_transactions']
            
            txraw, amount = self.signTx(device, path, utxos, pivx_address_to, fee, rawtransactions)
            print(txraw)
            print(amount)
        
        except Exception:
            device.dongle.close()
            raise
        
        
        
        
    
    # from:
    # -- hwdevice.prepare_transfer_tx
    # -- hwdevice.signTxSign
    # -- hwdevice.signTxFinish
    # without gui
    def signTx(self, device, bip32_path,  utxos_to_spend, dest_address, tx_fee, rawtransactions):
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

            trusted_input = device.chip.getTrustedInput(prev_transaction, utxo_tx_index)
            self.trusted_inputs.append(trusted_input)
           
            # Hash check
            curr_pubkey = compress_public_key(device.chip.getWalletPublicKey(bip32_path)['publicKey'])
            pubkey_hash = bin_hash160(curr_pubkey)
            pubkey_hash_from_script = extract_pkh_from_locking_script(prev_transaction.outputs[utxo_tx_index].script)
            if pubkey_hash != pubkey_hash_from_script:
                text = "Error: different public key hashes for the BIP32 path and the UTXO"
                text += "locking script. Your signed transaction will not be validated by the network.\n"
                text += "pubkey_hash: %s\n" % str(pubkey_hash)
                text += "pubkey_hash_from_script: %s\n" % str(pubkey_hash_from_script)
                print(text)

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
        
        starting = True
        # sign all inputs on Ledger and add inputs in the self.new_transaction object for serialization
        for idx, new_input in enumerate(self.arg_inputs):
            device.chip.startUntrustedTransaction(starting, idx, self.trusted_inputs, new_input['locking_script'])
            
            device.chip.finalizeInputFull(self.all_outputs_raw)

            sig = device.chip.untrustedHashSign(new_input['bip32_path'], lockTime=0)
            
            new_input['signature'] = sig
            inputTx = bitcoinInput()
            inputTx.prevOut = bytearray.fromhex(new_input['txid'])[::-1] + int.to_bytes(new_input['outputIndex'], 4, byteorder='little')
            
            inputTx.script = bytearray([len(sig)]) + sig + bytearray([0x21]) + new_input['pubkey']

            inputTx.sequence = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

            self.new_transaction.inputs.append(inputTx)

            starting = False
    
            self.new_transaction.lockTime = bytearray([0, 0, 0, 0])
            self.tx_raw = bytearray(self.new_transaction.serialize())

        if self.tx_raw is not None:
            return (self.tx_raw, str(round(self.amount / 1e8, 8)))
        else:
            # transaction refused by user
            return (None, "")
            
        
        
    
    if __name__ == '__main__':
        unittest.main()