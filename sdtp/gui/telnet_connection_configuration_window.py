# -*- coding: utf-8 -*-
__version__ = "0.0.0"
__changelog__ = {
    "0.0.0" : "Initial version."
    }

from sdtp.gui.children_window import children_window

import sys
from PyQt4 import QtGui, QtCore
#from PySide import QtGui, QtCore

#class telnet_connection_configuration_window ( children_window ):
class telnet_connection_configuration_window ( QtGui.QDialog ):
    def __init__ ( self, parent, controller ):
        super ( self.__class__, self ).__init__ ( parent )

        self.controller = controller
        self.enabled = False
       
        layout = QtGui.QVBoxLayout ( self )
        self.setLayout ( layout )

        self.auto_connection_checkbox = QtGui.QCheckBox ( "Automatically connect to server when disconnected.", self )
        self.auto_connection_checkbox.setChecked ( self.controller.config.values [ 'auto_connect' ] )
        self.auto_connection_checkbox.stateChanged.connect ( self.__update_auto_connection )
        layout.addWidget ( self.auto_connection_checkbox )

        self.telnet_IP_button = QtGui.QPushButton ( "Telnet IP", self )
        self.telnet_IP_button.clicked.connect ( self.__config_telnet_IP )
        layout.addWidget ( self.telnet_IP_button )

        self.telnet_port_button = QtGui.QPushButton ( "Telnet port", self )
        self.telnet_port_button.clicked.connect ( self.__config_telnet_port )
        layout.addWidget ( self.telnet_port_button )

        self.telnet_password_button = QtGui.QPushButton ( "Telnet password", self )
        self.telnet_password_button.clicked.connect ( self.__config_telnet_password )
        layout.addWidget ( self.telnet_password_button )

        connection_layout = QtGui.QHBoxLayout ( )
        
        self.connect_button = QtGui.QPushButton ( "Connect", self )
        self.connect_button.setEnabled ( not controller.telnet_ongoing )
        self.connect_button.clicked.connect ( self.__connect )
        connection_layout.addWidget ( self.connect_button )

        self.disconnect_button = QtGui.QPushButton ( "Disconnect", self )
        self.disconnect_button.setEnabled ( not controller.telnet_ongoing )
        self.disconnect_button.clicked.connect ( self.__disconnect )
        connection_layout.addWidget ( self.disconnect_button )

        self.controller.telnet.connectable.connect ( self.__disconnect )
        self.controller.telnet.disconnectable.connect ( self.__connect )
        
        layout.addLayout ( connection_layout )
        
        ok_button = QtGui.QPushButton ( "Ok", self )
        #ok_button.clicked.connect ( self.accept )
        ok_button.clicked.connect ( self.close )
        layout.addWidget ( ok_button )

    def __update_auto_connection ( self, qt_checked_value ):
        if ( qt_checked_value == 2 ):
            self.controller.config.values [ 'auto_connect' ] = True
            self.controller.log ( "info", "Enabled automatic connection to telnet." )
        else:
            self.controller.config.values [ 'auto_connect' ] = False
            self.controller.log ( "info", "Disabled automatic connection to telnet." )

    def __config_telnet_IP ( self ):
        raw, ok = QtGui.QInputDialog.getText( self, 'Telnet IP', 'Enter IPv4 address for telnet server:', QtGui.QLineEdit.Normal, self.controller.config.values [ "telnet_IP" ] )
        new_telnet_IP = str ( raw )
        if ( ok == False ):
            return
        
        self.controller.config.values [ 'telnet_IP' ] = new_telnet_IP
        self.controller.log ( "info", "Set telnet IP to {}.".format ( new_telnet_IP ) )

    def __config_telnet_port ( self ):
        raw, ok = QtGui.QInputDialog.getText( self, 'Telnet port', 'Enter the port used for the telnet server:', QtGui.QLineEdit.Normal, str ( self.controller.config.values [ "telnet_port" ] ) )
        try:
            new_telnet_port = int ( raw )
        except:
            return
        if ( ok == False ):
            return
        
        self.controller.config.values [ 'telnet_port' ] = new_telnet_port
        self.controller.log ( "info", "Set telnet port to {}.".format ( new_telnet_port ) )

    def __config_telnet_password ( self ):
        raw, ok = QtGui.QInputDialog.getText( self, 'Telnet password', 'Enter your password: (WILL BE SAVED IN PLAINTEXT)', QtGui.QLineEdit.Normal, self.controller.config.values [ "telnet_password" ] )
        new_telnet_password = str ( raw )
        if ( ok == False ):
            return
        
        self.controller.config.values [ 'telnet_password' ] = new_telnet_password
        self.controller.log ( "info", "Set telnet password to {}.".format ( new_telnet_password ) )
        self.controller.log ( "critical", "The password will be saved in clear text on the configuration file!" )

    def __connect ( self ):
        self.connect_button.setEnabled ( False )
        self.disconnect_button.setEnabled ( True )

        if ( not self.controller.telnet_ongoing ):
            self.controller.connect_telnet ( self )

    def __disconnect ( self ):
        self.connect_button.setEnabled ( True )
        self.disconnect_button.setEnabled ( False )

        if ( self.controller.telnet_ongoing ):
            self.controller.disconnect_telnet ( self )
