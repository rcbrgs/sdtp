# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import random
import re
import threading
import time

from sdtp.lkp_table import lkp_table
from sdtp.mods.llp_table import llp_table

class Challenge(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_challenge_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
            self.run_challenges()
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.help = {
            "challenge": "toggles wether you are in the challenge or not. In the challenge, you are teleported randomly and have to fight incresing hordes of zombies."}
        self.controller.help.registered_commands["challenge"] = self.help
        self.ongoing_challenges = {}
        self.challenged_today = []
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)
        self.controller.dispatcher.register_callback(
            "new day", self.reset_daily_counts)
        self.controller.dispatcher.register_callback(
            "player died", self.check_for_challenge_death)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)
        self.controller.dispatcher.deregister_callback(
            "new day", self.reset_daily_counts)
        self.controller.dispatcher.deregister_callback(
            "player died", self.check_for_challenge_death)

    def check_for_commands(self, match_group):        
        matcher = re.compile(r"^/challenge[\s]*(.*)$")
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
        player = self.controller.worldstate.get_player_steamid(match_group[7])
        
        self.logger.debug("Checking for challenge command.")
        if argument == "":
            self.toggle_challenge(player)
            return
        
    # Mod specific
    ##############
    
    def toggle_challenge(self, player):
        if player["steamid"] in self.ongoing_challenges.keys():
            self.check_for_quitters_teleport(player)
            self.remove_from_challenge(player)
            return
        
        if player["steamid"] in self.challenged_today:
            self.controller.server.pm(
                player, "You have already been challenged today.")
            return
        self.challenged_today.append(player["steamid"])
        
        self.ongoing_challenges[player["steamid"]] = {
            "level": 0,
            "latest_turn": time.time(),
            "player_id": player["player_id"],
            "deaths": player["deaths"],
            "initial longitude": int(player["longitude"]),
            "initial height": int(player["height"]),
            "initial latitude": int(player["latitude"])}
        self.random_teleport(player)

    def check_for_quitters_teleport(self, player):
        if self.controller.config.values[
                "mod_challenge_quitters_teleport_enable"]:
            self.controller.telnet.write('tele {} {} {} {}'.format(
                player["steamid"],
                self.ongoing_challenges[player["steamid"]]["initial longitude"],
                self.ongoing_challenges[player["steamid"]]["initial height"],
                self.ongoing_challenges[player["steamid"]]["initial latitude"]))
            self.controller.server.pm(
                player, "Sending you back to where you belong, quitter!")
        
    def remove_from_challenge(self, player):
        self.controller.telnet.write('say "{}\'s challenge is over at level {}."'.format(player["name"], self.ongoing_challenges[player["steamid"]]["level"]))
        del self.ongoing_challenges[player["steamid"]]
        
    def run_challenges(self):
        now = time.time()
        for key in self.ongoing_challenges.keys():
            self.logger.debug("Checking if player died at least once.")
            player = self.controller.worldstate.get_player_steamid(key)
            if player["deaths"] > self.ongoing_challenges[key]["deaths"]:
                self.remove_from_challenge(player)
                continue
            entry = self.ongoing_challenges[key]
            if now - entry["latest_turn"] > self.controller.config.values[
                    "mod_challenge_round_interval"]:
                entry["latest_turn"] = now
                entry["level"] += 1
                self.challenge_round(
                    player,
                    entry["level"])

    def reset_daily_counts(self, match_groups):
        self.challenged_today = []
                
    def challenge_round(self, player, level):
        regular_zombies = self.controller.server.normal_zombies
        feral_zombies = self.controller.server.feral_zombies
        radiated_zombies = self.controller.server.radiated_zombies
        regulars = 0
        ferals = 0
        radiated = 0
        if level < 5:
            regulars = level
            ferals = 0
            radiated = 0
        if level >= 5 and level < 10:
            regulars = 2
            ferals = 3
            radiated = 0
        if level >= 10 and level < 15:
            regulars = 1
            ferals = 3
            radiated = 1
        if level >= 30:
            regulars = 1
            ferals = 2
            radiated = int(level / 10)

        for zombie in range(regulars):
            self.controller.server.se(
                player, random.choice(regular_zombies))
        for zombie in range(ferals):
            self.controller.server.se(
                player, random.choice(feral_zombies))
        for zombie in range(radiated):
            self.controller.server.se(
                player, random.choice(radiated_zombies))

    def check_for_challenge_death(self, match_groups):
        name = match_groups[7]
        self.logger.debug(
            "Trying to ascertain whether {} was in a challenge.".format(name))
        db_answer = self.controller.database.blocking_consult(
            lkp_table,
            [(lkp_table.name, "==", name)])
        if len(db_answer) != 1:
            self.logger.error("Player entry not unique in DB.")
            return
        player = db_answer[0]
        if player["steamid"] in self.ongoing_challenges.keys():
            self.remove_from_challenge(player)

    def random_teleport(self, player):
        distance = self.controller.config.values["mod_challenge_distance"]
        longitude = random.randint(-distance, distance)
        latitude = random.randint(-distance, distance)
        self.logger.info("Checking for claims near {}, {}.".format(
            longitude, latitude))
        nearby_claims = False
        claims = self.controller.database.blocking_consult(
            llp_table,
            [])
        for claim in claims:
            if abs(longitude - claim["longitude"]) < 100 and \
               abs(latitude - claim["latitude"]) < 100:
                self.logger.info("Too near claim at {}, {}.".format(
                    claim["longitude"], claim["latitude"]))
                return self.random_teleport(player)
        self.logger.info("Teleporting player to {}, -1, {}.".format(
            longitude, latitude))
        self.controller.telnet.write("tele {} {} -1 {}".format(
            player["steamid"], longitude, latitude))
