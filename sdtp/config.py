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
            "db_engine" : "sqlite",
            "configuration_file_name" : "default.json",
            "database_file_name" : "sdtp_sqlite.db",
            "forbidden_countries" : [ "" ],
            "enable_per_country_bans" : False,
            "log_file_name" : "sdtp.log",
            "log_file_path" : "",
            "enable_lp" : True,
            "lp_interval" : 2,
            "enable_ping_limiter" : False,
            "max_ping" : 10000,
            "show_ping_limiter_window" : False,
            "show_players_window" : False,
            "sdtp_greetings" : "[SDTP] Seven Days To Py: started.",
            "sdtp_goodbye" : "[SDTP] Seven Days To Py: stopped.",
            "telnet_password" : "BEWARE - PASSWORD WILL BE STORED UNENCRYPTED",
            "telnet_IP" : "127.0.0.1",
            "telnet_port" : 8081,
            "auto_connect" : False,
            # mods
            "enable_challenge" : False,
            "enable_auto_horde_portals" : False,
            "enable_player_portals" : False,
            "max_portals_per_player" : 0,
            "portal_cost" : 0,
            "teleport_cost" : 0,
            "alarm_reboots_time" : -1,
            "enable_alarm_reboots" : False,
            "enable_frequency_reboots" : False,
            "frequency_reboots_interval" : 24,
            "latest_reboot" : 0,
            "server_empty_condition" : True,
            "server_reboots_widget_show" : False,
        }
        self.values["config_file"] = "{}_preconfig.json".format(self.values["app_name"])
        self.values["db_sqlite_file_path"] = "{}_default_db.sqlite".format(self.values["app_name"])

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
        json.dump ( self.values, config_file )
        self.logger.debug("Configuration file '{}' saved.".format ( self.get ( "config_file" ) ) )

    def toggle ( self, key ):
        if self.values [ key ] == True:
            self.values [ key ] = False
            return
        if self.values [ key ] == False:
            self.values [ key ] = True
            return
        self.logger.error("config.toggle ( {} ) called, but value for key is not a boolean.".format ( key ) )
