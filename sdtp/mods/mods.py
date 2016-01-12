# -*- coding: utf-8 -*-

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
        
        server_reboots = QtGui.QPushButton ( "Configure server reboots", self )
        server_reboots.clicked.connect ( self.spawn_subwindow )
        if self.controller.config.get ( "server_reboots_widget_show" ):
            server_reboots.clicked.emit ( True )

        layout = QtGui.QVBoxLayout ( self )
        layout.addWidget ( server_reboots )
        self.setLayout ( layout )

        self.controller.config.verify ( "{}_show".format ( self.__class__.__name__ ) )
        if self.title != None:
            self.setWindowTitle ( self.title )
    
    def close ( self ):
        self.controller.config.values [ "{}_show".format ( self.__class__.__name__ ) ] = False
        super ( self.__class__, self ).close ( )

    def closeEvent ( self, event ):
        self.controller.log ( )
        
        event.ignore ( )
        self.parent.subwindow_actions [ "{}_show_action".format ( self.__class__.__name__ ) ].setChecked ( False )

    def spawn_subwindow ( self ):
        self.controller.log ( )

        server_reboots_subwindow = server_reboots_widget ( self.parent, self.controller, "Server reboots configuration" )
        subwindow_index = self.parent.mdi_area.addSubWindow ( server_reboots_subwindow )
        subwindows_list = self.parent.mdi_area.subWindowList ( )
        for sub in subwindows_list:
            if sub.widget ( ) == server_reboots_subwindow:
                sub.show ( )
