#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from time import time

'''
Connects with database and rpc clients to keep a cache for rawtxes
'''
class TxCache():

    def __init__(self, main_wnd):
        self.main_wnd = main_wnd


    '''
    tries to fetch rawtx from database.
    if not found, tries with rpc (and if successful, updates the database)
    '''
    def __getitem__(self, item):
        rawtx = self.main_wnd.parent.db.getRawTx(item)
        if rawtx is None:
            # double check that the rpc connection is still active, else reconnect
            if self.main_wnd.rpcClient is None:
                self.main_wnd.updateRPCstatus(None)

            rawtx = self.main_wnd.rpcClient.getRawTransaction(item)

            # update DB
            if rawtx is not None:
                self.main_wnd.parent.db.addRawTx(item, rawtx, time())
        else:
            rawtx = rawtx['rawtx']

        return rawtx