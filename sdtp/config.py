# -*- coding: utf-8 -*-

import json
import logging
import os
import pathlib
import sys

class Config(object):
    def __init__ ( self, controller = None ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.logger = logging.getLogger(__name__)

        self.configuration_file_valid = False
        self.values = {
            "app_name" : "sdtp",
            "chat_input_name" : "",
            "configuration_file_name" : "sdtp_config.json",
            "database_file_name" : "sdtp_db.sqlite",
            "db_engine" : "sqlite",
            "interval_gt": 15,
            "interval_lkp": 3600,
            "interval_llp": 60,
            "interval_lp" : 5,
            "interval_tick": 60,
            "latest_reboot" : 0,
            "night_time_begins_at": 22,
            "night_time_ends_at": 4,
            "sdtp_greetings" : "[sdtp] Seven Days To Py: started.",
            "sdtp_goodbye" : "[sdtp] Seven Days To Py: stopped.",
            "telnet_password" : "BEWARE - PASSWORD WILL BE STORED UNENCRYPTED",
            "telnet_IP" : "127.0.0.1",
            "telnet_port" : 8081,
            "auto_connect" : False,
            # mod announcements
            "mod_announcements_enable": True,
            "mod_announcements_commands": {"sdtp":
                                            {"command": False,
                                             "text": "Seven Days To Py - get it at https://github.com/rcbrgs/sdtp",
                                             "interval": 24*3600,
                                             "latest": -1}},
            # mod biome load hang
            "mod_biomeloadhang_enable": False,
            "mod_biomeloadhang_countdown": 60,
            "mod_biomeloadhang_kill": False,
            # mod challenge
            "mod_challenge_distance": 1600,
            "mod_challenge_enable": False,
            "mod_challenge_quitters_teleport_enable": True,
            "mod_challenge_round_interval": 15,
            # mod chatlogger
            "mod_chatlogger_enable": True,
            "mod_chatlogger_file_path": "chat.txt",
            # mod chat translator
            "mod_chattranslator_enable": False,
            # mod claim alarm
            "mod_claimalarm_distance": 10,
            "mod_claimalarm_enable": False,
            # mod forbidden countries
            "mod_forbiddencountries_enable": False,
            "mod_forbiddencountries_banned_countries": ["ch", "ru"],
            # mod leg fix
            "mod_legfix_enable": False,
            # mod most kills
            "mod_mostkills_enable": False,
            # mod portals
            "mod_portals_player_cooldown_seconds": 3600,
            "mod_portals_portal_cooldown_seconds": 3600,
            "mod_portals_enable" : False,
            "mod_portals_max_portals_per_player" : -1,
            # mod qol
            "mod_qol_bears_cooldown_seconds": 24*3600,
            "mod_qol_enable": False,
            "mod_qol_animals_quantity": 1,
            "mod_qol_gimme_cooldown_minutes": 15,
            "mod_qol_gimme_quantity": 1,
            "mod_qol_gimme_what": "food",
            "mod_qol_greeting": "[00FFFF]Ah! Fresh meat to feed my hungry zombies!",
            # mod relax
            "mod_relax_cooldown_seconds": 24*3600, 
            "mod_relax_enable": False,
            "mod_relax_percentage_doubling_zombies": 25,
            # mod server reboots
            "mod_serverreboots_enable": False,
            "mod_serverreboots_interval": 12,
            "mod_serverreboots_empty_condition" : True,
            # mod vote
            "mod_vote_enable": False,
            "mod_vote_prize_bag": [{"what": "",
                                    "quality": "",
                                    "quantity": ""}],
            "mod_vote_server_api_key": "Get it from https://7daystodie-servers.com",
        }

    def falsify ( self, key ):
        self.values [ key ] = False

    def verify ( self, key ):
        self.values [ key ] = True

    def get ( self, key ):
        try:
            return self.values [ key ]
        except:
            self.logger.error("unable to find key '{}' among configuration values.".format ( key ) )
            return None

    def set ( self, key, value ):
        self.values [ key ] = value

    def load_configuration_file (self):
        try:
            config_file = open(self.get("configuration_file_name"), "r")
        except:
            self.logger.error("Could not open the configuration file {}.".format(
                self.get("configuration_file_name")))
            self.configuration_file_valid = True
            return
        try:
            config = json.load ( config_file )
            for key in list ( config.keys ( ) ):
                self.logger.debug("config[\"{}\"] = {}".format(
                    key, config[key]))
                self.values [ key ] = config [ key ]
            self.configuration_file_valid = True
            self.logger.info("Loaded configuration file {}.".format(
                self.get("configuration_file_name")))
        except ValueError:
            self.logger.error(
                "Configuration file named '{}' is invalid.".format(
                    self.get("configuration_file_name")))
            return

    def save_configuration_file ( self ):
        if not self.configuration_file_valid:
            self.logger.error("Not saving invalid configuration file.")
            return
        self.logger.info("Saving current configuration in '{}'.".format(
            self.get("configuration_file_name")))
        config_file = open(self.get("configuration_file_name"), "w")
        json.dump(self.values, config_file, indent=4, sort_keys=True)
        self.logger.debug("Configuration file '{}' saved.".format(
            self.get("configuration_file_name")))

    def toggle ( self, key ):
        if self.values [ key ] == True:
            self.values [ key ] = False
            return
        if self.values [ key ] == False:
            self.values [ key ] = True
            return
        self.logger.error(
            "config.toggle({}) called, but value for key is not a boolean.".\
            format(key))
