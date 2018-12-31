from .config import Config
from .database import Database
from .dispatcher import Dispatcher
from .friendships import Friendships
from .help import Help
from .metronomer import Metronomer
from .parser import Parser
from .telnet import Telnet
from .worldstate import WorldState

#from .mods.challenge import challenge
from .mods.chatlogger import ChatLogger
from .mods.chattranslator import ChatTranslator
from .mods.claimalarm import ClaimAlarm
#from .mods.forbidden_countries import forbidden_countries
#from .mods.ping_limiter import ping_limiter
from .mods.mostkills import MostKills
from .mods.portals import Portals
from .mods.qol import Qol
#from .mods.server_reboots import server_reboots

import importlib
import json
import logging
import os
import sys
import threading
import time

import sdtp

class Controller(threading.Thread):

    def __init__ ( self ):
        super(self.__class__, self).__init__ ( )
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.lock = False

        # Components
        self.config = None
        self.dispatcher = None
        self.friendships = None
        self.help = None
        self.metronomer = None
        self.parser = None
        self.telnet = None
        self.database = None
        self.worldstate = None

        # Mods
        self.chatlogger = None
        self.chattranslator = None
        #self.challenge = None
        self.claimalarm = None
        #self.forbidden_countries = None
        self.mostkills = None
        #self.ping_limiter = None
        self.portals = None
        self.qol = None
        #self.server_reboots = None

    def run ( self ):
        self.setup()
        # poll for input / events
        while(self.keep_running):
            time.sleep(1)
            self.components_check()
            self.mods_check()
        self.tear_down()
        self.logger.debug("run() exiting.")

    def setup(self):
        # Components
        self.config = Config ( self )
        self.config.load_configuration_file ( )
        self.logger.debug("controller.run: dispatcher")
        self.dispatcher = Dispatcher ( self )
        self.dispatcher.start ( )
        self.logger.debug("controller.run: metronomer")
        self.metronomer = Metronomer ( self )
        self.metronomer.start ( )
        self.logger.debug("controller.run: telnet")
        self.telnet = Telnet(self)
        self.telnet.start()
        self.logger.debug("controller.run: parser")
        self.parser = Parser ( self )
        self.parser.start ( )
        self.database = Database ( self )
        self.database.start()
        self.help = Help(self)
        self.help.start()
        self.friendships = Friendships(self)
        self.friendships.start()
        self.worldstate = WorldState ( self )

        # Mods
        self.components = [ self.dispatcher,
                            self.friendships,
                            self.help,
                            self.metronomer,
                            self.parser,
                            self.telnet,
                            self.database,
                            self.worldstate ]
        #self.challenge = challenge ( self )
        self.chatlogger = ChatLogger(self)
        self.chattranslator = ChatTranslator(self)
        self.claimalarm = ClaimAlarm(self)
        #self.forbidden_countries = forbidden_countries ( self )
        #self.forbidden_countries.start ( )
        self.mostkills = MostKills(self)
        self.mostkills.start()
        #self.ping_limiter = ping_limiter ( self )
        self.portals = Portals(self)
        self.qol = Qol(self)
        self.qol.start()
        #self.server_reboots = server_reboots ( self )
        self.mods = [
            #self.challenge,
            self.chatlogger,
            self.chattranslator,
            self.claimalarm,
            #self.forbidden_countries,
            self.mostkills,
            #self.ping_limiter,
            self.portals,
            self.qol,
            #self.server_reboots ]
        ]
        
        self.telnet.write(
            'say "{}"'.format(self.config.values["sdtp_greetings"]))        
        
    def stop ( self ):
        self.logger.info("sdtp shutdown initiated.")
        self.keep_running = False

    def tear_down(self):
        self.telnet.write(
            'say "{}"'.format(self.config.values["sdtp_goodbye"]))
        for mod in self.mods:
            self.logger.debug(
                "controller.stop: calling mod.stop in {}.".format(mod.__class__))
            mod.stop()
        for mod in self.mods:
            while (mod.is_alive()):
                self.logger.debug(
                    "controller.stop: Waiting on mod {} to stop.".format(
                        mod.__class__))
                time.sleep(0.1)
        self.config.save_configuration_file()
        self.friendships.stop()
        self.help.stop()
        self.worldstate.stop()
        self.metronomer.stop()
        self.database.stop()
        self.parser.stop()
        self.telnet.stop()
        for component in self.components:
            if component == self.dispatcher:
                continue
            count = 0
            while(component.is_alive()):
                if count == 0:
                    self.logger.debug("Waiting on component {} to stop.".format(
                        component.__class__))
                time.sleep ( 0.1 )
                count += 1
                if count == 100:
                    self.logger.warning("Ignoring component {} stop.".format(
                        component.__class__))
                    break
        self.dispatcher.stop ( )
        while ( self.dispatcher.is_alive ( ) ):
            self.logger.debug("controller.stop: Waiting on dispatcher to stop.")
            time.sleep ( 0.1 )       

    def components_check(self):
        for component in self.components:
            if not component.is_alive():
                self.logger.error("Component not alive: {}.".format(
                    component.__class__.__name__))
                self.components.remove(component)
                self.logger.info("Component re-start: {}.".format(
                    component.__class__.__name__))
                class_name = component.__class__.__name__
                module_name = "sdtp." + class_name.lower()
                module = importlib.import_module(module_name)
                class_reference = getattr(module, class_name)
                setattr(self, class_name.lower(), class_reference(self))
                object = getattr(self, class_name.lower())
                object.start()
                self.components.append(object)

    def mods_check(self):
        for mod in self.mods:
            mod_enable_string = "mod_{}_enable".format(
                mod.__class__.__name__.lower())
            if not self.config.values[mod_enable_string]:
                self.logger.debug("Mod is disabled.")
                continue
            if not mod.is_alive():
                self.logger.error("Mod is not alive: {}.".format(
                    mod.__class__.__name__))
                self.mods.remove(mod)
                self.logger.info("Mod re-start: {}.".format(
                    mod.__class__.__name__))
                class_name = mod.__class__.__name__
                module_name = "sdtp.mods." + class_name.lower()
                module = importlib.import_module(module_name)
                class_reference = getattr(module, class_name)
                setattr(self, class_name.lower(), class_reference(self))
                object = getattr(self, class_name.lower())
                object.start()
                self.mods.append(object)

    def get_lock(self, locker_object):
        count = 0
        while self.lock:
            time.sleep(0.1)
            count += 1
            if count > 100:
                self.logger.warning(
                    ".get_lock({}) grabbing lock forcefully.".format(
                        locker_object.__class__.__name__))
                break
        self.logger.debug(
            ".get_lock({})".format(locker_object.__class__.__name__))
        self.lock = True

    def let_lock(self, locker_object):
        self.logger.debug(
            ".let_lock({})".format(locker_object.__class__.__name__))       
        self.lock = False
