# -*- coding: utf-8 -*-

from .forbidden_countries import forbidden_countries_widget
from .ping_limiter import ping_limiter_widget
from .server_reboots import server_reboots_widget

from PyQt4 import QtGui, QtCore
#from PySide import QtCore
import time


class mods_widget ( QtGui.QWidget ):
    def __init__ ( self, parent = None, controller = None, title = "Mods configuration" ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.parent = parent
        self.title = title

        self.init_GUI ( )
        
    def init_GUI ( self ):
        self.controller.log ( )
        
        forbidden_countries_button = QtGui.QPushButton ( 'Configure per-country bans', self )
        forbidden_countries_button.clicked.connect ( lambda: self.spawn_subwindow ( forbidden_countries_widget ( self.parent, self.controller ) ) )
        if self.controller.config.get ( "forbidden_countries_widget_show" ):
            forbidden_countries_button.clicked.emit ( True )

        ping_limiter_button = QtGui.QPushButton ( 'Configure ping limit', self )
        ping_limiter_button.clicked.connect ( lambda: self.spawn_subwindow ( ping_limiter_widget ( self.parent, self.controller ) ) )
        if self.controller.config.get ( "ping_limiter_widget_show" ):
            ping_limiter_button.clicked.emit ( True )
            
        server_reboots = QtGui.QPushButton ( "Configure server reboots", self )
        server_reboots.clicked.connect ( lambda: self.spawn_subwindow ( server_reboots_widget ( self.parent, self.controller, "Server reboots configuration" ) ) )
        if self.controller.config.get ( "server_reboots_widget_show" ):
            server_reboots.clicked.emit ( True )

        layout = QtGui.QVBoxLayout ( self )
        layout.addWidget ( forbidden_countries_button )
        layout.addWidget ( ping_limiter_button )
        layout.addWidget ( server_reboots )
        self.setLayout ( layout )

        if self.title != None:
            self.setWindowTitle ( self.title )
    
    def close ( self ):
        self.controller.config.values [ "{}_show".format ( self.__class__.__name__ ) ] = False
        super ( self.__class__, self ).close ( )

    def closeEvent ( self, event ):
        self.controller.log ( )
        
        event.ignore ( )
        self.parent.subwindow_actions [ "{}_show_action".format ( self.__class__.__name__ ) ].setChecked ( False )

    def spawn_subwindow ( self, widget ):
        self.controller.log ( )

        subwindow_index = self.parent.mdi_area.addSubWindow ( widget )
        subwindows_list = self.parent.mdi_area.subWindowList ( )
        for sub in subwindows_list:
            if sub.widget ( ) == widget:
                sub.show ( )
                self.parent.organize_subwindows ( )
