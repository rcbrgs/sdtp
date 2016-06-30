# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import re
from sdtp.lp_table import lp_table
from sdtp.mods.portals_tables import portals_table
import sys
import time

class portals ( QtCore.QThread ):

    # Boilerplate
    debug = QtCore.pyqtSignal ( str, str, str, str )

    def log ( self, level, message ):
        self.debug.emit ( message, level, self.__class__.__name__,
                          sys._getframe ( 1 ).f_code.co_name )

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.auto_horde_portal = None
        self.start ( )

    def run ( self ):
        self.controller.dispatcher.register_callback ( "chat message", self.check_for_command )
        self.controller.dispatcher.register_callback ( "AI scouts", self.advertise_horde )
        count = 0
        while ( self.keep_running ):
            count += 1
            if count % 600 == 0:
                self.log ( "debug", "Tick." )
            time.sleep ( 0.1 )
        self.controller.dispatcher.deregister_callback ( "chat message", self.check_for_command )
        self.controller.dispatcher.deregister_callback ( "AI scouts", self.advertise_horde )
        self.log ( "debug", "return." )

    def stop ( self ):
        self.keep_running = False

    # Mod specific
    ##############

    def check_for_command ( self, match_group ):
        if self.check_auto_horde_portal ( match_group ):
            return
        matcher = re.compile ( r"^(.*): /go (.*)$" )
        match = matcher.search ( match_group [ 7 ] )
        if not match:
            self.log ( "debug", "Regex did not match." )
            matcher = re.compile ( r"^(.*): /go$" )
            match = matcher.search ( match_group [ 7 ] )
            if match:
                self.list_portals ( match.groups ( ) [ 0 ] )
            return
        self.log ( "info", "input matches regex." )
        possible_player_name = match.groups ( ) [ 0 ]
        possible_portal_name = match.groups ( ) [ 1 ]
        self.log ( "info", "'{}' used portal command with argument '{}'.".format ( possible_player_name, possible_portal_name ) )
        self.log ( "info", "checking for public portals" )
        if self.check_for_public_portal_use ( possible_player_name, possible_portal_name ):
            return
        if not self.controller.config.values [ "enable_player_portals" ]:
            self.log ( "debug", "ignoring player command since mod is disabled." )
            return
        self.log ( "debug", "mod is enabled." )
        if possible_portal_name [ -1 ] == "-":
            self.delete_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            return
        if possible_portal_name [ -1 ] == "+":
            self.delete_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            self.add_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            return
        session = self.controller.database.get_session ( )
        query = session.query ( lp_table ).filter ( lp_table.name == possible_player_name )
        self.controller.database.let_session ( session )
        if query.count ( ) == 0:
            self.log ( "info", "unable to match '{}' to a player name in lp table.".format ( possible_player_name ) )
            return
        session = self.controller.database.get_session ( )
        query = session.query ( lp_table ).filter ( lp_table.name == possible_player_name )
        player_lp = query.one ( )
        player_steamid = player_lp.steamid
        query = session.query ( portals_table ).filter ( portals_table.steamid == player_steamid, portals_table.name == possible_portal_name )
        if query.count ( ) == 0:
            self.controller.database.let_session ( session )
            self.add_portal ( possible_player_name, possible_portal_name )
            return
        else:
            portal = query.one ( )
            if ( int ( float ( portal.longitude ) ) == int ( float ( player_lp.longitude ) ) and
                 int ( float ( portal.height ) ) == int ( float ( player_lp.height ) ) and
                 int ( float ( portal.latitude ) ) == int ( float ( player_lp.latitude ) ) ):
                self.controller.database.let_session ( session )
                self.delete_portal ( possible_player_name, possible_portal_name )
            else:
                self.log ( "info", "teleporting player to portal '{}'.".format ( portal.name ) )
                self.controller.telnet.write ( 'pm {} "Teleporting to {}."'.format ( player_lp.steamid, portal.name ) )
                teleport_string = 'tele {} {} {} {}'.format ( player_lp.steamid, int ( float ( portal.longitude ) ), int ( float ( portal.height ) ), int ( float ( portal.latitude ) ) )
                self.controller.telnet.write ( teleport_string )
                self.log ( "info", teleport_string )
        self.controller.database.let_session ( session )
        self.log ( "info", "return." )

    def check_for_public_portal_use ( self, player_name, possible_portal_name ):
        self.log ( "debug",
            "player_name = {}, possible_portal_name = {}".format (
                player_name, possible_portal_name ) )
        self.controller.database.consult (
            portals_table,
            [ ( portals_table.name, "==", possible_portal_name ),
              ( portals_table.steamid, "==", -1 ) ],
            self.consulted_portal )
        self.log ( "debug", "Consult request sent." )

    def consulted_portal ( self, answer ):
        self.log ( "debug", "answer = {}".format ( answer ) )
        if len ( answer ) != 1:
            return False
        portal = query [ 0 ]
        self.log ( "debug", "portal = {}".format ( portal ) )
        player_query = self.controller.database.consult (
            lp_table, [ ( lp_table.name, "==", player_name ) ] )
        player_lp = player_query [ 0 ]
        self.log ( "debug", "player_lp = {}".format ( player_lp ) )
        self.controller.telnet.write ( 'pm {} "Teleporting to {}."'.format ( player_lp.steamid, portal.name ) )
        teleport_string = 'tele {} {} {} {}'.format ( player_lp.steamid, int ( float ( portal.longitude ) ), int ( float ( portal.height ) ), int ( float ( portal.latitude ) ) )
        self.controller.telnet.write ( teleport_string )
        self.log ( "info", teleport_string )
        return True

    def OLDcheck_for_public_portal_use ( self, player_name, possible_portal_name ):
        self.log ( "debug",
                   "player_name = {}, possible_portal_name = {}".format (
                       player_name, possible_portal_name ) )
        session = self.controller.database.get_session ( )
        self.log ( "debug", "Got a session." )
        query = session.query ( portals_table ).filter (
            portals_table.name == possible_portal_name, portals_table.steamid == str ( -1 ) )
        self.log ( "debug", "query.count ( ) = {}".format ( query.count ( ) ) )
        if query.count ( ) != 1:
            self.controller.database.let_session ( session )
            return False
        portal = query.one ( )
        self.log ( "debug", "portal = {}".format ( portal ) )
        query = session.query ( lp_table ).filter ( lp_table.name == player_name )
        player_lp = query.one ( )
        self.log ( "debug", "player_lp = {}".format ( player_lp ) )
        self.controller.telnet.write ( 'pm {} "Teleporting to {}."'.format ( player_lp.steamid, portal.name ) )
        teleport_string = 'tele {} {} {} {}'.format ( player_lp.steamid, int ( float ( portal.longitude ) ), int ( float ( portal.height ) ), int ( float ( portal.latitude ) ) )
        self.controller.database.let_session ( session )
        self.controller.telnet.write ( teleport_string )
        self.log ( "info", teleport_string )
        return True

    def create_portal_from_coordinates ( self, y_quadrant, y_value, x_quadrant, x_value, z_value, name, public = True ):
        if not public:
            return
        position_x = int ( float ( x_value ) )
        if str ( x_quadrant ) == "W":
            position_x *= -1
        position_y = int ( float ( y_value ) )
        if str ( y_quadrant ) == "S":
            position_y *= -1
        session = self.controller.database.get_session ( )
        session.add ( portals_table ( steamid = -1, name = name, longitude = position_x, latitude = position_y, height = int ( float ( z_value ) ) ) )
        self.controller.database.let_session ( session )

    def add_portal ( self, possible_player_name, possible_portal_name ):
        session = self.controller.database.get_session ( )
        player_query = session.query ( lp_table ).filter ( lp_table.name == possible_player_name )
        if player_query.count ( ) == 0:
            self.log ( "info", "unable to match '{}' to a player name in lp table.".format ( possible_player_name ) )
            self.controller.database.let_session ( session )
            return
        player_lp = player_query.one ( )
        session.add_all ( [
            portals_table (
                steamid = player_lp.steamid,
                name = possible_portal_name,
                longitude = player_lp.longitude,
                height = player_lp.height,
                latitude = player_lp.latitude )
        ] )
        self.controller.telnet.write ( 'pm {} "Portal {} created."'.format ( player_lp.steamid, possible_portal_name ) )
        self.controller.database.let_session ( session )

    def delete_portal ( self, possible_player_name, possible_portal_name ):
        session = self.controller.database.get_session ( )
        player_query = session.query ( lp_table ).filter ( lp_table.name == possible_player_name )
        if player_query.count ( ) == 0:
            self.log ( "info", "unable to match '{}' to a player name in lp table.".format ( possible_player_name ) )
            self.controller.database.let_session ( session )
            return
        player_lp = player_query.one ( )
        query = session.query ( portals_table ).filter ( portals_table.steamid == player_lp.steamid, portals_table.name == possible_portal_name )
        if query.count ( ) == 0:
            self.log ( "error", "unable to find portal to delete." )
        else:
            deletable = query.one ( )
            self.log ( "info", "deleting portal '{}'.".format ( possible_portal_name ) )
            self.controller.telnet.write ( 'pm {} "Deleted portal {}."'.format ( player_lp.steamid, deletable.name ) )
            session.delete ( deletable )
        self.controller.database.let_session ( session )

    def list_portals ( self, player_name ):
        session = self.controller.database.get_session ( )
        query = session.query ( lp_table ).filter ( lp_table.name == player_name )
        if query.count ( ) == 0:
            self.log ( "info", "player does not exist in lp table." )
            return
        player_lp = query.one ( )
        portal_query = session.query ( portals_table ).filter ( portals_table.steamid == player_lp.steamid )
        if portal_query.count ( ) == 0:
            self.log ( "info", "player has no portals." )
            self.controller.telnet.write ( 'pm {} "You do not have portals set."'.format ( player_lp.steamid ) )
        else:
            self.log ( "info", "listing player portals." )
            for portal in portal_query:
                try:
                    portal_string += ", " + portal.name
                except:
                    portal_string = portal.name
            portals_string = 'pm {} "Your portals are: {}"'.format ( player_lp.steamid, portal_string )
            self.log ( "info", "" + portals_string )
            self.controller.telnet.write ( portals_string )
        self.controller.database.let_session ( session )

    def add_public_portal ( self, name, pos_x, pos_y, pos_z ):
        pass

    # Horde portal
    ##############

    def advertise_horde ( self, match_group ):
        self.log ( "info", "Horde scouts at {}, {}.".format ( match_group [ 7 ], match_group [ 9 ] ) )
        self.auto_horde_portal = ( int ( float ( match_group [ 7 ] ) ), -1, int ( float ( match_group [ 9 ] ) ) )
        #self.auto_horde_portal = ( match_group [ 9 ], -1, match_group [ 7 ] )
        if self.controller.config.values [ "enable_auto_horde_portals" ]:
            self.controller.telnet.write ( 'say "Scout zombie detected! Chat /go auto_horde to fight!"' )

    def check_auto_horde_portal ( self, match_group ):
        matcher = re.compile ( r"^(.*): /go auto_horde$" )
        match = matcher.search ( match_group [ 7 ] )
        if not match:
            return False
        self.log ( "info", "input matches regex." )
        possible_player_name = str ( match.groups ( ) [ 0 ] ) [ 1 : -1 ]
        self.log ( "debug", "Calling join_auto_horde with possible_player_name '{}'.".format ( possible_player_name ) )
        return self.join_auto_horde ( possible_player_name )

    def join_auto_horde ( self, possible_player_name ):
        if not self.controller.config.values [ "enable_auto_horde_portals" ]:
            return False
        self.log ( "debug", "Automatic horde portals are enabled." )
        if self.auto_horde_portal == None:
            self.controller.telnet.write ( 'say "No horde in sight!"' )
            return True
        self.controller.database.consult ( lp_table, [ ( lp_table.name, "==", possible_player_name ) ], self.consulted_auto_horde )
        return False

    def consulted_auto_horde ( self, answer ):
        if len ( answer ) != 1:
            self.log ( "info", "player does not exist in lp table." )
            return False
        player_lp = answer [ 0 ]
        player_steamid = player_lp [ "steamid" ]
        self.controller.telnet.write ( "tele {} {} {} {}".format ( player_steamid, self.auto_horde_portal [ 0 ], self.auto_horde_portal [ 1 ], self.auto_horde_portal [ 2 ] ) )

