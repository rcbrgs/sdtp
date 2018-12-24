# -*- coding: utf-8 -*-

import logging
import re
from sdtp.lp_table import lp_table
from sdtp.mods.portals_tables import PortalsTable
import sys
import threading
import time

class Portals(threading.Thread):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.start ( )

    def run(self):
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
        self.logger.info("Command = {}".format(command))
        possible_player_name = match_group[10]
        argument = match.groups()[0].strip()
        self.logger.info("'{}' used portal command with argument '{}'.".format (
            possible_player_name, argument))
        self.controller.database.consult(
            lp_table,
            [(lp_table.name, "==", possible_player_name)],
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

        self.logger.info("Checking for help usage.")
        if argument == "help":
            self.print_help_message(player)
            return
        
        self.logger.info("Checking for public portal listing.")
        if argument == "public":
            self.list_public_portals(player)
            return        

        self.logger.info("Checking for portal with name '{}'.".format(
            argument))
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.name, "==", argument)],
             self.check_for_command_3,
             {"player": player, "argument": argument})

    def check_for_command_3(self, answer, player, argument):
        if len(answer) > 1:
            self.logger.error("Multiple db entries.")
            return
        if len(answer) == 0:
            self.check_for_command_4(player, argument)
            return
        portal = answer[0]
        
        self.logger.info("Teleporting if portal is owned by player.")
        if portal["steamid"] == player["steamid"]:
            self.teleport_to_portal(player, portal)
            return

        self.logger.info("Checking for public portals." )
        if self.check_for_public_portal_use(portal):
            self.teleport_player_to_portal(player, portal)
            return

    def check_for_command_4(self, player, argument):
        self.logger.info("Searching DB for portal with name '{}'.".format(
            argument[:-1]))
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.name, "==", argument[:-1])],
            self.check_for_command_5,
            {"player": player, "argument": argument})

    def check_for_command_5(self, answer, player, argument):
        if len(answer) > 1:
            self.log.error("Multiple DB entries.")
            return
        if len(answer) == 0:
            self.check_for_command_6(player, argument)
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
            self.check_for_command_6(player, argument)

    def check_for_command_6(self, player, argument):        
        self.logger.debug("Checking for additions.")
        if argument[-1] == "+":
            self.add_portal(player, argument[:-1])
            return

    # Commands
        
    def list_portals(self, player):
        self.logger.debug(
            "Listing portals for player {}.".format(player["name"]))
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"])],
            self.list_portals_2,
            {"player": player})

    def list_portals_2(self, answer, player):
        if len(answer) == 0:
            self.logger.debug("Player has no portals." )
            self.controller.telnet.write ( 'pm {} "You do not have portals set."'.format ( player_lp.steamid ) )
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
        self.logger.debug(
            "teleporting player to portal '{}'.".format ( portal["name"]) )
        self.controller.telnet.write ( 'pm {} "Teleporting you to {}."'.format (
            player["steamid"], portal["name"] ) )
        teleport_string = 'tele {} {} {} {}'.format(
            player["steamid"],
            int(float(portal["longitude"])),
            int(float(portal["height"])),
            int(float(portal["latitude"])))
        self.controller.telnet.write(teleport_string)
        self.logger.debug(teleport_string)

    def check_for_public_portal_use(self, portal):
        return portal["public"]

    def delete_portal(self, player, portal):
        if portal["steamid"] != player["steamid"]:
            self.logger.info("Player {} attempted to delete portal {} that does not belong to him/her.".format(player["name"], portal["name"]))
            self.controller.telnet.write('pm {} "You cannot delete portals you do not own."'.format(player["steamid"]))
            return
        
        self.logger.debug("Deleting portal {} from {}.".format(
            portal["name"], player["name"]))
        self.controller.telnet.write('pm {} "Deleted portal {}."'.format ( player["steamid"], portal["name"]))
        self.controller.database.delete(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"]),
             (PortalsTable.name, "==", portal["name"])],
            print)

    def add_portal(self, player, portal_name, public = False):
        # check no portal has name
        self.logger.debug("Creating portal from position of player: {}.".format(
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
            self.log.info("Player {} attempted to toggle portal {} which he does not own.".format(player["name"], portal["name"]))
            self.controller.telnet.write('pm {} "You can only toggle portals you own."'.format(player["steamid"]))
            return
        
        self.logger.debug("Portal is currently public? '{}'.".format ( portal["public"] ) )
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
        self.logger.info("Checking public portals for player {}.".format(
            player["name"]))
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.public, "==", True)],
            self.list_public_portals_2,
            {"player": player})

    def list_public_portals_2(self, answer, player):
        self.logger.info("Found {} public portals to list to player {}.".format(
            len(answer), player["steamid"]))
        for portal in answer:
            try:
                response += ", {}".format(portal["name"])
            except:
                response = "{}".format(portal["name"])
        self.controller.telnet.write('pm {} "Public portals are: {}."'.format(
            player["steamid"], response))
