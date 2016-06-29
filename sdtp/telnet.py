# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
import re
import socket
import sys
import telnetlib
import time
import threading

class telnet ( QtCore.QThread ):

    # Boilerplate
    debug = QtCore.pyqtSignal ( str, str, str, str )

    def log ( self, level, message ):
        self.debug.emit ( message, level, self.__class__.__name__,
                          sys._getframe ( 1 ).f_code.co_name )

    connectable = QtCore.pyqtSignal ( )
    disconnectable = QtCore.pyqtSignal ( )
    status = QtCore.pyqtSignal ( str )

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        self.keep_running = True

        self.auto_connect = False
        self.connectivity_level = 0
        self.latest_handshake = 0
        self.output_matchers = [ re.compile ( b'^.*\n' ),
                                 re.compile ( b'^Day [\d]+, [\d]{2}:[\d]{2} ' ),
                                 re.compile ( b'Total of [\d]+ in the game' ) ]
        self.telnet = None

    def run ( self ):
        self.controller.dispatcher.register_callback ( "password incorrect", self.close_connection_wrapper )
        while ( self.keep_running ):
            if ( not self.check_connection ( ) ):
                time.sleep ( 1 )
                continue
            line = self.chomp ( )
            if line == '':
                continue
            try:
                line_string = ""
                if line:
                    line_string = line.decode ( 'utf-8' )
                    line_string = line_string.strip ( )
            except Exception as e:
                self.log ( "error", "Error {} while processing line.decode ( '{}' )".format ( e, line ) )
            self.log ( "debug", line_string )
            self.controller.parser.enqueue ( line_string )
        self.close_connection ( )

    def stop ( self ):
        self.keep_running = False

    # Connection methods
    def check_connection ( self ):
        """
        Should return True if everything is fine with the connection.
        Do not rely on metadata for this; this function is supposed to be reliable, and the metadata set according to its results.
        """
        if self.controller.config.values [ "auto_connect" ]:
            self.open_connection ( )
        if self.connectivity_level != 2:
            return False
        if self.telnet == None:
            return False
        if not isinstance ( self.telnet.get_socket ( ), socket.socket ):
            return False
        return True

    def close_connection ( self ):
        self.log ( "info", "Closing connection." )
        if self.connectivity_level == 2:
            self.handshake_bye ( )
        self.controller.telnet_ongoing = False
        self.telnet = None
        self.connectivity_level = 0
        self.connectable.emit ( )

    def handshake_bye ( self ):
        self.write ( "exit" )
        self.telnet.close ( )
        self.connectivity_level = 1
        self.log ( "debug", "Telnet connection closed." )

    def close_connection_wrapper ( self, match_groups ):
        self.close_connection ( )

    def create_telnet_object ( self ):
        self.telnet = telnetlib.Telnet ( timeout = 10 )
        if self.telnet != None:
            self.connectivity_level = 1
        self.log ( "debug", "Telnet step 1 completed." )

    def handshake_hi ( self ):
        if time.time ( ) - self.latest_handshake < 10:
            self.log ( "info", "Sleeping 10 seconds before attempting to connect again." )
            self.status.emit ( "Waiting 10s before retry." )
            time.sleep ( 10 )
        self.latest_handshake = time.time ( )
        try:
            self.telnet.open ( self.controller.config.values [ 'telnet_IP' ], self.controller.config.values [ 'telnet_port' ], timeout = 5 )
            self.telnet.read_until ( b"Please enter password:" )
            self.log ( "debug", "Password requested by server." )
            self.write ( self.controller.config.values [ 'telnet_password' ] )
            self.log ( "debug", "Password was sent to server." )
        except Exception as e:
            self.log ( "error", "Error while opening connection: %s." % str ( e ) )
            return
        self.log ( "debug", "Waiting for 'Logon successful'" )
        try:
            linetest = self.telnet.read_until ( b'Logon successful.' )
        except Exception as e:
            self.log ( "error", "linetest exception: {}.".format ( e ) )
            return
        if b'Logon successful.' in linetest:
            self.log ( "debug", linetest.decode ( 'utf-8' ) )
            self.log ( "info", "Telnet connected successfully." )
        else:
            self.log ( "error", "Logon failed.")
            return
        self.log ( "debug", "Telnet step 2 completed." )
        self.connectivity_level = 2

    def open_connection ( self ):
        if self.connectivity_level == 2:
            self.log ( "debug", "Attempted to re-open connection, ignoring call." )
            self.status.emit ( "connected." )
            self.disconnectable.emit ( )
            return
        self.log ( "info", "Trying to open connection." )
        if self.connectivity_level == 0:
            self.create_telnet_object ( )
            self.status.emit ( "trying to connect." )
        if self.connectivity_level == 1:
            self.handshake_hi ( )
            self.status.emit ( "handshake accepted." )
        if self.connectivity_level != 2:
            self.log ( "warning", "open_connection failed." )
            self.status.emit ( "connection failed." )
            self.close_connection ( )
            return
        self.controller.telnet_ongoing = True
        self.disconnectable.emit ( )

    # I/O methods
    def chomp ( self ):
        try:
            result = self.telnet.expect ( self.output_matchers, 5 )
            self.log ( "debug", "result = {}".format ( result ) )
            if len ( result ) == 3:
                line = result [ 2 ]
                if result [ 0 ] == -1:
                    if result [ 2 ] != b'':
                        self.log ( "debug", "expect timed out on '{}'.".format ( result [ 2 ] ) )
                        return
                elif result [ 0 ] != 0:
                    self.log ( "info",  "output_matcher [ {} ] hit. result = '{}'.".format ( result [ 0 ], result ) )
        except EOFError as e:
            self.log ( "warning", "chomp EOFError '{}'.".format ( e ) )
            self.close_connection ( )
            return
        except Exception as e:
            if not self.check_connection ( ):
                self.log ( "warning", "chomp had an exception, because the connection is off." )
                self.close_connection ( )
                return
            if "[Errno 104] Connection reset by peer" in str ( e ):
                self.log ( "warning", "chomp: game server closed the connection." )
                self.close_connection ( )
                return
            self.log ( "error", "Exception in chomp: {}, sys.exc_info = '{}'.".format ( e, sys.exc_info ( ) ) )
            self.log ( "error", "type ( self.telnet ) == {}".format ( type ( self.telnet ) ) )
            self.log ( "error", "isinstance ( self.telnet.get_socket ( ), socket.socket ) = {}".format ( self.check_connection ( ) ) )
            self.close_connection ( )
            return
        return line

    def write ( self, input_msg ):
        if self.connectivity_level == 0:
            self.log ( "info", "Ignoring attempt to write  with level 0 connectivity." )
            return

        if self.connectivity_level == 1:
            self.log ( "info", "Writing with level 1 connectivity." )
        self.log ( "debug", "Type ( input_msg ) == {}".format ( type ( input_msg ) ) )
        try:
            msg = input_msg + "\n"
        except Exception as e:
            self.log ( "error", "Newline exception: {}".format ( e ) )
            return
        self.log ( "debug", "Raw write" )
        try:
            self.telnet.write ( msg.encode ( "utf8", "replace" ) )
        except Exception as e:
            self.log ( "error", "telnet.write had exception: {}".format ( e ) )
            return
        self.log ( "debug", "Message written." )

