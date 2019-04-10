#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from random import choice
import requests

from misc import getCallerName, getFunctionName, printException

api_keys = ["b62b40b5091e", "f1d66708a077", "ed85c85c0126", "ccc60d06f737"]


def process_cryptoID_exceptions(func):

    def process_cryptoID_exceptions_int(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            message = "CryptoID Client exception"
            printException(getCallerName(True), getFunctionName(True), message, str(e))
            return None

    return process_cryptoID_exceptions_int



def UTXOS_cryptoID_to_trezor(utxos):
    # convert JSON labels
    new_utxos = []
    for u in utxos:
        new_u = {}
        new_u["txid"] = u["tx_hash"]
        new_u["vout"] = u["tx_ouput_n"]
        new_u["satoshis"] = u["value"]
        new_u["confirmations"] = u["confirmations"]
        new_u["script"] = u["script"]
        new_utxos.append(new_u)

    return new_utxos


class CryptoIDClient:

    def __init__(self, isTestnet=False):
        if isTestnet:
            raise Exception("\nNo CryptoID Testnet server\n")
        self.isTestnet = False
        self.url = "http://chainz.cryptoid.info/pivx/api.dws"
        self.parameters = {}



    def checkResponse(self, parameters):
        key = choice(api_keys)
        parameters['key'] = key
        resp = requests.get(self.url, params=parameters)
        if resp.status_code == 200:
            data = resp.json()
            return data
        return None



    @process_cryptoID_exceptions
    def getAddressUtxos(self, address):
        self.parameters = {}
        self.parameters['q'] = 'unspent'
        self.parameters['active'] = address
        res = self.checkResponse(self.parameters)
        if res is None:
            return None
        else:
            return UTXOS_cryptoID_to_trezor(res['unspent_outputs'])



    @process_cryptoID_exceptions
    def getBalance(self, address):
        self.parameters = {}
        self.parameters['q'] = 'getbalance'
        self.parameters['a'] = address
        return self.checkResponse(self.parameters)

