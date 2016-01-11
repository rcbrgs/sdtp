# -*- coding: utf-8 -*-

import os
import pygeoip
from PyQt4 import QtCore
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
