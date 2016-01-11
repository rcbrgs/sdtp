# -*- coding: utf-8 -*-

from ..auto_updater import fetch_update_confirm_dialog, fetch_update_execute_dialog, install_update_confirm_dialog, reinitialize_update_confirm_dialog
from ..controller import controller
from .chat_window import chat_window
from .country_ban_window import country_ban_window
from .log_window import log_window
from .metronomer_window import metronomer_window
from .ping_limiter_window import ping_limiter_window
from .player_portals_window import player_portals_window
from .players_window import players_window
from .telnet_connection_configuration_window import telnet_connection_configuration_window
from ..version import api, feature, bug

from ..mods.server_reboot import server_reboot_window

from PyQt4 import QtGui, QtCore
#from PySide import QtGui, QtCore
import sys
import time

class main_window ( QtGui.QWidget ):

    def __init__( self ):
        super ( main_window, self ).__init__ ( )
        self.children = [ ]
        
        self.init_GUI ( )
        
    def init_GUI ( self ):
        self.controller = controller ( self )
        self.controller.start ( )
        while ( not self.controller.ready_for_gui ( ) ):
            time.sleep ( 1 )

        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )
        
        mainLayout = QtGui.QHBoxLayout ( self )
        QtGui.QToolTip.setFont ( QtGui.QFont ( 'SansSerif', 10 ) )
        self.setWindowTitle ( 'Seven Days To Py v{}.{}.{}'.format ( api, feature, bug ) )

        self.controller.log ( "debug", "Create country ban dialog." )
        self.country_ban_dialog = country_ban_window ( self, self.controller )

        self.controller.log ( "debug", "Create telnet connection configuration dialog." )
        telnet_connection_configuration_dialog = telnet_connection_configuration_window ( self, self.controller )
        
        self.controller.log ( "debug", "Country ban button." )                
        country_ban_button = QtGui.QPushButton ( 'Configure per-country bans', self )
        country_ban_button.clicked.connect ( self.country_ban_dialog.show )
        country_ban_button.setToolTip ( 'Opens the country ban configuration tool.' )
        country_ban_button.resize ( country_ban_button.sizeHint() )

        self.controller.log ( "debug", "Creating telnet config button." )
        telnet_config_button = QtGui.QPushButton ( 'Configure Telnet', self )
        telnet_config_button.clicked.connect ( telnet_connection_configuration_dialog.show )
        telnet_config_button.setToolTip ( 'Opens the Telnet configuration tool.' )
        telnet_config_button.resize ( telnet_config_button.sizeHint() )

        metronomer_window_button = QtGui.QPushButton ( "Configure metronomer", self )
        metronomer_window_button.clicked.connect ( lambda: self.children.append ( metronomer_window ( self, self.controller, "Metronomer configuration" ) ) )
        if self.controller.config.values [ "show_metronomer_window" ]:
            metronomer_window_button.clicked.emit ( True )
        
        open_ping_limiter_window = QtGui.QPushButton ( "Configure ping limiter", self )
        open_ping_limiter_window.clicked.connect ( lambda: self.children.append ( ping_limiter_window ( self, self.controller, "Ping limiter configuration" ) ) )
        if self.controller.config.values [ "show_ping_limiter_window" ]:
            open_ping_limiter_window.clicked.emit ( True )

        show_player_portals_window = QtGui.QPushButton ( "Configure player portals", self )
        show_player_portals_window.clicked.connect ( lambda: self.children.append ( player_portals_window ( self, self.controller, "Player portals configuration" ) ) )
        if self.controller.config.values [ "show_player_portals_window" ]:
            show_player_portals_window.clicked.emit ( True )
            
        players_window_button = QtGui.QPushButton ( "Open players window", self )
        players_window_button.clicked.connect ( lambda: self.children.append ( players_window ( self, self.controller, "Players" ) ) )
        if self.controller.config.values [ "show_players_window" ]:
            self.children.append ( players_window ( self, self.controller, "Players" ) )

        chat_window_button = QtGui.QPushButton ( "Open chat window", self )
        chat_window_button.clicked.connect ( lambda: self.children.append ( chat_window ( self, self.controller, "Chat" ) ) )
        if self.controller.config.values [ "show_chat_window" ]:
            chat_window_button.clicked.emit ( True ) 
            
        log_window_button = QtGui.QPushButton ( "Open log window", self )
        log_window_button.clicked.connect ( lambda: self.children.append ( log_window ( self, self.controller, "Log" ) ) )
        if self.controller.config.values [ "show_log_window" ]:
            self.children.append ( log_window ( self, self.controller, "Log" ) )

        # Mods
        ######
        server_reboots = QtGui.QPushButton ( "Configure server reboots", self )
        server_reboots.clicked.connect ( lambda: self.children.append ( server_reboot_window ( self, self.controller, "Server reboots configuration" ) ) )
        if self.controller.config.values [ "show_server_reboot_window" ]:
            server_reboots.clicked.emit ( True )
        
        self.controller.log ( "debug", "Quit button." )        
        quitButton = QtGui.QPushButton ( '&Quit', self )
        quitButton.clicked.connect ( self.stop )
        quitButton.setToolTip ( 'Exits program' )
        quitButton.resize ( quitButton.sizeHint() )

        self.controller.log ( "debug", "Main window post-layout." )        
        topLeftFrame = QtGui.QFrame ( self )
        topLeftFrame.setFrameShape ( QtGui.QFrame.StyledPanel )
        topLeftFrameLayout = QtGui.QVBoxLayout ( )
        topLeftFrame.setLayout ( topLeftFrameLayout )
        topCenterFrame = QtGui.QFrame ( self )
        topCenterFrame.setFrameShape ( QtGui.QFrame.StyledPanel )
        topCenterFrameLayout = QtGui.QVBoxLayout ( )
        topCenterFrame.setLayout ( topCenterFrameLayout )
        topRightFrame = QtGui.QFrame ( self )
        topRightFrame.setFrameShape ( QtGui.QFrame.StyledPanel )
        topRightFrameLayout = QtGui.QVBoxLayout ( )
        topRightFrame.setLayout ( topRightFrameLayout )
        modsFrame = QtGui.QFrame ( self )
        modsFrame.setFrameShape ( QtGui.QFrame.StyledPanel )
        modsFrameLayout = QtGui.QVBoxLayout ( )
        modsFrame.setLayout ( modsFrameLayout )

        topLeftSplitter = QtGui.QSplitter ( QtCore.Qt.Horizontal )
        topLeftSplitter.addWidget ( topLeftFrame )
        topLeftSplitter.addWidget ( topCenterFrame )
        topRightSplitter = QtGui.QSplitter ( QtCore.Qt.Horizontal )
        topRightSplitter.addWidget ( topLeftSplitter )
        topRightSplitter.addWidget ( topRightFrame )
        bottomSplitter = QtGui.QSplitter( QtCore.Qt.Vertical )
        bottomSplitter.addWidget ( topRightSplitter )
        bottomSplitter.addWidget ( modsFrame )
        mainLayout.addWidget ( bottomSplitter )

        topLeftFrameLayout.addWidget ( telnet_config_button )
        topLeftFrameLayout.addWidget ( metronomer_window_button )
        topCenterFrameLayout.addWidget ( players_window_button )
        topCenterFrameLayout.addWidget ( chat_window_button )
        topCenterFrameLayout.addWidget ( log_window_button )
        topRightFrameLayout.addWidget ( quitButton )
        modsFrameLayout.addWidget ( server_reboots )       
        modsFrameLayout.addWidget ( country_ban_button )       
        modsFrameLayout.addWidget ( open_ping_limiter_window )
        modsFrameLayout.addWidget ( show_player_portals_window )
       
        self.setLayout ( mainLayout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        self.show ( )

    def stop ( self ):
        self.controller.stop ( )
        while self.controller.isRunning ( ):
            pass
        QtCore.QCoreApplication.instance().quit ( )

    def force_repaint ( self ):
        # don't log here, or it will spam the log.

        QtGui.QApplication.processEvents ( )

    # auto updater
    ##############
        
    def ask_about_fetching_update ( self ):
        self.controller.log ( )

        dialog = fetch_update_confirm_dialog ( self.controller, self )
        result = dialog.exec_ ( )
        if result:
            dialog = fetch_update_execute_dialog ( self.controller, self )
            dialog.exec_ ( )
            self.controller.auto_updater.to_install = self.controller.auto_updater.to_update
        self.controller.auto_updater.to_update = None

    def ask_about_installing_update ( self ):
        self.controller.log ( )

        dialog = install_update_confirm_dialog ( self.controller, self )
        result = dialog.exec_ ( )
        if result:
            self.controller.auto_updater.install_update ( )
            self.controller.auto_updater.to_install = None

    def ask_about_reinitialize_update ( self ):
        self.controller.log ( )

        dialog = reinitialize_update_confirm_dialog ( self.controller, self )
        result = dialog.exec_ ( )
        if result:
            self.controller.auto_updater.reinitialize ( )
            self.controller.auto_updater.to_reinitialize = None
            self.stop ( )
        
def run ( ):
    app = QtGui.QApplication ( sys.argv )
    main_window_object = main_window ( )
    app.exec_ ( )
    
if __name__ == '__main__':
    run ( )    

