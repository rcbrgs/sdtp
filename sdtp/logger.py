# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from datetime import datetime
import logging
import os
import sys
import time

class logger ( QtCore.QThread ):

    log_gui = QtCore.pyqtSignal ( str, str )
    
    def __init__ ( self, controller = None ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        
        self.formatter = None
        self.handler = None
        self.keep_running = True
        self.log_buffer = [ ]
        self.log_buffer_size = 500
        self.logger = None

        self.logger = logging.getLogger ( "SDTP" )
        self.logger.setLevel ( logging.DEBUG )
        self.handler = logging.StreamHandler ( stream = sys.stdout )
        self.handler.setLevel ( logging.DEBUG )
        self.formatter = logging.Formatter ( fmt = "%(message)s", datefmt = '%Y-%m-%d %H:%M:%S' )
        self.handler.setFormatter ( self.formatter )
        self.logger.addHandler ( self.handler )
        self.start ( )
        
    def run ( self ):
        while self.keep_running:
            time.sleep ( 0.01 )

    def stop ( self ):
        self.keep_running = False

    # specific
    ##########

    def add_to_buffer ( self, gui_message ):
        if len ( self.log_buffer ) > self.log_buffer_size:
            self.log_buffer = self.log_buffer [ 1 : ]
        self.log_buffer.append ( gui_message )
        
    def log_call ( self, log_level, log_message ):
        self.log_gui.emit ( log_level, log_message )
        if ( log_level.lower ( ) == "debug" ):
            self.logger.debug ( log_message )
        if ( log_level.lower ( ) == "info" ):
            self.logger.info ( log_message )
        if ( log_level.lower ( ) == "warning" ):
            self.logger.warning ( log_message )
        if ( log_level.lower ( ) == "error" ):
            self.logger.error ( log_message )
        if ( log_level.lower ( ) == "critical" ):
            self.logger.critical ( log_message )
        self.add_to_buffer ( log_message )

    def log ( self, log_level, log_message ):
        frame = sys._getframe ( 2 )
        if log_message == None:
            for variable_index in range ( frame.f_code.co_argcount ):
                try:
                    variables_string += ", {}".format ( frame.f_code.co_varnames [ variable_index ] )
                except:
                    variables_string = "( {}".format ( frame.f_code.co_varnames [ variable_index ] )
            variables_string += " )"
            log_message = variables_string
        prefix = "{}.{} {}".format ( frame.f_locals [ "self" ].__class__.__name__, frame.f_code.co_name, log_message )
        self.log_call ( log_level, prefix )

    def set_level ( self, log_level ):
        if ( log_level.lower ( ) == "debug" ):
            self.logger.setLevel ( logging.DEBUG )
        if ( log_level.lower ( ) == "info" ):
            self.logger.setLevel ( logging.INFO )
        if ( log_level.lower ( ) == "warning" ):
            self.logger.setLevel ( logging.WARNING )
        if ( log_level.lower ( ) == "error" ):
            self.logger.setLevel ( logging.ERROR )
        if ( log_level.lower ( ) == "critical" ):
            self.logger.setLevel ( logging.CRITICAL )

    def set_initial_level ( self ):
        if self.controller.config.values [ "show_debug" ]:
            #print ( "logging.DEBUG" )
            self.logger.setLevel ( logging.DEBUG )
            return
        if self.controller.config.values [ "show_info" ]:
            #print ( "logging.INFO" )
            self.logger.setLevel ( logging.INFO )
            return
        if self.controller.config.values [ "show_warning" ]:
            #print ( "logging.WARNING" )
            self.logger.setLevel ( logging.WARNING )
            return
        if self.controller.config.values [ "show_error" ]:
            #print ( "logging.ERROR" )
            self.logger.setLevel ( logging.ERROR )
            return
        if self.controller.config.values [ "show_critical" ]:
            #print ( "logging.CRITICAL" )
            self.logger.setLevel ( logging.CRITICAL )
            return
    
class log_widget ( QtGui.QWidget ):
    def __init__ ( self, controller = None, parent = None, title = None ):
        super ( self.__class__, self ).__init__ ( parent )
        self.controller = controller
        self.parent = parent
        self.title = title
        
        self.init_GUI ( )

    def init_GUI ( self ):
        self.controller.log ( )

        layout = QtGui.QHBoxLayout ( )
        self.log_list = QtGui.QListWidget ( )
        self.add_buffer ( )
        self.controller.logger.log_gui.connect ( self.insert_log )
        layout.addWidget ( self.log_list )
        self.setLayout ( layout )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def closeEvent ( self, event ):
        self.controller.log ( )
        
        event.ignore ( )
        self.parent.subwindow_actions [ "{}_show_action".format ( self.__class__.__name__ ) ].setChecked ( False )
            
    def add_buffer ( self ):
        for item in self.controller.logger.log_buffer:
            self.insert_log ( item )

    def insert_log ( self, log_message ):
        self.log_list.insertItem ( 0, log_message )
        
