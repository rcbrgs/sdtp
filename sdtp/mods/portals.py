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

        self.auto_horde_portal = None

        self.start ( )

    def run ( self ):
        self.controller.dispatcher.register_callback ( "chat message", self.check_for_command )
        count = 0
        while ( self.keep_running ):
            count += 1
            if count % 600 == 0:
                self.logger.debug("Tick.")
            time.sleep ( 0.1 )
        self.controller.dispatcher.deregister_callback ( "chat message", self.check_for_command )

    def stop ( self ):
        self.keep_running = False

    # Mod specific
    ##############

    def check_for_command ( self, match_group ):
        if not self.controller.config.values [ "mod_portals_enable" ]:
            self.logger.debug("Ignoring possible player command since portals mod is disabled.")
            return
        self.logger.debug("mod is enabled.")
        
        matcher = re.compile(r"^/go (.*)$")
        match = matcher.search(match_group [11])
        if not match:
            self.logger.debug("Regex did not match: {}".format(match_group[11]))
            matcher = re.compile(r"^/go[\w]*$")
            match = matcher.search(match_group[11])
            if match:
                self.list_portals(match_group[10])
            return
        self.logger.info("Input from {} matches regex.".format(match_group[10]))
        possible_player_name = match_group[10]
        possible_portal_name = match.groups()[0]
        self.logger.info("'{}' used portal command with argument '{}'.".format (possible_player_name, possible_portal_name))

        
        self.logger.info("Checking for public portals." )
        if self.check_for_public_portal_use(possible_player_name, possible_portal_name):
            return

        self.logger.info("Checking for deletions.")
        if possible_portal_name [ -1 ] == "-":
            self.delete_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            return

        self.logger.info("Checking for additions.")
        if possible_portal_name [ -1 ] == "+":
            self.delete_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            self.add_portal ( possible_player_name, possible_portal_name [ : -1 ] )
            return

        self.logger.info("Checking for toggling public/non-public portal.")
        if possible_portal_name [ -1 ] == "*":
            self.toggle_portal_public(possible_player_name, possible_portal_name[:-1])
            return

        self.logger.info("Teleporting if portal exist.")
        self.teleport_to_portal(possible_player_name, possible_portal_name)

    def teleport_to_portal(self, possible_player_name, possible_portal_name):
        player = self.controller.database.consult(
            lp_table,
            [(lp_table.name, "==", possible_player_name)],
            self.teleport_to_portal_2,
            {"possible_portal_name": possible_portal_name})

    def teleport_to_portal_2(self, answer, possible_portal_name):
        self.logger.info("answer = {}".format(answer))
        if len(answer) != 1:
            self.logger.error("Player name not in lp_table!")
            return
        player = answer[0]
        portal = self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.name, "==", possible_portal_name),
             (PortalsTable.steamid, "==", player["steamid"])],
            self.teleport_to_portal_3,
            {"player": player})

    def teleport_to_portal_3(self, answer, player):
        self.logger.info("answer = {}".format(answer))
        if len(answer) != 1:
            self.logger.error("Portal name not in portal table!")
            return
        portal = answer[0]
        self.logger.info("teleporting player to portal '{}'.".format ( portal["name"]) )
        self.controller.telnet.write ( 'pm {} "Teleporting you to {}."'.format (
            player["steamid"], portal["name"] ) )
        teleport_string = 'tele {} {} {} {}'.format ( player["steamid"], int ( float ( portal["longitude"] ) ), int ( float ( portal["height"] ) ), int ( float ( portal["latitude"] ) ) )
        self.controller.telnet.write ( teleport_string )
        self.logger.info(teleport_string)

    def check_for_public_portal_use ( self, player_name, possible_portal_name ):
        self.logger.info(
            "player_name = {}, possible_portal_name = {}".format (
                player_name, possible_portal_name ) )
        self.controller.database.consult (
            PortalsTable,
            [ ( PortalsTable.name, "==", possible_portal_name ),
              ( PortalsTable.public, "==", True ) ],
            self.check_for_public_portal_use_2,
            {"player_name": player_name})
        self.logger.info("Consult request sent.")

    def check_for_public_portal_use_2(self, answer, player_name):
        self.logger.info("answer = {}".format ( answer ) )
        if len ( answer ) != 1:
            return False
        portal = answer [ 0 ]
        self.logger.info("portal = {}".format ( portal ) )
        player_query = self.controller.database.consult (
            lp_table, [ ( lp_table.name, "==", player_name ) ],
            self.check_for_public_portal_use_3,
            {"portal": portal})

    def check_for_public_portal_use_3(self, answer, portal):
        player_lp = answer [ 0 ]
        self.logger.info("player_lp = {}".format ( player_lp ) )
        self.controller.telnet.write ( 'pm {} "Teleporting you to {}."'.format ( player_lp["steamid"], portal["name"] ) )
        teleport_string = 'tele {} {} {} {}'.format ( player_lp["steamid"],
                                                      int ( float ( portal["longitude"] ) ),
                                                      int ( float ( portal["height"] ) ),
                                                      int ( float ( portal["latitude"] ) ) )
        self.controller.telnet.write ( teleport_string )
        self.logger.info(teleport_string)
        return True

    def delete_portal(self, possible_player_name, possible_portal_name):
        self.logger.info("Deleting portal {} from {}.".format(
            possible_portal_name, possible_player_name))
        self.controller.database.consult(
            lp_table,
            [(lp_table.name, "==", possible_player_name)],
            self.delete_portal_2,
            {"possible_portal_name": possible_portal_name})
        
    def delete_portal_2(self, answer, possible_portal_name):
        if len(answer) != 1:
            self.logger.info("Player name not in lp_table.")
            return
        player = answer[0]
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"]),
             (PortalsTable.name, "==", possible_portal_name)],
            self.delete_portal_3,
            {"player": player})

    def delete_portal_3(self, answer, player):
        if len(answer) != 1:
            self.logger.error("Unable to find portal to delete." )
            return
        portal = answer[0]
        self.logger.info("Deleting portal '{}'.".format ( portal["name"] ) )
        self.controller.telnet.write('pm {} "Deleted portal {}."'.format ( player["steamid"], portal["name"]))
        self.controller.database.delete(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"]),
             (PortalsTable.name, "==", portal["name"])],
            print)

    def add_portal(self, possible_player_name, possible_portal_name, public = False):
        self.controller.database.consult(
            lp_table,
            [(lp_table.name, "==", possible_player_name)],
            self.add_portal_2,
            {"possible_portal_name": possible_portal_name,
             "public": public})

    def add_portal_2(self, answer, possible_portal_name, public):
        if len(answer) != 1:
            self.logger.error("Unable to find player name. Answer = {}.".format(answer))
        player = answer[0]
        self.logger.info("Creating portal from position of player: {}.".format(player))
        self.controller.database.add_all(
            PortalsTable,
            [PortalsTable(
                steamid = player["steamid"],
                name = possible_portal_name,
                longitude = int(player["longitude"]),
                height = int(player["height"]),
                latitude = int(player["latitude"]),
                public = public)],
            print)
        self.controller.telnet.write('pm {} "Portal {} created."'.format(
            player["steamid"], possible_portal_name))

    def list_portals ( self, player_name ):
        self.controller.database.consult(
            lp_table,
            [(lp_table.name, "==", player_name)],
            self.list_portals_2)

    def list_portals_2(self, answer):
        if len(answer) != 1:
            self.logger.error("While listing portals could not find player on db.")
            return
        player = answer[0]
        self.logger.info("Listing portals for player {}.".format(player["name"]))
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"])],
            self.list_portals_3,
            {"player": player})

    def list_portals_3(self, answer, player):
        if len(answer) == 0:
            self.logger.info("Player has no portals." )
            self.controller.telnet.write ( 'pm {} "You do not have portals set."'.format ( player_lp.steamid ) )
        else:
            self.logger.info("listing player portals." )
            for portal in answer:
                try:
                    portal_string += ", " + portal["name"]
                except:
                    portal_string = portal["name"]
                if portal["public"]:
                    portal_string += "*"
            portals_string = 'pm {} "Your portals are: {}"'.format ( player["steamid"], portal_string )
            self.logger.info("" + portals_string )
            self.controller.telnet.write ( portals_string )

    def toggle_portal_public(self, possible_player_name, possible_portal_name):
        self.controller.database.consult(
            lp_table,
            [(lp_table.name, "==", possible_player_name)],
            self.toggle_portal_public_2,
            {"possible_portal_name": possible_portal_name})
        
    def toggle_portal_public_2(self, answer, possible_portal_name):
        if len(answer) != 1:
            self.logger.info("Player name not in lp_table.")
            return
        player = answer[0]
        self.controller.database.consult(
            PortalsTable,
            [(PortalsTable.steamid, "==", player["steamid"]),
             (PortalsTable.name, "==", possible_portal_name)],
            self.toggle_portal_public_3,
            {"player": player})

    def toggle_portal_public_3(self, answer, player):
        if len(answer) != 1:
            self.logger.error("Unable to find portal to delete." )
            return
        portal = answer[0]
        self.logger.info("Portal is currently public? '{}'.".format ( portal["public"] ) )
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
