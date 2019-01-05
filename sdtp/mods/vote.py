# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import threading
import time
import urllib3

from sdtp.lkp_table import lkp_table

class Vote(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_vote_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.help = {
            "claim": "Claim your prize if you voted today.",
            "vote": "The address of where to vote." }
        self.controller.dispatcher.register_callback(
            "chat message", self.check_for_commands)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "chat message", self.check_for_commands)

    def check_for_commands(self, match_groups):
        self.logger.debug("check_for_command({})".format(match_groups))
        command = ""
        for key in self.help.keys():
            matcher = re.compile("^/{}(.*)$".format(key))
            matches = matcher.search(match_groups[11])
            if matches:
                self.logger.debug("Command {} detected.".format(key))
                command = key
        if command == "":
            self.logger.debug("No match detected.")
            return
        
        matcher = re.compile("^/{}(.*)$".format(command))
        matches = matcher.search(match_groups[11])
        arguments = matches.groups()[0].strip().split(" ")
        self.logger.debug("command: '{}', arguments: {}".format(
            command, arguments))
        
        player = self.controller.worldstate.get_player_steamid(match_groups[7])

        if command == "claim":
            self.claim(player, arguments)
            return
        if command == "vote":
            self.vote(player, arguments)
            return
        
    # Mod specific
    ##############

    def claim(self, player, arguments):
        self.logger.debug("Checking if {} has voted.".format(player["name"]))
        http = urllib3.PoolManager()
        r = http.request('GET', 'https://7daystodie-servers.com/api/?object='\
                         'votes&element=claim&key={}&steamid={}'.format(
                             self.controller.config.values[
                                 "mod_vote_server_api_key"], player["steamid"]))
        count = 0
        while(r.status != 200):
            time.sleep(0.1)
            count +=1
            if count > 100:
                self.logger.warning("HTTP 200 never reached.")
                return
        self.logger.debug("r = {}".format(r.data))

        response = r.data

        if response == b"0":
            self.controller.server.pm(player, "Could not find your vote.")
            return
        if response == b"2":
            self.controller.server.pm(player, "Vote has already been claimed.")
            return
        
        s = http.request('POST', 'https://7daystodie-servers.com/api/?action='\
                         'post&object=votes&element=claim&key={}&steamid='\
                         '{}'.format(self.controller.config.values[
                             "mod_vote_server_api_key"], player["steamid"]))
        self.logger.debug("s = {}".format(s.data))

        count = 0
        while(s.status != 200):
            time.sleep(0.1)
            count +=1
            if count > 100:
                self.logger.warning("HTTP 200 never reached.")
                return

        if s.data == b"0":
            self.logger.error("Vote has not been claimed.")
            return

        self.controller.server.pm(player, "Giving you your prize.")
        for item in self.controller.config.values["mod_vote_prize_bag"]:
            self.controller.server.give(player, item["what"], item["quantity"],
                                        item["quality"])
        
    def vote(self, player, arguments):
        self.controller.server.pm(
            player, "Cast your vote at http://7daystodie-servers.com/server/83443. When done, use /claim to get your prize.")

        
