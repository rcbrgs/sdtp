# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
#from PySide import QtCore, QtGui
import sys

class players_window ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

        self.controller.config.verify ( "show_players_window" )

    def init_GUI ( self ):

        self.player_selected_label = QtGui.QLabel ( "No player selected", self )
        self.player_selected_steamid = None
        self.player_selected_id = None

        player_kick_button = QtGui.QPushButton ( "Kick", self )
        player_kick_button.clicked.connect ( self.kick_player )
        player_ban1week_button = QtGui.QPushButton ( "Ban for 1 week", self )
        player_ban1week_button.clicked.connect ( self.ban1week_player )
        player_screamer_button = QtGui.QPushButton ( "Give a screamer", self )
        player_screamer_button.clicked.connect ( self.give_screamer_player )
        player_challenge_button = QtGui.QPushButton ( "Challenge player", self )
        player_challenge_button.clicked.connect ( self.challenge_player )
        abort_challenge = QtGui.QPushButton ( "Abort challenge", self )
        abort_challenge.clicked.connect ( self.controller.challenge.abort_challenge )
        
        self.players_list_widget = QtGui.QTableWidget ( self )
        self.players_list_widget.setColumnCount ( 18 )
        self.players_list_widget.setHorizontalHeaderLabels ( [ "id", "name", "y", "z", "x", "rot_y", "rot_z", "rot_x", "remote", "health", "deaths", "zombies", "players", "score", "level", "steamid", "ip", "ping" ] )
        self.controller.dispatcher.register_callback ( "lp output", self.update_players_list )
        self.controller.metronomer.lp_sent.connect ( self.cleanup_players_list )
        self.players_list_widget.cellClicked.connect ( self.change_selected_player )

        close_button = QtGui.QPushButton ( "Close", self )
        close_button.clicked.connect ( self.close )

        main_layout = QtGui.QVBoxLayout ( )
        player_actions_layout = QtGui.QHBoxLayout ( )
        player_actions_layout.addWidget ( self.player_selected_label )
        player_actions_layout.addWidget ( player_kick_button )
        player_actions_layout.addWidget ( player_ban1week_button )
        player_actions_layout.addWidget ( player_screamer_button )
        player_actions_layout.addWidget ( player_challenge_button )
        player_actions_layout.addWidget ( abort_challenge )
        main_layout.addLayout ( player_actions_layout )
        main_layout.addWidget ( self.players_list_widget )
        main_layout.addWidget ( close_button )
        self.setLayout ( main_layout )

        if self.title != None:
            self.setWindowTitle ( self.title )

    def challenge_player ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )
    
        if self.player_selected_steamid == None:
            self.controller.log ( "warning", "No player selected to challenge!" )
            return

        self.controller.challenge.run_challenge ( self.player_selected_steamid )
        
    def change_selected_player ( self, row, column ):
        try:
            self.player_selected_label.setText ( self.players_list_widget.item ( row, 1 ).text ( ) )
            self.player_selected_steamid = self.players_list_widget.item ( row, 15 ).text ( )
            self.player_selected_id = self.players_list_widget.item ( row, 0 ).text ( )
        except AttributeError as e:
            self.controller.log ( "debug", "Selected player update tried with invalid selection. Exception: {}".format ( e ) )

    def close ( self ):
        self.controller.config.falsify ( "show_players_window" )
        super ( self.__class__, self ).close ( )

    def give_screamer_player ( self ):
        self.controller.log ( "debug", "gui.players_window.give_screamer ( )" )
        if self.player_selected_label.text ( ) == "No player selected":
            self.controlller.log ( "debug", "No player selected, so no player got a screamer." )
            return
        self.controller.telnet.write ( "se {} 8".format ( self.player_selected_id ) )
        self.controller.log ( "info", "Player {} ({}) got a screamer.".format ( self.player_selected_label.text ( ), self.player_selected_steamid ) )        
        
    def kick_player ( self ):
        self.controller.log ( "debug", "gui.players_window.kick_player ( )" )
        if self.player_selected_label.text ( ) == "No player selected":
            self.controlller.log ( "debug", "No player selected, so no player was kicked." )
            return
        self.controller.telnet.write ( "kick {}".format ( self.player_selected_steamid ) )
        self.controller.log ( "info", "Player {} ({}) kicked.".format ( self.player_selected_label.text ( ), self.player_selected_steamid ) )

    def ban1week_player ( self ):
        self.controller.log ( "debug", "gui.players_window.ban1week_player ( )" )
        if self.player_selected_label.text ( ) == "No player selected":
            self.controlller.log ( "info", "No player selected, so no player was banned." )
            return
        self.controller.telnet.write ( 'ban add {} 1 week'.format ( self.player_selected_steamid ) )
        self.controller.log ( "info", "Player {} ({}) banned for 1 week.".format ( self.player_selected_label.text ( ), self.player_selected_steamid ) )
            
    def update_players_list ( self, match_groups ):
        row = self.players_list_widget.rowCount ( )
        self.players_list_widget.setRowCount ( row + 1 )
        for index in range ( len ( match_groups ) ):
            self.players_list_widget.setItem ( row, index, QtGui.QTableWidgetItem ( str ( match_groups [ index ] ) ) )
            #self.controller.log ( "debug", "{} {} {}".format ( row, index, str ( match_groups [ index ] ) ) )

    def cleanup_players_list ( self ):
        self.players_list_widget.setRowCount ( 0 )