class telnet_widget ( QtGui.QWidget ):

    # Boilerplate
    debug = QtCore.pyqtSignal ( str, str, str, str )

    def log ( self, level, message ):
        self.debug.emit ( message, level, self.__class__.__name__,
                          sys._getframe ( 1 ).f_code.co_name )

    def __init__ ( self, parent = None, controller = None, title = "Telnet configuration" ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.enabled = False
        self.parent = parent
        self.title = title
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
        self.status_label = QtGui.QLabel ( "Current status: unknown" )
        self.controller.telnet.status.connect ( self.change_status )
        self.controller.telnet.connectable.connect ( self.__disconnect )
        self.controller.telnet.disconnectable.connect ( self.__connect )
        layout.addLayout ( connection_layout )
        layout.addWidget ( self.status_label )
        layout.addStretch ( )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def change_status ( self, status ):
        self.status_label.setText ( "Connection status: {}".format ( status ) )

    def __update_auto_connection ( self, qt_checked_value ):
        if ( qt_checked_value == 2 ):
            self.controller.config.values [ 'auto_connect' ] = True
            self.log ( "info", "Enabled automatic connection to telnet." )
        else:
            self.controller.config.values [ 'auto_connect' ] = False
            self.log ( "info", "Disabled automatic connection to telnet." )

    def __config_telnet_IP ( self ):
        raw, ok = QtGui.QInputDialog.getText( self, 'Telnet IP', 'Enter IPv4 address for telnet server:', QtGui.QLineEdit.Normal, self.controller.config.values [ "telnet_IP" ] )
        new_telnet_IP = str ( raw )
        if ( ok == False ):
            return
        self.controller.config.values [ 'telnet_IP' ] = new_telnet_IP
        self.log ( "info", "Set telnet IP to {}.".format ( new_telnet_IP ) )

    def __config_telnet_port ( self ):
        raw, ok = QtGui.QInputDialog.getText( self, 'Telnet port', 'Enter the port used for the telnet server:', QtGui.QLineEdit.Normal, str ( self.controller.config.values [ "telnet_port" ] ) )
        try:
            new_telnet_port = int ( raw )
        except:
            return
        if ( ok == False ):
            return
        self.controller.config.values [ 'telnet_port' ] = new_telnet_port
        self.log ( "info", "Set telnet port to {}.".format ( new_telnet_port ) )

    def __config_telnet_password ( self ):
        raw, ok = QtGui.QInputDialog.getText( self, 'Telnet password', 'Enter your password: (WILL BE SAVED IN PLAINTEXT)', QtGui.QLineEdit.Normal, self.controller.config.values [ "telnet_password" ] )
        new_telnet_password = str ( raw )
        if ( ok == False ):
            return
        self.controller.config.values [ 'telnet_password' ] = new_telnet_password
        self.log ( "info", "Set telnet password to {}.".format ( new_telnet_password ) )
        self.log ( "critical", "The password will be saved in clear text on the configuration file!" )

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

    def close ( self ):
        self.controller.config.values [ "{}_show".format ( self.__class__.__name__ ) ] = False
        super ( self.__class__, self ).close ( )

    def closeEvent ( self, event ):
        event.ignore ( )
        self.parent.subwindow_actions [ "{}_show_action".format ( self.__class__.__name__ ) ].setChecked ( False )
