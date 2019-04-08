#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

from misc import getCallerName, getFunctionName, printException



def process_blockbook_exceptions(func):

    def process_blockbook_exceptions_int(*args, **kwargs):
        client = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if client.isTestnet:
                new_url = "https://testnet.pivx.link"
            else:
                new_url = "https://explorer.pivx.link"
            message = "BlockBook Client exception on %s\nTrying backup server %s" % (client.url, new_url)
            printException(getCallerName(True), getFunctionName(True), message, str(e))

            try:
                client.url = new_url
                return func(*args, **kwargs)

            except Exception:
                raise

    return process_blockbook_exceptions_int




class BlockBookClient:

    def __init__(self, isTestnet=False):
        self.isTestnet = isTestnet
        if isTestnet:
            self.url = "https://blockbook-testnet.pivx.link"
        else:
            self.url = "https://blockbook.pivx.link"



    def checkResponse(self, method, param=""):
        url = self.url + "/api/%s" % method
        if param != "":
            url += "/%s" % param
        resp = requests.get(url, data={}, verify=True)
        if resp.status_code == 200:
            data = resp.json()
            return data
        raise Exception("Invalid response")



    @process_blockbook_exceptions
    def getAddressUtxos(self, address):
        utxos = self.checkResponse("utxo", address)
        # Add script for cryptoID legacy
        for u in utxos:
            u["script"] = ""
        return utxos



    @process_blockbook_exceptions
    def getBalance(self, address):
        return self.checkResponse("address", address)

