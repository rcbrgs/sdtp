# -*- coding: utf-8 -*-

from sdtp.lp_table import lp_table

import logging
from sqlalchemy import Integer
import sys
import threading
import time

class WorldState(threading.Thread):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)
        
        self.online_players_count = 100000
        self.latest_nonzero_players = time.time ( )
        self.server_empty = False
        self.start ( )

    # Thread control
    def run ( self ):
        self.logger.debug("world_state.run ( )" )
        self.register_callbacks ( )
        while ( self.keep_running ):
            time.sleep ( 0.1 )
        self.deregister_callbacks ( )
        self.logger.debug("world_state.run returning" )

    def stop ( self ):
        self.logger.debug("{}.stop ( )".format ( self.__class__ ) )
        self.keep_running = False

    # Component-specific
    ####################

    def register_callbacks ( self ):
        self.controller.dispatcher.register_callback ( "lp output", self.update_lp_table )
        self.controller.dispatcher.register_callback ( "le/lp output footer", self.update_online_players_count )

    def deregister_callbacks ( self ):
        self.controller.dispatcher.deregister_callback ( "lp output", self.update_lp_table )

    def update_lp_table ( self, match_group ):
        self.logger.debug("({})".format (match_group))
        this_steamid = int ( match_group [ 15 ] ),
        self.controller.database.consult (
            lp_table, [ ( lp_table.steamid, "==", match_group [ 15 ] ) ],
            self.update_lp_table_2,
            { "match_group" : match_group } )

    def update_lp_table_2 ( self, results, match_group = None ):
        self.logger.debug("results = {}.".format ( results ) )
        if len ( results ) == 0:
            self.logger.debug("New entry." )
            self.controller.database.add_all (
                lp_table,
                [ lp_table (
                    player_id = match_group [ 0 ],
                    name = match_group [ 1 ],
                    longitude = match_group [ 2 ],
                    height = match_group [ 3 ],
                    latitude = match_group [ 4 ],
                    rotation_height = match_group [ 5 ],
                    rotation_longitude = match_group [ 6 ],
                    rotation_latitude = match_group [ 7 ],
                    remote = match_group [ 8 ],
                    health = match_group [ 9 ],
                    deaths = match_group [ 10 ],
                    zombies = match_group [ 11 ],
                    players = match_group [ 12 ],
                    score = match_group [ 13 ],
                    level = match_group [ 14 ],
                    steamid = match_group [ 15 ],
                    ip = match_group [ 16 ],
                    ping = match_group [ 17 ] ) ],
                print )
        else:
            self.logger.debug("update entry." )
            entry = results [ 0 ]
            self.logger.debug("obtained entry." )
            entry [ "name" ] = match_group [ 1 ]
            entry [ "longitude" ] = match_group [ 2 ]
            entry [ "height" ] = match_group [ 3 ]
            entry [ "latitude" ] = match_group [ 4 ]
            entry [ "rotation_height" ] = match_group [ 5 ]
            entry [ "rotation_longitude" ] = match_group [ 6 ]
            entry [ "rotation_latitude" ] = match_group [ 7 ]
            entry [ "remote" ] = match_group [ 8 ]
            entry [ "health" ] = match_group [ 9 ]
            entry [ "deaths" ] = match_group [ 10 ]
            entry [ "zombies" ] = match_group [ 11 ]
            entry [ "players" ] = match_group [ 12 ]
            entry [ "score" ] = match_group [ 13 ]
            entry [ "level" ] = match_group [ 14 ]
            entry [ "ip" ] = match_group [ 16 ]
            entry [ "ping" ] = match_group [ 17 ]
            table_entry = lp_table ( )
            lp_entry = table_entry.create_from_dictionary ( entry )
            self.controller.database.add_all (
                lp_table, [ lp_entry ],
                print )
            self.logger.debug("added entry." )
        self.logger.debug("returning." )

    def update_online_players_count ( self, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.logger.debug(prefix + " ( {} )".format ( match_group ) )

        count = int ( match_group [ 0 ] )
        self.online_players_count = count
        if count == 0:
            if time.time ( ) - self.latest_nonzero_players > 300:
                self.server_empty = True
                return
        else:
            self.server_empty = False
            self.latest_nonzero_players = time.time ( )
