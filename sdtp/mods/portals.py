# -*- coding: utf-8 -*-

import logging
import re
from sdtp.lp_table import lp_table
from sdtp.mods.portals_tables import PortalsTable
import sys
import threading
import time

import sdtp

class Portals(threading.Thread):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.cooldowns = {}
        self.start ( )

    def run(self):
        self.logger.info("Start.")
        self.help = {
            "go": "will list your portals.",
            "go public": "will list public portals.",
            "go <portal name>": "teleports you to <portal name>.",
            "go <portal name>+": "will add your current location as a portal.",
            "go <portal name>-": "will remove that portal.",
            "go <portal name>*": "will toggle if the portal is public.",
            "go <player>": "will teleport you to player location if you are friends."}
        self.controller.help.registered_commands["go"] = self.help
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_command)
        count = 0
        while(self.keep_running):
            count += 1
            if count % 600 == 0:
                self.logger.debug("Tick.")
            time.sleep ( 0.1 )
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_command)

    def stop ( self ):
        self.logger.info("Stop.")
        self.keep_running = False

    # Mod specific
    ##############

    def check_for_command ( self, match_group ):
        if not self.controller.config.values [ "mod_portals_enable" ]:
            self.logger.debug("Ignoring possible player command since portals mod is disabled.")
            return
        self.logger.debug("mod is enabled.")
        
        matcher = re.compile(r"^/go[\w]*(.*)$")
        match = matcher.search(match_group [11])
        if not match:
            self.logger.debug("Regex did not match: {}".format(match_group[11]))
            return
        self.logger.debug("Input from {} matches regex.".format(match_group[10]))
        command = match.groups()[0].strip()
        self.logger.debug("Command = {}".format(command))
        possible_player_name = match_group[10]
        argument = match.groups()[0].strip()
        self.logger.debug("'{}' used portal command with argument '{}'.".format (
            possible_player_name, argument))
        self.controller.database.consult(
            sdtp.lkp_table.lkp_table,
            [(sdtp.lkp_table.lkp_table.name, "==", possible_player_name)],
            self.check_for_command_2,
            {"argument": argument})

    def check_for_command_2(self, answer, argument):
        if len(answer) != 1:
            self.logger.error("DB entry for player name is not unique.")
            return
        player = answer[0]
        
        self.logger.debug("Checking for list command.")
        if argument == "":
            self.list_portals(player)
            return

        self.logger.debug("Checking for help usage.")
        if argument == "help":
            self.print_help_message(player)
            return
        
        self.logger.debug("Checking for public portal listing.")
        if argument == "public":
            self.list_public_portals(player)
            return        

        if argument[-1] in ["-", "+", "*"]:
            portal_name = argument[:-1]
        else:
            portal_name = argument
        self.logger.debug("Portal name is {}.".format(portal_name))
        
        self.logger.debug("Searching DB for portal with name '{}' from player {}.".format(portal_name, player["name"]))
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.name, "==", portal_name),
             (PortalsTable.steamid, "==", player["steamid"])],
            self.check_for_command_3,
            {"player": player, "portal_name": portal_name, "argument": argument})

    def check_for_command_3(self, answer, player, portal_name, argument):
        if len(answer) > 1:
            self.logger.error("Multiple db entries.")
            return
        if len(answer) == 0:
            self.check_for_command_4(player, portal_name, argument)
            return
        portal = answer[0]
        
        self.logger.debug("Checking for deletions.")
        if argument[-1] == "-":
            self.delete_portal(player, portal)
            return

        self.logger.debug("Checking for toggling public/non-public portal.")
        if argument[-1] == "*":
            self.toggle_portal_public(player, portal)
            return

        # Adding an existing portal (moving):
        if argument[-1] == "+":
            self.delete_portal(player, portal)
            self.add_portal(player, portal_name)
            return

        self.logger.info("Teleporting to portal owned by player.")
        self.teleport_player_to_portal(player, portal)

    def check_for_command_4(self, player, portal_name, argument):
        self.logger.debug("Checking for additions.")
        if argument[-1] == "+":
            self.add_portal(player, argument[:-1])
            return
        else:
            self.logger.debug("Checking for public portals.")
            self.check_for_public_portal_use(player, portal_name)

        self.logger.debug("Checking for player to player teleport.")
        self.controller.database.consult(
            sdtp.lkp_table.lkp_table,
            [(sdtp.lkp_table.lkp_table.name, "==", portal_name)],
            self.check_for_command_5,
            {"argument": argument, "player": player, "portal_name": portal_name})
        
    def check_for_command_5(self, db_answer, argument, player, portal_name):
        if len(db_answer) == 1:
            possible_friend = db_answer[0]
            friendships = self.controller.database.blocking_consult(
                sdtp.friendships_table.FriendshipsTable,
                [(sdtp.friendships_table.FriendshipsTable.player_steamid, "==",
                  possible_friend["steamid"]),
                 (sdtp.friendships_table.FriendshipsTable.friend_steamid, "==",
                  player["steamid"])])
            if len(friendships) == 1:
                if self.check_for_cooldown(player):
                    return
                self.controller.telnet.write('pm {} "Teleporting you to {}."'.format(player["steamid"], possible_friend["name"]))
                self.controller.telnet.write("tele {} {} {} {}".format(
                    player["steamid"], int(possible_friend["longitude"]),
                    int(possible_friend["height"]), int(possible_friend["latitude"])))
                return
            self.controller.telnet.write('pm {} "You are not {}\'s friend."'.format(player["steamid"], possible_friend["name"]))
            return
        
        # Portal is missing.
        self.controller.telnet.write('pm {} "Portal {} does not exist."'.format(
            player["steamid"], argument))

    # Commands
        
    def list_portals(self, player):
        self.logger.info(
            "Listing portals for player {}.".format(player["name"]))
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"])],
            self.list_portals_2,
            {"player": player})

    def list_portals_2(self, answer, player):
        if len(answer) == 0:
            self.logger.debug("Player has no portals." )
            self.controller.telnet.write('pm {} "You do not have portals set."'.format (player["steamid"]))
        else:
            self.logger.debug("listing player portals." )
            for portal in answer:
                try:
                    portal_string += ", " + portal["name"]
                except:
                    portal_string = portal["name"]
                if portal["public"]:
                    portal_string += "*"
            portals_string = 'pm {} "Your portals are: {}"'.format(
                player["steamid"], portal_string)
            self.logger.debug("" + portals_string)
            self.controller.telnet.write(portals_string)

    def print_help_message(self, player):
        self.logger.info("Printing help to {}.".format(player["name"]))
        text = "/go will list your portals."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
        text = "/go public will list public portals."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
        text = "/go <portal name> will teleport you to the portal."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
        text = "/go <portal name>+ will add your current location as a portal."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
        text = "/go <portal name>- will remove that portal."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
        text = "/go <portal name>* will toggle if the portal is public."
        self.controller.telnet.write(
            'pm {} "{}"'.format(player["steamid"], text))
            
    def teleport_player_to_portal(self, player, portal):
        if self.check_for_cooldown(player):
            return
        self.logger.info(
            "Teleporting {} to {}.".format(player["name"], portal["name"]))
        self.controller.telnet.write ( 'pm {} "Teleporting you to {}."'.format (
            player["steamid"], portal["name"] ) )
        teleport_string = 'tele {} {} {} {}'.format(
            player["steamid"],
            int(float(portal["longitude"])),
            int(float(portal["height"])),
            int(float(portal["latitude"])))
        self.controller.telnet.write(teleport_string)
        self.logger.debug(teleport_string)

    def check_for_public_portal_use(self, player, argument):
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.name, "==", argument),
             (PortalsTable.public, "==", True)],
            self.check_for_public_portal_use_2,
            {"player": player})

    def check_for_public_portal_use_2(self, answer, player):
        if len(answer) != 1:
            return
        portal = answer[0]
        self.logger.info("Public portal use detected.")
        self.teleport_player_to_portal(player, portal)
        return

    def delete_portal(self, player, portal):
        if portal["steamid"] != player["steamid"]:
            self.logger.info("Player {} attempted to delete portal {} that does not belong to him/her.".format(player["name"], portal["name"]))
            self.controller.telnet.write('pm {} "You cannot delete portals you do not own."'.format(player["steamid"]))
            return
        
        self.logger.info("Deleting portal {} from {}.".format(
            portal["name"], player["name"]))
        self.controller.telnet.write('pm {} "Deleted portal {}."'.format ( player["steamid"], portal["name"]))
        self.controller.database.delete(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"]),
             (PortalsTable.name, "==", portal["name"])],
            print)

    def add_portal(self, player, portal_name, public = False):
        # check player has portals left
        if self.controller.config.values[
                "mod_portals_max_portals_per_player"] > 0:
            player_portals = self.controller.database.blocking_consult(
                PortalsTable,
                [(PortalsTable.steamid, "==", player["steamid"])])
            if len(player_portals) >= self.controller.config.values[
                    "mod_portals_max_portals_per_player"]:
                self.controller.telnet.write('pm {} "You already have the maximum allowed portals set."'.format(player["steamid"]))
                return
        self.logger.info("Creating portal from position of {}.".format(
            player["name"]))
        self.controller.database.add_all(
            PortalsTable,
            [PortalsTable(
                steamid = player["steamid"],
                name = portal_name,
                longitude = int(player["longitude"]),
                height = int(player["height"]),
                latitude = int(player["latitude"]),
                public = public)],
            print)
        self.controller.telnet.write('pm {} "Portal {} created."'.format(
            player["steamid"], portal_name))

    def toggle_portal_public(self, player, portal):
        if player["steamid"] != portal["steamid"]:
            self.logger.info("Player {} attempted to toggle portal {} which he does not own.".format(player["name"], portal["name"]))
            self.controller.telnet.write('pm {} "You can only toggle portals you own."'.format(player["steamid"]))
            return

        self.logger.debug("Is there another public portal with this name?")
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.name, "==", portal["name"]),
             (PortalsTable.public, "==", True)],
            self.toggle_portal_public_2,
            {"player": player, "portal": portal})

    def toggle_portal_public_2(self, answer, player, portal):
        if len(answer) > 1:
            self.log.error("Multiple public portals named {}.".format(portal["name"]))
            return
        if len(answer) == 1:
            if answer[0]["steamid"] != player["steamid"]:
                self.logger.info("Player {} tried to toggle a public portal he/she doesn't own.".format(player["name"]))
                self.controller.telnet.write('pm {} "You cannot toggle a portal you do not own."'.format(player["steamid"]))
                return
        
        self.logger.debug("Portal is currently public? '{}'.".format ( portal["public"] ) )
        self.logger.info("Toggling portal {} from {}.".format(
            portal["name"], player["name"]))
        self.controller.telnet.write('pm {} "Toggling portal {}."'.format(player["steamid"], portal["name"]))
        self.controller.database.update(
            PortalsTable,
            {"aid": portal["aid"],
             "steamid": portal["steamid"],
             "name": portal["name"],
             "longitude": portal["longitude"],
             "height": portal["height"],
             "latitude": portal["latitude"],
             "public": not portal["public"]},
            print)

    def list_public_portals(self, player):
        self.logger.info("Listing public portals for player {}.".format(
            player["name"]))
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.public, "==", True)],
            self.list_public_portals_2,
            {"player": player})

    def list_public_portals_2(self, answer, player):
        self.logger.debug("Found {} public portals to list to player {}.".format(
            len(answer), player["steamid"]))
        for portal in answer:
            try:
                response += ", {}".format(portal["name"])
            except:
                response = "{}".format(portal["name"])
        self.controller.telnet.write('pm {} "Public portals are: {}."'.format(
            player["steamid"], response))

    def check_for_cooldown(self, player):
        now = time.time()
        if player["steamid"] in self.cooldowns:
            if now - self.cooldowns[player["steamid"]] < self.controller.config.values["mod_portals_cooldown"]:
                self.controller.telnet.write('pm {} "Your portal use is in cooldown for another {} seconds."'.format(player["steamid"], int(self.controller.config.values["mod_portals_cooldown"] - now + self.cooldowns[player["steamid"]])))
                return True
        self.cooldowns[player["steamid"]] = now
        return False
