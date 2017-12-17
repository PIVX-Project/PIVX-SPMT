#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from misc import getCallerName, getFunctionName, printException

class ApiClient:
    
    def __init__(self):
        self.url = "http://chainz.cryptoid.info/pivx/api.dws"
        self.parameters = {"key": "b62b40b5091e"}
        
    
    
    def getAddressUtxos(self, address):
        try:
            self.parameters['q'] = 'unspent'
            self.parameters['active'] = address
            return self.checkResponse(self.parameters)
        except Exception as e:
            err_msg = "error in getAddressUtxos"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            
            
            
    def getBalance(self, address):
        try:
            self.parameters['q'] = 'getbalance'
            self.parameters['a'] = address
            return self.checkResponse(self.parameters)
        except Exception as e:
            err_msg = "error in getAddressUtxos"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
    
        
    
    def getStatus(self):
        try:
            self.parameters['q'] = 'getblockcount'
            resp = requests.get(self.url, self.parameters)
            return resp.status_code
        
        except Exception as e:
            err_msg = "Unable to connect to API provider"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            return 0
        
    
        
    def getStatusMess(self, statusCode):
        message = {
            0: "No response from server",
            200: "OK! Connected"}
        
        if statusCode in message:
            return message[statusCode]
    
        return "Not Connected! Status: %s" % str(statusCode)
    
    
    
    def checkResponse(self, parameters):
        resp = requests.get(self.url, params=parameters)
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            print("Invalid response from API provider")
            print("Status code: %s" % str(resp.status_code))
            return None
                
    
    
    def getBlockCount(self):
        try:
            self.parameters['q'] = 'getblockcount'
            return self.checkResponse(self.parameters)
        except Exception as e:
            err_msg = "error in getBlockCount"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            
    
    
    def getBlockHash(self, blockNum):
        try:
            self.parameters['q'] = 'getblockhash'
            self.parameters['height'] = str(blockNum)
            return self.checkResponse(self.parameters)
        except Exception as e:
            err_msg = "error in getBlockHash"
            printException(getCallerName(), getFunctionName(), err_msg, e.args)