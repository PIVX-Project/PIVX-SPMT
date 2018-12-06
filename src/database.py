#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sqlite3
import threading

from constants import user_dir, database_File, trusted_RPC_Servers, DEFAULT_MN_CONF
from proposals import Proposal, vote_type, vote_index
from misc import printDbg, getCallerName, getFunctionName, printException, add_defaultKeys_to_dict


class Database():
    
    '''
    class methods
    '''
    def __init__(self, app):
        self.app = app
        self.file_name = database_File
        self.lock = threading.Lock()
        self.isOpen = False
        self.conn = None
        
        
    
    def open(self):
        if self.isOpen:
            raise Exception("Database already open")

        printDbg("trying to open database...")
        with self.lock:
            try:
                if self.conn is None:
                    self.conn = sqlite3.connect(self.file_name)
                
                self.initTables()
                self.conn.commit()
                self.conn.close()
                self.conn = None
                self.isOpen = True
                printDbg("Database open")
    
            except Exception as e:
                err_msg = 'SQLite initialization error'
                printException(getCallerName(), getFunctionName(), err_msg, e)
            
        
        
            
    def close(self):
        if not self.isOpen:
            err_msg = "Database already closed"
            printException(getCallerName(), "close()", err_msg, "")
            return
        
        printDbg("trying to close database...")
        with self.lock:
            try:
                if self.conn is not None:
                    self.conn.close()
                    
                self.conn = None
                self.isOpen = False
                printDbg("Database closed")
                
            except Exception as e:
                err_msg = 'SQLite closing error'
                printException(getCallerName(), getFunctionName(), err_msg, e.args)


        
        
        
    def getCursor(self):
        if self.isOpen:
            self.lock.acquire()
            try:
                if self.conn is None:
                    self.conn = sqlite3.connect(self.file_name)
                return self.conn.cursor()
            
            except Exception as e:
                err_msg = 'SQLite error getting cursor'
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
                self.lock.release()
                
        else:
            raise Exception("Database closed")

        
        
    def releaseCursor(self, rollingBack=False, vacuum=False):
        if self.isOpen:
            try:
                if self.conn is not None:
                    # commit
                    if rollingBack:
                        self.conn.rollback()
                    
                    else:
                        self.conn.commit()
                        if vacuum:
                            self.conn.execute('vacuum')
                    
                    # close connection
                    self.conn.close()
                        
                self.conn = None
                    
            except Exception as e:
                err_msg = 'SQLite error releasing cursor'
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
                
            finally:
                self.lock.release()
        
        else:
            raise Exception("Database closed")

        
        
    def initTables(self):
        try:
            cursor = self.conn.cursor()
            
            # Tables for RPC Servers
            cursor.execute("CREATE TABLE IF NOT EXISTS PUBLIC_RPC_SERVERS("
                           " id INTEGER PRIMARY KEY, protocol TEXT, host TEXT,"
                           " user TEXT, pass TEXT)")
            
            cursor.execute("CREATE TABLE IF NOT EXISTS CUSTOM_RPC_SERVERS("
                           " id INTEGER PRIMARY KEY, protocol TEXT, host TEXT,"
                           " user TEXT, pass TEXT)")
            
            self.initTable_RPC(cursor)
            
            # Tables for Masternodes
            cursor.execute("CREATE TABLE IF NOT EXISTS MASTERNODES("
                           " name TEXT PRIMARY KEY, ip TEXT, port INTEGER, mnPrivKey TEXT,"
                           " hwAcc INTEGER, isTestnet INTEGER, isHardware INTEGER,"
                           " address TEXT, spath INTEGER, pubkey TEXT, txid TEXT, txidn INTEGER)")
            
            # Tables for Rewards
            cursor.execute("CREATE TABLE IF NOT EXISTS REWARDS("
                           " tx_hash TEXT, tx_ouput_n INTEGER,"
                           " value INTEGER, confirmations INTEGER, script TEXT, raw_tx TEXT, mn_name TEXT,"
                           " PRIMARY KEY (tx_hash, tx_ouput_n))")
            
            # Tables for Governance Objects
            cursor.execute("CREATE TABLE IF NOT EXISTS PROPOSALS("
                           " name TEXT, url TEXT, hash TEXT PRIMARY KEY, feeHash TEXT,"
                           " blockStart INTEGER, blockEnd INTEGER, totalPayCount INTEGER,"
                           " remainingPayCount INTEGER, paymentAddress TEXT,"
                           " yeas INTEGER, nays INTEGER, abstains INTEGER, "
                           " totalPayment REAL, monthlyPayment REAL)")
            
            #cursor.execute("CREATE TABLE IF NOT EXISTS PROJECTED_PROPOSALS("
            #               " name TEXT, hash TEXT PRIMARY KEY, "
            #               " allotted REAL, votes INTEGER, totaAllotted REAL)")
            
            cursor.execute("CREATE TABLE IF NOT EXISTS MY_VOTES("
                           " mn_name TEXT, p_hash, vote INTEGER, timeslip INTEGER, "
                           " PRIMARY KEY (mn_name, p_hash))")

            
        except Exception as e:
            err_msg = 'error initializing tables'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
    
    
    
    def initTable_RPC(self, cursor):
        s = trusted_RPC_Servers
        # Insert Default public trusted servers
        cursor.execute("INSERT OR REPLACE INTO PUBLIC_RPC_SERVERS VALUES"
                       " (?, ?, ?, ?, ?),"
                       " (?, ?, ?, ?, ?),"
                       " (?, ?, ?, ?, ?);",
                       (0, s[0][0], s[0][1], s[0][2], s[0][3],
                        1, s[1][0], s[1][1], s[1][2], s[1][3],
                        2, s[2][0], s[2][1], s[2][2], s[2][3]))
        
        # Insert Local wallet
        cursor.execute("INSERT OR IGNORE INTO CUSTOM_RPC_SERVERS VALUES"
                       " (?, ?, ?, ?, ?);",
                       (0, "http", "127.0.0.1:51473", "rpcUser", "rpcPass"))

    
    
    '''
    General methods
    '''  
    def clearTable(self,  table_name):
        cleared_RPC = False
        try:
            cursor = self.getCursor()
            cursor.execute("DELETE FROM %s" % table_name)
            # in case, reload default RPC and emit changed signal
            if table_name == 'CUSTOM_RPC_SERVERS':
                self.initTable_RPC(cursor)
                cleared_RPC = True
            
        except Exception as e:
            err_msg = 'error clearing %s in database' % table_name
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
   
        finally:
            self.releaseCursor(vacuum=True)
            if cleared_RPC:
                self.app.sig_changed_rpcServers.emit()
                
        
        
        
    '''
    RPC servers methods
    '''
    def addRPCServer(self, protocol, host, user, passwd):
        added_RPC = False
        try:
            cursor = self.getCursor()

            cursor.execute("INSERT INTO CUSTOM_RPC_SERVERS (protocol, host, user, pass) "
                           "VALUES (?, ?, ?, ?)",
                           (protocol, host, user, passwd)
                           )
            added_RPC = True
            
        except Exception as e:
            err_msg = 'error adding RPC server entry to DB'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)      
        finally:
            self.releaseCursor()
            if added_RPC:
                self.app.sig_changed_rpcServers.emit()
        
        
        
        
    def editRPCServer(self, protocol, host, user, passwd, id):
        changed_RPC = False
        try:
            cursor = self.getCursor()

            cursor.execute("UPDATE CUSTOM_RPC_SERVERS "
                           "SET protocol = ?, host = ?, user = ?, pass = ?"
                           "WHERE id = ?",
                           (protocol, host, user, passwd, id)
                           )
            changed_RPC = True
                    
        except Exception as e:
            err_msg = 'error editing RPC server entry to DB'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)       
        finally:
            self.releaseCursor()
            if changed_RPC:
                self.app.sig_changed_rpcServers.emit()   
        
        
        
        
    def getRPCServers(self, custom, id=None):
        tableName = "CUSTOM_RPC_SERVERS" if custom else "PUBLIC_RPC_SERVERS"
        try:
            cursor = self.getCursor()
            if id is None:
                cursor.execute("SELECT * FROM %s" % tableName)
            else:
                cursor.execute("SELECT * FROM %s WHERE id = ?" % tableName, (id,))
            rows = cursor.fetchall()
            
        except Exception as e:
            err_msg = 'error getting RPC servers from database'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            rows = []     
        finally:
            self.releaseCursor() 
        
        server_list = []
        for row in rows:
            server = {}
            server["id"] = row[0]
            server["protocol"] = row[1]
            server["host"] = row[2]
            server["user"] = row[3]
            server["password"] = row[4]
            server["isCustom"] = custom
            server_list.append(server)
        
        if id is not None:
            return server_list[0]
        
        return server_list
        
            
    
    def removeRPCServer(self, id):
        removed_RPC = False
        try:
            cursor = self.getCursor()
            cursor.execute("DELETE FROM CUSTOM_RPC_SERVERS"
                           " WHERE id=?", (id,))
            removed_RPC = True
            
        except Exception as e:
            err_msg = 'error removing RPC servers from database'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
   
        finally:
            self.releaseCursor(vacuum=True)
            if removed_RPC:
                self.app.sig_changed_rpcServers.emit()
            

            
        
        
    '''
    Masternode methods
    '''
    def getMasternodeList(self):
        try:
            cursor = self.getCursor()

            cursor.execute("SELECT * FROM MASTERNODES")
            rows = cursor.fetchall()
            
        except Exception as e:
            err_msg = 'error getting masternode list'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            rows = []       
        finally:
            self.releaseCursor() 
        
        mnlist = []
        
        for row in rows:
            # fetch masternode item
            new_masternode = {}
            new_masternode['name'] = row[0]
            new_masternode['ip'] = row[1]
            new_masternode['port'] = row[2]
            new_masternode['mnPrivKey'] = row[3]
            new_masternode['hwAcc'] = row[4]
            new_masternode['isTestnet'] = row[5]
            new_masternode['isHardware'] = (row[6] > 0)          
            coll = {}
            coll['address'] = row[7]
            coll['spath'] = row[8]
            coll['pubKey'] = row[9]
            coll['txid'] = row[10]
            coll['txidn'] = row[11]
            new_masternode['collateral'] = coll
            # add to list
            mnlist.append(new_masternode)
        
        return mnlist

     
            
    def addNewMasternode(self, mn):
        try:
            cursor = self.getCursor()

            cursor.execute("INSERT INTO MASTERNODES(name, ip, port, mnPrivKey,"
                           " hwAcc, isTestnet, isHardware,  address, spath, pubkey, txid, txidn) "
                           "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                           (mn['name'], mn['ip'], mn['port'], mn['mnPrivKey'], mn['hwAcc'], mn['isTestnet'], 
                            1 if mn['isHardware'] else 0, 
                            mn['collateral'].get('address'), mn['collateral'].get('spath'), 
                            mn['collateral'].get('pubKey'), mn['collateral'].get('txid'), mn['collateral'].get('txidn'))
                           )
            
        except Exception as e:
            err_msg = 'error writing new masternode to DB'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        finally:
            self.releaseCursor() 
            
    
    
    def addMasternode(self, mn, old_mn=None):
        add_defaultKeys_to_dict(mn, DEFAULT_MN_CONF)
        
        if not old_mn is None:
            try:
                cursor = self.getCursor()
    
                cursor.execute("UPDATE MASTERNODES "
                               "SET name = ?, ip = ?, port = ?, mnPrivKey = ?, hwAcc = ?, isTestnet = ?, isHardware = ?,"
                               "    address = ?, spath = ?, pubkey = ?, txid = ?, txidn = ?"
                               "WHERE name = ?",
                               (mn['name'], mn['ip'], mn['port'], mn['mnPrivKey'], mn['hwAcc'], mn['isTestnet'], 
                                1 if mn['isHardware'] else 0,  
                                mn['collateral'].get('address'), mn['collateral'].get('spath'), 
                                mn['collateral'].get('pubKey'), mn['collateral'].get('txid'), mn['collateral'].get('txidn'),
                                old_mn['name'])
                               )
                
            except Exception as e:
                err_msg = 'error writing masternode to DB'
                printException(getCallerName(), getFunctionName(), err_msg, e.args)                
            finally:
                self.releaseCursor() 
                
        else:
            # Add new record to the table
            self.addNewMasternode(mn)
            

            
    def deleteMasternode(self, mn_name):
        try:
            cursor = self.getCursor()
            cursor.execute("DELETE FROM MASTERNODES WHERE name = ? ", (mn_name,))
            
        except Exception as e:
            err_msg = 'error deleting masternode from DB'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        finally:
            self.releaseCursor(vacuum=True) 
    
    
    
    '''
    Rewards methods
    '''
    def rewards_from_rows(self, rows):
        rewards = []
        
        for row in rows:
            # fetch masternode item
            utxo = {}
            utxo['tx_hash'] = row[0]
            utxo['tx_ouput_n'] = row[1]
            utxo['value'] = row[2]
            utxo['confirmations'] = row[3]
            utxo['script'] = row[4]
            utxo['raw_tx'] = row[5]
            utxo['mn_name'] = row[6]
            # add to list
            rewards.append(utxo)
            
        return rewards
        
    
    
    def addReward(self, utxo):
        try:
            cursor = self.getCursor()
            
            cursor.execute("INSERT INTO REWARDS "
                           "VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (utxo['tx_hash'], utxo['tx_ouput_n'], utxo['value'], 
                            utxo['confirmations'], utxo['script'], utxo['raw_tx'], utxo['mn_name'])
                           )
            
        except Exception as e:
            err_msg = 'error adding reward UTXO to DB'
            printException(getCallerName(), getFunctionName(), err_msg, e)

        finally:
            self.releaseCursor()
            
            
            
            
    def deleteReward(self, txid, txidn):
        try:
            cursor = self.getCursor()
            cursor.execute("DELETE FROM REWARDS WHERE tx_hash = ? AND tx_ouput_n = ?", (txid, txidn))
            
        except Exception as e:
            err_msg = 'error deleting UTXO from DB'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
        finally:
            self.releaseCursor(vacuum=True) 
            
    
    
    
    def getReward(self, txid, txidn):
        try:
            cursor = self.getCursor()

            cursor.execute("SELECT * FROM REWARDS"
                           " WHERE tx_hash = ? AND tx_ouput_n = ?", (txid, txidn))
            rows = cursor.fetchall()
            
        except Exception as e:
            err_msg = 'error getting reward %s-%d' % (txid, txidn)
            printException(getCallerName(), getFunctionName(), err_msg, e)
            rows = []       
        finally:
            self.releaseCursor() 
        
        return self.rewards_from_rows(rows)[0]
    
    
    
    def getRewardsList(self, mn_name=None):
        try:
            cursor = self.getCursor()

            if mn_name is None:
                cursor.execute("SELECT * FROM REWARDS")
            else:
                cursor.execute("SELECT * FROM REWARDS WHERE mn_name = ?", (mn_name,))
            rows = cursor.fetchall()
            
        except Exception as e:
            err_msg = 'error getting rewards list for masternode %s' % mn_name
            printException(getCallerName(), getFunctionName(), err_msg, e)
            rows = []       
        finally:
            self.releaseCursor() 
        
        return self.rewards_from_rows(rows)




    '''
    Proposals methods
    '''
    def myVotes_from_rows(self, rows):
        myVotes = []
        
        for row in rows:
            # fetch vote item
            vote = {}
            vote["mn_name"] = row[0]
            vote["p_hash"] = row[1]
            vote["vote"] = vote_type[str(row[2])]
            vote["time"] = row[3]
            # add to list
            myVotes.append(vote)
            
        return myVotes
    


    
    def proposals_from_rows(self, rows):
        proposals = []
        
        for row in rows:
            # fetch proposal item
            p = Proposal(row[0], row[1], row[2], row[3], row[4], row[5], row[6],
                         row[7], row[8], row[9], row[10], row[11], row[12], row[13])
            # add to list
            proposals.append(p)
            
        return proposals
    


    
    def addMyVote(self, mn_name, p_hash, vote):
        try:
            cursor = self.getCursor()
            
            cursor.execute("INSERT OR REPLACE INTO MY_VOTES "
                           "VALUES (?, ?, ?, ?)",
                           (mn_name, p_hash, vote_index[vote["Vote"]], vote["nTime"])
                           )
            
        except Exception as e:
            err_msg = 'error adding my votes to DB'
            printException(getCallerName(), getFunctionName(), err_msg, e)

        finally:
            self.releaseCursor()
            
            
            
            
    def addProposal(self, p):
        try:
            cursor = self.getCursor()
            
            cursor.execute("INSERT OR REPLACE INTO PROPOSALS "
                           "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (p.name, p.URL, p.Hash, p.FeeHash, p.BlockStart, p.BlockEnd, 
                            p.TotalPayCount, p.RemainingPayCount, p.PaymentAddress, 
                            p.Yeas, p.Nays, p.Abstains, p.ToalPayment, p.MonthlyPayment)
                           )
            
        except Exception as e:
            err_msg = 'error adding proposal to DB'
            printException(getCallerName(), getFunctionName(), err_msg, e)

        finally:
            self.releaseCursor()

    
    
    
    
    def getMyVotes(self, p_hash=None):
        try:
            cursor = self.getCursor()

            if p_hash is None:
                cursor.execute("SELECT * FROM MY_VOTES")
            else:
                cursor.execute("SELECT * FROM MY_VOTES WHERE p_hash = ?", (p_hash,))
            rows = cursor.fetchall()
            
        except Exception as e:
            err_msg = 'error getting myVotes from DB'
            printException(getCallerName(), getFunctionName(), err_msg, e)
            rows = []       
        finally:
            self.releaseCursor() 
        
        return self.myVotes_from_rows(rows)
    
            
            
            
    def getProposalsList(self):
        try:
            cursor = self.getCursor()
            cursor.execute("SELECT * FROM PROPOSALS")
            rows = cursor.fetchall()
            
        except Exception as e:
            err_msg = 'error getting proposals from DB'
            printException(getCallerName(), getFunctionName(), err_msg, e)
            rows = []       
        finally:
            self.releaseCursor() 
        
        return self.proposals_from_rows(rows)

