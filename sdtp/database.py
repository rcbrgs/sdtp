# -*- coding: utf-8 -*-

import datetime
import os
import pathlib
import queue
from PyQt4 import QtCore
from sqlalchemy import create_engine
from sqlalchemy import ( create_engine, Column, Float, Integer, MetaData, String, Table )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import time

Base = declarative_base ( )
from sdtp.lp_table import lp_table
from sdtp.mods.portals_tables import portals_table

class database ( QtCore.QThread ):

    # Boilerplate
    debug = QtCore.pyqtSignal ( str, str, str, str )

    def log ( self, level, message ):
        self.debug.emit ( message, level, self.__class__.__name__,
                          sys._getframe ( 1 ).f_code.co_name )

    has_changed = QtCore.pyqtSignal ( )

    def __init__ ( self, controller = None, parent = None ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.parent = None
        self.ready = False
        self.engine = None
        self.metadata = None
        self.queue = queue.Queue ( )
        self.queue_mutex = QtCore.QMutex ( )
        self.session_mutex = QtCore.QMutex ( )
        self.start ( )

    # API
    def add_all ( self, table, records, callback ):
        self.log ( "debug", "table = {}".format ( table ) )
        self.enqueue ( self.__add_all, [ table, records, callback ] )

    def consult ( self, table, conditions, callback, pass_along = { } ):
        self.log ( "debug", "table = {}".format ( table ) )
        self.enqueue ( self.__consult, [ table, conditions, callback ], { "pass_along" : pass_along } )

    def run ( self ):
        self.controller.log ( )
        self.create_engine ( )
        self.create_tables ( )
        self.ready = True
        count = 0
        while ( self.keep_running ):
            self.execute ( )
            self.sleep ( 0.1 )
            count =+ 1
            if count % 600 == 0:
                self.log ( "debug", "tick" )
        self.ready = False
        self.log ( "debug", "Returning." )

    def enqueue ( self, method, arguments = [ ], keyword_arguments = { } ):
        self.log ( "debug", "Trying to enqueue a task." )
        mutex_loader = QtCore.QMutexLocker ( self.queue_mutex )
        self.queue.put ( { "method" : method,
                           "arguments" : arguments,
                           "keyword_arguments" : keyword_arguments } )

    def execute ( self ):
        mutex_loader = QtCore.QMutexLocker ( self.queue_mutex )
        if self.queue.empty ( ):
            return
        self.log ( "debug", "Attempting to execute a task." )
        task = self.queue.get ( )
        mutex_loader.unlock ( )
        task [ "method" ] ( *task [ "arguments" ], **task [ "keyword_arguments" ] )

    def stop ( self ):
        self.controller.log ( )
        self.keep_running = False

    def emit_has_changed ( self ):
        self.controller.log ( )
        self.has_changed.emit ( )

    def create_engine ( self ):
        self.controller.log ( )
        config = self.controller.config.values
        if config [ "db_engine" ] == "sqlite":
            engine_string = "sqlite:///" + config [ "db_sqlite_file_path" ]
            # this code bridges 0.9.0 to 0.10.0
            possible_old = config [ "workdir" ] + config [ "separator" ] + "sdtp_sqlite.db"
            possibility = pathlib.Path ( possible_old )
            if possibility.exists ( ):
                self.controller.log ( "info", "old database found - renaming." )
                os.rename ( possible_old, config [ "db_sqlite_file_path" ] )
            # bridge ends here
        else:
            engine_string = config [ "db_engine" ] + config [ "db_user" ] + ":" + config [ "db_host_user" ] + "@" + config [ "db_host" ] + ":" +config [ "db_port" ] + config [ "separator" ] + config [ "db_name" ]
        self.log ( "debug", "engine_string = {}".format ( engine_string ) )
        self.engine = create_engine ( engine_string )
        self.metadata = MetaData ( self.engine )
        self.metadata.reflect ( bind = self.engine )
        for table in self.metadata.tables:
            self.log ( "debug", "table '{}' found in db.".format ( table ) )
        self.log ( "debug", "returning." )

    def create_tables ( self ):
        self.controller.log ( )
        self.lp_table = lp_table ( )
        self.portals = portals_table ( )
        global Base
        Base.metadata.create_all ( self.engine )
        self.log ( "debug", "database.create_tables returning." )

    def __add_all ( self, table, records, callback ):
        self.log ( "debug", "Querying table {}.".format ( table ) )
        mutex = QtCore.QMutexLocker ( self.session_mutex )
        session = self.get_session ( )
        query = session.query ( table )
        results = session.add_all ( records )
        self.let_session ( session )
        if callback == print:
            self.log ( "debug", "Ignoring 'print' callback." )
            return
        self.log ( "debug", "Trying callback '{} ( {} )'.".format ( callback, results ) )
        callback ( results )

    def __consult ( self, table, conditions, callback, pass_along ):
        self.log ( "debug", "Querying table {} with conditions '{}'.".format ( table, conditions ) )
        mutex = QtCore.QMutexLocker ( self.session_mutex )
        session = self.get_session ( )
        query = session.query ( table )
        for condition in conditions:
            before = query.count ( )
            query = query.filter ( condition [ 0 ] == condition [ 2 ] )
            self.log ( "debug", "Applying condition '{}' diminished query count from {} to {}".format ( condition, before, query.count ( ) ) )
        results = query.all ( )
        self.log ( "debug", "results = {}".format ( results ) )
        self.let_session ( session )
        if callback == print:
            self.log ( "debug", "Ignoring 'print' callback." )
            return
        self.log ( "debug", "Trying callback." )
        callback ( results, **pass_along )

    def get_session ( self ):
        session = sessionmaker ( bind = self.engine )
        return session ( )

    def let_session ( self, session ):
        self.controller.log ( )
        try:
            session.commit ( )
        except Exception as e:
            self.controller.log ( "info", "exception during commit: {}".format ( e ) )
            time.sleep ( 1 )
            session.rollback ( )
            self.let_session ( session )
        session.close ( )
