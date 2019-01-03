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
        self.logger.info("Start.")
        if not self.controller.config.values["mod_claimalarm_enable"]:
            return
        self.setup()
        while ( self.keep_running ):
            time.sleep(0.1)
        self.tear_down()
            
    def stop ( self ):
        self.logger.info("Stop.")
        self.keep_running = False

    # Mod specific
    ##############

    def setup(self):
        self.help = {
            "alarm": "Prints your alarm configuration.",
            "alarm me": "Sets your alarm to PMs to you only.",
            "alarm friends": "Sets your alarm to PMs to you and your friends.",
            "alarm all": "Sets your alarm to a server-wide message."}
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
        answer = self.controller.database.blocking_consult(
            llp_table,
            [(llp_table.steamid, "==", self.parsing_steamid),
             (llp_table.longitude, "==", int(match_groups[0])),
             (llp_table.height, "==", int(match_groups[1])),
             (llp_table.latitude, "==", int(match_groups[2]))])
        if len(answer) == 0:
            self.controller.database.blocking_add(
                llp_table,
                [llp_table(steamid = steamid,
                           longitude = int(match_groups[0]),
                           height = int(match_groups[1]),
                           latitude = int(match_groups[2]))])
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
        player = self.controller.worldstate.get_player_steamid(match_groups[7])
        self.logger.info("Parsing command '{}'.".format(command))

        if command == "":
            self.print_current_configuration(player)
            return
        self.configure_alarm(command, player)

    def check_for_presences(self):
        players = self.controller.worldstate.online_players
        claims = self.controller.database.blocking_consult(llp_table, [])
        self.logger.debug("Checking for presences 2. len(players) = {}".format(
            len(players)))
        for player in players:
            for claim in claims:
                self.logger.debug("Checking if {} at {}, {} is inside claim {}" \
                                  ", {}".format(player["name"],
                                                player["longitude"],
                                                player["latitude"],
                                                claim["longitude"],
                                                claim["latitude"]))
                if abs(player["longitude"] - claim["longitude"]) < self.controller.config.values["mod_claimalarm_distance"]:
                    if abs(player["latitude"] - claim["latitude"]) < self.controller.config.values["mod_claimalarm_distance"]:
                        if player["steamid"] == claim["steamid"]:
                            self.logger.debug("{} inside own claim.".format(
                                player["name"]))
                            break
                        db_answer = self.controller.database.blocking_consult(
                            lkp_table,
                            [(lkp_table.steamid, "==", claim["steamid"])])
                        if len(db_answer) != 1:
                            self.logger.error("DB entry non unique.")
                            return
                        claim_player = db_answer[0]
                        self.logger.debug("{} is inside {}'s claim.".format(
                            player["name"], claim_player["name"]))
                        db_answer = self.controller.database.blocking_consult(
                            FriendshipsTable,
                            [(FriendshipsTable.player_steamid, "==",
                              claim_player["steamid"]),
                             (FriendshipsTable.friend_steamid, "==",
                              player["steamid"])])
                        if len(db_answer) == 1:
                            self.logger.debug("{} inside friend {}'s claim.".format(
                                player["name"], claim_player["name"]))
                            return
                        self.logger.debug("{} is invading {}'s claim!".format(
                            player["name"], claim_player["name"]))
                        if claim["alarm_type"] == "me":
                            self.controller.server.pm(
                                claim_player, "{} is invading your claim at {}, {}!".format(player["name"], claim["longitude"], claim["latitude"]))
                            return
                        if claim["alarm_type"] == "friends":
                            self.warn_friends(claim_player, player, claim)
                            return
                        if claim["alarm_type"] == "all":
                            self.controller.telnet.write('say "{} is invading {}\'s claim at {}, {}!"'.format(player["name"], claim_player["name"], claim["longitude"], claim["latitude"]))
                            return

    def warn_friends(self, claim_player, player, claim):
        db_answer = self.controller.database.blocking_consult(
            FriendshipsTable,
            [(FriendshipsTable.player_steamid, "==", claim_player["steamid"])])
        for friendship in db_answer:
            claim_player_friend = self.controller.worldstate.get_player_steamid(
                friendship["friendship_steamid"])
            self.controller.server.pm(
                claim_player_friend,
                "{} is invading {}\'s claim at {}, {}!".format(
                    player["name"], claim_player["name"],
                    claim["longitude"], claim["latitude"]))

    def print_current_configuration(self, player):
        self.logger.info("Printing configuration for {}.".format(player["name"]))
        db_answer = self.controller.database.blocking_consult(
            llp_table,
            [(llp_table.steamid, "==", player["steamid"])])
        if len(db_answer) == 0:
            self.controller.server.pm(
                player, "You do not have any landclaims in the DB.")
            return
        for claim in db_answer:
            self.controller.server.pm(
                player, "Your claim at {}, {} is set to \'{}\'.".format(
                    claim["longitude"], claim["latitude"], claim["alarm_type"]))

    def configure_alarm(self, argument, player):
        db_answer = self.controller.database.blocking_consult(
            llp_table,
            [(llp_table.steamid, "==", player["steamid"])])
        if argument not in ["me", "friends", "all"]:
            self.controller.server.pm(
                player, "Unknown argument to command alarm.")
            return
        for claim in db_answer:
            claim["alarm_type"] = argument
            self.controller.database.blocking_update(
                llp_table,
                claim)
            self.controller.server.pm(
                player, "Updated claim at {}, {} to alarm \'{}\'.".format(
                    claim["longitude"], claim["latitude"], argument))