class portals_widget ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.title = title
        self.init_GUI ( )
        self.show ( )

    # GUI
    def init_GUI ( self ):
        enable = QtGui.QCheckBox ( "Enable players to set portals.", self )
        enable.setChecked ( self.controller.config.values [ "enable_player_portals" ] )
        enable.stateChanged.connect ( lambda: self.controller.config.toggle ( "enable_player_portals" ) )
        enable_auto_horde = QtGui.QCheckBox ( "Enable automatic screamer zombie portals.", self )
        enable_auto_horde.setChecked ( self.controller.config.values [ "enable_auto_horde_portals" ] )
        enable_auto_horde.stateChanged.connect ( lambda: self.controller.config.toggle ( "enable_auto_horde_portals" ) )
        add_portal_button = QtGui.QPushButton ( "Add a public portal" )
        add_portal_button.clicked.connect ( self.add_portal )
        remove_portal_button = QtGui.QPushButton ( "Remove a public portal" )
        remove_portal_button.clicked.connect ( self.remove_portal )
        main_layout = QtGui.QVBoxLayout ( )
        main_layout.addWidget ( enable )
        main_layout.addWidget ( enable_auto_horde )
        main_layout.addWidget ( add_portal_button )
        main_layout.addWidget ( remove_portal_button )
        self.setLayout ( main_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        if self.title != None:
            self.setWindowTitle ( self.title )
        self.log ( "debug", "return." )

    def close ( self ):
        self.controller.config.falsify ( "show_{}".format ( self.__class__.__name__ ) )
        super ( self.__class__, self ).close ( )

    def closeEvent ( self, event ):
        self.parent.mdi_area.removeSubWindow ( self )

    # Model
    def add_portal ( self ):
        dialog = create_portal_dialog ( self.controller )
        dialog.exec_ ( )
        if dialog.result ( ) == QtGui.QDialog.Rejected:
            return
        self.controller.portals.create_portal_from_coordinates ( y_quadrant = dialog.position_y_combobox.currentText ( ), y_value = dialog.position_y_lineedit.text ( ), x_quadrant = dialog.position_x_combobox.currentText ( ), x_value = dialog.position_x_lineedit.text ( ), z_value = dialog.position_z_lineedit.text ( ), name = dialog.name_lineedit.text ( ) )

    def remove_portal ( self ):
        dialog = remove_portal_dialog ( self.controller )
        dialog.exec_ ( )
        if dialog.result ( ) == QtGui.QDialog.Rejected:
            return
        if dialog.name_combobox.currentText ( ) == "":
            return
        session = self.controller.database.get_session ( )
        query = session.query ( portals_table ).filter ( portals_table.name == dialog.name_combobox.currentText ( ), portals_table.steamid == str ( -1 ) )
        session.delete ( query.one ( ) )
        self.controller.database.let_session ( session )

class create_portal_dialog ( QtGui.QDialog ):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        position_label = QtGui.QLabel ( "Position: " )
        self.position_y_lineedit = QtGui.QLineEdit ( )
        self.position_y_combobox = QtGui.QComboBox ( )
        self.position_y_combobox.addItem ( "N" )
        self.position_y_combobox.addItem ( "S" )
        self.position_x_lineedit = QtGui.QLineEdit ( )
        self.position_x_combobox = QtGui.QComboBox ( )
        self.position_x_combobox.addItem ( "E" )
        self.position_x_combobox.addItem ( "W" )
        self.position_z_lineedit = QtGui.QLineEdit ( )
        height_label = QtGui.QLabel ( "height" )
        position_layout = QtGui.QHBoxLayout ( )
        position_layout.addWidget ( position_label )
        position_layout.addWidget ( self.position_y_lineedit )
        position_layout.addWidget ( self.position_y_combobox )
        position_layout.addWidget ( self.position_x_lineedit )
        position_layout.addWidget ( self.position_x_combobox )
        position_layout.addWidget ( self.position_z_lineedit )
        position_layout.addWidget ( height_label )
        name_label = QtGui.QLabel ( "Portal name:" )
        self.name_lineedit = QtGui.QLineEdit ( )
        name_layout = QtGui.QHBoxLayout ( )
        name_layout.addWidget ( name_label )
        name_layout.addWidget ( self.name_lineedit )
        accept_button = QtGui.QPushButton ( "Ok" )
        accept_button.clicked.connect ( self.accept )
        cancel_button = QtGui.QPushButton ( "Cancel" )
        cancel_button.clicked.connect ( self.reject )
        buttons_layout = QtGui.QHBoxLayout ( )
        buttons_layout.addWidget ( accept_button )
        buttons_layout.addWidget ( cancel_button )
        main_layout = QtGui.QVBoxLayout ( )
        main_layout.addLayout ( position_layout )
        main_layout.addLayout ( name_layout )
        main_layout.addLayout ( buttons_layout )
        self.setLayout ( main_layout )

class remove_portal_dialog ( QtGui.QDialog ):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        name_label = QtGui.QLabel ( "Portal name:" )
        self.name_combobox = QtGui.QComboBox ( )
        session = self.controller.database.get_session ( )
        query = session.query ( portals_table ).filter ( portals_table.steamid == str ( -1 ) )
        public_portals_list = query.all ( )
        for entry in public_portals_list:
            self.name_combobox.addItem ( entry.name )
        self.controller.database.let_session ( session )
        name_layout = QtGui.QHBoxLayout ( )
        name_layout.addWidget ( name_label )
        name_layout.addWidget ( self.name_combobox )
        accept_button = QtGui.QPushButton ( "Ok" )
        accept_button.clicked.connect ( self.accept )
        cancel_button = QtGui.QPushButton ( "Cancel" )
        cancel_button.clicked.connect ( self.reject )
        buttons_layout = QtGui.QHBoxLayout ( )
        buttons_layout.addWidget ( accept_button )
        buttons_layout.addWidget ( cancel_button )
        main_layout = QtGui.QVBoxLayout ( )
        main_layout.addLayout ( name_layout )
        main_layout.addLayout ( buttons_layout )
        self.setLayout ( main_layout )
