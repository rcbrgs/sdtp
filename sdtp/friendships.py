# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import threading
import time

import sdtp
from sdtp.alias_table import AliasTable
from sdtp.friendships_table import FriendshipsTable
from sdtp.lkp_table import lkp_table

class Friendships(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop ( self ):
        self.keep_running = False
        self.logger.info("Stop.")

    def setup(self):
        self.help = {
            "friend": "List your friends.",
            "friend <name>": "Toggle <name> in your list of friends.",
            "friend <name>+": "Add <name> to your list of friends.",
            "friend <name>-": "Remove <name> from your list of friends.",
            "friend alias <name>": "Create an alias that other people can use to refer to you." }
        self.controller.help.registered_commands["friend"] = self.help
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_command)
        
    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_command)
    
    # Component specific
    ####################

    def check_for_command(self, match_groups):
        self.logger.debug("check_for_command({})".format(match_groups))
        matcher = re.compile("^/friend[\s]*(.*)$")
        matches = matcher.search(match_groups[11])
        if not matches:
            self.logger.debug("No command detected.")
            return
        argument = matches.groups()[0].strip()
        self.logger.debug("Argument detected: '{}'".format(argument))
        command = ""
        name = argument
        if len(argument) > 0:
            if argument[-1] in ["-", "+"]:
                command = argument[-1]
                name = argument[:-1]
            if "alias " in argument:
                command = "alias"
                name = argument[6:].strip()
        self.logger.info("argument = {}, command = {}, name = {}".format(
            argument, command, name))
        db_answer = self.controller.database.blocking_consult(
            lkp_table,
            [(lkp_table.steamid, "==", match_groups[7])])
        if len(db_answer) > 1:
            self.logger.info("DB entry non unique: {}".format(db_answer))
            return
        player = db_answer[0]
        if command == "":
            if argument == "":
                self.list_player_friends(player)
                return
        if command == "alias":
            self.create_alias(player, name)
            return
        self.toggle_friendship(player, name, argument)
            
    def toggle_friendship(self, player, name, argument):
        other = self.controller.worldstate.get_player_string(name)
        if other is None:
            self.controller.telnet.write(
                'pm {} "No player named \'{}\' found."'.format(
                    player["steamid"], name))
            return
        friend = other
        db_answer = self.controller.database.blocking_consult(
            FriendshipsTable,
            [(FriendshipsTable.player_steamid, "==", player["steamid"]),
             (FriendshipsTable.friend_steamid, "==", friend["steamid"])])
        existing_friendship = False
        if len(db_answer) == 1:
            existing_friendship = True
        if existing_friendship and argument[-1] == "+":
            self.controller.telnet.write(
                'pm {} "You are already friends with {}."'.format(
                    player["steamid"], friend["name"]))
            return
        if existing_friendship and (argument[-1] == "-" or \
                                    friend["name"] == argument):
            self.controller.database.blocking_delete(
                FriendshipsTable,
                [(FriendshipsTable.player_steamid, "==", player["steamid"]),
                 (FriendshipsTable.friend_steamid, "==", friend["steamid"])])
            self.controller.telnet.write('pm {} "Removed friendship with {}."'.format(player["steamid"], friend["name"]))
            return
        if argument[-1] == "-":
            self.controller.telnet.write(
                'pm {} "You cannot delete friendships you don\'t have."'.format(
                    player["steamid"]))
            return
        self.controller.database.blocking_add(
            FriendshipsTable,
            [FriendshipsTable(
                player_steamid = player["steamid"],
                friend_steamid = friend["steamid"])])
        self.controller.telnet.write(
            'pm {} "You are now friends with {}."'.format(
                player["steamid"], friend["name"]))

    def list_player_friends(self, player):
        db_answer = self.controller.database.blocking_consult(
            FriendshipsTable,
            [(FriendshipsTable.player_steamid, "==", player["steamid"])])
        for friendship in db_answer:
            friend = self.controller.database.blocking_consult(
                lkp_table,
                [(lkp_table.steamid, "==", friendship["friend_steamid"])])[0]
            try:
                response += ", {}".format(friend["name"])
            except:
                response = "{}".format(friend["name"])
        try:
            self.controller.telnet.write('pm {} "Your friends are: {}."'.format(
                player["steamid"], response))
        except UnboundLocalError:            
            self.controller.telnet.write(
                'pm {} "You do not have any friends (yet)!"'.format(
                    player["steamid"]))
        db = self.controller.database.blocking_consult(
            AliasTable, [(AliasTable.steamid, "==", player["steamid"])])
        if len(db) == 1:
            self.controller.server.pm(player, "You have an alias: {}.".format(
                db[0]["alias"]))

    def create_alias(self, player, name):
        self.logger.info("{} setting alias {}.".format(player["name"], name))
        other = self.controller.worldstate.get_player_string(name)
        if other is not None:
            self.logger.info("Another player has name or alias {}: {}.".format(
                other["name"], name))
            self.controller.server.pm(
                player, "Another player has name or alias {}.".format(name))
            return
        db = self.controller.database.blocking_consult(
            AliasTable, [(AliasTable.steamid, "==", player["steamid"])])
        if len(db) == 1:
            db[0]["alias"] = name
            self.controller.database.blocking_update(AliasTable, db[0])
            self.controller.server.pm(
                player, "Your alias was updated to {}.".format(name))
            return
        if len(db) == 0:
            self.controller.database.blocking_add(
                AliasTable, [AliasTable(steamid = player["steamid"],
                                        alias = name)])
            self.controller.server.pm(
                player, "Your alias was set to {}.".format(name))
            return
        self.logger.error("Multiple DB entries in AliasTable for {}.".format(
            player["name"]))

                                                  
