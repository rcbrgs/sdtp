from .config import config
#from .logger import logger

from .auto_updater import auto_updater
from .database import database
from .dispatcher import dispatcher
from .metronomer import metronomer
from .parser import parser
from .telnet import telnet
from .world_state import world_state

from .mods.challenge import challenge
from .mods.forbidden_countries import forbidden_countries
from .mods.ping_limiter import ping_limiter
from .mods.portals import portals
from .mods.server_reboots import server_reboots

import json
import os
from PyQt4 import QtCore
#from PySide import QtCore
import sdtp
import sys
import threading
import time

class controller ( QtCore.QThread ):

    log_gui = QtCore.pyqtSignal ( str, str )

    def __init__ ( self, gui_thread ):
        super ( self.__class__, self ).__init__ ( )
        self.keep_running = False
        self.telnet_ongoing = False
        self.gui_thread = gui_thread
        self.logger = sdtp.logger ( self )
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
        self.config = config ( self )
        self.config.load_configuration_file ( )
        self.logger.set_initial_level ( )
        self.log ( "debug", "controller.run: dispatcher" )
        self.dispatcher = dispatcher ( self )
        self.dispatcher.debug.connect ( self.debug )
        self.dispatcher.start ( )
        self.log ( "debug", "controller.run: metronomer" )
        self.metronomer = metronomer ( self )
        self.metronomer.start ( )
        self.log ( "debug", "controller.run: parser" )
        self.parser = parser ( self )
        self.parser.start ( )
        self.log ( "debug", "controller.run: telnet" )
        self.telnet = telnet ( self )
        self.telnet.start ( )
        self.database = database ( self )
        self.database.debug.connect ( self.debug )
        self.world_state = world_state ( self )
        self.world_state.debug.connect ( self.debug )
        self.components = [ self.dispatcher,
                            self.metronomer,
                            self.parser,
                            self.telnet,
                            self.database,
                            self.world_state ]
        self.challenge = challenge ( self )
        self.forbidden_countries = forbidden_countries ( self )
        self.forbidden_countries.start ( )
        self.ping_limiter = ping_limiter ( self )
        self.portals = portals ( self )
        self.portals.debug.connect ( self.debug )
        self.server_reboots = server_reboots ( self )
        self.mods = [ self.challenge,
                      self.forbidden_countries,
                      self.ping_limiter,
                      self.portals,
                      self.server_reboots ]
        if ( self.config.values [ 'auto_connect' ] ):
            self.log ( "debug", "Automatically initiating connection." )
            self.telnet.open_connection ( )
        self.telnet.write ( 'say "{}"'.format ( self.config.values [ "sdtp_greetings" ] ) )
        self.auto_updater = auto_updater ( self )
        self.auto_updater.update_available.connect ( self.gui_thread.ask_about_fetching_update )
        self.auto_updater.install_available.connect ( self.gui_thread.ask_about_installing_update )
        self.auto_updater.reinitialization_available.connect ( self.gui_thread.ask_about_reinitialize_update )
        # poll for input / events
        self.keep_running = True
        while ( self.keep_running ):
            time.sleep ( 1 )
        self.config.save_configuration_file ( )
        if ( self.telnet_ongoing ):
            self.telnet.close_connection ( )
        self.log ( "debug", "controller.run exiting." )

    def stop ( self ):
        self.log ( "info", "Shutdown of sdtp initiated." )
        self.telnet.write ( 'say "{}"'.format ( self.config.values [ "sdtp_goodbye" ] ) )
        for mod in self.mods:
            self.log ( "debug", "controller.stop: calling mod.stop in {}.".format ( mod.__class__ ) )
            mod.stop ( )
        for mod in self.mods:
            while ( mod.isRunning ( ) ):
                self.log ( "debug", "controller.stop: Waiting on mod {} to stop.".format ( mod.__class__ ) )
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
            while ( component.isRunning ( ) ):
                if count == 0:
                    self.log ( "debug", "controller.stop: Waiting on component {} to stop.".format ( component.__class__ ) )
                time.sleep ( 0.1 )
                count += 1
                if count == 100:
                    self.log ( "warning", "calling terminate on component." )
                    component.terminate ( )
        self.dispatcher.stop ( )
        while ( self.dispatcher.isRunning ( ) ):
            self.log ( "debug", "controller.stop: Waiting on dispatcher to stop." )
            time.sleep ( 0.1 )
        if self.keep_running:
            self.keep_running = False
            self.gui_thread.stop ( )

    def connect_telnet ( self, telnet_widget ):
        self.log ( "debug", "Telnet connection requested from user." )
        if ( self.telnet_ongoing ):
            self.log ( "debug", "Ignoring request for telnet connection since one is already ongoing." )
            return
        self.telnet.open_connection ( )

    def disconnect_telnet ( self, telnet_widget ):
        self.log ( "debug", "Telnet disconnection requested from user." )
        if ( not self.telnet_ongoing ):
            return
        self.telnet_ongoing = False
        telnet_widget.connect_button.setChecked ( False )
        self.telnet.close_connection ( )

    def ready_for_gui ( self ):
        return self.keep_running

    def log ( self, log_level = "debug", log_message = None ):
        if self.logger != None:
            self.logger.log ( log_level, log_message )
        else:
            print ( log_message )

    def debug ( self, message, level = "debug", caller_class = "", caller_function = "" ):
        if self.logger == None:
            print ( "[DUMMY] {}.{} {} {}".format (
                caller_class, caller_function, level.upper ( ), message ) )
            return
        self.logger.debug ( message, level, caller_class, caller_function )
