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

        self.values = {
            "app_name" : "sdtp",
            "chat_input_name" : "",
            "configuration_file_name" : "default.json",
            "database_file_name" : "sdtp_sqlite.db",
            "db_engine" : "sqlite",
            "enable_lp" : True,
            "enable_ping_limiter" : False,
            "interval_gt": 15,
            "interval_lkp": 3600,
            "interval_llp": 60,
            "interval_lp" : 5,
            "interval_tick": 60,
            "latest_reboot" : 0,
            "log_file_name" : "sdtp.log",
            "log_file_path" : "",
            "max_ping" : 10000,
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
                                            {"text": "Seven Days To Py - get it at https://github.com/rcbrgs/sdtp",
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
            "mod_portals_cooldown_seconds": 3600,
            "mod_portals_enable" : False,
            "mod_portals_max_portals_per_player" : -1,
            "mod_portals_teleport_cost" : 0,
            # mod qol
            "mod_qol_bears_cooldown_seconds": 24*3600,
            "mod_qol_enable": False,
            "mod_qol_animals_quantity": 1,
            "mod_qol_gimme_cooldown_minutes": 15,
            "mod_qol_gimme_quantity": 1,
            "mod_qol_gimme_what": "food",
            "mod_qol_greeting": "[00FFFF]Ah! Fresh meat to feed my hungry zombies!",
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
        self.values["config_file"] = "{}_preconfig.json".format(
            self.values["app_name"])
        self.values["db_sqlite_file_path"] = "{}_default_db.sqlite".format(
            self.values["app_name"])

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

    def load_configuration_file ( self ):
        try:
            preconfig_file = open ( self.get ( "config_file" ), "r" )
        except:
            self.logger.error("Could not open the pre-configuration file {}.".format ( self.get ( "config_file" ) ) )
            return
        try:
            preconfig = json.load ( preconfig_file )
            for key in list ( preconfig.keys ( ) ):
                self.logger.debug("config [ \"{}\" ] = {}".format ( key, preconfig [ key ] ) )
                self.values [ key ] = preconfig [ key ]
            self.logger.debug("Loaded pre-configuration file." )
        except ValueError:
            self.logger.info("Configuration file named '{}' is invalid. Using default values.".format ( self.get ( "config_file" ) ) )
            return

        try:
            config_file = open ( self.get ( "config_file" ), "r" )
        except IOError:
            self.logger.error("Could not open the configuration file {}.".format ( self.get ( "config_file" ) ) )
            return
        try:
            final_config = json.load ( config_file )
            for key in list ( final_config.keys ( ) ):
                self.logger.debug("config [ \"{}\" ] = {}".format ( key, final_config [ key ] ) )
                self.values [ key ] = final_config [ key ]
            self.logger.debug("Loaded configuration file." )
        except ValueError:
            self.logger.info("Configuration file named '{}' is invalid. Using default values.".format ( self.get ( "config_file" ) ) )

    def save_configuration_file ( self ):
        self.logger.debug("saving current configuration in '{}'.".format ( self.get ( "config_file" ) ) )
        config_file = open ( self.get ( "config_file" ), "w" )
        json.dump(self.values, config_file, indent=4, sort_keys=True)
        self.logger.debug("Configuration file '{}' saved.".format ( self.get ( "config_file" ) ) )

    def toggle ( self, key ):
        if self.values [ key ] == True:
            self.values [ key ] = False
            return
        if self.values [ key ] == False:
            self.values [ key ] = True
            return
        self.logger.error("config.toggle ( {} ) called, but value for key is not a boolean.".format ( key ) )
