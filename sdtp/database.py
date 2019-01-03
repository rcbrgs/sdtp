# -*- coding: utf-8 -*-

import datetime
import logging
import os
import pathlib
import queue
from sqlalchemy import create_engine, update
from sqlalchemy import ( create_engine, Column, Float, Integer, MetaData, String, Table )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import threading
import time

Base = declarative_base ( )
from sdtp.friendships_table import FriendshipsTable
from sdtp.lkp_table import lkp_table
from sdtp.lp_table import lp_table
from sdtp.mods.chat_translator_table import ChatTranslatorTable
from sdtp.mods.llp_table import llp_table
from sdtp.mods.portals_tables import PortalsTable

class Database(threading.Thread):
    def __init__(self, controller = None):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)
        
        self.ready = False
        self.engine = None
        self.lock = False
        self.metadata = None
        self.queue = queue.Queue ( )

    # blocking API
    def blocking_add(self, table, records):
        self.get_lock("add")
        session = self.get_session ( )
        query = session.query ( table )
        results = session.add_all ( records )
        self.let_session ( session )
        self.let_lock("add")
    
    def blocking_consult(self, table, conditions):
        self.get_lock("consult")
        session = self.get_session ( )
        query = session.query(table)
        for condition in conditions:
            if condition[1] == "==":
                query = query.filter(condition[0] == condition[2])
        results = query.all()
        self.logger.debug("results = {}".format ( results ) )
        retval = [ ]
        for entry in results:
            retval.append(entry.get_dictionary())
        self.let_session(session)
        self.let_lock("consult")       
        return retval

    def blocking_delete(self, table, conditions):
        self.get_lock("delete")
        session = self.get_session()
        query = session.query(table)
        for condition in conditions:
            if condition[1] == "==":
                query = query.filter(condition[0] == condition[2])
        query.delete()
        self.let_session(session)
        self.let_lock("delete")       

    def blocking_update(self, table, entry):
        self.get_lock("update")
        session = self.get_session()
        statement = update(table).where(table.aid == entry["aid"]).\
                    values(entry)
        try:
            result = session.execute(statement)
        except Exception as e:
            self.logger.error("Exception while executing statement: {}.".format(e))
            raise e
        self.let_session(session)
        self.let_lock("update")
        
    def get_lock(self, debug = ""):
        self.logger.debug("get_lock({})".format(debug))
        count = 0
        while self.lock:
            time.sleep(0.1)
            count += 1
            if count > 100:
                self.logger.warning(".get_lock({}) grabbing lock forcefully.".format(debug))
                break
        self.lock = True

    def let_lock(self, debug = ""):
        self.logger.debug("let_lock({})".format(debug))
        self.lock = False
        
    # non-blocking API
    def add_all ( self, table, records, callback ):
        self.logger.debug("table = {}".format ( table ) )
        self.enqueue ( self.__add_all, [ table, records, callback ] )

    def consult ( self, table, conditions, callback, pass_along = { } ):
        self.logger.debug("table = {}".format ( table ) )
        self.enqueue ( self.__consult, [ table, conditions, callback ], { "pass_along" : pass_along } )

    def delete(self, table, conditions, callback, pass_along = {}):
        self.logger.debug("table = {}".format(table))
        self.enqueue(self.__delete, [table, conditions, callback], {"pass_along": pass_along})

    def update(self, table, record, callback, pass_along = {}):
        self.enqueue(self.__update, [table, record, callback], {"pass_along": pass_along})

    # /API
        
    def run ( self ):
        self.logger.info("Start.")
        self.create_engine()
        self.create_tables()
        self.ready = True
        count = 0
        while ( self.keep_running ):
            self.execute ( )
            time.sleep ( 0.1 )
            count =+ 1
            if count % 600 == 0:
                self.logger.debug("tick" )
        self.ready = False
        self.logger.debug("Returning." )

    def enqueue ( self, method, arguments = [ ], keyword_arguments = { } ):
        self.logger.debug("Trying to enqueue a task." )
        self.queue.put ( { "method" : method,
                           "arguments" : arguments,
                           "keyword_arguments" : keyword_arguments } )

    def execute ( self ):
        if self.queue.empty ( ):
            return
        self.logger.debug("Attempting to execute a task." )
        task = self.queue.get ( )
        count = 0
        self.get_lock("execute")
        task["method"](*task["arguments"], **task["keyword_arguments"])
        self.let_lock("execute")

    def stop ( self ):
        self.keep_running = False
        self.logger.info("Stop.")

    def create_engine(self):
        self.logger.debug("create_engine()")
        config = self.controller.config.values
        if config [ "db_engine" ] == "sqlite":
            engine_string = "sqlite:///" + config [ "db_sqlite_file_path" ]
        else:
            engine_string = config [ "db_engine" ] + config [ "db_user" ] + ":" + config [ "db_host_user" ] + "@" + config [ "db_host" ] + ":" +config [ "db_port" ] + config [ "separator" ] + config [ "db_name" ]
        self.logger.debug("engine_string = {}".format ( engine_string ) )
        self.engine = create_engine ( engine_string )
        self.logger.debug("self.engine = {}".format(self.engine))
        self.metadata = MetaData ( self.engine )
        self.metadata.reflect ( bind = self.engine )
        for table in self.metadata.tables:
            self.logger.debug("table '{}' found in db.".format ( table ) )
        self.logger.debug("\create_engine()" )

    def create_tables(self):
        self.logger.debug("create_tables()")
        self.friendships_table = FriendshipsTable()
        self.friendships_table.create(self.engine)
        self.lkp_table = lkp_table()
        self.lkp_table.create(self.engine)
        self.lp_table = lp_table()
        self.lp_table.create(self.engine)
        self.chat_translation = ChatTranslatorTable()
        self.chat_translation.create(self.engine)
        self.llp_table = llp_table()
        self.llp_table.create(self.engine)
        self.portals = PortalsTable()
        self.portals.create(self.engine)
        global Base
        Base.metadata.create_all(self.engine)
        self.logger.debug("self.metadata = {}".format(self.metadata))
        self.logger.debug("\create_tables()" )

    def __add_all ( self, table, records, callback ):
        self.logger.debug("Querying table {}.".format ( table ) )
        session = self.get_session ( )
        query = session.query ( table )
        results = session.add_all ( records )
        self.let_session ( session )
        if callback == print:
            self.logger.debug("Ignoring 'print' callback." )
            return
        self.logger.debug("Trying callback '{} ( {} )'.".format ( callback, results ) )
        callback ( results )

    def __consult ( self, table, conditions, callback, pass_along ):
        self.logger.debug("Querying table {} with conditions '{}'.".format ( table, conditions ) )
        session = self.get_session ( )
        query = session.query ( table )
        for condition in conditions:
            before = query.count ( )
            query = query.filter ( condition [ 0 ] == condition [ 2 ] )
            self.logger.debug("Applying condition '{}' diminished query count from {} to {}".format ( condition, before, query.count ( ) ) )
        results = query.all ( )
        self.logger.debug("results = {}".format ( results ) )
        retval = [ ]
        for entry in results:
            retval.append ( entry.get_dictionary ( ) )
        self.let_session ( session )
        if callback == print:
            self.logger.debug("Ignoring 'print' callback." )
            return
        self.logger.debug("Trying callback." )
        callback ( retval, **pass_along )

    def __delete( self, table, conditions, callback, pass_along ):
        self.logger.debug("Querying table {} with conditions '{}'.".format ( table, conditions ) )
        session = self.get_session ( )
        query = session.query ( table )
        for condition in conditions:
            before = query.count ( )
            query = query.filter ( condition [ 0 ] == condition [ 2 ] )
            self.logger.debug("Applying condition '{}' diminished query count from {} to {}".format ( condition, before, query.count ( ) ) )
        results = query.all ( )
        self.logger.debug("results = {}".format ( results ) )
        retval = [ ]
        for entry in results:
            retval.append ( entry.get_dictionary ( ) )
        query.delete()
        self.let_session ( session )
        if callback == print:
            self.logger.debug("Ignoring 'print' callback." )
            return
        self.logger.debug("Trying callback." )
        callback ( retval, **pass_along )       
        
    def __update(self, table, record_dict, callback, pass_along):
        self.logger.debug("Updating record_dict '{}' of table {}.".format(record_dict, table))
        session = self.get_session()
        query = session.query(table)
        query = query.filter(table.aid == record_dict["aid"])
        results = query.all()
        if len(results) != 1:
            self.logger.error("update for {} had results = {}".format(
                record_dict, results))
            self.let_session(session)
            return
        statement = update(table).where(table.aid == record_dict["aid"]).\
                    values(record_dict)
        try:
            result = session.execute(statement)
        except Exception as e:
            self.logger.error("Exception while executing statement: {}.".format(e))
            raise e
        self.let_session(session)
        if callback == print:
            self.logger.debug("Ignoring 'print' callback.")
            return
        self.logger.debug("Trying callback.")
        callback(**pass_along)
        
    def get_session ( self ):
        session = sessionmaker(bind = self.engine)
        return session()

    def let_session ( self, session ):
        try:
            session.commit()
        except Exception as e:
            self.logger.debug("Exception during commit: {}".format ( e ) )
            session.rollback()
            self.let_session(session)
            return
        session.close()
