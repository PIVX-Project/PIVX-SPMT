#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2019 Random.Zebra (https://github.com/random-zebra/)
# Distributed under the MIT software license, see the accompanying
# file LICENSE.txt or http://www.opensource.org/licenses/mit-license.php.

from bitcoinrpc.authproxy import AuthServiceProxy
import threading

from constants import DEFAULT_PROTOCOL_VERSION, MINIMUM_FEE
from misc import getCallerName, getFunctionName, printException, printDbg, now, timeThis
from proposals import Proposal


def process_RPC_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            # If httpConnection exists, connect manually
            if hasattr(args[0], 'httpConnection') and args[0].httpConnection:
                args[0].httpConnection.connect()
            return func(*args, **kwargs)
        except Exception as e:
            message = "Exception in RPC client"
            printException(getCallerName(True), getFunctionName(True), message, str(e))
            # Return a default value based on the expected return structure of the wrapped function
            if func.__name__ == 'getStatus':
                return False, "Error: RPC call failed", 0, None, False
            elif func.__name__ == 'isBlockchainSynced':
                return False, None
            # Handle other functions or provide a general default return
            else:
                return None
        finally:
            # If httpConnection exists, close it
            if hasattr(args[0], 'httpConnection') and args[0].httpConnection:
                try:
                    args[0].httpConnection.close()
                except Exception as e:
                    printDbg(e)
                    pass
    return wrapper


