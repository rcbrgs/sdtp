# -*- coding: utf-8 -*-

#from PySide import QtCore, QtGui
from PyQt4 import QtCore, QtGui
import sys

class player_portals_window ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

        self.controller.config.verify ( "show_player_portals_window" )

    # GUI
    #####
        
    def init_GUI ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        enable = QtGui.QCheckBox ( "Enable players to set portals.", self )
        enable.setChecked ( self.controller.config.values [ "enable_player_portals" ] )
        enable.stateChanged.connect ( lambda: self.controller.config.toggle ( "enable_player_portals" ) )

        enable_auto_horde = QtGui.QCheckBox ( "Enable automatic screamer zombie portals.", self )
        enable_auto_horde.setChecked ( self.controller.config.values [ "enable_auto_horde_portals" ] )
        enable_auto_horde.stateChanged.connect ( lambda: self.controller.config.toggle ( "enable_auto_horde_portals" ) )

        close = QtGui.QPushButton ( "Close", self )
        close.clicked.connect ( self.close )

        main_layout = QtGui.QVBoxLayout ( )
        main_layout.addWidget ( enable )
        main_layout.addWidget ( enable_auto_horde )
        main_layout.addWidget ( close )

        self.setLayout ( main_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        if self.title != None:
            self.setWindowTitle ( self.title )

        self.controller.log ( "debug", prefix + " return." )
            
    def close ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        self.controller.config.falsify ( "show_player_portals_window" )
        super ( self.__class__, self ).close ( )
