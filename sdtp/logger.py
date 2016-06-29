# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from datetime import datetime
import logging
import os
import sdtp
import sys
import time

class logger ( QtCore.QThread ):

    log_gui = QtCore.pyqtSignal ( str, str )
    debug_toggle = {
        "config" : "debug",
        "controller" : "info",
        "database" : "info",
        "dispatcher" : "debug",
        "telnet" : "debug",
        "world_state" : "debug",
        "portals" : "info",
        "server_reboots" : "debug",
        }

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

    def debug ( self, message, level, caller_class, caller_method ):
        log_message = "{}.{} {} {}".format (
            caller_class, caller_method, level.upper ( ), message )
        self.log_gui.emit ( level, log_message )
        if ( level.lower ( ) == "debug" ):
            if caller_class in self.debug_toggle:
                if self.debug_toggle [ caller_class ] != "debug":
                    self.debug (
                        message, self.debug_toggle [ caller_class ],
                        caller_class, caller_method )
            else:
                self.debug ( message, "info", caller_class, caller_method )
            self.logger.debug ( log_message )
        if ( level.lower ( ) == "info" ):
            self.logger.info ( log_message )
        if ( level.lower ( ) == "warning" ):
            self.logger.warning ( log_message )
        if ( level.lower ( ) == "error" ):
            self.logger.error ( log_message )
        if ( level.lower ( ) == "critical" ):
            self.logger.critical ( log_message )
        self.add_to_buffer ( level, log_message )

    # Boilerplate
    def run ( self ):
        while self.keep_running:
            time.sleep ( 0.01 )

    def stop ( self ):
        self.keep_running = False

    # specific
    ##########

    def add_to_buffer ( self, log_level, gui_message ):
        if len ( self.log_buffer ) > self.log_buffer_size:
            self.log_buffer = self.log_buffer [ 1 : ]
        self.log_buffer.append ( ( log_level, gui_message ) )

    def log_call ( self, log_level, log_message, frame_level = 3 ):
        self.log_gui.emit ( log_level, log_message )
        caller_frame = sys._getframe ( frame_level )
        caller_class = caller_frame.f_locals [ "self" ].__class__
        #log_message = "[{}] {}".format ( caller_class.__name__, log_message )
        if ( log_level.lower ( ) == "debug" ):
            if caller_class in self.debug_toggle:
                if self.debug_toggle [ caller_class ] != "debug":
                    self.logger.info ( log_message )
            self.logger.debug ( log_message )
        if ( log_level.lower ( ) == "info" ):
            self.logger.info ( log_message )
        if ( log_level.lower ( ) == "warning" ):
            self.logger.warning ( log_message )
        if ( log_level.lower ( ) == "error" ):
            self.logger.error ( log_message )
        if ( log_level.lower ( ) == "critical" ):
            self.logger.critical ( log_message )
        self.add_to_buffer ( log_level, log_message )

    def log ( self, log_level, log_message, log_prefix = None ):
        if log_prefix == None:
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
        else:
            self.log_call ( log_level, log_prefix + " " + log_message )

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
        if self.controller.config.values [ "log_show_debug" ]:
            self.logger.debug ( "Setting logger level to debug." )
            self.logger.setLevel ( logging.DEBUG )
            return
        if self.controller.config.values [ "log_show_info" ]:
            self.logger.debug ( "Setting logger level to info." )
            self.logger.setLevel ( logging.INFO )
            return
        if self.controller.config.values [ "log_show_warning" ]:
            self.logger.debug ( "Setting logger level to warning." )
            self.logger.setLevel ( logging.WARNING )
            return
        if self.controller.config.values [ "log_show_error" ]:
            self.logger.debug ( "Setting logger level to error." )
            self.logger.setLevel ( logging.ERROR )
            return
        if self.controller.config.values [ "log_show_critical" ]:
            self.logger.debug ( "Setting logger level to critical." )
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
        self.debug_checkbox = QtGui.QCheckBox ( "Show DEBUG messages", self )
        self.debug_checkbox.setChecked ( self.controller.config.values [ "log_show_debug" ] )
        self.debug_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "log_show_debug" ) )
        self.info_checkbox = QtGui.QCheckBox ( "Show INFO messages", self )
        self.info_checkbox.setChecked ( self.controller.config.values [ "log_show_info" ] )
        self.info_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "log_show_info" ) )
        self.warning_checkbox = QtGui.QCheckBox ( "Show WARNING messages", self )
        self.warning_checkbox.setChecked ( self.controller.config.values [ "log_show_warning" ] )
        self.warning_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "log_show_warning" ) )
        self.error_checkbox = QtGui.QCheckBox ( "Show ERROR messages", self )
        self.error_checkbox.setChecked ( self.controller.config.values [ "log_show_error" ] )
        self.error_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "log_show_error" ) )
        self.critical_checkbox = QtGui.QCheckBox ( "Show CRITICAL messages", self )
        self.critical_checkbox.setChecked ( self.controller.config.values [ "log_show_critical" ] )
        self.critical_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "log_show_critical" ) )
        self.log_widget = QtGui.QListWidget ( self )
        self.log_widget.setFont ( QtGui.QFont ( 'Monospace', 10 ) )
        checkboxes_layout = QtGui.QVBoxLayout ( )
        checkboxes_layout.addWidget ( self.debug_checkbox )
        checkboxes_layout.addWidget ( self.info_checkbox )
        checkboxes_layout.addWidget ( self.warning_checkbox )
        checkboxes_layout.addWidget ( self.error_checkbox )
        checkboxes_layout.addWidget ( self.critical_checkbox )
        checkboxes_frame = QtGui.QFrame ( )
        checkboxes_frame.setLayout ( checkboxes_layout )
        main_layout = QtGui.QHBoxLayout ( )
        main_layout.addWidget ( self.log_widget )
        main_frame = QtGui.QFrame ( )
        main_frame.setLayout ( main_layout )
        tabs = QtGui.QTabWidget ( )
        tabs.addTab ( checkboxes_frame, "Config" )
        tabs.addTab ( main_frame, "Log" )
        tab_layout = QtGui.QHBoxLayout ( )
        tab_layout.addWidget ( tabs )
        self.setLayout ( tab_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )       
        if self.title != None:
            self.setWindowTitle ( self.title )
        self.add_buffer ( )
        self.controller.logger.log_gui.connect ( self.insert_log )

    def add_buffer ( self ):
        for item in self.controller.logger.log_buffer:
            self.insert_log ( item [ 0 ], item [ 1 ] )

    def insert_log ( self, log_level_input, log_message_input ):
        try:
            log_message = str ( log_message_input )
        except UnicodeEncodeError as e:
            print ( "UnicodeEncodeError at logger.add_log: {}".format ( e ) )
            return
        log_level = str ( log_level_input )
        now = datetime.strftime ( datetime.now ( ), "%Y-%m-%d %H:%M:%S" )
        if log_level == "debug":
            if self.debug_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:5s} {}".format ( now, log_level.upper ( ), log_message ) )
        if log_level == "info":
            if self.info_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:5s} {}".format ( now, log_level.upper ( ), log_message ) )
        if log_level == "warning":
            if self.warning_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:5s} {}".format ( now, log_level.upper ( ), log_message ) )
        if log_level == "error":
            if self.error_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:5s} {}".format ( now, log_level.upper ( ), log_message ) )
        if log_level == "critical":
            if self.critical_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:5s} {}".format ( now, log_level.upper ( ), log_message ) )

    def show_checkbox_changed_state ( self, log_level_config ):
        if self.controller.config.values [ log_level_config ]:
            self.controller.config.values [ log_level_config ] = False
        else:
            self.controller.config.values [ log_level_config ] = True

        if self.controller.config.values [ "log_show_debug" ]:
            self.controller.logger.set_level ( "debug" )
            return
        if self.controller.config.values [ "log_show_info" ]:
            self.controller.logger.set_level ( "info" )
            return
        if self.controller.config.values [ "log_show_warning" ]:
            self.controller.logger.set_level ( "warning" )
            return
        if self.controller.config.values [ "log_show_error" ]:
            self.controller.logger.set_level ( "error" )
            return
        if self.controller.config.values [ "log_show_critical" ]:
            self.controller.logger.set_level ( "critical" )
            return

    def closeEvent ( self, event ):
        self.controller.log ( )

        event.ignore ( )
        self.parent.subwindow_actions [ "{}_show_action".format ( self.__class__.__name__ ) ].setChecked ( False )

    def close ( self ):
        self.controller.config.values [ "{}_show".format ( self.__class__.__name__ ) ] = False
        super ( self.__class__, self ).close ( )
