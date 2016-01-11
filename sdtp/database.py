# -*- coding: utf-8 -*-

from sdtp.lp_table import lp_table
from sdtp.mods.portals_tables import portals_table

import os
from PyQt4 import QtCore
#from PySide import QtCore
from sqlalchemy import create_engine
from sqlalchemy import ( create_engine, Column, Float, Integer, MetaData, String, Table )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import time

class database ( QtCore.QThread ):

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

        self.engine = None
        self.mutex = False
        self.metadata = None
        
        self.start ( )

    # Thread control
    ################        
        
    def run ( self ):
        self.controller.log ( "debug", "database.run ( )" )

        self.create_engine ( )
        self.create_tables ( )
        
        while ( self.keep_running ):
            time.sleep ( 0.1 )

        self.controller.log ( "debug", "database.run returning" )

    def stop ( self ):
        self.controller.log ( "debug", "database.stop ( )" )
        self.keep_running = False

    # Database
    ##########

    def create_engine ( self ):
        self.controller.log ( "debug", "database.create_engine ( )" )

        separator = "/"
        if os.name == "nt":
            separator = "\\\\"
        engine_file_name = "sqlite:///" + self.controller.config.values [ "configuration_file_path" ] + separator + self.controller.config.values [ "database_file_name" ]
        self.controller.log ( "debug", "database: engine_fine_name = {}".format ( engine_file_name ) )
        self.engine = create_engine ( engine_file_name )
        self.metadata = MetaData ( self.engine )
        self.metadata.reflect ( bind = self.engine )
        for table in self.metadata.tables:
            self.controller.log ( "debug", "database.create_engine: table '{}' exists in db.".format ( table ) )
        self.controller.log ( "debug", "database.create_engine returning." )
        
    def create_tables ( self ):
        self.controller.log ( "debug", "database.create_tables ( )" )

        self.lp_table = lp_table ( )
        self.lp_table.create ( self.engine )
        self.portals = portals_table ( )
        self.portals.create ( self.engine )

        self.controller.log ( "debug", "database.create_tables returning." )

    def get_session ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )

        self.controller.log ( "debug", prefix + " {} asking for session.".format ( sys._getframe ( ).f_back.f_code.co_name ) )                                                                    
        counter = 0
        while self.mutex:
            self.controller.log ( "debug", prefix + ": {} waiting mutex become False.".format ( sys._getframe ( ).f_back.f_code.co_name ) )
            time.sleep ( 1 )
            counter += 1
            if counter > 100:
                self.controller.log ( "error", prefix + " database session locked for 100 cycles by {}.".format ( sys._getframe ( ).f_back.f_code.co_name ) )
                
        self.mutex = True
        self.controller.log ( "debug", prefix + " mutex just locked by {}".format ( sys._getframe ( ).f_back.f_code.co_name ) )
        session = sessionmaker ( bind = self.engine )
            
        return session ( )

    def let_session ( self, session ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )

        try:
            session.commit ( )
        except Exception as e:
            self.controller.log ( "info", prefix + " exception during commit: {}".format ( e ) )
            time.sleep ( 1 )
            session.rollback ( )
            self.let_session ( session )
        session.close ( )
        self.mutex = False
