#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

import requests

from misc import getCallerName, getFunctionName, printException


def process_blockbook_exceptions(func):
    def process_blockbook_exceptions_int(*args, **kwargs):
        client = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if client.isTestnet:
                new_url = "https://testnet.duddino.com/"
            else:
                new_url = "https://zkbitcoin.com/"
            message = f"BlockBook Client exception on {client.url}\nTrying backup server {new_url}"
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
            self.url = "https://testnet.fuzzbawls.pw"
        else:
            self.url = "https://explorer.duddino.com/"

    def checkResponse(self, method, param=""):
        url = f"{self.url}/api/{method}"
        if param != "":
            url += "/{param}"
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
        return self.checkResponse("address", address)["balance"]
