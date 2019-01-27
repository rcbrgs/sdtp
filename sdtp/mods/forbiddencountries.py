# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import pygeoip
import re
import threading
import time

from sdtp.lkp_table import lkp_table

class ForbiddenCountries(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_forbiddencountries_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.geoip = pygeoip.GeoIP(
            "/usr/share/GeoIP/GeoIP.dat", pygeoip.MEMORY_CACHE)
        self.controller.dispatcher.register_callback(
            "lp output", self.check_IP_is_blocked)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback (
            "lp output", self.check_IP_is_blocked)
        
    # Mod specific
    ##############

    def check_IP_is_blocked ( self, match ):
        name = match [ 1 ]
        steamid = int(match [ 15 ])
        ip = match [ 16 ]

        if steamid in self.controller.config.values["mod_forbiddencountries_whitelist"]:
            return
        
        country = self.geoip.country_code_by_addr ( ip )

        matcher_home192 = re.compile ( r"^192\.168\." )
        matcher_home10 = re.compile ( r"^10\." )
        matcher_home127001 = re.compile ( r"^127\.0\.0\.1" )

        for matcher in [ matcher_home192, matcher_home10, matcher_home127001 ]:
            match = matcher.search ( ip )
            if match:
                self.logger.debug("Player '{}', steamid {}, has IP {} from intranet.".format ( name, steamid, ip ) )
                return

        if country == '':
            self.logger.debug("Unable to detect country of '{}'.".format(name))
            return

        self.logger.debug("{} connected from {}".format ( name, country ) )
        
        if country in self.controller.config.values [ 'mod_forbiddencountries_banned_countries' ]:
            self.logger.info("Player '{}', steamid {}, has IP {} from forbidden region {}.".format ( name, steamid, ip, country ) )
            self.controller.telnet.write ( 'ban add {} 1 week "griefer IP block"'.format ( steamid ) )
            self.controller.telnet.write ( 'say "[SDTP] Player {} banned for 1 week, region: {}."'.format ( name, country ) )
        else:
            self.logger.debug("Player '{}', steamid {}, has IP {} from allowed region {}.".format ( name, steamid, ip, country ) )
