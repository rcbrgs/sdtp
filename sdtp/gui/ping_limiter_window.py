# -*- coding: utf-8 -*-

#from PySide import QtCore, QtGui
from PyQt4 import QtCore, QtGui

class ping_limiter_window ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

        self.controller.config.verify ( "show_ping_limiter_window" )
        
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
                                              
        close_button = QtGui.QPushButton ( "Close", self )
        close_button.clicked.connect ( self.close )

        main_layout = QtGui.QVBoxLayout ( )
        main_layout.addWidget ( enable_button )
        max_layout = QtGui.QHBoxLayout ( )
        max_layout.addWidget ( self.max_label )
        max_layout.addWidget ( self.max_ping )
        main_layout.addLayout ( max_layout )
        main_layout.addWidget ( close_button )

        self.setLayout ( main_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def close ( self ):
        self.controller.config.falsify ( "show_ping_limiter_window" )
        super ( self.__class__, self ).close ( )

    def set_max_ping ( self ):
        self.controller.config.values [ "max_ping" ] = int ( self.max_ping.text ( ) ) 
        self.max_label.setText ( "Maximum allowed ping: {}".format ( self.max_ping.text ( ) ) )
        self.max_ping.setText ( "" )
        
