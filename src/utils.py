#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
from misc import getCallerName, getFunctionName, printException
from bitcoin import b58check_to_hex, ecdsa_raw_sign, ecdsa_raw_verify, privkey_to_pubkey, encode_sig, decode_sig, dbl_sha256
from pivx_hashlib import wif_to_privkey
from pivx_b58 import b58decode
from bitcoin import bin_dbl_sha256
from ipaddress import ip_address
# Bitcoin opcodes used in the application
OP_DUP = b'\x76'
OP_HASH160 = b'\xA9'
OP_QEUALVERIFY = b'\x88'
OP_CHECKSIG = b'\xAC'
OP_EQUAL = b'\x87'
OP_RETURN = b'\x6a'
# Prefixes - Check P2SH
P2PKH_PREFIXES = ['D']
P2SH_PREFIXES = ['7']


def b64encode(text):
    return base64.b64encode(bytearray.fromhex(text)).decode('utf-8')
    


def checkPivxAddr(address):
    try:
        # check leading char 'D'
        if address[0] != 'D':
            return False
        
        # decode and verify checksum
        addr_bin = bytes.fromhex(b58decode(address).hex())
        addr_bin_check = bin_dbl_sha256(addr_bin[0:-4])[0:4]
        if addr_bin[-4:] != addr_bin_check:
            return False
        
        return True
    except Exception:
        return False



def compose_tx_locking_script(dest_address):
    """
    Create a Locking script (ScriptPubKey) that will be assigned to a transaction output.
    :param dest_address: destination address in Base58Check format
    :return: sequence of opcodes and its arguments, defining logic of the locking script
    """
    pubkey_hash = bytearray.fromhex(b58check_to_hex(dest_address)) # convert address to a public key hash
    if len(pubkey_hash) != 20:
        raise Exception('Invalid length of the public key hash: ' + str(len(pubkey_hash)))

    if dest_address[0] in P2PKH_PREFIXES:
        # sequence of opcodes/arguments for p2pkh (pay-to-public-key-hash)
        scr = OP_DUP + \
              OP_HASH160 + \
              int.to_bytes(len(pubkey_hash), 1, byteorder='little') + \
              pubkey_hash + \
              OP_QEUALVERIFY + \
              OP_CHECKSIG
    elif dest_address[0] in P2SH_PREFIXES:
        # sequence of opcodes/arguments for p2sh (pay-to-script-hash)
        scr = OP_HASH160 + \
              int.to_bytes(len(pubkey_hash), 1, byteorder='little') + \
              pubkey_hash + \
              OP_EQUAL
    else:
        raise Exception('Invalid dest address prefix: ' + dest_address[0])
    return scr



def compose_tx_locking_script_OR(message):
    """
    Create a Locking script (ScriptPubKey) that will be assigned to a transaction output.
    :param message: data for the OP_RETURN
    :return: sequence of opcodes and its arguments, defining logic of the locking script
    """

    scr = OP_RETURN + int.to_bytes(len(data), 1, byteorder='little') + message.encode()
              
    return scr



def ecdsa_sign(msg, priv):
    """
    Based on project: https://github.com/chaeplin/dashmnb.
    """
    v, r, s = ecdsa_raw_sign(electrum_sig_hash(msg), priv)
    sig = encode_sig(v, r, s)
    pubkey = privkey_to_pubkey(wif_to_privkey(priv))

    ok = ecdsa_raw_verify(electrum_sig_hash(msg), decode_sig(sig), pubkey)
    if not ok:
        raise Exception('Bad signature!')
    return sig    



def electrum_sig_hash(message):
    """
    Based on project: https://github.com/chaeplin/dashmnb.
    """
    padded = b'\x18DarkNet Signed Message:\n' + num_to_varint(len(message)) + from_string_to_bytes(message)
    return dbl_sha256(padded)


    
def extract_pkh_from_locking_script(script):
    if len(script) == 25:
        if script[0:1] == OP_DUP and script[1:2] == OP_HASH160:
            if read_varint(script, 2)[0] == 20:
                return script[3:23]
            else:
                raise Exception('Non-standard public key hash length (should be 20)')
    raise Exception('Non-standard locking script type (should be P2PKH)')
    


def from_string_to_bytes(a):
    return a if isinstance(a, bytes) else bytes(a, 'utf-8')



def ipmap(ip, port):
    try:
        ipv6map = ''
        
        if len(ip)>6 and ip.endswith('.onion'):
            pchOnionCat = bytearray([0xFD,0x87,0xD8,0x7E,0xEB,0x43])
            vchAddr = base64.b32decode(ip[0:-6], True)
            if len(vchAddr) != 16-len(pchOnionCat):
                raise Exception('Invalid onion %s' % s)
            return pchOnionCat.hex() + vchAddr.hex() + int(port).to_bytes(2, byteorder='big').hex()
            
        ipAddr = ip_address(ip)
        
        if ipAddr.version==4:
            ipv6map = '00000000000000000000ffff'
            ip_digits = map(int, ipAddr.exploded.split('.'))
            for i in ip_digits:
                ipv6map += i.to_bytes(1, byteorder='big')[::-1].hex()
        
        elif ipAddr.version==6:
            ip_hextets = map(str, ipAddr.exploded.split(':'))
            for a in ip_hextets:
                ipv6map += a
        
        else:
            raise Exception("invalid version number (%d)" % version)
        
              
        ipv6map += int(port).to_bytes(2, byteorder='big').hex()
        if len(ipv6map) != 36:
            raise Exception("Problems! len is %d" % len(ipv6map))
        return ipv6map
    
    except Exception as e:
            err_msg = "error in ipmap"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            
            
            
def num_to_varint(a):
    """
    Based on project: https://github.com/chaeplin/dashmnb
    """
    x = int(a)
    if x < 253:
        return x.to_bytes(1, byteorder='big')
    elif x < 65536:
        return int(253).to_bytes(1, byteorder='big') + x.to_bytes(2, byteorder='little')
    elif x < 4294967296:
        return int(254).to_bytes(1, byteorder='big') + x.to_bytes(4, byteorder='little')
    else:
        return int(255).to_bytes(1, byteorder='big') + x.to_bytes(8, byteorder='little')
    
    
       
def read_varint(buffer, offset):
    if (buffer[offset] < 0xfd):
        value_size = 1
        value = buffer[offset]
    elif (buffer[offset] == 0xfd):
        value_size = 3
        value = int.from_bytes(buffer[offset + 1: offset + 3], byteorder='little')
    elif (buffer[offset] == 0xfe):
        value_size = 5
        value = int.from_bytes(buffer[offset + 1: offset + 5], byteorder='little')
    elif (buffer[offset] == 0xff):
        value_size = 9
        value = int.from_bytes(buffer[offset + 1: offset + 9], byteorder='little')
    else:
        raise Exception("Invalid varint size")
    return value, value_size
            
            

def serialize_input_str(tx, prevout_n, sequence, script_sig):
    """
    Based on project: https://github.com/chaeplin/dashmnb.
    """
    s = ['CTxIn(']
    s.append('COutPoint(%s, %s)' % (tx, prevout_n))
    s.append(', ')
    if tx == '00' * 32 and prevout_n == 0xffffffff:
        s.append('coinbase %s' % script_sig)
        
    else:
        script_sig2 = script_sig
        if len(script_sig2) > 24:
            script_sig2 = script_sig2[0:24]
        s.append('scriptSig=%s' % script_sig2)

    if sequence != 0xffffffff:
        s.append(', nSequence=%d' % sequence)
        
    s.append(')')
    return ''.join(s)