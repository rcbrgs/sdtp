# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import threading
import time

import sdtp

class Friendships(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop ( self ):
        self.keep_running = False

    def setup(self):
        self.help = {
            "friend": "List your friends.",
            "friend <name>": "Toggle <name> in your list of friends.",
            "friend <name>+": "Add <name> to your list of friends.",
            "friend <name>-": "Remove <name> from your list of friends."}
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
        matcher = re.compile("/friend[\w]*(.*)$")
        matches = matcher.search(match_groups[11])
        if not matches:
            self.logger.debug("No command detected.")
            return
        argument = matches.groups()[0].strip()
        self.logger.debug("Argument detected: '{}'".format(argument))
        name = argument
        if len(argument) > 0:
            if argument[-1] in[ "-", "+"]:
                name = argument[:-1]
        self.controller.database.consult(
            sdtp.lkp_table.lkp_table,
            [(sdtp.lkp_table.lkp_table.steamid, "==", match_groups[7])],
            self.check_for_command_2,
            {"argument": argument, "name": name})

    def check_for_command_2(self, db_answer, argument, name):
        if len(db_answer) != 1:
            self.logger.info("DB entry non unique: {}".format(db_answer))
            return
        player = db_answer[0]
        if argument == "":
            self.list_player_friends(player)
            return
        self.controller.database.consult(
            sdtp.lkp_table.lkp_table,
            [(sdtp.lkp_table.lkp_table.name, "==", name)],
            self.check_for_command_3,
            {"argument": argument, "name": name, "player": player})

    def check_for_command_3(self, db_answer, argument, name, player):
        if len(db_answer) == 0:
            self.controller.telnet.write('pm {} "No player named \'{}\' found."'.format(player["steamid"], name))
            return
        if len(db_answer) > 1:
            self.controller.telnet.write('pm {} "ERROR: multiple DB entries for \'{}\'."'.format(player["steamid"], name))
            return
        friend = db_answer[0]
        self.controller.database.consult(
            sdtp.friendships_table.FriendshipsTable,
            [(sdtp.friendships_table.FriendshipsTable.player_steamid, "==", player["steamid"]),
             (sdtp.friendships_table.FriendshipsTable.friend_steamid, "==", friend["steamid"])],
            self.check_for_command_4,
            {"argument": argument, "friend": friend, "player": player})

    def check_for_command_4(self, db_answer, argument, friend, player):
        existing_friendship = False
        if len(db_answer) == 1:
            existing_friendship = True
        if existing_friendship and argument[-1] == "+":
            self.controller.telnet.write('pm {} "You are already friends with {}."'.format(player["steamid"], friend["name"]))
            return
        if existing_friendship and (argument[-1] == "-" or \
                                    friend["name"] == argument):
            self.controller.database.delete(
                sdtp.friendships_table.FriendshipsTable,
                [(sdtp.friendships_table.FriendshipsTable.player_steamid, "==",
                  player["steamid"]),
                 (sdtp.friendships_table.FriendshipsTable.friend_steamid, "==",
                  friend["steamid"])],
                print)
            self.controller.telnet.write('pm {} "Removed friendship with {}."'.format(player["steamid"], friend["name"]))
            return
        if argument[-1] == "-":
            self.controller.telnet.write('pm {} "You cannot delete friendships you don\'t have."'.format(player["steamid"]))
            return
        self.controller.database.add_all(
            sdtp.friendships_table.FriendshipsTable,
            [sdtp.friendships_table.FriendshipsTable(
                player_steamid = player["steamid"],
                friend_steamid = friend["steamid"])],
            print)
        self.controller.telnet.write('pm {} "You are now friends with {}."'.format(player["steamid"], friend["name"]))

    def list_player_friends(self, player):
        self.controller.database.consult(
            sdtp.friendships_table.FriendshipsTable,
            [(sdtp.friendships_table.FriendshipsTable.player_steamid, "==", player["steamid"])],
            self.list_player_friends_2,
            {"player": player})

    def list_player_friends_2(self, db_answer, player):
        for friendship in db_answer:
            friend = self.controller.database.get_records(
                sdtp.lkp_table.lkp_table,
                [(sdtp.lkp_table.lkp_table.steamid, "==", friendship["friend_steamid"])])[0]
            try:
                response += ", {}".format(friend["name"])
            except:
                response = "{}".format(friend["name"])
        try:
            self.controller.telnet.write('pm {} "Your friends are: {}."'.format(
                player["steamid"], response))
        except UnboundLocalError:            
            self.controller.telnet.write('pm {} "You do not have any friends (yet)!"'.format(player["steamid"]))
