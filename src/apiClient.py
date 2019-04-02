#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from random import choice
import requests

from misc import getCallerName, getFunctionName, printException, printDbg

api_keys = ["b62b40b5091e", "f1d66708a077", "ed85c85c0126", "ccc60d06f737"]


def process_api_exceptions(func):

    def process_api_exceptions_int(*args, **kwargs):
        apiClient = args[0]
        try:
            return func(*args, **kwargs)
        except Exception as e:
            message = "API Client exception"
            printException(getCallerName(True), getFunctionName(True), message, str(e))
            return None

    return process_api_exceptions_int




class ApiClient:

    def __init__(self):
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



    @process_api_exceptions
    def getAddressUtxos(self, address):
        self.parameters = {}
        self.parameters['q'] = 'unspent'
        self.parameters['active'] = address
        return self.checkResponse(self.parameters)



    @process_api_exceptions
    def getBalance(self, address):
        self.parameters = {}
        self.parameters['q'] = 'getbalance'
        self.parameters['a'] = address
        return self.checkResponse(self.parameters)



    def getStatus(self):
        status_code = 0
        self.parameters = {}
        self.parameters['q'] = 'getblockcount'
        try:
            resp = requests.get(self.url, self.parameters)
            status_code = resp.status_code
        except Exception as e:
            printException(getCallerName(True), getFunctionName(True), "API ERR", str(e))

        return status_code



    def getStatusMess(self, statusCode):
        message = {
            0: "No response from server",
            200: "OK! Connected"}

        if statusCode in message:
            return message[statusCode]

        return "Not Connected! Status: %s" % str(statusCode)



    @process_api_exceptions
    def getBlockCount(self):
        self.parameters = {}
        self.parameters['q'] = 'getblockcount'
        return self.checkResponse(self.parameters)



    @process_api_exceptions
    def getBlockHash(self, blockNum):
        self.parameters = {}
        self.parameters['q'] = 'getblockhash'
        self.parameters['height'] = str(blockNum)
        return self.checkResponse(self.parameters)