class RpcClient:

    def __init__(self, rpc_protocol, rpc_host, rpc_user, rpc_password):
        # Lock for threads
        self.lock = threading.RLock()

        self.rpc_url = f"{rpc_protocol}://{rpc_user}:{rpc_password}@{rpc_host}"


        self.conn = AuthServiceProxy(self.rpc_url, timeout=1000)

    @process_RPC_exceptions
    def getBlockCount(self):
        n = 0
        with self.lock:
            n = self.conn.getblockcount()

        return n

    @process_RPC_exceptions
    def getBlockHash(self, blockNum):
        h = None
        with self.lock:
            h = self.conn.getblockhash(blockNum)

        return h

    @process_RPC_exceptions
    def getBudgetVotes(self, proposal):
        votes = {}
        with self.lock:
            votes = self.conn.getbudgetvotes(proposal)

        return votes

    @process_RPC_exceptions
    def getFeePerKb(self):
        res = MINIMUM_FEE
        with self.lock:
            # get transaction data from last 200 blocks
            feePerKb = float(self.conn.getfeeinfo(200)['feeperkb'])
            res = (feePerKb if feePerKb > MINIMUM_FEE else MINIMUM_FEE)

        return res

    @process_RPC_exceptions
    def getMNStatus(self, address):
        mnStatus = None
        with self.lock:
            mnStatusList = self.conn.listmasternodes(address)
            if not mnStatusList:
                return None
            mnStatus = mnStatusList[0]
            mnStatus['mnCount'] = self.conn.getmasternodecount()['enabled']

        return mnStatus

    @process_RPC_exceptions
    def getMasternodeCount(self):
        ans = None
        with self.lock:
            ans = self.conn.getmasternodecount()

        return ans

    @process_RPC_exceptions
    def getMasternodes(self):
        printDbg("RPC: Getting masternode list...")
        mnList = {}
        score = []
        masternodes = []
        with self.lock:
            masternodes = self.conn.listmasternodes()

        for mn in masternodes:
            if mn.get('status') == 'ENABLED':
                # compute masternode score
                if mn.get('lastpaid') == 0:
                    mn['score'] = mn.get('activetime')
                else:
                    lastpaid_ago = now() - mn.get('lastpaid')
                    mn['score'] = min(lastpaid_ago, mn.get('activetime'))

            else:
                mn['score'] = 0

            score.append(mn)

        # sort masternodes by decreasing score
        score.sort(key=lambda x: x['score'], reverse=True)

        # save masternode position in the payment queue
        for mn in masternodes:
            mn['queue_pos'] = score.index(mn)

        mnList['masternodes'] = masternodes

        return mnList

    @process_RPC_exceptions
    def getNextSuperBlock(self):
        n = 0
        with self.lock:
            n = self.conn.getnextsuperblock()

        return n

    @process_RPC_exceptions
    def getProposals(self):
        printDbg("RPC: Getting proposals list...")
        proposals = []
        data = []
        with self.lock:
            # get proposals JSON data
            data = self.conn.getbudgetinfo()

        for p in data:
            # create proposal Object
            new_proposal = Proposal(p.get('Name'), p.get('URL'), p.get('Hash'), p.get('FeeHash'), p.get('BlockStart'),
                                    p.get('BlockEnd'), p.get('TotalPaymentCount'), p.get('RemainingPaymentCount'), p.get('PaymentAddress'),
                                    p.get('Yeas'), p.get('Nays'), p.get('Abstains'),
                                    float(p.get('TotalPayment')), float(p.get('MonthlyPayment')))
            # append object to list
            proposals.append(new_proposal)

        # return proposals list
        return proposals

    @process_RPC_exceptions
    def getProposalsProjection(self):
        printDbg("RPC: Getting proposals projection...")
        data = []
        proposals = []
        with self.lock:
            # get budget projection JSON data
            data = self.conn.getbudgetprojection()

        for p in data:
            # create proposal-projection dictionary
            new_proposal = {}
            new_proposal['Name'] = p.get('Name')
            new_proposal['Allotted'] = float(p.get("Allotted"))
            new_proposal['Votes'] = p.get('Yeas') - p.get('Nays')
            new_proposal['Total_Allotted'] = float(p.get('TotalBudgetAllotted'))
            # append dictionary to list
            proposals.append(new_proposal)

        # return proposals list
        return proposals

    @process_RPC_exceptions
    def getProtocolVersion(self):
        res = DEFAULT_PROTOCOL_VERSION
        with self.lock:
            prot_version = self.conn.getinfo().get('protocolversion')
            res = int(prot_version)

        return res

    @process_RPC_exceptions
    def getRawTransaction(self, txid):
        res = None
        with self.lock:
            res = self.conn.getrawtransaction(txid)

        return res

    @process_RPC_exceptions
    def getStatus(self):
        status = False
        statusMess = "Unable to connect to a PIVX RPC server.\n"
        statusMess += "Either the local PIVX wallet is not open, or the remote RPC server is not responding."
        n = 0
        response_time = None
        with self.lock:
            isTestnet = self.conn.getinfo()['testnet']
            n, response_time = timeThis(self.conn.getblockcount)
            if n is None:
                n = 0

        if n > 0:
            status = True
            statusMess = "Connected to PIVX Blockchain"

        return status, statusMess, n, response_time, isTestnet

    @process_RPC_exceptions
    def isBlockchainSynced(self):
        res = False
        response_time = None
        with self.lock:
            status, response_time = timeThis(self.conn.mnsync, 'status')
            if status is not None:
                res = status.get("IsBlockchainSynced")

        return res, response_time

    @process_RPC_exceptions
    def mnBudgetRawVote(self, mn_tx_hash, mn_tx_index, proposal_hash, vote, time, vote_sig):
        res = None
        with self.lock:
            res = self.conn.mnbudgetrawvote(mn_tx_hash, mn_tx_index, proposal_hash, vote, time, vote_sig)

        return res

    @process_RPC_exceptions
    def decodemasternodebroadcast(self, work):
        printDbg("RPC: Decoding masternode broadcast...")
        res = ""
        with self.lock:
            res = self.conn.decodemasternodebroadcast(work.strip())

        return res

    @process_RPC_exceptions
    def relaymasternodebroadcast(self, work):
        printDbg("RPC: Relaying masternode broadcast...")
        res = ""
        with self.lock:
            res = self.conn.relaymasternodebroadcast(work.strip())

        return res

    @process_RPC_exceptions
    def sendRawTransaction(self, tx_hex):
        dbg_mess = "RPC: Sending raw transaction"
        dbg_mess += "..."
        printDbg(dbg_mess)
        tx_id = None
        with self.lock:
            tx_id = self.conn.sendrawtransaction(tx_hex, True)

        return tx_id

    @process_RPC_exceptions
    def verifyMessage(self, pivxaddress, signature, message):
        printDbg("RPC: Verifying message...")
        res = False
        with self.lock:
            res = self.conn.verifymessage(pivxaddress, signature, message)

        return res
