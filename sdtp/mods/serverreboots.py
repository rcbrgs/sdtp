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

        self.countdown = 0
        self.in_countdown = False
        self.uptime_triggered = False
        self.latest_uptime_announcement = -1

    def run(self):
        self.controller.dispatcher.register_callback (
            "mem output", self.check_server_uptime )
        self.controller.dispatcher.register_callback (
            "chat message", self.check_server_uptime_2 )
        while ( self.keep_running ):
            time.sleep ( 1 )
            if self.uptime_triggered:
                if self.in_countdown:
                    self.do_reboot()
                else:
                    self.try_to_reboot()
        self.controller.dispatcher.deregister_callback (
            "mem output", self.check_server_uptime )
        self.controller.dispatcher.deregister_callback (
            "chat message", self.check_server_uptime_2 )

    def stop ( self ):
        self.keep_running = False

    # Mod specific
    ##############

    def check_server_uptime ( self, match_group ):
        self.logger.debug(match_group)
        uptime_string = match_group [ 0 ]
        self.logger.debug("uptime_string = {}".format ( uptime_string ) )
        uptime = int ( float ( uptime_string ) / 60 )
        self.announce_uptime(uptime)

    def check_server_uptime_2 ( self, match_group ):
        self.logger.debug(match_group)
        uptime_string = match_group[6]
        self.logger.debug("uptime_string = {}".format(uptime_string))
        uptime = int(float(uptime_string) / 3600)
        self.announce_uptime(uptime)

    def announce_uptime(self, uptime):
        self.logger.debug("uptime = {} hours".format ( uptime ) )
        if uptime > self.latest_uptime_announcement:
            if self.latest_uptime_announcement != -1:
                self.logger.debug("Server online for {} hours.".format(uptime))
                self.controller.telnet.write (
                    'say "Server online for {} hours.".'.format ( uptime ) )
            self.latest_uptime_announcement = uptime
        self.check_for_reboot(uptime)

    def check_for_reboot (self, uptime):
        if self.controller.config.values [ "mod_serverreboots_enable" ]:
            if uptime >= int (self.controller.config.values[
                    "mod_serverreboots_interval"]):
                self.logger.debug("Reboot triggered by uptime.")
                self.uptime_triggered = True

    def try_to_reboot ( self ):
        self.logger.debug("try_to_reboot()")
        if self.controller.config.values [ "mod_serverreboots_empty_condition" ]:
            if not self.controller.worldstate.server_empty:
                self.logger.debug("Server not empty preventing shutdown.")
                return
        if time.time ( ) < self.controller.config.values [ "latest_reboot" ] + 3601:
            self.logger.info("Latest reboot was less than an hour ago.")
            return

        if not self.in_countdown:
            self.logger.info("Shutting down server for automatic reboot.")
            self.in_countdown = True
            self.countdown = time.time()

    def do_reboot(self):            
        now = time.time()
        time_difference = int(now - self.countdown)
        if time_difference >= 300:
            self.controller.telnet.write ( "kickall" ) 
            self.controller.telnet.write ( "saveworld" )
            self.controller.telnet.write ( "shutdown" )
            self.controller.config.values [ "latest_reboot" ] = time.time ( )
            self.uptime_triggered = False
            self.latest_uptime_announcement = -1
            self.in_countdown = False
            self.countdown = 0
            return

        time_to_shutdown = 300 - time_difference
        if time_to_shutdown % 60 == 0 or \
           (time_to_shutdown < 30 and time_to_shutdown % 5 == 0):
            self.controller.telnet.write('say "Shutdown in {}."'.format(
                self.controller.qol.pretty_print_seconds(time_to_shutdown)))
