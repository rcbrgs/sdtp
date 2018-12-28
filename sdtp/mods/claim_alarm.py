# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import threading
import time

from sdtp.friendships_table import FriendshipsTable
from sdtp.lkp_table import lkp_table
from sdtp.lp_table import lp_table
from sdtp.mods.llp_table import llp_table

import sdtp

class ClaimAlarm(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.abort = False
        self.start ( )

    def run(self):
        if not self.controller.config.values["mod_claim_alarm_enable"]:
            return
        self.setup()
        while ( self.keep_running ):
            time.sleep(0.1)
        self.tear_down()
            
    def stop ( self ):
        self.keep_running = False

    # Mod specific
    ##############

    def setup(self):
        self.help = {
            "/alarm": "Prints your alarm configuration.",
            "/alarm me": "Sets your alarm to PMs to you only.",
            "/alarm friends": "Sets your alarm to PMs to you and your friends.",
            "/alarm all": "Sets your alarm to a server-wide message."}
        self.controller.help.registered_commands["alarm"] = self.help
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)
        self.controller.dispatcher.register_callback(
            "claim player", self.parse_player_summary)
        self.controller.dispatcher.register_callback(
            "claim stone", self.parse_claim_position)
        self.controller.dispatcher.register_callback(
            "claim finished", self.parse_server_summary)
    
    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)
        self.controller.dispatcher.deregister_callback(
            "claim player", self.parse_player_summary)
        self.controller.dispatcher.deregister_callback(
            "claim stone", self.parse_claim_position)
        self.controller.dispatcher.deregister_callback(
            "claim finished", self.parse_server_summary)

    def parse_player_summary(self, match_groups):
        self.logger.debug("Parsing claim summary for steamid: {}.".format(
            match_groups[0]))
        self.parsing_steamid = match_groups[0]

    def parse_claim_position(self, match_groups):
        self.logger.debug("Parsing claim position {}.".format(match_groups))
        self.controller.database.consult(
            llp_table,
            [(llp_table.steamid, "==", self.parsing_steamid),
             (llp_table.longitude, "==", int(match_groups[0])),
             (llp_table.height, "==", int(match_groups[1])),
             (llp_table.latitude, "==", int(match_groups[2]))],
            self.parse_claim_position_2,
            {"match_groups": match_groups, "steamid": self.parsing_steamid})

    def parse_claim_position_2(self, answer, match_groups, steamid):
        if len(answer) == 0:
            self.controller.database.add_all(
                llp_table,
                [llp_table(steamid = steamid,
                           longitude = int(match_groups[0]),
                           height = int(match_groups[1]),
                           latitude = int(match_groups[2]))],
                print)
            return
        if len(answer) == 1:
            self.logger.debug("Claim already in DB.")
            return
        self.logger.error("Multiple DB entries for claim stone.")

    def parse_server_summary(self, match_groups):
        self.controller.telnet.write_lock = False
        self.check_for_presences()
        
    def check_for_commands(self, match_groups):
        matcher = re.compile(r"^/alarm[\w]*(.*)$")
        match = matcher.search(match_groups[11])
        if not match:
            self.logger.debug("No match for command regex: {}".format(match_groups[11]))
            return
        command = match.groups()[0].strip()
        self.logger.debug("command = '{}'".format(command))
        self.controller.database.consult(
            sdtp.lkp_table.lkp_table,
            [(sdtp.lkp_table.lkp_table.name, "==", match_groups[10])],
            self.check_for_commands_2,
            {"command": command})

    def check_for_commands_2(self, answer, command):
        if len(answer) != 1:
            self.logger.error("Player name not unique in db.")
            return
        player = answer[0]
        self.logger.info("Parsing command '{}'.".format(command))
        if command == "help":
            self.print_help_message(player)
            return
        if command == "":
            self.print_current_configuration(player)
            return
        self.configure_alarm(command, player)

    def print_help_message(self, player):
        for key in self.help.keys():
            self.controller.telnet.write(
                'pm {} "{} {}"'.format(player["steamid"], key, self.help[key]))

    def check_for_presences(self):
        players = self.controller.world_state.online_players
        self.controller.database.consult(
            llp_table,
            [],
            self.check_for_presences_2,
            {"players": players})

    def check_for_presences_2(self, claims, players):
        self.logger.debug("Checking for presences 2. len(players) = {}".format(
            len(players)))
        for player in players:
            for claim in claims:
                self.logger.debug("Checking if {} at {}, {} is inside claim {}, {}".format(player["name"], player["longitude"], player["latitude"], claim["longitude"], claim["latitude"]))
                if abs(player["longitude"] - claim["longitude"]) < self.controller.config.values["mod_claim_alarm_distance"]:
                    if abs(player["latitude"] - claim["latitude"]) < self.controller.config.values["mod_claim_alarm_distance"]:
                        if player["steamid"] == claim["steamid"]:
                            self.logger.debug("{} inside own claim.".format(
                                player["name"]))
                            break
                        self.controller.database.consult(
                            lkp_table,
                            [(lkp_table.steamid, "==", claim["steamid"])],
                            self.check_for_presences_3,
                            {"player": player, "claim": claim})
                        break

    def check_for_presences_3(self, db_answer, player, claim):
        if len(db_answer) != 1:
            self.logger.error("DB entry non unique.")
            return
        claim_player = db_answer[0]
        self.logger.info("{} is inside {}'s claim.".format(player["name"],
                                                           claim_player["name"]))
        self.controller.database.consult(
            FriendshipsTable,
            [(FriendshipsTable.player_steamid, "==", claim_player["steamid"]),
             (FriendshipsTable.friend_steamid, "==", player["steamid"])],
            self.check_for_presences_4,
            {"claim": claim, "claim_player": claim_player, "player": player})

    def check_for_presences_4(self, db_answer, claim, claim_player, player):
        if len(db_answer) == 1:
            self.logger.info("{} inside friend {}'s claim.".format(
                player["name"], claim_player["name"]))
            return
        self.logger.info("{} is invading {}'s claim!".format(
            player["name"], claim_player["name"]))
        if claim["alarm_type"] == "me":
            self.controller.telnet.write('pm {} "{} is invading your claim at {}, {}!"'.format(claim_player["steamid"], player["name"], claim["longitude"], claim["latitude"]))
            return
        if claim["alarm_type"] == "friends":
            self.warn_friends(claim_player, player, claim)
            return
        if claim["alarm_type"] == "all":
            self.controller.telnet.write('say "{} is invading {}\'s claim at {}, {}!"'.format(player["name"], claim_player["name"], claim["longitude"], claim["latitude"]))
            return

    def warn_friends(self, claim_player, player, claim):
        self.controller.database.consult(
            FriendshipsTable,
            [(FriendshipsTable.player_steamid, "==", claim_player["steamid"])],
            self.warn_friends_2,
            {"claim_player": claim_player, "player": player, "claim": claim})

    def warn_friends_2(self, db_answer, claim_player, player, claim):
        for friendship in db_answer:
            self.controller.telnet.write('pm {} "{} is invading {}\'s claim at {}, {}!"'.format(friendship["friend_steamid"], player["name"], claim_player["name"], claim["longitude"], claim["latitude"]))

    def print_current_configuration(self, player):
        self.logger.info("Printing configuration for {}.".format(player["name"]))
        self.controller.database.consult(
            llp_table,
            [(llp_table.steamid, "==", player["steamid"])],
            self.print_current_configuration_2,
            {"player": player})

    def print_current_configuration_2(self, db_answer, player):
        if len(db_answer) == 0:
            self.controller.telnet.write('pm {} "You do not have any landclaims in the DB."'.format(player["steamid"]))
            return
        for claim in db_answer:
            self.controller.telnet.write('pm {} "Your claim at {}, {} is set to \'{}\'."'.format(player["steamid"], claim["longitude"], claim["latitude"], claim["alarm_type"]))

    def configure_alarm(self, argument, player):
        self.controller.database.consult(
            llp_table,
            [(llp_table.steamid, "==", player["steamid"])],
            self.configure_alarm_2,
            {"argument": argument, "player": player})

    def configure_alarm_2(self, db_answer, argument, player):
        if argument not in ["me", "friends", "all"]:
            self.controller.telnet.write('pm {} "Unknown argument to command alarm."'.format(player["steamid"]))
            return
        for claim in db_answer:
            claim["alarm_type"] = argument
            self.controller.database.update(
                llp_table,
                claim,
                print)
            self.controller.telnet.write('pm {} "Updated claim at {}, {} to alarm \'{}\'."'.format(player["steamid"], claim["longitude"], claim["latitude"], argument))
