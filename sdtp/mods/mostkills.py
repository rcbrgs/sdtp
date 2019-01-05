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
        self.horde_kill_counts = {}
        self.yesterday_players = {}
        self.controller.dispatcher.register_callback(
            "new day", self.reset_daily_counts)
        self.controller.dispatcher.register_callback(
            "new hour", self.announce_counts)
        self.controller.dispatcher.register_callback(
            "new hour", self.horde_night_counts)
        self.controller.dispatcher.register_callback(
            "sunrise", self.horde_night_finishes)
        self.controller.dispatcher.register_callback(
            "sunset", self.horde_night_starts)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "new day", self.reset_daily_counts)
        self.controller.dispatcher.deregister_callback(
            "new hour", self.announce_counts)
        self.controller.dispatcher.deregister_callback(
            "new hour", self.horde_night_counts)
        self.controller.dispatcher.deregister_callback(
            "sunrise", self.horde_night_finishes)
        self.controller.dispatcher.register_callback(
            "sunset", self.horde_night_starts)
        
    # Mod specific
    ##############

    def reset_daily_counts(self, match_groups):
        self.logger.debug(match_groups)
        max_player, max_count = self.count_most_kills(self.yesterday_players)
        if max_count > 0:
            self.controller.telnet.write(
                'say "[FF0000]{}[FFFFFF] killed the most zombies today: {}."'.format(
                    max_player["name"], max_count))
            self.controller.telnet.write(
                'give {} ammo762mmBulletFMJSteel 50'.format(
                    max_player["player_id"]))
            self.logger.info("Gave 50 ammo762mmBulletFMJSteel to {}.".format(
                max_player["name"]))

        self.logger.debug("Resetting most kills counts.")
        self.yesterday_players = {}
        players = self.controller.worldstate.get_online_players()
        for player in players:
            self.yesterday_players[player["steamid"]] = player
            self.logger.debug("Adding {} to most kills count.".format(
                player["name"]))

    def count_most_kills(self, collection):
        self.logger.debug("count_most_kills()")
        players = self.controller.worldstate.get_online_players()
        self.logger.debug("players = {}".format(players))
        max_player = None
        max_count = 0
        for player in players:
            if player["steamid"] in collection.keys():
                count = player["zombies"] - \
                        collection[player["steamid"]]["zombies"]
                self.logger.debug("{} killed {} zombies.".format(
                    player["name"], count))
                if count > max_count:
                    max_count = count
                    max_player = player
            else:
                collection[player["steamid"]] = player
                self.logger.debug("Adding {} to most kills count.".format(
                    player["name"]))
        self.logger.debug("max_player = {}".format(max_player))
        return (max_player, max_count)

    def announce_counts(self, match_groups):
        self.logger.debug(match_groups)
        max_player, max_count = self.count_most_kills(self.yesterday_players)
        if int(match_groups[1]) not in [4, 8, 12, 16, 20]:
            return
        self.logger.debug("Announcing most kills counts.")
        if max_count > 0:
            self.controller.telnet.write('say "[990000]{}[FFFFFF] has the most ({}) zombies killed so far."'.format(max_player["name"], max_count))
        else:
            self.logger.info("No player has killed zombies yet today.")

    def horde_night_counts(self, match_groups):
        if int(match_groups[0]) % 7 != 1:
            return
        
        hour = int(match_groups[1])
        if hour > self.controller.config.values["night_time_begins_at"] or \
           hour < self.controller.config.values["night_time_ends_at"]:
            for player in self.controller.worldstate.get_online_players():
                if player["steamid"] not in self.horde_kill_counts.keys():
                    self.horde_kill_counts[player["steamid"]] = player
            return

    def horde_night_finishes(self, match_groups):
        max_player, max_count = self.count_most_kills(self.horde_kill_counts)
        if max_count > 0:
            self.controller.server.say(
                "{} killed the most zombies during the blood moon: {}.".format(
                    max_player["name"], max_count))

    def horde_night_starts(self, match_groups):
        self.horde_kill_counts = {}
        for player in self.controller.worldstate.get_online_players():
            if player["steamid"] not in self.horde_kill_counts.keys():
                self.horde_kill_counts[player["steamid"]] = player
