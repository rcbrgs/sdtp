# -*- coding: utf-8 -*-

from sdtp.lp_table import lp_table
from sdtp.mods.portals_tables import portals_table

from PyQt4 import QtCore
#from PySide import QtCore
import re
import sys
import time

class portals ( QtCore.QThread ):

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

        self.auto_horde_portal = None
        
        self.start ( )

    def run ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        self.controller.dispatcher.register_callback ( "chat message", self.check_for_command )
        self.controller.dispatcher.register_callback ( "AI scouts", self.advertise_horde )
        while ( self.keep_running ):
            time.sleep ( 0.1 )
        self.controller.dispatcher.deregister_callback ( "chat message", self.check_for_command )
        self.controller.dispatcher.deregister_callback ( "AI scouts", self.advertise_horde )

        self.controller.log ( "debug", prefix + " return." )
            
    def stop ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        self.keep_running = False

    # Mod specific
    ##############

    def check_for_command ( self, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( {} )".format ( match_group ) )

        if not self.controller.config.values [ "enable_player_portals" ]:
            self.controller.log ( "debug", prefix + " ignoring player command since mod is disabled." )
            self.check_auto_horde_portal ( match_group )
            return
        self.controller.log ( "debug", prefix + " mod is enabled." )

        matcher = re.compile ( r"^(.*): /go (.*)$" )
        match = matcher.search ( match_group [ 7 ] )
        if not match:
            self.controller.log ( "debug", prefix + " regex did not match." )
            matcher = re.compile ( r"^(.*): /go$" )
            match = matcher.search ( match_group [ 7 ] )
            if match:
                self.list_portals ( match.groups ( ) [ 0 ] )
            return
        self.controller.log ( "info", prefix + " input matches regex." )
        possible_player_name = match.groups ( ) [ 0 ]
        possible_portal_name = match.groups ( ) [ 1 ]
        self.controller.log ( "info", prefix + " '{}' used portal command with argument '{}'.".format ( possible_player_name, possible_portal_name ) )

        if possible_portal_name == "auto_horde":
            self.join_auto_horde ( possible_player_name )
            return
        
        if possible_portal_name [ -1 ] == "-":
            self.delete_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            return
        if possible_portal_name [ -1 ] == "+":
            self.delete_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            self.add_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            return
        
        session = self.controller.database.get_session ( )
        query = session.query ( lp_table ).filter ( lp_table.name == possible_player_name )
        if query.count ( ) == 0:
            self.controller.log ( "info", prefix + " unable to match '{}' to a player name in lp table.".format ( possible_player_name ) )
            self.controller.database.let_session ( session )
            return
        
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
                self.controller.log ( "info", prefix + " teleporting player to portal '{}'.".format ( portal.name ) )
                self.controller.telnet.write ( 'pm {} "Teleporting to {}."'.format ( player_lp.steamid, portal.name ) )
                teleport_string = 'tele {} {} {} {}'.format ( player_lp.steamid, int ( float ( portal.longitude ) ), int ( float ( portal.height ) ), int ( float ( portal.latitude ) ) )
                self.controller.telnet.write ( teleport_string )
                self.controller.log ( "info", prefix + " " + teleport_string )                
            
        self.controller.database.let_session ( session )
        
        self.controller.log ( "info", prefix + " return." )
    
    def add_portal ( self, possible_player_name, possible_portal_name ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        session = self.controller.database.get_session ( )
        
        player_query = session.query ( lp_table ).filter ( lp_table.name == possible_player_name )
        if player_query.count ( ) == 0:
            self.controller.log ( "info", prefix + " unable to match '{}' to a player name in lp table.".format ( possible_player_name ) )
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
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        session = self.controller.database.get_session ( )
        
        player_query = session.query ( lp_table ).filter ( lp_table.name == possible_player_name )
        if player_query.count ( ) == 0:
            self.controller.log ( "info", prefix + " unable to match '{}' to a player name in lp table.".format ( possible_player_name ) )
            self.controller.database.let_session ( session )
            return
        player_lp = player_query.one ( )

        query = session.query ( portals_table ).filter ( portals_table.steamid == player_lp.steamid, portals_table.name == possible_portal_name )
        if query.count ( ) == 0:
            self.controller.log ( "error", prefix + " unable to find portal to delete." )
        else:
            deletable = query.one ( )
            self.controller.log ( "info", prefix + " deleting portal '{}'.".format ( possible_portal_name ) )
            self.controller.telnet.write ( 'pm {} "Deleted portal {}."'.format ( player_lp.steamid, deletable.name ) )
            session.delete ( deletable )

        self.controller.database.let_session ( session )
        
    def list_portals ( self, player_name ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( {} )".format ( player_name ) )

        session = self.controller.database.get_session ( )
        query = session.query ( lp_table ).filter ( lp_table.name == player_name )
        if query.count ( ) == 0:
            self.controller.log ( "info", prefix + " player does not exist in lp table." )
            return
        player_lp = query.one ( )
        portal_query = session.query ( portals_table ).filter ( portals_table.steamid == player_lp.steamid )
        if portal_query.count ( ) == 0:
            self.controller.log ( "info", prefix + " player has no portals." )
            self.controller.telnet.write ( 'pm {} "You do not have portals set."'.format ( player_lp.steamid ) )
        else:
            self.controller.log ( "info", prefix + " listing player portals." )
            for portal in portal_query:
                try:
                    portal_string += ", " + portal.name
                except:
                    portal_string = portal.name

            portals_string = 'pm {} "Your portals are: {}"'.format ( player_lp.steamid, portal_string )
            self.controller.log ( "info", prefix + " " + portals_string )
            self.controller.telnet.write ( portals_string )
                        
        self.controller.database.let_session ( session )

    # Horde portal
    ##############

    def advertise_horde ( self, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( {} )".format ( match_group ) )

        self.controller.log ( "info", prefix + " Horde scouts at {}, {}.".format ( match_group [ 7 ], match_group [ 9 ] ) )
        self.auto_horde_portal = ( int ( float ( match_group [ 7 ] ) ), -1, int ( float ( match_group [ 9 ] ) ) )
        #self.auto_horde_portal = ( match_group [ 9 ], -1, match_group [ 7 ] )
        if self.controller.config.values [ "enable_auto_horde_portals" ]:
            self.controller.telnet.write ( 'say "Scout zombie detected! Chat /go auto_horde to fight!"' )

    def check_auto_horde_portal ( self, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( {} )".format ( match_group ) )

        matcher = re.compile ( r"^(.*): /go auto_horde$" )
        match = matcher.search ( match_group [ 7 ] )
        if not match:
            return
        self.controller.log ( "info", prefix + " input matches regex." )
        possible_player_name = match.groups ( ) [ 0 ]
        self.join_auto_horde ( possible_player_name )
            
    def join_auto_horde ( self, possible_player_name ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( {} )".format ( possible_player_name ) )

        if not self.controller.config.values [ "enable_auto_horde_portals" ]:
            return
        if self.auto_horde_portal == None:
            self.controller.telnet.write ( 'say "No horde in sight!"' )
            return

        session = self.controller.database.get_session ( )
        query = session.query ( lp_table ).filter ( lp_table.name == possible_player_name )
        if query.count ( ) == 0:
            self.controller.log ( "info", prefix + " player does not exist in lp table." )
            return
        player_lp = query.one ( )
        player_steamid = player_lp.steamid
        self.controller.database.let_session ( session )
        
        self.controller.telnet.write ( "tele {} {} {} {}".format ( player_steamid, self.auto_horde_portal [ 0 ], self.auto_horde_portal [ 1 ], self.auto_horde_portal [ 2 ] ) )
        
