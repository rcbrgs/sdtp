# -*- coding: utf-8 -*-

from sdtp.lp_table import lp_table

from PyQt4 import QtCore
#from PySide import QtCore
from sqlalchemy import Integer
import sys
import time

class world_state ( QtCore.QThread ):

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

        self.online_players_count = 100000
        self.latest_nonzero_players = time.time ( )
        self.server_empty = False
        self.start ( )

    # Thread control
    ################        
        
    def run ( self ):
        self.controller.log ( "debug", "world_state.run ( )" )

        self.register_callbacks ( )
        while ( self.keep_running ):
            time.sleep ( 0.1 )
        self.deregister_callbacks ( )

        self.controller.log ( "debug", "world_state.run returning" )

    def stop ( self ):
        self.controller.log ( "debug", "{}.stop ( )".format ( self.__class__ ) )
        self.keep_running = False

    # Component-specific
    ####################

    def register_callbacks ( self ):
        self.controller.dispatcher.register_callback ( "lp output", self.update_lp_table )
        self.controller.dispatcher.register_callback ( "le/lp output footer", self.update_online_players_count )

    def deregister_callbacks ( self ):
        self.controller.dispatcher.deregister_callback ( "lp output", self.update_lp_table )
    
    def update_lp_table ( self, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( {} )".format ( match_group ) )

        this_steamid = int ( match_group [ 15 ] ),
        session = self.controller.database.get_session ( )
        self.controller.log ( "debug", prefix + " got session." )
        try:
            query = session.query ( lp_table ).filter ( lp_table.steamid == match_group [ 15 ] )
            self.controller.log ( "debug", prefix + " queried." )
        except Exception as e:
            self.controller.log ( "debug", prefix + ": exception during query: {}.".format ( e ) )
            self.controller.database.let_session ( session )
            self.controller.log ( "debug", prefix + " let session." )
            return

        if query.count ( ) == 0:
            self.controller.log ( "debug", prefix + ": New entry." )
            session.add_all ( [
                lp_table (
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
                    ping = match_group [ 17 ] )
            ] )                
        else:
            self.controller.log ( "debug", prefix + ": update entry." )
            entry = query.one ( )
            self.controller.log ( "debug", prefix + ": obtained entry." )
            entry.name = match_group [ 1 ]
            entry.longitude = match_group [ 2 ]
            entry.height = match_group [ 3 ]
            entry.latitude = match_group [ 4 ]
            entry.rotation_height = match_group [ 5 ]
            entry.rotation_longitude = match_group [ 6 ]
            entry.rotation_latitude = match_group [ 7 ]
            entry.remote = match_group [ 8 ]
            entry.health = match_group [ 9 ]
            entry.deaths = match_group [ 10 ]
            entry.zombies = match_group [ 11 ]
            entry.players = match_group [ 12 ]
            entry.score = match_group [ 13 ]
            entry.level = match_group [ 14 ]
            entry.ip = match_group [ 16 ]
            entry.ping = match_group [ 17 ]
            self.controller.log ( "debug", prefix + ": setup update." )
            session.add ( entry )
            self.controller.log ( "debug", prefix + ": added entry." )
            #session.commit ( )
            #self.controller.log ( "info", prefix + ": commit session." )
        self.controller.log ( "debug", prefix + " let session." )
        self.controller.database.let_session ( session )
        
        self.controller.log ( "debug", prefix + " returning." )

    def update_online_players_count ( self, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( {} )".format ( match_group ) )

        count = int ( match_group [ 0 ] )
        self.online_players_count = count
        if count == 0:
            if time.time ( ) - self.latest_nonzero_players > 300:
                self.server_empty = True
                return
        else:
            self.latest_nonzero_players = time.time ( )


