# -*- coding: utf-8 -*-

import os
import pygeoip
from PyQt4 import QtGui, QtCore
import re
import sys
import threading
import time

class forbidden_countries ( QtCore.QThread ):

    log = QtCore.pyqtSignal ( object, object )
    
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

    def run ( self ):
        self.log.emit ( "info", "forbidden_countries waiting for controller ready." )
        while ( not self.controller.ready_for_gui ( ) ):
            time.sleep ( 0.1 )
        self.log.emit ( "info", "forbidden_countries acks controller ready." )

        location = os.path.dirname ( sys.executable )
        separator = self.controller.config.values [ "separator" ]
        self.geoip = pygeoip.GeoIP ( location + separator + "GeoIP.dat", pygeoip.MEMORY_CACHE )
        self.register_callbacks ( )
        while ( self.keep_running ):
            time.sleep ( 1 )

    def stop ( self ):
        self.deregister_callbacks ( )
        self.keep_running = False

    def register_callbacks ( self ):
        self.controller.dispatcher.register_callback ( "lp output", self.check_IP_is_blocked )
        
    def deregister_callbacks ( self ):
        self.controller.dispatcher.deregister_callback ( "lp output", self.check_IP_is_blocked )

    def check_IP_is_blocked ( self, match ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        if not self.controller.config.values [ "enable_per_country_bans" ]:
            self.controller.log ( "debug", "mods.forbidden_countries.check_IP_is_blocked: disabled." )
            return
        name = match [ 1 ]
        steamid = match [ 15 ]
        ip = match [ 16 ]
        country = self.geoip.country_code_by_addr ( ip )

        matcher_home192 = re.compile ( r"^192\.168\." )
        matcher_home10 = re.compile ( r"^10\." )
        matcher_home127001 = re.compile ( r"^127\.0\.0\.1" )

        for matcher in [ matcher_home192, matcher_home10, matcher_home127001 ]:
            match = matcher.search ( ip )
            if match:
                self.log.emit ( "info", "Player '{}', steamid {}, has IP {} from allowed region {}.".format ( name, steamid, ip, country ) )
                return

        if country == '':
            self.controller.log ( "debug", "Unable to detect country of '{}'.".format ( name ) )
            return

        self.controller.log ( "debug", "{} connected from {}".format ( name, country ) )
        
        if country in self.controller.config.values [ 'forbidden_countries' ]:
            self.log.emit ( "info", "Player '{}', steamid {}, has IP {} from forbidden region {}.".format ( name, steamid, ip, country ) )
            self.controller.telnet.write ( 'ban add {} 1 week "griefer IP block"'.format ( steamid ) )
            self.controller.telnet.write ( 'say "[SDTP] Player {} banned for 1 week, region: {}."'.format ( name, country ) )
        else:
            self.log.emit ( "info", "Player '{}', steamid {}, has IP {} from allowed region {}.".format ( name, steamid, ip, country ) )


class forbidden_countries_widget ( QtGui.QDialog ):
    
    def __init__ ( self, parent, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.parent = parent
        
        self.controller.log ( "debug", "country_ban_window.__init__ ( {}, {} )".format ( parent, controller ) )
        self.enabled = False

        layout = QtGui.QVBoxLayout ( self )
        self.setLayout ( layout )

        self.enabled_checkbox = QtGui.QCheckBox ( "Ban users who connect from the forbidden countries.", self )
        self.enabled_checkbox.setChecked ( self.controller.config.values [ 'enable_per_country_bans' ] )
        self.enabled_checkbox.stateChanged.connect ( self.__update_enabled )
        layout.addWidget ( self.enabled_checkbox )

        self.forbidden_countries_listwidget = QtGui.QListWidget ( self )
        self.controller.log ( "debug", str ( self.controller.config ) )
        self.controller.log ( "debug", str ( self.controller.config.values [ 'forbidden_countries' ] ) )
        self.__update_country_list ( )
        layout.addWidget ( self.forbidden_countries_listwidget )

        add_country_button = QtGui.QPushButton ( "Add country", self )
        layout.addWidget ( add_country_button )
        add_country_button.clicked.connect ( self.__add_country_dialog )

        del_country_button = QtGui.QPushButton ( "Del country", self )
        layout.addWidget ( del_country_button )
        del_country_button.clicked.connect ( self.__del_country_dialog )

    def __update_enabled ( self, qt_checked_value ):
        config = self.controller.config
        if ( qt_checked_value == 2 ):
            config.values [ 'enable_per_country_bans' ] = True
            self.controller.forbidden_countries.register_callbacks ( )
            self.controller.log ( "info", "Enabling per-country bans." )
        else:
            config.values [ 'enable_per_country_bans' ] = False
            self.controller.forbidden_countries.deregister_callbacks ( )
            self.controller.log ( "info", "Disabling per-country bans." )

    def __add_country_dialog ( self ):
        config = self.controller.config
        raw, ok = QtGui.QInputDialog.getText( self, 'Blacklist country', 'Enter 2-letter country code:' )
        new_banee = str ( raw ).upper ( )
        if ( ok == False ):
            return
        if ( len ( new_banee ) != 2 ):
            return
        if ( new_banee in config.values [ 'forbidden_countries' ] ):
            return
        
        config.values [ 'forbidden_countries' ].append ( new_banee )
        self.forbidden_countries_listwidget.addItem ( new_banee )
        self.controller.log ( "info", "Adding country code {} to forbidden countries.".format ( new_banee ) )

    def __del_country_dialog ( self ):
        config = self.controller.config
        raw, ok = QtGui.QInputDialog.getText( self, 'Whitelist country', 'Enter 2-letter country code:' )
        new_unbanee = str ( raw ).upper ( )
        if ( not ok ):
            return
        if ( len ( new_unbanee ) != 2 ):
            return
        if ( not new_unbanee in config.values [ 'forbidden_countries' ] ):
            return
        
        config.values [ 'forbidden_countries' ].remove ( new_unbanee )
        self.__update_country_list ( )
        self.controller.log ( "info", "Removing country code {} to forbidden countries.".format ( new_unbanee ) )

    def __update_country_list ( self ):
        config = self.controller.config
        self.forbidden_countries_listwidget.clear ( )
        self.forbidden_countries_listwidget.addItems ( config.values [ 'forbidden_countries' ] )

    def close ( self ):
        self.controller.config.falsify ( "show_{}".format ( self.__class__.__name__ ) )
        super ( self.__class__, self ).close ( )

    def closeEvent ( self, event ):
        self.controller.log ( )
        
        self.parent.mdi_area.removeSubWindow ( self )

