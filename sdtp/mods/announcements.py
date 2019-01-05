# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import threading
import time

from sdtp.lkp_table import lkp_table

class Announcements(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_announcements_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
            self.check_for_announcements()
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.commands = self.controller.config.values[
            "mod_announcements_commands"]
        for key in self.commands:
            self.controller.help.registered_commands[
                key] = self.commands[key]["text"]
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)
    
    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)

    def check_for_commands(self, match_groups):
        self.logger.debug("check_for_command({})".format(match_groups))
        command = ""
        for key in self.commands.keys():
            matcher = re.compile("^/{}(.*)$".format(key))
            matches = matcher.search(match_groups[11])
            if matches:
                self.logger.info("Command {} detected.".format(key))
                command = key
        if command == "":
            self.logger.debug("No match detected.")
            return
        
        matcher = re.compile("^/{}(.*)$".format(command))
        matches = matcher.search(match_groups[11])
        arguments = matches.groups()[0].strip().split(" ")
        self.logger.debug("command: '{}', arguments: {}".format(
            command, arguments))
        
        player = self.controller.worldstate.get_player_steamid(match_groups[7])

        self.print_announcements(player, command, arguments)

    # Mod specific
    ##############
    
    def print_announcements(self, player, command, arguments):
        self.controller.server.pm(
            player,
            self.controller.config.values[
                "mod_announcements_commands"][command]["text"])

    def check_for_announcements(self):
        now = time.time()
        for key in self.controller.config.values[
                "mod_announcements_commands"].keys():
            item = self.controller.config.values[
                "mod_announcements_commands"][key]
            if item["interval"] == -1:
                continue
            if now - item["latest"] > item["interval"]:
                item["latest"] = now
                if self.controller.telnet.ready:
                    self.controller.telnet.write('say "{}"'.format(item["text"]))
