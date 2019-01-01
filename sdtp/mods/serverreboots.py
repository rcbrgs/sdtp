# -*- coding: utf-8 -*-

from sdtp.lp_table import lp_table

import logging
import sys
import threading
import time

class ServerReboots(threading.Thread):

    def __init__(self,controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)
        
        self.uptime_triggered = False
        self.latest_uptime_announcement = -1

    def run ( self ):
        self.controller.dispatcher.register_callback (
            "executing command", self.announce_server_uptime )
        while ( self.keep_running ):
            time.sleep ( 1 )
            if self.uptime_triggered:
                self.try_to_reboot ( )
        self.controller.dispatcher.deregister_callback (
            "executing command", self.announce_server_uptime )

    def stop ( self ):
        self.keep_running = False

    # Mod specific
    ##############

    def announce_server_uptime ( self, match_group ):
        uptime_string = match_group [ 6 ]
        self.logger.debug("uptime_string = {}".format ( uptime_string ) )
        uptime = int ( float ( uptime_string ) / 3600 )
        self.logger.debug("uptime = {} hours".format ( uptime ) )
        if uptime > self.latest_uptime_announcement:
            if self.latest_uptime_announcement != -1:
                self.logger.info("Server online for {} hours.".format(uptime))
                self.controller.telnet.write (
                    'say "Server online for {} hours.".'.format ( uptime ) )
            self.latest_uptime_announcement = uptime
        self.check_for_reboot ( uptime, match_group )

    def check_for_reboot ( self, uptime, match_group ):
        if self.controller.config.values [ "mod_serverreboots_enable" ]:
            if uptime > int ( self.controller.config.values [ "mod_serverreboots_interval" ] ):
                self.controller.log (
                    "info", "reboot triggered by uptime." )
                self.try_to_reboot ( )
                self.uptime_triggered = True
                return

    def try_to_reboot ( self ):
        if self.controller.config.values [ "mod_serverreboots_empty_condition" ]:
            if not self.controller.worldstate.server_empty:
                return
        if time.time ( ) < self.controller.config.values [ "latest_reboot" ] + 3601:
            return
        self.controller.log ( "info", "Shutting down server for automatic reboot." )
        countdown = 600
        while countdown > 0:
            if countdown % 60 == 0 or ( countdown < 60 and countdown % 5 == 0 ):
                self.controller.telnet.write ( 'say "Shutdown in {} seconds."'.format ( countdown ) )
            time.sleep ( 1 )
            countdown -= 1
        self.controller.telnet.write ( "kickall" ) 
        self.controller.telnet.write ( "saveworld" )
        self.controller.telnet.write ( "shutdown" )
        self.controller.config.values [ "latest_reboot" ] = time.time ( )
        self.uptime_triggered = False
