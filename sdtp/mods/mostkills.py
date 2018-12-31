# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import random
import re
import threading
import time

from sdtp.lkp_table import lkp_table

class MostKills(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_mostkills_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.yesterday_players = {}
        self.controller.dispatcher.register_callback(
            "new day", self.reset_daily_counts)
        self.controller.dispatcher.register_callback(
            "new hour", self.announce_counts)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "new day", self.reset_daily_counts)
        self.controller.dispatcher.register_callback(
            "new hour", self.announce_counts)
        
    # Mod specific
    ##############

    def reset_daily_counts(self, match_groups):
        self.logger.debug(match_groups)
        max_player, max_count = self.count_most_kills()
        if max_count > 0:
            self.controller.telnet.write('say "{} killed the most zombies today."'.format(max_player["name"]))
            self.controller.telnet.write('give {} ammo762mmBulletFMJSteel 50'.format(max_player["player_id"]))

        self.yesterday_players = {}
        players = self.controller.worldstate.online_players
        for player in players:
            self.yesterday_players[player["steamid"]] = player

    def count_most_kills(self):
        players = self.controller.worldstate.online_players
        max_player = None
        max_count = 0
        for player in players:
            if player["steamid"] in self.yesterday_players:
                count = player["zombies"] - \
                        self.yesterday_players[player["steamid"]]["zombies"]
                self.logger.debug("{} killed {} zombies.".format(
                    player["name"], count))
                if count > max_count:
                    max_count = count
                    max_player = player
            else:
                self.yesterday_players[player["steamid"]] = player
        return (max_player, max_count)

    def announce_counts(self, match_groups):
        max_player, max_count = self.count_most_kills()
        if int(match_groups[1]) != [4, 8, 12, 16, 20]:
            return
        if max_count > 0:
            self.controller.telnet.write('say "{} is the leader with {} zombies killed."'.format(max_player["name"], max_count))
