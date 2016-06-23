# -*- coding: utf-8 -*-
# 0.2.0

import datetime
import os
import pathlib
from PyQt4 import QtCore
#from PySide import QtCore
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

    has_changed = QtCore.pyqtSignal ( )

    def __init__ ( self, controller = None, parent = None ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.parent = None
        self.ready = False
        self.engine = None
        self.mutex = False
        self.metadata = None
        self.start ( )

    # Thread control
    def run ( self ):
        self.controller.log ( )
        self.create_engine ( )
        self.create_tables ( )
        self.ready = True
        while ( self.keep_running ):
            time.sleep ( 0.1 )
        self.ready = False
        self.controller.log ( "debug", "returning." )

    def stop ( self ):
        self.controller.log ( )
        self.keep_running = False

    # GUI
    def emit_has_changed ( self ):
        self.controller.log ( )
        self.has_changed.emit ( )

    # Database
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
        self.controller.log ( "debug", "engine_string = {}".format ( engine_string ) )
        self.engine = create_engine ( engine_string )
        self.metadata = MetaData ( self.engine )
        self.metadata.reflect ( bind = self.engine )
        for table in self.metadata.tables:
            self.controller.log ( "debug", "table '{}' found in db.".format ( table ) )
        self.controller.log ( "debug", "returning." )

    def create_tables ( self ):
        self.controller.log ( )
        self.lp_table = lp_table ( )
        self.portals = portals_table ( )
        global Base
        Base.metadata.create_all ( self.engine )
        self.controller.log ( "debug", "database.create_tables returning." )

    # API
    def consult ( self, table, conditions ):
        self.controller.log ( )
        session = self.get_session ( )
        query = session.query ( table )
        for condition in conditions:
            query = query.filter ( condition [ 0 ] == condition [ 2 ] )
        results = query.all ( )
        self.let_session ( session )
        return results

    def get_session ( self ):
        self.controller.log ( )
        self.controller.log ( "debug", "{} asking for session.".format ( sys._getframe ( ).f_back.f_code.co_name ) )
        counter = 0
        large_number = 1000
        while self.mutex:
            self.controller.log ( "debug", "{} waiting mutex become False.".format ( sys._getframe ( ).f_back.f_code.co_name ) )
            time.sleep ( 1 )
            counter += 1
            if counter > large_number:
                self.controller.log ( "error", "database session locked for {} cycles by {}.".format ( large_number, sys._getframe ( ).f_back.f_code.co_name ) )
                counter = 0
        self.mutex = True
        self.controller.log ( "debug", "mutex just locked by {}".format ( sys._getframe ( ).f_back.f_code.co_name ) )
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
        self.mutex = False
