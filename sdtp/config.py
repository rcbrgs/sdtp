# -*- coding: utf-8 -*-

import json
import os
import sys

class config ( object ):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        
        self.values = {
            "app_name" : "SDTP",
            
            "auto_updater_url" : "https://github.com/rcbrgs/sdtp/releases/download/0.9.0/",
            
            "show_chat_window" : False,

            "enable_challenge" : False,
            "show_challenge_window" : False,
            
            "configuration_file_name" : "default.json",

            "database_file_name" : "sdtp_sqlite.db",
            
            "forbidden_countries" : [ "" ],
            "enable_per_country_bans" : False,
    
            "log_file_name" : "sdtp.log",
            "log_file_path" : "",
            "show_log_window" : False,
            "show_debug" : False,
            "show_info" : False,
            "show_warning" : True,
            "show_error" : True,
            "show_critical" : True,

            "enable_lp" : True,
            "lp_interval" : 2,
            "show_metronomer_window" : False,
            
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
            "enable_auto_horde_portals" : False,
            "enable_player_portals" : False,
            "show_player_portals_window" : False,
            "max_portals_per_player" : 0,
            "portal_cost" : 0,
            "teleport_cost" : 0,

            "alarm_reboots_time" : -1,
            "enable_alarm_reboots" : False,
            "enable_frequency_reboots" : False,
            "frequency_reboots_interval" : 24,
            "latest_reboot" : 0,
            "server_empty_condition" : True,
            "show_server_reboot_window" : False,
        }

        if os.name == "nt":
            self.values [ "configuration_file_path" ] = os.environ [ "ALLUSERSPROFILE" ]
            self.values [ "separator" ] = "\\\\"
        else:
            self.values [ "configuration_file_path" ] = os.path.expanduser ( "~" )
            self.values [ "separator" ] = "/"

    def falsify ( self, key ):
        self.values [ key ] = False

    def load_configuration_file ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        try:
            if os.name == 'posix':
                config_file_name = self.values [ 'configuration_file_path' ] + "/" + self.values [ 'configuration_file_name' ]
            elif os.name == 'nt':
                config_file_name = self.values [ 'configuration_file_path' ] + "\\" + self.values [ 'configuration_file_name' ]
            config_file = open ( config_file_name, "r" )
        except IOError:
            self.controller.log ( "warning", "Could not find configuration file {}.".format ( config_file_name ) )
            return
        try:
            new_config = json.load ( config_file )
            self.controller.log ( "debug", str ( new_config ) )
            for key in list ( self.values.keys ( ) ):
                if key in list ( new_config.keys ( ) ):
                    self.values [ key ] = new_config [ key ]
            self.controller.log ( "debug", "Loaded configuration file {}.".format ( config_file_name ) )
        except ValueError:
            self.controller.log ( "info", "Configuration file named '{}' is invalid. Using default values.".format ( config_file_name ) )

    def save_configuration_file ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        if os.name == 'posix':
            config_file =  open ( self.values [ 'configuration_file_path' ] + "/" + self.values [ 'configuration_file_name' ], "w" )
        elif os.name == 'nt':
            config_file =  open ( self.values [ 'configuration_file_path' ] + "\\" + self.values [ 'configuration_file_name' ], "w" )
        json.dump ( self.values, config_file )
        self.controller.log ( "debug", "Configuration file saved." )

    def toggle ( self, key ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( {} )".format ( key ) )

        if self.values [ key ] == True:
            self.values [ key ] = False
            return
        if self.values [ key ] == False:
            self.values [ key ] = True
            return
        self.controller.log ( "error", "config.toggle ( {} ) called, but value for key is not a boolean.".format ( key ) )
        
    def verify ( self, key ):
        self.values [ key ] = True

    def get ( self, key ):
        self.controller.log ( )
        
        try:
            return self.values [ key ]
        except:
            self.controller.log ( "error", "unable to find key '{}' among configuration values.".format ( key ) )
            return None
