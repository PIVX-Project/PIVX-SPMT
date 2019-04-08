#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from blockbookClient import BlockBookClient
from cryptoIDClient import CryptoIDClient

from misc import getCallerName, getFunctionName, printException, printError

def process_api_exceptions(func):

    def process_api_exceptions_int(*args, **kwargs):
        client = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            message = "Primary API source not responding. Trying secondary"
            printException(getCallerName(True), getFunctionName(True), message, str(e))
            try:
                client.api = CryptoIDClient(client.isTestnet)
                return func(*args, **kwargs)

            except Exception as e:
                printError(str(e))
                return None

    return process_api_exceptions_int

class ApiClient:

    def __init__(self, isTestnet=False):
        self.isTestnet = isTestnet
        self.api = BlockBookClient(isTestnet)


    @process_api_exceptions
    def getAddressUtxos(self, address):
        return self.api.getAddressUtxos(address)


    @process_api_exceptions
    def getBalance(self, address):
        return self.api.getBalance(address)

