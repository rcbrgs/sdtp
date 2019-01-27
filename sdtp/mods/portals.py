# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------8081

import logging
import re
import sys
import threading
import time

import sdtp
from sdtp.friendships_table import FriendshipsTable
from sdtp.lp_table import lp_table
from sdtp.mods.portals_tables import PortalsTable
from sdtp.table_cooldowns import TableCooldowns

class Portals(threading.Thread):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

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
        steamid = int(match_group[7])
        self.logger.debug("'{}' used portal command with argument '{}'.".format (
            possible_player_name, argument))
        player = self.controller.worldstate.get_player_steamid(steamid)
        if player is None:
            self.logger.error("DB entry for player name is not unique.")
            return
        
        self.logger.debug("Checking for list command.")
        if argument == "":
            self.list_portals(player)
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
        answer = self.controller.database.blocking_consult(
            PortalsTable,
            [(PortalsTable.name, "==", portal_name),
             (PortalsTable.steamid, "==", player["steamid"])])
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
            if self.check_for_public_portal_use(player, portal_name):
                return

        self.logger.debug("Checking for player to player teleport.")
        other = self.controller.worldstate.get_player_string(portal_name)
        if other is not None:
            friendships = self.controller.database.blocking_consult(
                FriendshipsTable,
                [(FriendshipsTable.player_steamid, "==",
                  other["steamid"]),
                 (FriendshipsTable.friend_steamid, "==",
                  player["steamid"])])
            if len(friendships) == 1:
                if self.check_for_cooldown(player, "player"):
                    return
                self.controller.server.pm(
                    player, "Teleporting you to {}.".format(other["name"]))
                self.controller.telnet.write("tele {} {} {} {}".format(
                    player["steamid"], int(other["longitude"]),
                    int(other["height"]), int(other["latitude"])))
                return
            self.controller.server.pm(
                player, "You are not {}\'s friend.".format(other["name"]))
            return
        
        # Portal is missing.
        self.controller.server.pm(player, "Portal {} does not exist.".format(
            argument))

    # Commands
        
    def list_portals(self, player):
        self.logger.info(
            "Listing portals for player {}.".format(player["name"]))
        answer = self.controller.database.blocking_consult(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"])])
        if len(answer) == 0:
            self.logger.debug("Player has no portals." )
            self.controller.server.pm(
                player, "You do not have portals set.")
        else:
            self.logger.debug("listing player portals." )
            for portal in answer:
                try:
                    portal_string += ", " + portal["name"]
                except:
                    portal_string = portal["name"]
                if portal["public"]:
                    portal_string += "*"
            portals_string = "Your portals are: {}".format(
                portal_string)
            self.logger.debug("" + portals_string)
            self.controller.server.pm(player, portals_string)
            
    def teleport_player_to_portal(self, player, portal):
        if self.check_for_cooldown(player, "portal"):
            return
        self.logger.info(
            "Teleporting {} to {}.".format(player["name"], portal["name"]))
        self.controller.server.pm(
            player, "Teleporting you to {}.".format(portal["name"]))
        teleport_string = 'tele {} {} {} {}'.format(
            player["steamid"],
            int(float(portal["longitude"])),
            int(float(portal["height"])),
            int(float(portal["latitude"])))
        self.controller.telnet.write(teleport_string)
        self.logger.debug(teleport_string)

    def check_for_public_portal_use(self, player, argument):
        answer = self.controller.database.blocking_consult(
            PortalsTable,
            [(PortalsTable.name, "==", argument),
             (PortalsTable.public, "==", True)])
        if len(answer) != 1:
            return False
        portal = answer[0]
        self.logger.info("Public portal use detected.")
        self.teleport_player_to_portal(player, portal)
        return True

    def delete_portal(self, player, portal):
        if portal["steamid"] != player["steamid"]:
            self.logger.info("Player {} attempted to delete portal {} that does"\
                             " not belong to him/her.".format(
                                 player["name"], portal["name"]))
            self.controller.server.pm(
                player, "You cannot delete portals you do not own.")
            return
        
        self.logger.info("Deleting portal {} from {}.".format(
            portal["name"], player["name"]))
        self.controller.server.pm(
            player, "Deleted portal {}.".format(portal["name"]))
        self.controller.database.blocking_delete(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"]),
             (PortalsTable.name, "==", portal["name"])])

    def add_portal(self, player, portal_name, public = False):
        # check player has portals left
        if self.controller.config.values[
                "mod_portals_max_portals_per_player"] >= 0:
            player_portals = self.controller.database.blocking_consult(
                PortalsTable,
                [(PortalsTable.steamid, "==", player["steamid"])])
            if len(player_portals) >= self.controller.config.values[
                    "mod_portals_max_portals_per_player"]:
                self.controller.server.pm(
                    player, "You already have the maximum allowed portals set.")
                return
        self.logger.info("Creating portal from position of {}.".format(
            player["name"]))
        self.controller.database.blocking_add(
            PortalsTable,
            [PortalsTable(
                steamid = player["steamid"],
                name = portal_name,
                longitude = int(player["longitude"]),
                height = int(player["height"]),
                latitude = int(player["latitude"]),
                public = public)])
        self.controller.server.pm(player, "Portal {} created.".format(
            portal_name))

    def toggle_portal_public(self, player, portal):
        if player["steamid"] != portal["steamid"]:
            self.logger.info("Player {} attempted to toggle portal {} which he does not own.".format(player["name"], portal["name"]))
            self.controller.server.pm(
                player, "You can only toggle portals you own.")
            return

        self.logger.debug("Is there another public portal with this name?")
        answer = self.controller.database.blocking_consult(
            PortalsTable,
            [(PortalsTable.name, "==", portal["name"]),
             (PortalsTable.public, "==", True)])
        if len(answer) > 1:
            self.log.error("Multiple public portals named {}.".format(portal["name"]))
            return
        if len(answer) == 1:
            if answer[0]["steamid"] != player["steamid"]:
                self.logger.info("Player {} tried to toggle a public portal he/she doesn't own.".format(player["name"]))
                self.controller.server.pm(
                    player, "You cannot toggle a portal you do not own.")
                return
        
        self.logger.debug("Portal is currently public? '{}'.".format ( portal["public"] ) )
        self.logger.info("Toggling portal {} from {}.".format(
            portal["name"], player["name"]))
        self.controller.server.pm(
            player, "Toggling portal {}.".format(portal["name"]))
        self.controller.database.blocking_update(
            PortalsTable,
            {"aid": portal["aid"],
             "steamid": portal["steamid"],
             "name": portal["name"],
             "longitude": portal["longitude"],
             "height": portal["height"],
             "latitude": portal["latitude"],
             "public": not portal["public"]})

    def list_public_portals(self, player):
        self.logger.info("Listing public portals for player {}.".format(
            player["name"]))
        answer = self.controller.database.blocking_consult(
            PortalsTable,
            [(PortalsTable.public, "==", True)])
        self.logger.debug("Found {} public portals to list to player {}.".format(
            len(answer), player["steamid"]))
        for portal in answer:
            try:
                response += ", {}".format(portal["name"])
            except:
                response = "{}".format(portal["name"])
        try:
            self.controller.server.pm(
                player, "Public portals are: {}.".format(response))
        except UnboundLocalError:
            self.controller.server.pm(
                player, "There are no public portals.")

    def check_for_cooldown(self, player, type_of_cooldown):
        now = time.time()
        cooldowns = self.controller.database.blocking_consult(
            TableCooldowns, [(TableCooldowns.steamid, "==", player["steamid"])])
        if len(cooldowns) == 0:
            self.logger.info("Cooldown db entry for {} does not exist.".format(
                player["name"]))
            if type_of_cooldown == "player":
                self.controller.database.blocking_add(
                    TableCooldowns, [TableCooldowns(
                        steamid = player["steamid"],
                        portals_player = now)])
            if type_of_cooldown == "portal":
                self.controller.database.blocking_add(
                    TableCooldowns, [TableCooldowns(
                        steamid = player["steamid"],
                        portals_portal = now)])
            return False

        self.logger.info("Cooldown db entry for {} exists.".format(
            player["name"]))
        if type_of_cooldown == "player":
            difference = now - cooldowns[0]["portals_player"]
            if difference < self.controller.config.values[
                   "mod_portals_player_cooldown_seconds"]:
                self.controller.server.pm(
                    player, "Your teleport to player is in cooldown for another"\
                    " {}.".format(self.controller.qol.pretty_print_seconds(
                        int(self.controller.config.values[
                            "mod_portals_player_cooldown_seconds"] -\
                            difference))))
                return True
        if type_of_cooldown == "portal":
            difference = now - cooldowns[0]["portals_portal"]
            if difference < self.controller.config.values[
                   "mod_portals_portal_cooldown_seconds"]:
                self.controller.server.pm(
                    player, "Your teleport to portal is in cooldown for another"\
                    " {}.".format(self.controller.qol.pretty_print_seconds(
                        int(self.controller.config.values[
                            "mod_portals_portal_cooldown_seconds"] -\
                            difference))))
                return True

        self.logger.info("Player {} not yet in cooldown.".format(player["name"]))
        if type_of_cooldown == "player":
            cooldowns[0]["portals_player"] = now
            self.controller.database.blocking_update(
                TableCooldowns, cooldowns[0])
            return False
        if type_of_cooldown == "portal":
            cooldowns[0]["portals_portal"] = now
            self.controller.database.blocking_update(
                TableCooldowns, cooldowns[0])
            return False
