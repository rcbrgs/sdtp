from .config import Config
from .database import Database
from .dispatcher import Dispatcher
from .metronomer import Metronomer
from .parser import Parser
from .telnet import TelnetClient
from .world_state import WorldState

#from .mods.challenge import challenge
#from .mods.forbidden_countries import forbidden_countries
#from .mods.ping_limiter import ping_limiter
#from .mods.portals import portals
#from .mods.server_reboots import server_reboots

import json
import logging
import os
import sdtp
import sys
import threading
import time

class Controller(threading.Thread):

    def __init__ ( self ):
        super(self.__class__, self).__init__ ( )
        self.keep_running = False
        self.telnet_ongoing = False
        self.logger = logging.getLogger(__name__)
        
        self.config = None
        self.auto_updater = None
        self.dispatcher = None
        self.metronomer = None
        self.parser = None
        self.telnet = None
        self.database = None
        self.world_state = None
        self.challenge = None
        self.forbidden_countries = None
        self.ping_limiter = None
        self.portals = None
        self.server_reboots = None

    def run ( self ):
        self.config = Config ( self )
        self.config.load_configuration_file ( )
        self.logger.debug("controller.run: dispatcher")
        self.dispatcher = Dispatcher ( self )
        self.dispatcher.start ( )
        self.logger.debug("controller.run: metronomer")
        self.metronomer = Metronomer ( self )
        self.metronomer.start ( )
        self.logger.debug("controller.run: parser")
        self.parser = Parser ( self )
        self.parser.start ( )
        self.logger.debug("controller.run: telnet")
        self.telnet = TelnetClient(self)
        self.telnet.start()
        self.database = Database ( self )
        #self.database.start()
        self.world_state = WorldState ( self )
        self.components = [ self.dispatcher,
                            self.metronomer,
                            self.parser,
                            self.telnet,
                            self.database,
                            self.world_state ]
        #self.challenge = challenge ( self )
        #self.forbidden_countries = forbidden_countries ( self )
        #self.forbidden_countries.start ( )
        #self.ping_limiter = ping_limiter ( self )
        #self.portals = portals ( self )
        #self.portals.debug.connect ( self.debug )
        #self.server_reboots = server_reboots ( self )
        self.mods = [ #self.challenge,
                      #self.forbidden_countries,
                      #self.ping_limiter,
                      #self.portals,
                      #self.server_reboots ]
            ]
        if ( self.config.values [ 'auto_connect' ] ):
            self.logger.debug("Automatically initiating connection.")
            self.telnet.open_connection ( )
        self.telnet.write ( 'say "{}"'.format ( self.config.values [ "sdtp_greetings" ] ) )
        # poll for input / events
        self.keep_running = True
        while ( self.keep_running ):
            time.sleep ( 1 )
        self.config.save_configuration_file ( )
        if ( self.telnet_ongoing ):
            self.telnet.close_connection ( )
        self.logger.debug("controller.run exiting." )

    def stop ( self ):
        self.logger.info("Shutdown of sdtp initiated.")
        self.telnet.write ( 'say "{}"'.format ( self.config.values [ "sdtp_goodbye" ] ) )
        for mod in self.mods:
            self.logger.debug("controller.stop: calling mod.stop in {}.".format ( mod.__class__ ) )
            mod.stop ( )
        for mod in self.mods:
            while ( mod.isRunning ( ) ):
                self.logger.debug("controller.stop: Waiting on mod {} to stop.".format(mod.__class__))
                time.sleep ( 0.1 )
        self.world_state.stop ( )
        self.metronomer.stop ( )
        self.database.stop ( )
        self.telnet.stop ( )
        self.parser.stop ( )
        for component in self.components:
            if component == self.dispatcher:
                continue
            count = 0
            while ( component.is_alive ( ) ):
                if count == 0:
                    self.logger.debug("controller.stop: Waiting on component {} to stop.".format(component.__class__))
                time.sleep ( 0.1 )
                count += 1
                if count == 100:
                    self.logger.warning("Calling terminate on component.")
                    component.terminate()
        self.dispatcher.stop ( )
        while ( self.dispatcher.is_alive ( ) ):
            self.logger.debug("controller.stop: Waiting on dispatcher to stop.")
            time.sleep ( 0.1 )
        if self.keep_running:
            self.keep_running = False

    def connect_telnet(self):
        self.logger.debug("Telnet connection requested from user.")
        if ( self.telnet_ongoing ):
            self.logger.debug("Ignoring request for telnet connection since one is already ongoing.")
            return
        self.telnet.open_connection ( )

    def disconnect_telnet(self):
        self.logger.debug("Telnet disconnection requested from user.")
        if ( not self.telnet_ongoing ):
            return
        self.telnet_ongoing = False
        self.telnet.close_connection ( )
