# -*- coding: utf-8 -*-

from sdtp.alias_table import AliasTable
from sdtp.lkp_table import lkp_table
from sdtp.lp_table import lp_table

import logging
from sqlalchemy import Integer
import sys
import threading
import time

class WorldState(threading.Thread):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.online_players = []
        self.online_players_count = 100000
        self.online_players_changed = False
        self.latest_day = 0
        self.latest_hour = 0
        self.server_empty = False
        self.start ( )

    # Thread control
    def run ( self ):
        self.logger.info("Start.")
        self.register_callbacks ( )
        while ( self.keep_running ):
            time.sleep ( 0.1 )
        self.deregister_callbacks ( )
        self.logger.debug("world_state.run returning" )

    def stop ( self ):
        self.keep_running = False
        self.logger.info("Stop.")

    # Component-specific
    ####################

    def register_callbacks ( self ):
        self.controller.dispatcher.register_callback(
            "gt command output", self.log_time_of_day)
        self.controller.dispatcher.register_callback(
            "lkp output", self.parse_lkp_output)
        self.controller.dispatcher.register_callback(
            "lp output", self.update_lkp_table )
        self.controller.dispatcher.register_callback(
            "lp output", self.update_lp_table )
        self.controller.dispatcher.register_callback(
            "le/lp output footer", self.update_online_players_count )
        self.controller.dispatcher.register_callback(
            "player joined", self.player_connected)
        self.controller.dispatcher.register_callback(
            "player left", self.player_disconnected)

    def deregister_callbacks ( self ):
        self.controller.dispatcher.deregister_callback(
            "gt command output", self.log_time_of_day)
        self.controller.dispatcher.deregister_callback (
            "lp output", self.update_lp_table )
        self.controller.dispatcher.deregister_callback (
            "le/lp output footer", self.update_online_players_count )
        self.controller.dispatcher.deregister_callback(
            "player joined", self.player_connected)
        self.controller.dispatcher.deregister_callback(
            "player left", self.player_disconnected)

    def player_connected(self, match_group):
        self.logger.info("Player {} connected.".format(match_group[7]))
        self.online_players_changed = True
        
    def player_disconnected(self, match_group):
        self.logger.info("Player {} disconnected.".format(match_group[7]))
        self.online_players_changed = True
        
    def update_lkp_table ( self, match_group ):
        self.logger.debug("update_lkp_table for {}.".format(match_group[1]))
        self.logger.debug("({})".format (match_group))
        this_steamid = int ( match_group [ 15 ] ),
        results = self.controller.database.blocking_consult(
            lkp_table, [ ( lkp_table.steamid, "==", match_group [ 15 ] ) ])
        self.logger.debug("results = {}.".format ( results ) )
        if len ( results ) == 0:
            self.logger.info("New lkp entry: {}".format(match_group[1]))
            self.controller.database.blocking_add(
                lkp_table,
                [ lkp_table (
                    player_id = match_group [ 0 ],
                    name = match_group [ 1 ],
                    longitude = match_group [ 2 ],
                    height = match_group [ 3 ],
                    latitude = match_group [ 4 ],
                    rotation_height = match_group [ 5 ],
                    rotation_longitude = match_group [ 6 ],
                    rotation_latitude = match_group [ 7 ],
                    remote = match_group [ 8 ],
                    health = match_group [ 9 ],
                    deaths = match_group [ 10 ],
                    zombies = match_group [ 11 ],
                    players = match_group [ 12 ],
                    score = match_group [ 13 ],
                    level = match_group [ 14 ],
                    steamid = match_group [ 15 ],
                    ip = match_group [ 16 ],
                    ping = match_group [ 17 ] ) ] )
        else:
            self.logger.debug("Update lkp entry." )
            entry = results [ 0 ]
            self.logger.debug("entry before: {}".format(entry))
            entry [ "name" ] = match_group [ 1 ]
            entry [ "longitude" ] = match_group [ 2 ]
            entry [ "height" ] = match_group [ 3 ]
            entry [ "latitude" ] = match_group [ 4 ]
            entry [ "rotation_height" ] = match_group [ 5 ]
            entry [ "rotation_longitude" ] = match_group [ 6 ]
            entry [ "rotation_latitude" ] = match_group [ 7 ]
            entry [ "remote" ] = match_group [ 8 ]
            entry [ "health" ] = match_group [ 9 ]
            entry [ "deaths" ] = match_group [ 10 ]
            entry [ "zombies" ] = match_group [ 11 ]
            entry [ "players" ] = match_group [ 12 ]
            entry [ "score" ] = match_group [ 13 ]
            entry [ "level" ] = match_group [ 14 ]
            entry["steamid"] = match_group[15]
            entry [ "ip" ] = match_group [ 16 ]
            entry [ "ping" ] = match_group [ 17 ]
            self.logger.debug("entry after: {}".format(entry))
            self.controller.database.blocking_update(
                lkp_table,
                entry )
            self.logger.debug("added entry." )
        self.logger.debug("returning." )

    def update_lp_table ( self, match_group ):
        self.logger.debug("({})".format (match_group))
        if self.online_players_changed:
            self.controller.database.blocking_delete(
                lp_table, [])
            self.online_players_changed = False
        this_steamid = int ( match_group [ 15 ] )
        results = self.controller.database.blocking_consult (
            lp_table, [ ( lp_table.steamid, "==", match_group [ 15 ] ) ])
        self.logger.debug("results = {}.".format ( results ) )
        if len ( results ) == 0:
            self.logger.debug("New entry." )
            self.controller.database.blocking_add(
                lp_table,
                [ lp_table (
                    player_id = match_group [ 0 ],
                    name = match_group [ 1 ],
                    longitude = match_group [ 2 ],
                    height = match_group [ 3 ],
                    latitude = match_group [ 4 ],
                    rotation_height = match_group [ 5 ],
                    rotation_longitude = match_group [ 6 ],
                    rotation_latitude = match_group [ 7 ],
                    remote = match_group [ 8 ],
                    health = match_group [ 9 ],
                    deaths = match_group [ 10 ],
                    zombies = match_group [ 11 ],
                    players = match_group [ 12 ],
                    score = match_group [ 13 ],
                    level = match_group [ 14 ],
                    steamid = match_group [ 15 ],
                    ip = match_group [ 16 ],
                    ping = match_group [ 17 ] ) ])
        else:
            self.logger.debug("Update lp entry." )
            entry = results [ 0 ]
            self.logger.debug("entry before: {}".format(entry))
            entry [ "name" ] = match_group [ 1 ]
            entry [ "longitude" ] = match_group [ 2 ]
            entry [ "height" ] = match_group [ 3 ]
            entry [ "latitude" ] = match_group [ 4 ]
            entry [ "rotation_height" ] = match_group [ 5 ]
            entry [ "rotation_longitude" ] = match_group [ 6 ]
            entry [ "rotation_latitude" ] = match_group [ 7 ]
            entry [ "remote" ] = match_group [ 8 ]
            entry [ "health" ] = match_group [ 9 ]
            entry [ "deaths" ] = match_group [ 10 ]
            entry [ "zombies" ] = match_group [ 11 ]
            entry [ "players" ] = match_group [ 12 ]
            entry [ "score" ] = match_group [ 13 ]
            entry [ "level" ] = match_group [ 14 ]
            entry["steamid"] = match_group[15]
            entry [ "ip" ] = match_group [ 16 ]
            entry [ "ping" ] = match_group [ 17 ]
            self.logger.debug("Entry after: {}".format(entry))
            self.controller.database.blocking_update(
                lp_table,
                entry)
            self.logger.debug("Updated entry." )
        self.logger.debug("returning." )

    def update_online_players_count(self, match_group):
        self.logger.debug(match_group)
        count = int ( match_group [ 0 ] )
        self.online_players_count = count
        if count == 0:
            self.controller.database.blocking_delete(lp_table, [])
            self.server_empty = True
            return
        else:
            self.server_empty = False
            
        answer = self.controller.database.blocking_consult(lp_table, [])
        if len(answer) != self.online_players_count:
            self.logger.debug(
                "Number of online players does not match number of DB entries.")
            self.online_players_changed = True

    def get_online_players(self):
        answer = self.controller.database.blocking_consult(
            lp_table,
            [])
        if len(answer) != self.online_players_count:
            self.logger.warning(
                "Number of online players {} does not match number of DB " \
                "entries {}.".format(self.online_players_count, len(answer)))
        self.online_players = answer
        self.logger.debug("{} players online now.".format(len(self.online_players)))
        return self.online_players

    def log_time_of_day(self, match_group):
        self.day = int(match_group[0])
        self.hour = int(match_group[1])
        self.minute = int(match_group[2])
        if self.day != self.latest_day:
            self.latest_day = self.day
            self.controller.dispatcher.call_registered_callbacks(
                "new day", [self.day, self.hour, self.minute])
        if self.hour != self.latest_hour:
            self.latest_hour = self.hour
            self.logger.info("Day {} {:02}:{:02}".format(
                self.day, self.hour, self.minute))
            self.controller.dispatcher.call_registered_callbacks(
                "new hour", [self.day, self.hour, self.minute])

    def parse_lkp_output(self, match_groups):
        name = match_groups[0]
        player_id = match_groups[1]
        steamid = match_groups[2]
        ip = match_groups[4]
        db = self.controller.database.blocking_consult(
            lkp_table, [(lkp_table.steamid, "==", steamid)])
        if len(db) != 0:
            self.logger.info("lkp output for {} ignored: already on db.".format(
                name))
            return
        self.controller.database.blocking_add(
            lkp_table, [lkp_table(name = name,
                                  player_id = player_id,
                                  steamid = steamid,
                                  ip = ip)])
        self.logger.info("Added lkp_table entry for {}.".format(name))

    # API
        
    def get_player_string(self, name_or_alias):
        self.logger.info("Trying to get player for name or alias '{}'.".format(
            name_or_alias))
        db = self.controller.database.blocking_consult(
            lkp_table, [(lkp_table.name, "==", name_or_alias)])
        if len(db) == 1:
            self.logger.info("Player {} found.".format(db[0]["name"]))
            return db[0]
        if len(db) > 1:
            self.logger.error("Multiple players with name {} on db.".format(
                name_or_alias))
            return None
        self.logger.info("No player with name {} on db.".format(name_or_alias))
        db = self.controller.database.blocking_consult(
            AliasTable, [(AliasTable.alias, "==", name_or_alias)])
        if len(db) > 1:
            self.logger.error("Multiple players with alias {} on db.".format(
                name_or_alias))
            return None
        if len(db) == 0:
            self.logger.warning("No player with alias {} on db.".format(
                name_or_alias))
            return None
        player = self.controller.database.blocking_consult(
            lkp_table, [(lkp_table.steamid, "==", db[0]["steamid"])])[0]
        self.logger.info("Found player {} with alias {}.".format(
            player["name"], name_or_alias))
        return player

    def get_player_steamid(self, steamid):
        self.logger.debug("Trying to find db entry for steamid {}.".format(
            steamid))
        db = self.controller.database.blocking_consult(
            lkp_table, [(lkp_table.steamid, "==", steamid)])
        if len(db) == 1:
            self.logger.debug("DB entry for steamid {} found: {}.".format(
                steamid, db[0]["name"]))
            return db[0]
        else:
            self.logger.warning(
                "Couldn't find single db entry for steamid {}.".format(
                    steamid))
            return None
