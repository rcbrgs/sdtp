# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import threading
import time

import sdtp
from sdtp.lkp_table import lkp_table

class Help(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.registered_commands = {}
        
    def run(self):
        self.logger.info("Start.")
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop ( self ):
        self.keep_running = False
        self.logger.info("Stop.")

    def setup(self):
        # register help items in help component.
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_command)
        
    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_command)
    
    # Component specific
    ####################

    def check_for_command(self, match_groups):
        self.logger.debug("check_for_command({})".format(match_groups))
        matcher = re.compile("^/help[\s]*(.*)$")
        matches = matcher.search(match_groups[11])
        if not matches:
            self.logger.debug("No command detected.")
            return
        argument = matches.groups()[0].strip()
        self.logger.debug("Argument detected: '{}'".format(argument))
        db_answer = self.controller.database.blocking_consult(
            lkp_table,
            [(lkp_table.steamid, "==", match_groups[7])])
        if len(db_answer) != 1:
            self.logger.info("DB entry non unique: {}".format(db_answer))
            return
        player = db_answer[0]
        if argument == "":
            self.list_commands(player)
            return
        if argument in self.registered_commands:
            for key in self.registered_commands[argument]:
                self.controller.server.pm(
                    player, "/{} {}".format(key,
                        self.registered_commands[argument][key]))

    def list_commands(self, player):
        for command in sorted(self.registered_commands.keys()):
            try:
                response += ", {}".format(command)
            except:
                response = "{}".format(command)
        self.controller.server.pm(
            player, "help <command>: Give help on <command>.")
        self.controller.server.pm(
            player, "Commands are: {}.".format(response))
