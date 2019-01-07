# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import random
import re
import threading
import time

from sdtp.lkp_table import lkp_table
from sdtp.table_cooldowns import TableCooldowns

class Relax(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_relax_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
            self.run_relaxation()
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.relaxing_players = {}
        self.help = {
            "relax": "Spawn one zombie at a time, so you can kill at leisure."}
        self.controller.help.registered_commands["relax"] = self.help
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)
    
    def tear_down(self):
        del self.controller.help.registered_commands["relax"]
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)

    def check_for_commands(self, match_groups):
        self.logger.debug("check_for_command({})".format(match_groups))
        command = ""
        for key in self.help.keys():
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

        if command == "relax":
            self.toggle_relax(player)
            return

    # Mod specific
    ##############
    
    def toggle_relax(self, player):
        if player["steamid"] not in self.relaxing_players.keys():
            cooldown = self.controller.database.blocking_consult(
                TableCooldowns,
                [(TableCooldowns.steamid, "==", player["steamid"])])
            now = time.time()
            if len(cooldown) == 1:
                difference = now - cooldown[0]["relax"]
                if difference < self.controller.config.values[
                        "mod_relax_cooldown_seconds"]:
                    self.controller.server.pm(
                        player,
                        "Your relaxation is in cooldown for another {}.".format(
                            self.controller.qol.pretty_print_seconds(
                                self.controller.config.values[
                                    "mod_relax_cooldown_seconds"] - difference)))
                    return
            self.controller.server.pm(player, "Your relaxation session begins.")
            self.relaxing_players[player["steamid"]] = player
            self.relaxing_players[player["steamid"]]["relax"] = False
            if len(cooldown) == 1:
                cooldown[0]["relax"] = now
                self.controller.database.blocking_update(
                    TableCooldowns, cooldown[0])
            else:
                self.controller.database.blocking_add(
                    TableCooldowns, [TableCooldowns(
                        steamid = player["steamid"],
                        relax = now)])
        else:
            del self.relaxing_players[player["steamid"]]
            self.controller.server.pm(player, "Your relaxation session ends.")

    def run_relaxation(self):
        try:
            for steamid in self.relaxing_players.keys():
                player = self.controller.worldstate.get_player_steamid(steamid)
                if player["deaths"] > self.relaxing_players[steamid]["deaths"]:
                    self.toggle_relax(player)
                    return
                if player["zombies"] > self.relaxing_players[steamid]["zombies"]:
                    self.relaxing_players[steamid]["relax"] = False
                    self.relaxing_players[steamid]["zombies"] = player["zombies"]
                if not self.relaxing_players[steamid]["relax"]:
                    self.relaxing_players[steamid]["relax"] = True
                    self.controller.server.se(
                        player, random.choice(
                            self.controller.server.normal_zombies))
                    if random.randint(0, 100) < self.controller.config.values[
                            "mod_relax_percentage_doubling_zombies"]:
                        self.controller.server.se(
                            player, random.choice(
                                self.controller.server.normal_zombies))
        except KeyError:
            self.log.debug(
                "Player toggled out while run_relaxation was in course.")
