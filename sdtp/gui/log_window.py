# -*- coding: utf-8 -*-

#from PySide import QtCore, QtGui
from PyQt4 import QtCore, QtGui
from time import sleep, strftime

class log_window ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

        self.controller.logger.log_gui.connect ( self.add_log )
        self.controller.config.values [ "show_log_window" ] = True
        
    def init_GUI ( self ):

        self.debug_checkbox = QtGui.QCheckBox ( "Show DEBUG messages", self )
        self.debug_checkbox.setChecked ( self.controller.config.values [ "show_debug" ] )
        self.debug_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "show_debug" ) )
        self.info_checkbox = QtGui.QCheckBox ( "Show INFO messages", self )
        self.info_checkbox.setChecked ( self.controller.config.values [ "show_info" ] )
        self.info_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "show_info" ) )        
        self.warning_checkbox = QtGui.QCheckBox ( "Show WARNING messages", self )
        self.warning_checkbox.setChecked ( self.controller.config.values [ "show_warning" ] )
        self.warning_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "show_warning" ) )
        self.error_checkbox = QtGui.QCheckBox ( "Show ERROR messages", self )
        self.error_checkbox.setChecked ( self.controller.config.values [ "show_error" ] )
        self.error_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "show_error" ) )
        self.critical_checkbox = QtGui.QCheckBox ( "Show CRITICAL messages", self )
        self.critical_checkbox.setChecked ( self.controller.config.values [ "show_critical" ] )
        self.critical_checkbox.stateChanged.connect ( lambda: self.show_checkbox_changed_state ( "show_critical" ) )
                
        self.log_widget = QtGui.QListWidget ( self )
        self.log_widget.setFont ( QtGui.QFont ( 'Monospace', 10 ) )

        close_button = QtGui.QPushButton ( "Close", self )
        close_button.clicked.connect ( self.close )

        checkboxes_layout = QtGui.QVBoxLayout ( )
        checkboxes_layout.addWidget ( self.debug_checkbox )
        checkboxes_layout.addWidget ( self.info_checkbox )
        checkboxes_layout.addWidget ( self.warning_checkbox )
        checkboxes_layout.addWidget ( self.error_checkbox )
        checkboxes_layout.addWidget ( self.critical_checkbox )
        main_layout = QtGui.QHBoxLayout ( )
        main_layout.addLayout ( checkboxes_layout )
        main_layout.addWidget ( self.log_widget )
        main_layout.addWidget ( close_button )
        self.setLayout ( main_layout )

        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        
        if self.title != None:
            self.setWindowTitle ( self.title )

    def add_log ( self, log_level_input, log_message_input ):
        try:
            log_message = str ( log_message_input )
        except UnicodeEncodeError as e:
            print ( "UnicodeEncodeError at logger.add_log: {}".format ( e ) )
            return
        log_level = str ( log_level_input )
        now = strftime ( "%Y-%m-%d %H:%M:%S" )
        if log_level == "debug":
            if self.debug_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:8s} {}".format ( now, log_level.upper ( ), log_message ) )
        if log_level == "info":
            if self.info_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:8s} {}".format ( now, log_level.upper ( ), log_message ) )
        if log_level == "warning":
            if self.warning_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:8s} {}".format ( now, log_level.upper ( ), log_message ) )
        if log_level == "error":
            if self.error_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:8s} {}".format ( now, log_level.upper ( ), log_message ) )
        if log_level == "critical":
            if self.critical_checkbox.isChecked ( ):
                self.log_widget.insertItem ( 0, "{} {:8s} {}".format ( now, log_level.upper ( ), log_message ) )
        
    def show_checkbox_changed_state ( self, log_level_config ):
        if self.controller.config.values [ log_level_config ]:
            self.controller.config.values [ log_level_config ] = False
        else:
            self.controller.config.values [ log_level_config ] = True

        if self.controller.config.values [ "show_debug" ]:
            self.controller.logger.set_level ( "debug" )
            return
        if self.controller.config.values [ "show_info" ]:
            self.controller.logger.set_level ( "info" )
            return
        if self.controller.config.values [ "show_warning" ]:
            self.controller.logger.set_level ( "warning" )
            return
        if self.controller.config.values [ "show_error" ]:
            self.controller.logger.set_level ( "error" )
            return
        if self.controller.config.values [ "show_critical" ]:
            self.controller.logger.set_level ( "critical" )
            return

    def close ( self ):
        self.controller.config.values [ "show_log_window" ] = False
        super ( self.__class__, self ).close ( )
