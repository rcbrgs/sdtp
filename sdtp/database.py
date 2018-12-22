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
from sdtp.lp_table import lp_table
from sdtp.mods.portals_tables import PortalsTable

class Database(threading.Thread):
    def __init__(self, controller = None):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)
        
        self.ready = False
        self.engine = None
        self.metadata = None
        self.queue = queue.Queue ( )
        self.start()

    # API
    def add_all ( self, table, records, callback ):
        self.logger.debug("table = {}".format ( table ) )
        self.enqueue ( self.__add_all, [ table, records, callback ] )

    def consult ( self, table, conditions, callback, pass_along = { } ):
        self.logger.debug("table = {}".format ( table ) )
        self.enqueue ( self.__consult, [ table, conditions, callback ], { "pass_along" : pass_along } )

    def delete(self, table, conditions, callback, pass_along = {}):
        self.logger.debug("table = {}".format(table))
        self.enqueue(self.__delete, [table, conditions, callback], {"pass_along": pass_along})
        
    def update_lp(self, steamid, values, callback, pass_along = {}):
        self.enqueue(self.__update_lp, [steamid, values, callback],{"pass_along": pass_along})

    # /API
        
    def run ( self ):
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
        task [ "method" ] ( *task [ "arguments" ], **task [ "keyword_arguments" ] )

    def stop ( self ):
        self.keep_running = False

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
        self.lp_table = lp_table()
        self.lp_table.create(self.engine)
        self.portals = PortalsTable ( )
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
        self.let_session ( session )
        query.delete()
        if callback == print:
            self.logger.debug("Ignoring 'print' callback." )
            return
        self.logger.debug("Trying callback." )
        callback ( retval, **pass_along )
        
    def __update_lp(self, steamid, values, callback, pass_along):
        self.logger.debug("Updating lp_table record for '{}'.".format(steamid))
        session = self.get_session()
        query = session.query(lp_table)
        query.filter(lp_table.steamid == values["steamid"])
        results = query.all()
        if len(results) != 1:
            self.logger.error("update_lp called with query results = {}".format(results))
            self.let_session(session)
            return
        statement = update(lp_table).where(lp_table.steamid == values["steamid"]).\
            values(player_id = values["player_id"],
                   name = values["name"],
                   longitude = values["longitude"],
                   height = values["height"],
                   latitude = values["latitude"],
                   rotation_height = values["rotation_height"],
                   rotation_longitude = values["rotation_longitude"],
                   rotation_latitude = values["rotation_latitude"],
                   remote = values["remote"],
                   health = values["health"],
                   deaths = values["deaths"],
                   zombies = values["zombies"],
                   players = values["players"],
                   score = values["score"],
                   level = values["level"],
                   steamid = values["steamid"],
                   ip = values["ip"],
                   ping = values["ping"])
        result = session.execute(statement)
        self.let_session(session)
        self.logger.info("result of update: {}".format(result))
        if callback == print:
            self.logger.debug("Ignoring 'print' callback.")
            return
        self.logger.debug("Trying callback.")
        callback(**pass_along)
        
    def get_session ( self ):
        session = sessionmaker ( bind = self.engine )
        return session ( )

    def let_session ( self, session ):
        try:
            session.commit ( )
        except Exception as e:
            self.logger.debug("exception during commit: {}".format ( e ) )
            time.sleep ( 1 )
            session.rollback ( )
            self.let_session ( session )
        session.close ( )
