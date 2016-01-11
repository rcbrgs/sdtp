# -*- coding: utf-8 -*-
__version__ = "0.0.0"
__changelog__ = {
    "0.0.0" : "Initial version."
    }

from sdtp.gui.children_window import children_window

import sys
from PyQt4 import QtGui, QtCore
#from PySide import QtGui, QtCore

class country_ban_window ( QtGui.QDialog ):
#class country_ban_window ( QtGui.QWidget ):

    def __init__ ( self, parent, controller ):
        #super ( self.__class__, self ).__init__ ( parent )
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
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

        ok_button = QtGui.QPushButton ( "Ok", self )
        ok_button.clicked.connect ( self.close )
        layout.addWidget ( ok_button )

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
