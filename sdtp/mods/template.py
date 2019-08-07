# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import threading
import time

class Mod(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_{}_enable".format(__name__)]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.help = {
            "mod": "The mod." }
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)

    def check_for_commands(self, match_groups):
        self.logger.debug("check_for_command({})".format(match_groups))
        command = ""
        for key in self.help.keys():
            matcher = re.compile("^/{}(.*)$".format(key))
            matches = matcher.search(match_groups[11])
            if matches:
                self.logger.debug("Command {} detected.".format(key))
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

        if command == "mod":
            self.mod_function(player, arguments)
            return
        
    # Mod specific
    ##############

    def mod_function(self, player, arguments):
        pass
