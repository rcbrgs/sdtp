# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import threading
import time

from sdtp.lkp_table import lkp_table

class LegFix(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_legfix_enable"]:
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
            "legfix": "instantly heals your broken leg."}
        self.controller.help.registered_commands["legfix"] = self.help
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)

    def check_for_commands(self, match_group):        
        matcher = re.compile(r"^/legfix[\s]*(.*)$")
        match = matcher.search(match_group[11])
        if not match:
            self.logger.debug("Regex did not match: {}".format(match_group[11]))
            return
        self.logger.debug("Input from {} matches regex.".format(match_group[10]))
        possible_player_name = match_group[10]
        argument = match.groups()[0].strip()
        self.logger.debug(
            "'{}' used challenge command with argument '{}'.".format (
            possible_player_name, argument))
        db_answer = self.controller.database.blocking_consult(
            lkp_table,
            [(lkp_table.name, "==", possible_player_name)])
        if len(db_answer) != 1:
            self.logger.error("DB entry for player name is not unique.")
            return
        player = db_answer[0]
        
        if argument == "":
            self.fix_broken_leg(player)
            return

        self.logger.debug("Checking for help usage.")
        if argument == "help":
            self.print_help_message(player)
            return

    def print_help_message(self, player):
        for key in self.help.keys():
            self.controller.telnet.write('pm {} "{} {}"'.format(
                player["steamid"], key, self.help[key]))
        
    # Mod specific
    ##############
    
    def fix_broken_leg(self, player):
        self.controller.telnet.write('debuffplayer {} buffLegBroken'.format(
            player["steamid"]))
        self.controller.telnet.write('debuffplayer {} buffLegSprained'.format(
            player["steamid"]))
