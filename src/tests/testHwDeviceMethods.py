import unittest
from hwdevice import HWdevice
from rpcClient import RpcClient
from btchip.btchipUtils import compress_public_key, bitcoinTransaction, bitcoinInput, bitcoinOutput
from bitcoin import bin_hash160
from utils import extract_pkh_from_locking_script, compose_tx_locking_script

class TestHwDeviceMethods(unittest.TestCase):
    def setUp(self):
        self.device = HWdevice()
        self.rpcClient = RpcClient()
        hwStatus = self.device.getStatusCode()
        rpcStatus, blockNum = self.rpcClient.getStatus()
        if hwStatus != 2:
            self.skipTest("Ledger not connected or pivx app closed")
        if not rpcStatus:
            self.skipTest("RPC not connected")
        
        
    
    def tearDown(self):
        if hasattr(self.device, 'dongle'):
            self.device.dongle.close()
            self.device.parent = None
            print("Dongle Closed")
        if hasattr(self.rpcClient, 'conn'):
            self.rpcClient.parent = None
    

    
    
    def test_transaction(self):
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
        print("=================================")
        print("   Press 'OK' on Ledger device   ")
        print("---------------------------------")
        txraw, amount = self.signTx(self.device, path, utxos, pivx_address_to, fee, rawtransactions)
        
        # Check total amount
        total = sum([int(utxo['value']) for utxo in utxos], 0)
        amount = round(float(amount)*1e8)
        self.assertEqual(total-fee, amount)
        
        # Decode Raw Tx to inspect and check inputs
        inputs = [utxo["tx_hash"] for utxo in utxos]
        decodedTx = self.rpcClient.decodeRawTx(txraw.hex())
        decoded_inputs = [decoded_input["txid"] for decoded_input in decodedTx["vin"]]
        while len(inputs) > 0:
            input_tx = inputs.pop()
            self.assertIn(input_tx, decoded_inputs)
            decoded_inputs.remove(input_tx)

        
        
    
    def test_scanForBip32(self):
        # Get accounts obtained from seed outside ledger 
        # (5 accounts. 5 addresses per account)
        with open('accounts.data.txt') as datafile:
            # datafile has 4 lines of header (lines_offset)
            for i in range(4):
                datafile.readline()
            for account_n in range(5):
                for address_n in range(5):
                    address = datafile.readline().split()[0]
                    
                    result, index = self.device.scanForBip32(account_n, address, starting_spath=address_n, spath_count=1)
                    # Address found in account_n  with index.
                    self.assertTrue(result)
            
            
            
            
    def test_scanForPubKey(self):
        # Get accounts obtained from seed outside ledger 
        # (5 accounts. 5 addresses per account)
        with open('accounts.data.txt') as datafile:
            # datafile has 4 lines of header (lines_offset)
            for i in range(4):
                datafile.readline()
            for account_n in range(5):
                for address_n in range(5):
                    pubkey = datafile.readline().split()[1]
                    
                    result = self.device.scanForPubKey(account_n, address_n)
                    # Pubkey checks out
                    self.assertEqual(result, pubkey)
                
                
          
                
                
    def test_signature(self):
        # Get message and path from datafile
        import simplejson as json
        with open('test_signature.data.json') as data_file:
            input_data = json.load(data_file)
            
        # Rename input data
        message = input_data['message']
        path = input_data['path']
        pivx_address = self.device.chip.getWalletPublicKey(path).get('address')[12:-2]
        
        # sign message on ledger
        print("=================================")
        print("   Press 'OK' on Ledger device   ")
        print("---------------------------------")
        signature = self.signMess(path, message)
        
        # verify with rpc client
        result = self.rpcClient.verifyMessage(pivx_address, signature, message)
        print("sig = %s\naddress=%s" % (signature, pivx_address))
        self.assertTrue(result)
        
   
   
   
        
    # from:
    # -- hwdevice.signMess
    # -- hwdevice.signMessSign
    # -- hwdevice.signMessFinish
    # without gui
    def signMess(self, path, message):
        from utils import b64encode 
        # Ledger doesn't accept characters other that ascii printable:
        # https://ledgerhq.github.io/btchip-doc/bitcoin-technical.html#_sign_message
        message = message.encode('ascii', 'ignore')
        self.device.chip.signMessagePrepare(path, message)
        signature = self.device.chip.signMessageSign(None)
        if signature != None:
            if len(signature) > 4:
                rLength = signature[3]
                r = signature[4 : 4 + rLength]
                if len(signature) > 4 + rLength + 1:               
                    sLength = signature[4 + rLength + 1]
                    if len(signature) > 4 + rLength + 2: 
                        s = signature[4 + rLength + 2:]
                        if rLength == 33:
                            r = r[1:]
                        if sLength == 33:
                            s = s[1:]
            
                        work = bytes(chr(27 + 4 + (signature[0] & 0x01)), "utf-8") + r + s
                        print("Message signed")
                        sig1 = work.hex()
                    else:
                        print('client.signMessageSign() returned invalid response (code 3): ' + signature.hex())
                        sig1 = "None"
                else:
                    print('client.signMessageSign() returned invalid response (code 2): ' + signature.hex())
                    sig1 = "None"
            else:
                print('client.signMessageSign() returned invalid response (code 1): ' + signature.hex())
                sig1 = "None"
        else:
            print("Signature refused by the user")
            sig1 = "None"
            
        return b64encode(sig1)
    
    
    
    
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

            trusted_input = self.device.chip.getTrustedInput(prev_transaction, utxo_tx_index)
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
        unittest.main(verbosity=2)