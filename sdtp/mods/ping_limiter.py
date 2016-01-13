# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
#from PySide import QtCore
import threading
import time

class ping_limiter ( QtCore.QThread ):

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

        self.controller.dispatcher.register_callback ( "lp output", self.check_ping )
        self.start ( )

    def run ( self ):
        while ( self.keep_running ):
            time.sleep ( 0.1 )

    def stop ( self ):
        self.keep_running = False

    def check_ping ( self, match_group ):
        self.controller.log ( "debug", "mods.ping_limiter.check_ping ( {} )".format ( match_group ) )
        if not self.controller.config.values [ "enable_ping_limiter" ]:
            return
        if int ( match_group [ 17 ] ) > self.controller.config.values [ "max_ping" ]:
            self.controller.telnet.write ( 'kick {} "Ping too high (max is {})."'.format ( match_group [ 15 ], self.controller.config.values [ "max_ping" ] ) )

class ping_limiter_widget ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

    def init_GUI ( self ):

        enable_button = QtGui.QCheckBox ( "Enable kicking players with high ping", self )
        if self.controller.config.values [ "enable_ping_limiter" ]:
            enable_button.setChecked ( True )
        else:
            enable_button.setChecked ( False )
        enable_button.stateChanged.connect ( lambda: self.controller.config.toggle ( "enable_ping_limiter" ) )

        self.max_label = QtGui.QLabel ( "Maximum allowed ping: {}".format ( self.controller.config.values [ "max_ping" ] ), self )
        
        self.max_ping = QtGui.QLineEdit ( self )
        self.max_ping.returnPressed.connect ( self.set_max_ping )
                                              
        main_layout = QtGui.QVBoxLayout ( )
        main_layout.addWidget ( enable_button )
        max_layout = QtGui.QHBoxLayout ( )
        max_layout.addWidget ( self.max_label )
        max_layout.addWidget ( self.max_ping )
        main_layout.addLayout ( max_layout )
        
        self.setLayout ( main_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def set_max_ping ( self ):
        self.controller.config.values [ "max_ping" ] = int ( self.max_ping.text ( ) ) 
        self.max_label.setText ( "Maximum allowed ping: {}".format ( self.max_ping.text ( ) ) )
        self.max_ping.setText ( "" )
        
    def close ( self ):
        self.controller.config.falsify ( "show_{}".format ( self.__class__.__name__ ) )
        super ( self.__class__, self ).close ( )

    def closeEvent ( self, event ):
        self.controller.log ( )
        
        self.parent.mdi_area.removeSubWindow ( self )

