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
        matcher = re.compile("^/(friend)[\s]*(.*)$")
        matches = matcher.search(match_groups[11])
        if not matches:
            self.logger.debug("No command detected.")
            return
        command = matches.groups()[0].strip()
        arguments = matches.groups()[1].strip().split(" ")
        self.logger.debug("command: '{}', arguments: {}".format(
            command, arguments))
        
        name = ""
        subcommand = "print"
        if len(arguments) == 1:
            if arguments[0] != "":
                name = arguments[0]
                subcommand = "toggle"
                if name[-1] == "-":
                    subcommand = "delete"
                    name = name[:-1]
                if name[-1] == "+":
                    subcommand = "add"
                    name = name[:-1]
        if len(arguments) == 2:
            if arguments[0] == "alias":
                name = arguments[1].strip()
                subcommand = "alias"
        self.logger.debug("subcommand = {}, name = {}".format(subcommand, name))

        player = self.controller.worldstate.get_player_steamid(match_groups[7])
        other = self.controller.worldstate.get_player_string(name)
        
        if command == "friend":
            self.command_friend(subcommand, player, other)
            return

    def command_friend(self, subcommand, player, other):
        if subcommand == "add":
            self.add_friendship(player, other)
            return
        if subcommand == "alias":
            self.create_alias(player, name)
            return
        if subcommand == "delete":
            self.delete_friendship(player, other)
            return
        if subcommand == "print":
            self.print_friendships(player)
            return
        if subcommand == "toggle":
            self.toggle_friendship(player, other, name)
            return

    def add_friendship(self, player, other):
        self.controller.database.blocking_add(
            FriendshipsTable,
            [FriendshipsTable(
                player_steamid = player["steamid"],
                friend_steamid = other["steamid"])])
        self.controller.server.pm(
            player, "You are now friends with {}.".format(other["name"]))
        
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
        
    def delete_friendship(self, player, other):
        self.controller.database.blocking_delete(
            FriendshipsTable,
            [(FriendshipsTable.player_steamid, "==", player["steamid"]),
             (FriendshipsTable.friend_steamid, "==", other["steamid"])])
        self.controller.server.pm(
            player, "{} is no longer your friend.".format(other["name"]))
        
    def print_friendships(self, player):
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
            self.controller.server.pm(player, "Your friends are: {}.".format(
                response))
        except UnboundLocalError:            
            self.controller.server.pm(
                player, "You do not have any friends (yet)!")

        db = self.controller.database.blocking_consult(
            FriendshipsTable,
            [(FriendshipsTable.friend_steamid, "==", player["steamid"])])
        self.logger.info("db = {}".format(db))
        response = None
        for friendship in db:
            friend = self.controller.database.blocking_consult(
                lkp_table,
                [(lkp_table.steamid, "==", friendship["player_steamid"])])[0]
            try:
                response += ", {}".format(friend["name"])
            except:
                response = "{}".format(friend["name"])
        try:
            self.controller.server.pm(
                player, "People that have you as friend are: {}.".format(
                    response))
        except UnboundLocalError:            
            self.controller.server.pm(
                player, "Nobody has you as friend (yet)!")
            
        db = self.controller.database.blocking_consult(
            AliasTable, [(AliasTable.steamid, "==", player["steamid"])])
        if len(db) == 1:
            self.controller.server.pm(player, "You have an alias: {}.".format(
                db[0]["alias"]))

    def toggle_friendship(self, player, other, name):
        if other is None:
            self.controller.server.pm(
                player, "No player named \'{}\' found.".format(name))
            return
        friend = other
        db_answer = self.controller.database.blocking_consult(
            FriendshipsTable,
            [(FriendshipsTable.player_steamid, "==", player["steamid"]),
             (FriendshipsTable.friend_steamid, "==", friend["steamid"])])
        existing_friendship = False
        if len(db_answer) == 1:
            existing_friendship = True
        if existing_friendship:
            self.delete_friendship(player, other)
            return
        self.add_friendship(player, other)


                                                  
