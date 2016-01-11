# -*- coding: utf-8 -*-

from sdtp.lp_table import lp_table

from PyQt4 import QtCore, QtGui
#from PySide import QtCore
from random import randint
import re
import sys
import time

class challenge ( QtCore.QThread ):

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

        self.abort = False
        self.to_challenge = [ ]
        self.start ( )

    def run ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        self.cleanup_challenge ( )
        while ( self.keep_running ):
            time.sleep ( 0.1 )
            if len ( self.to_challenge ) != 0:
                self.do_challenge ( self.to_challenge.pop ( ) )

        self.controller.log ( "info", prefix + " return." )
            
    def stop ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        self.keep_running = False

    # Mod specific
    ##############

    def abort_challenge ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        self.abort = True
    
    def cleanup_challenge ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        self.to_challenge = [ ]
        self.abort = False
        self.challenger = None
        self.turns = None
        self.start = None
        self.end = None

    def get_player_deaths ( self, player_steamid ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        session = self.controller.database.get_session ( )
        query = session.query ( lp_table ).filter ( lp_table.steamid == str ( player_steamid ) )
        if query.count ( ) == 0:
            self.controller.log ( "error", prefix + " unable to find player." )
            self.controller.database.let_session ( session )
            self.cleanup_challenge ( )
            return
        player_lp = query.one ( )       
        player_deaths = player_lp.deaths
        self.controller.database.let_session ( session )
        self.controller.log ( "info", prefix + " player has {} deaths.".format ( player_deaths ) )
        return player_deaths

    def give_supplies ( self, player_steamid ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        self.controller.telnet.write ( 'give {} firstAidKit 1'.format ( player_steamid ) )
        self.controller.telnet.write ( 'give {} clubSpiked 1 {}'.format ( player_steamid, self.turns ) )
        self.controller.telnet.write ( 'give {} beer 1'.format ( player_steamid ) )
        
    def run_challenge ( self, player_steamid ):
        self.to_challenge.append ( player_steamid )

    def do_challenge ( self, player_steamid ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        session = self.controller.database.get_session ( )
        query = session.query ( lp_table ).filter ( lp_table.steamid == str ( player_steamid ) )
        if query.count ( ) == 0:
            self.controller.log ( "error", prefix + " unable to find player." )
            self.controller.database.let_session ( session )
            self.cleanup_challenge ( )
            return
        player_lp = query.one ( )       
        self.player_name = player_lp.name
        self.player_id = player_lp.player_id
        self.controller.database.let_session ( session )
        
        self.challenger = player_steamid
        self.turns = 0
        self.start = time.time ( )
        self.end = None

        player_deaths_at_start = self.get_player_deaths ( player_steamid )
        player_deaths = player_deaths_at_start
        
        self.controller.telnet.write ( 'say "{} is being challenged!"'.format ( self.player_name ) )
        while player_deaths == player_deaths_at_start and self.abort == False:
            self.turns += 1
            self.controller.telnet.write ( 'pm {} "Challenge level {}."'.format ( player_steamid, self.turns ) )
            self.controller.log ( "info", prefix + " challenge: turn {}.".format ( self.turns ) )
            if self.turns % 10 == 1:
                self.teleport_player ( )
                self.give_supplies ( player_steamid )
            self.spawn_at_player ( )
            time.sleep ( 10 + randint ( 0, 3 ) )
            player_deaths = self.get_player_deaths ( player_steamid )
        self.controller.telnet.write ( 'say "{} challenge ended at level {}!"'.format ( self.player_name, self.turns ) )
            
        self.end = time.time ( )
        duration = self.end - self.start

        self.controller.telnet.write ( "{} survived {} seconds!".format ( self.player_name, int ( self.end - self.start ) ) )

        self.cleanup_challenge ( )
                
    def spawn_at_player ( self ):
        for counter in range ( self.turns ):
            zombie = randint ( 1, 20 )
            self.controller.telnet.write ( "se {} {}".format ( self.player_id, zombie ) )
            time.sleep ( 0.1 + zombie * 0.01 )

    def teleport_player ( self ):
        longitude = randint ( 0, 5000 )
        latitude = randint ( 0, 5000 )
        self.controller.telnet.write ( "tele {} {} -1 {}".format ( self.player_id, longitude, latitude ) )
        time.sleep ( 1 )
