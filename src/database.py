#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sqlite3
import threading

from constants import user_dir, database_File
from misc import printDbg, getCallerName, getFunctionName, printException

class Database():
    '''
    class methods
    '''
    def __init__(self):
        self.file_name = database_File
        self.lock = threading.Lock()
        self.isOpen = False
        self.conn = None
        
        
    
    def open(self):
        if not self.isOpen:
            printDbg("trying to open database...")
            self.lock.acquire()
            try:
                if self.conn is None:
                    self.conn = sqlite3.connect(self.file_name)
                
                self.initTables()
                self.conn.close()
                self.conn = None
                self.isOpen = True
                printDbg("Database open")

            except Exception as e:
                err_msg = 'SQLite initialization error'
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
                
            finally:
                self.lock.release()
                
        else:
            raise Exception("Database already open")
        
        
            
    def close(self):
        if self.isOpen:
            printDbg("trying to close database...")
            self.lock.acquire()
            try:
                if self.conn is not None:
                    self.conn.close()
                    
                self.conn = None
                self.isOpen = False
                printDbg("Database closed")
                
            except Exception as e:
                err_msg = 'SQLite closing error'
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
                
            finally:
                self.lock.release()
        
        else:
            raise Exception("Database not open")
        
        
        
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
        
        
    def releaseCursor(self, rollingBack=False):
        if self.isOpen:
            try:
                if self.conn is not None:
                    # commit
                    if rollingBack:
                        self.conn.rollback()
                    
                    else:
                        self.conn.commit()
                    
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
            
            # Tables for Masternodes
            cursor.execute("CREATE TABLE IF NOT EXISTS MASTERNODES("
                        " name TEXT PRIMARY KEY, ip TEXT, port INTEGER, mnPrivKey TEXT,"
                        " hwAcc INTEGER, isTestnet INTEGER, isHardware INTEGER,"
                        " address TEXT, spath INTEGER, pubkey TEXT, txid TEXT, txidn INTEGER)")

            
        except Exception as e:
            err_msg = 'error initializing tables'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            
            
    '''
    Masternode methods
    '''
    def getMasternodeList(self):
        try:
            cursor = self.getCursor()

            cursor.execute("SELECT * FROM MASTERNODES")
            rows = cursor.fetchall()
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
            
        except Exception as e:
            err_msg = 'error getting masternode list'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            
            
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
            
            self.releaseCursor()
            
        except Exception as e:
            err_msg = 'error writing masternode to DB'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)
            
            
            
    def addMasternode(self, mn, old_mn=None):
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
                
                self.releaseCursor()
                
            except Exception as e:
                err_msg = 'error writing masternode to DB'
                printException(getCallerName(), getFunctionName(), err_msg, e.args)
                
        else:
            # Add new record to the table
            self.addNewMasternode(mn)
            
            
            
    def deleteMasternode(self, mn_name):
        try:
            cursor = self.getCursor()
            cursor.execute("DELETE FROM MASTERNODES WHERE name = ? ", (mn_name,))
            self.releaseCursor()
            
        except Exception as e:
            err_msg = 'error deleting masternode from DB'
            printException(getCallerName(), getFunctionName(), err_msg, e.args)

            
            
                