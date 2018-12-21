# -*- coding: utf-8 -*-

import inspect
import logging
import re
import sys
import threading
import time

class Parser(threading.Thread):

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)
        
        self.match_string_date = r'([0-9]{4})-([0-9]{2})-([0-9]{2}).+([0-9]{2}):([0-9]{2}):([0-9]{2}) ([+-]*[0-9]+\.[0-9]+)' # 7 groups
        self.match_string_date_simple = r'([\d]{4})-([\d]{2})-([\d]{2}) ([\d]{2}):([\d]{2})' # 5 groups
        self.match_string_ip = r'([\d]+\.[\d]+\.[\d]+\.[\d]+)' # 1 group
        self.match_string_pos = r'\(([-+]*[\d]*\.[\d]), ([-+]*[\d]*\.[\d]), ([-+]*[\d]*\.[\d])\)'
        self.match_prefix = r'^' + self.match_string_date + r' '
        self.matchers = { }
        self.queue = [ ]
        self.queue_lock = None
        self.telnet_output_matchers = {
            'adding observed entity' : self.match_prefix + r'INF Adding observed entity: [\d]+, ' + self.match_string_pos + r', [\d]+$',
#            'AI air drop paths' : self.match_prefix + r'INF AIAirDrop: Computed flight paths for 1 aircraft$',
#            'AI night horde' : self.match_prefix + r'INF AIDirector: Night Horde Spawn Finished \(all mobs spawned\).$',
#            'AI no good spot' : self.match_prefix + r'INF AIDirector: Could not find a valid position to spawn wandering horde \(trying again in 1 hour\)$',
#            'AI scout horde' : self.match_prefix + r'INF AIDirector: scout horde zombie \'\[type=EntityZombie, name=spiderzombie, id=[\d]+\]\' was spawned and is moving towards point of interest\.$',

            'AI scouts' : self.match_prefix + r'INF AIDirector: Spawning scouts @ \(' + self.match_string_pos + r'\) heading towards \(' + self.match_string_pos + r'\)$',
#            'AI scout fail' : self.match_prefix + r'INF AIDirector: Scout spawning failed, FindHordeTargets\(\) returned false!',
            'AI Director Scout Horde Spawn Finished' : self.match_prefix + r'INF AIDirector: Scout Horde Spawn Finished \(all mobs spawned\)\.$',
#            'AI scout remove' : self.match_prefix + r'INF AIDirector: scout horde zombie \'[type=[\w]+, name=[\w]+, id=[\d]+\]\' is being removed from horde control.$',
#                                       'to_call'  : [ ] },
#            'AI scout-trig fin' : self.match_prefix + r'INF AIDirector: Scout-Triggered Horde Finished \(all mobs spawned\).$',
#                                       'to_call'  : [ ] },
            'AI wanderer' : self.match_prefix + r'INF AIDirector: wandering horde zombie \'[type=[\w]+, name=[\w]+, id=[\d]+\]\' was spawned and is moving towards pitstop.$',
#            'AI wander finish' : self.match_prefix + r'INF AIDirector: Wandering Horde Spawn Finished \(all mobs spawned\)\.$',
#                                       'to_call'  : [ ] },
            'AI wanderer player' : self.match_prefix + r'INF AIDirector: Spawning wandering horde moving towards player \'\[type=EntityPlayer, name=.*, id=[\d]+\]\'$',
            'AI wander remove' : self.match_prefix + r'INF AIDirector: wandering horde zombie \'[type=[\w]+, name=[\w]+, id=[\d]+\]\' is being removed from horde control.$',
            'AI wander stop' : self.match_prefix + r'INF AIDirector: wandering horde zombie \'\[type=.*, name=.*, id=[\d]+\]\' has wandered long enough and is going to endstop now.$',
            'AI wander trouble' : self.match_prefix + r'INF AIDirector: wandering horde zombie \'\[type=.*, name=.*, id=[\d]+\]\' reached pitstop and will wander around for awhile looking for trouble.$',
#            'allowing player' : self.match_prefix + r'INF Allowing player with id [\d]+$',
#                                       'to_call'  : [ ] },
#            'behaviour' : r'The referenced script on this Behaviour is missing!$',
#                                       'to_call'  : [ ] },
#            'biome animal' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ AnimalsAll_Any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome animalSmall' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'AnimalsSmall_Any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome animalSmall zom' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'AnimalsSmall_Any: c=[\d]+/r=[\d]+ ZombiesAll_Any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome ani zom' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'AnimalsAll_Any: c=[\d]+/r=[\d]+ ZombiesAll_Any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome ani zom snow' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'AnimalsAll_Any: c=[\d]+/r=[\d]+ SnowZombies_Any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome sani zom' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'AnimalsSmall_Any: c=[\d]+/r=[\d]+ ZombiesAll_any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome snowzom' : self.match_prefix + r'INF BiomeSpawnManager spawned' + \
#                                      r' [\w\d]+ pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                      r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ SnowZombies_Any: c=[\d]+/r=[\d]+$',
#                                      'to_call'  : [ ] },

            "biome spawn manager" : self.match_prefix + r"INF BiomeSpawnManager spawned (.*)$",

#            'biomed zom' : self.match_prefix + r'INF BiomeSpawnManager spawned' + \
#                                      r' [\w\d]+ pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                      r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ZombiesAll_Any: c=[\d]+/r=[\d]+$',
#                                      'to_call'  : [ ] },
#            'biome zom ani' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'ZombiesAll_Any: c=[\d]+/r=[\d]+ AnimalsAll_Any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome zom ani snow' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'SnowZombies_Any: c=[\d]+/r=[\d]+ AnimalsAll_Any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome zom small ani' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'ZombiesAll_Any: c=[\d]+/r=[\d]+ AnimalsSmall_Any: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome waste day' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'ZombiesWasteland_Day: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome waste day night' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'ZombiesWasteland_Day: c=[\d]+/r=[\d]+ ZombiesWastelandNight_Night: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome waste night' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'ZombiesWastelandNight_Night: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'biome waste nit day' : self.match_prefix + r'INF BiomeSpawnManager spawned ' + \
#                                       r'.* pos=' + self.match_string_pos + r' id=[\d]+ CBD=BiomeId' + \
#                                       r'=[\d]+ XZ=[+-]*[\d]+/[+-]*[\d]+ ' + \
#                                       r'ZombiesWastelandNight_Night: c=[\d]+/r=[\d]+ ZombiesWasteland_Day: c=[\d]+/r=[\d]+$',
#                                       'to_call'  : [ ] },
#            'chunks saved' : r'.* INF Saving (.*) of chunks took (.*)ms',
#                                       'to_call'  : [ ] },
#            'claim finished' : r'Total of ([\d]+) keystones in the game',
#                                       'to_call'  : [ self.framework.world_state.buffer_claimstones ] },
#            'claim player' : r'Player ".* \(([\d]+)\)" owns ([\d]+) ' + \
#                                       r'keystones \(protected: [\w]+, current hardness multiplier: [\d]+\)',
#                                       'to_call'  : [ self.framework.world_state.buffer_claimstones ] },
#            'claim stone' : r'\(([-+]*[\d]*), ([-+]*[\d]*), ([-+]*[\d]*)\)$',
#                                       'to_call'  : [ self.framework.world_state.buffer_claimstones ] },
            "existing connection closed" : r"SocketException: An existing connection was forcibly closed by the remote host.",
#            'couldnt RPC' : r'^Couldn\'t send RPC function \'RPC_RawData\'$',
#                                       'to_call'  : [ ] },
#            'created new player' : self.match_prefix + r'INF Created new player entry for' + \
#                                       r' ID: [\d]+$',
#                                       'to_call'  : [ ] },
#            'deny match' : r'(.*) INF Player (.*) denied: ' + \
#                                       r'(.*) has been banned until (.*)',
#                                       'to_call'  : [ self.framework.game_events.player_denied ] },
#            'denying command' : self.match_prefix + r'INF Denying command \'gg (.*)\' from client (.*)$',
#                                       'to_call'  : [ self.framework.server.console_command ] },
#            'EAC backend conn' : self.match_prefix + r'INF \[EAC\] Log: Backend connection established\.$',
#                                       'to_call'  : [ ] },
#            'EAC callback' : self.match_prefix + r'INF \[EAC\] UserStatusHandler callback.'+\
#                                       r' Status: UserAuthenticated GUID: [\d]+ ReqKick: [\w]+ Message:.*$',
#                                       'to_call'  : [ ] },
            "EAC Cerberus" : self.match_prefix + r"WRN \[EAC\] Log: \[Cerberus\] Connection attempt to the back-end failed! Reconnecting in 60 seconds\.\.",
#            'EAC free user' : r'INF \[EAC\] FreeUser \(.*\)',
#                                       'to_call'  : [ ] },
#            'EAC kicking player' : self.match_prefix + r'Kicking player: Kicked by EAC. ' + \
#                                       r'Please check if you started the game with AntiCheat protection ' + \
#                                       r'software enabled$',
#                                       'to_call'  : [ ] },
#            'EAC log conn lost' : self.match_prefix + r'INF \[EAC\] Log: User EAC client connection lost: [\d]+$',
#                                       'to_call'  : [ ] },
#            'EAC log dconn' : self.match_prefix + r'INF \[EAC\] Log: User without EAC connection: [\d]+. User status: Disconnected$',
#                                       'to_call'  : [ ] },
#            'EAC Auth' : self.match_prefix + r'INF \[Steamworks\.NET\] Authenticating player: [\w]+ SteamId: [\d]+ TicketLen: [\d]+ Result: k_EBeginAuthSessionResultOK$',
#                                       'to_call'  : [ ] },
#            'EAC package' : self.match_prefix + r'ERR \[Steamworks\.NET\] NET: Could not send package to client [\d]+$',
#                                       'to_call'  : [ ] },
#            'EAC status change' : self.match_prefix + r'INF \[EAC\] Log: User status changed' + \
#                                       r': [\d]+. Status: Authenticated Message: N/A$',
#                                       'to_call'  : [ ] },
#            'EAC unregister' : self.match_prefix + r'INF \[EAC\] Log: User unregistered. GUID: [\d]+$',
#                                       'to_call'  : [ ] },
#            'empty line' : r'^$',
#                                       'to_call'  : [ ] },
#            'ERROR' : r'\*\*\* ERROR: unknown command \'(.*)\'',
#                                       'to_call'  : [ self.output_guard_error] },

# 2016-01-02T15:48:48 52857.460 INF Executing command \'say "[SDTP] Seven Days To Py: stopped."\' by Telnet from 90.37.160.230:55130'
            "executing command" : self.match_prefix + r"INF Executing command \'(.*)\' by Telnet from " + self.match_string_ip + r":[\d]+$",
#            'executing cmd give' : self.match_prefix + r'INF Executing command \'give ' + \
#                                       r'[\d]+ [\w\d]+ [\d]+\' by Telnet from ' + self.match_string_ip + \
#                                       r':[\d]+$',
#                                       'to_call'  : [ ] },
#            'executing cmd lkp' : self.match_prefix + r'INF Executing command \'lkp\' by Telnet from ' + self.match_string_ip + r':[\d]+$',
#                                       'to_call'  : [ ] },
#            'executing cmd se' : self.match_prefix + r'INF Executing command \'se ' + \
#                                       r'[\d]+ [\d]+\' by Telnet from ' + self.match_string_ip + \
#                                       r':[\d]+$',
#                                       'to_call'  : [ ] },
#            'executing version' : self.match_prefix + r'INF Executing command \'version\' from client [\d]+$',
#                                       'to_call'  : [ ] },
#            'failed set triangles' : r'Failed setting triangles. Some indices are referencing out of bounds vertices. IndexCount: [\d]+, VertexCount: [\d]+$',
#                                       'to_call'  : [ ] },
#            'failed extract' : r'Failed to extract collision data: Submesh [\d]+ uses unsupported primitive type "Unknown type". Please use either "TriangleStrip" or "Triangles". Mesh asset path "" Mesh name ""$',
#                                       'to_call'  : [ ] },
#            'failed mesh' : r'Failed getting triangles. Submesh [\d]+ has no indices. Mesh asset path "" Mesh name ""$',
#                                       'to_call'  : [ ] },
#            'falling tree' : r'^[\d]+. id=[\d]+, FallingTree_[\d]+' + \
#                                       r' \(EntityFallingTree\), pos=' +self.match_string_pos + r', rot=' + \
#                                       self.match_string_pos + r', lifetime=[\d]+\.[\d]+, remote=[\w]+, ' + \
#                                       r'dead=[\w]+,$',
#                                       'to_call'  : [ self.framework.game_events.tree_felled ] }, 
#            'fell off world' : self.match_prefix + r'WRN Entity \[type=.*, name=.*' +\
#                                       r', id=[\d]+\] fell off the world, id=[\d]+ pos=' + \
#                                       self.match_string_pos + r'$',
#                                       'to_call'  : [ ] },
#            'block fell off' : self.match_prefix + r'WRN Entity FallingBlock_[\d]+ \(EntityFallingBlock\) fell off the world, id=[\d]+ pos=' + self.match_string_pos + r'$',
#                                       'to_call'  : [ ] },
#            'could not save file' : self.match_prefix + r'ERR Could not save file \'.*\': Sharing violation on path .*$',
#                                       'to_call'  : [ ] },
#            'item fell off' : self.match_prefix + r'WRN Entity Item_([\d]+) \(EntityItem\) ' + \
#                                       r'fell off the world, id=([\d]+) pos=' + self.match_string_pos + r'$',
#                                       'to_call'  : [ ] },
            'chat message (pre A14)' : self.match_string_date + r' INF GMSG: (.*: .*)$',
            'chat message' : self.match_string_date + r' INF Chat: (.*: .*)$',
            # 0 - 6. date
            # 7. message
#                                       'to_call'  : [ self.advise_deprecation_chat ] },
#            'gt command executing' : self.match_string_date + \
#                                       r' INF Executing command \'gt\' by Telnet from ' + \
#                                       self.match_string_ip + ':([\d]+)',
#                                       'to_call'  : [ self.framework.server.update_server_time ] },
#            'gt command output' : r'Day ([0-9]+), ([0-9]{2}):([0-9]{2})',
#                                       'to_call'  : [ self.framework.world_state.process_gt ] },

            'header  0' : r'^\*\*\* Connected with 7DTD server\.$',

            'header  1' : r'^\*\*\* Server version: Alpha [\d]+\.[\d]+ \(.*\) Compatibility Version: Alpha [\d]+\.[\d]+.*$',
            'header  2' : r'^\*\*\* Dedicated server only build$',
            'header  3' : r'^Server IP:   ' + self.match_string_ip + r'$',
            'header server ip any' : r'^Server IP:   Any$',
            'header  4' : r'^Server port: [\d]+$',
            'header  5' : r'^Max players: [\d]+$',
            'header  6' : r'^Game mode:   GameModeSurvivalMP$',
            'header  7' : r'^World:       Random Gen$',
            'header  8' : r'Game name:   (.*)$',
            'header  9' : r'^Difficulty:  [\d]+$',
            'header 10' : r'Press \'help\' to get a list of all commands\. Press \'exit\' to end session.',
#            'icon nof found' : self.match_prefix + r'INF Web:IconHandler:FileNotFound: ".*"$',
#                                       'to_call'  : [ ] },
#            'static not found' : self.match_prefix + r'INF Web:Static:FileNotFound: ".*" @ ".*"$',
#                                       'to_call'  : [ ] },
#            'instantiate' : self.match_prefix + r'WRN InstantiateEntities: ignoring [\d]+ as it is already added\.$',
#                                       'to_call'  : [ ] },
#            'inventory belt/bag' : r'([\w]+) of player (.*):$',
#                                       'to_call'  : [ self.framework.world_state.update_inventory ] },
#            'inventory item' : r'^Slot ([\d]+): ([\d]+) \* (.*)$',
#                                       'to_call'  : [ self.framework.world_state.update_inventory ] },
            'IOException readline' : self.match_prefix + r'ERR IOException in ReadLine: Read failure$',
            'ERR telnet' : self.match_prefix + r'ERR ReadLine for TelnetClientReceive_.*: Read failure$',
            'IOException telnet' : self.match_prefix + r'ERR IOException in ReadLine for TelnetClientReceive_.*: Read failure$',
            'IOException sharing' : r'IOException: Sharing violation on path .*',
#            'item dropped' : r'^Dropped item$',
#                                       'to_call'  : [ ] },
#            'kicking executing' : self.match_prefix + r'INF Executing command \'kick' + \
#                                       r' [\d]+ .*\' by Telnet from ' + self.match_string_ip + r':[\d]+$',
#                                       'to_call'  : [ ] },
#            'kicking player' : self.match_prefix + r'INF Kicking player: .*$',
#                                       'to_call'  : [ ] },
#            'gg executing' : self.match_prefix + r'INF Executing command \'gg (.*)\' from client ([\d]+)$',
#                                       'to_call'  : [ self.admin_command_mod ] },
#            'le command executing' : self.match_string_date + \
#                                       r' INF Executing command \'le\' by Telnet from ' + \
#                                       self.match_string_ip + ':([\d]+)',
#                                       'to_call'  : [ ] },
#            'le output' : r'^[\d]+\. id=([\d]+), \[type=[\w]+, name=(.*),' +\
#                                       r' id=[\d]+\], pos=' + self.match_string_pos + r', rot=' + \
#                                       self.match_string_pos + r', lifetime=(.*), remote=([\w]+),' + \
#                                       r' dead=([\w]+), health=([\d]+)',
#                                       'to_call'  : [ self.framework.world_state.buffer_le ] },
#            'le item output' : r'^[\d]+\. id=([\d]+), Item_[\d]+ \(EntityItem\), ' + \
#                                       r'pos=' + self.match_string_pos + r', rot=' + \
#                                       self.match_string_pos + r', lifetime=(.*), remote=([\w])+,' + \
#                                       r' dead=([\w]+),$',
#                                       'to_call'  : [ ] },
#            'le falling output' : r'^[\d]+\. id=([\d]+), FallingBlock_[\d]+ \(EntityFallingBlo' +\
#                                       r'ck\), pos=' + self.match_string_pos + r', rot=' + self.match_string_pos + \
#                                       r', lifetime=(.*), remote=([\w])+, dead=([\w]+),$',
#                                       'to_call'  : [ ] },
#            'lkp output' : r'[\d]+\. (.*), id=([\d]+), steamid=([\d]+), online=([\w]+), ip=(.*), playtime=([\d]+) m, seen=' + self.match_string_date_simple + '$',
#                                       'to_call'  : [ self.framework.server.lkp_output_parser ] },
#            'lkp total' : r'Total of [\d]+ known$',
#                                       'to_call'  : [ ] },
#            'llp executing' : r'^' + self.match_string_date + r' INF Executing ' + \
#                                       r'command \'llp\' by Telnet from ' + self.match_string_ip + r':[\d]+$',
#                                       'to_call'  : [ ] },
#            'loglevel executing' : r'^' + self.match_string_date + r' INF Executing ' + \
#                                       r'command \'loglevel [\w]{3} [\w]+\' by Telnet from ' + \
#                                       self.match_string_ip + r':[\d]+$',
#                                       'to_call'  : [ ] },
#            'loglevels enable' : r'^[\w]+abling all loglevels on this connection.$',
#                                       'to_call'  : [ ] },
#            'lp command executing' : self.match_string_date + \
#                                       r' INF Executing command \'lp\' by Telnet from ' + \
#                                       self.match_string_ip + ':([\d]+)',
#                                       'to_call'  : [ ] },
            # 0 id
            # 1 name
            # 2, 3, 4 pos
            # 5, 6, 7 rot
            # 8 remote
            # 9 health
            # 10 deaths
            # 11 zombies
            # 12 players
            # 13 score
            # 14 level
            # 15 steamid
            # 16 ip
            # 17 ping
            'lp output' : r'^[\d]+\. id=([\d]+), (.*), pos=' + self.match_string_pos + r', rot=' + self.match_string_pos + r', remote=([\w]+), health=([\d]+), deaths=([\d]+), zombies=([\d]+), players=([\d]+), score=([\d]+), level=([\d]+), steamid=([\d]+), ip=' + self.match_string_ip + r', ping=([\d]+)',
            
            'le/lp output footer' : r'^Total of ([\d]+) in the game$',
            
            'mem output' : r'[0-9]{4}-[0-9]{2}-[0-9]{2}.* INF Time: ([0-9]+.[0-9]+)m FPS: ([0-9]+.[0-9]+) Heap: ([0-9]+.[0-9]+)MB Max: ([0-9]+.[0-9]+)MB Chunks: ([0-9]+) CGO: ([0-9]+) Ply: ([0-9]+) Zom: (.*) Ent: ([\d]+) \(([\d]+)\) Items: ([0-9]+)',
            
#            'message player' : r'Message to player ".*" sent with sender "Server"',
#                                       'to_call'  : [ ] },
#            'not found' : r'^Playername or entity ID not found.$',
#                                       'to_call'  : [ ] },
            "password incorrect" : r"^Password incorrect, please enter password:$",
#            'player created' : self.match_prefix + r'INF Created player with id=([\d]+)$',
#                                       'to_call'  : [ self.framework.game_events.player_created ] },
#            'player joined' : self.match_prefix + 'INF GMSG: .* joined the game',
#                                       'to_call'  : [ ] },
#            'player kicked' : self.match_prefix + r'INF Executing command \'kick [\d]+\'' + \
#                                       r' by Telnet from ' + self.match_string_ip + ':[\d]+$',
#                                       'to_call'  : [ ] },
#            'playerlogin' : self.match_prefix + r'INF PlayerLogin: .*/Alpha [\d]+\.[\d]+$',
#                                       'to_call'  : [ ] },
#            'playername not found' : r'^Playername or entity/steamid id not found$',
#                                       'to_call'  : [ ] },
#            'player offline' : self.match_prefix + r'INF Player set to offline: [\d]+$',
#                                       'to_call'  : [ ] },
#            'player online' : self.match_prefix + r'INF Player set to online' + \
#                                       r': ([\d]+)$',
#                                       #'to_call'  : [ self.framework.server.set_steamid_online ] },
#                                       'to_call'  : [ self.framework.game_events.player_connected ] },
#            'player connected' : self.match_prefix + r'INF Player connected, entityid=[\d]+, ' +\
#                                       r'name=.*, steamid=[\d]+, ip=' + self.match_string_ip + r'$',
#                                       'to_call'  : [ ] },
#            'player disconnected' : self.match_prefix + r'INF Player disconnected: EntityID=' + \
#                                       r'-*[\d]+, PlayerID=\'[\d]+\', OwnerID=\'[\d]+\', PlayerName=\'.*\'$',
#                                       'to_call'  : [ ] },
#            'player cdonn after' : self.match_prefix + r'INF Player .* disconnected after [\d]+\.[\d] minutes$',
#                                       'to_call'  : [ ] },
#            'player disconn error' : self.match_prefix + r'ERR DisconnectClient: Player ' + \
#                                       r'[\d]+ not found$',
#                                       'to_call'  : [ ] },
#            'player dconn NET' : self.match_prefix + r'INF \[NET\] Player disconnected: ' + \
#                                       r'EntityID=' + \
#                                       r'-*[\d]+, PlayerID=\'[\d]+\', OwnerID=\'[\d]+\', PlayerName=\'.*\'$',
#                                       'to_call'  : [ ] },
#            'player dconn NET2' : self.match_prefix + r'INF \[NET\] PlayerDisconnected ' + \
#                                       r'EntityID=' + \
#                                       r'-*[\d]+, PlayerID=\'([\d]+)\', OwnerID=\'[\d]+\', PlayerName=\'(.*)\'$',
#                                       'to_call'  : [ self.framework.game_events.player_disconnected ] },
#            'player died' : self.match_prefix + r'INF GMSG: Player (.*) died$',
#                                       'to_call'  : [ self.framework.game_events.player_died ] },
#            'player kill' : self.match_prefix + r'INF GMSG: Player (.*)' + \
#                                       r' eliminated Player (.*)',
#                                       'to_call'  : [ self.framework.game_events.player_kill ] },
            'player left' : self.match_prefix + r'INF GMSG: (.*) left the game$',
#            'player login' : self.match_prefix + r'INF PlayerLogin: .*/Alpha 11\.6$',
#                                       'to_call'  : [ ] },
#            'player req spawn' : self.match_prefix + r'INF RequestToSpawnPlayer: [\d]+, ' + \
#                                       r'.*, [\d]+$',
#                                       'to_call'  : [ ] },
#            'pm executing' : r'^' + self.match_string_date + r' INF Executing command' + \
#                                       r' \'pm (.*) (.*)\' by Telnet from ' + self.match_string_ip + r':[\d]+$',
#                                       'to_call'  : [ self.command_pm_executing_parser ] },
#            'registering player' : self.match_prefix + r'INF \[EAC\] Registering user: id=[\d]+,'+\
#                                       r' owner=[\d]+$',
#                                       'to_call'  : [ ] },

            'removing entity' : self.match_prefix + r'INF Removing observed entity [\d]+',

#            'request to enter' : self.match_prefix + r'INF RequestToEnterGame: [\d]+/.*$',
#                                       'to_call'  : [ ] },
#            'saveworld' : r'^' + self.match_string_date + r' INF Executing ' + \
#                                       r'command \'saveworld\' by Telnet from ' + self.match_string_ip + r':[\d]+$',
            "server disconnect" : self.match_string_date + r"INF Disconnect",
#                                       'to_call'  : [ ] },
#            'si command executing' : self.match_string_date + \
#                                       r' INF Executing command \'si [\d]+\' by Telnet from ' + \
#                                       self.match_string_ip + ':([\d]+)',
#                                       'to_call'  : [ ] },
#            'say executing' : self.match_string_date + \
#                                       r' INF Executing command \'say ".*"\' by Telnet from ' + \
#                                       self.match_string_ip + ':([\d]+)',
#                                       'to_call'  : [ ] },
#            'socket exception' : self.match_prefix + r'SocketException: An established connection was aborted by the software in your host machine.',
#                                       'to_call'  : [ ] },
#            'spawn feral horde' : self.match_prefix + r'INF Spawning Feral Horde\.$',
#                                       'to_call'  : [ ] },
#            'spawn night horde' : r'^' + self.match_string_date + \
#                                       r' INF Spawning Night Horde for day [\d]+',
#                                       'to_call'  : [ ] },
            'spawn wander horde' : self.match_prefix + r'INF Spawning Wandering Horde.$',
            'spawned' : r'^' + self.match_string_date + r' INF Spawned \[type=[\w]+, name=(.*), id=[\d]+\] at ' + self.match_string_pos + r' Day=[\d]+ TotalInWave=[\d]+ CurrentWave=[\d]+$',

#            'spawn ent wrong pos' : self.match_prefix + r'WRN Spawned entity with wrong pos: Item_([\d]+) \((EntityItem)\) id=([\d]+) pos=' + self.match_string_pos + r'$',
#                                       'to_call'  : [ self.framework.world_state.buffer_shop_item ] },
#            'spawn output' : r'^Spawned [\w\d]+$',
#                                       'to_call'  : [ ] },
            'spider spawn horde' : self.match_prefix + r'INF Spider scout spawned a zombie horde!$',
#            'steam auth ()' : self.match_prefix + r'INF \[Steamworks.NET\] Auth\.' + \
#                                       r'AuthenticateUser\(\)$',
#                                       'to_call'  : [ ] },
#            'steam auth' : self.match_prefix + r'INF \[Steamworks\.NET\] Authent' + \
#                                       r'icating player: .* SteamId: [\d]+ TicketLen: [\d]+ Result: ' + \
#                                       r'k_EBeginAuthSessionResultOK$',
#                                       'to_call'  : [ ] },
#            'steam auth callback' : self.match_prefix + r'INF \[Steamworks.NET\] ' + \
#                                       r'Authentication callback\. ID: [\d]+, owner: [\d]+, result: .*$',
#                                       'to_call'  : [ ] },
#            'steam drop client' : self.match_prefix + r'INF \[Steamworks\.NET\] NET: Dropping client: [\d]+$',
#                                       'to_call'  : [ ] },
#            'steam kick' : self.match_prefix + r'INF \[Steamworks\.NET\] Kick player for invalid login: [\d]+ .*$',
#                                       'to_call'  : [ ] },
#            'steam player connect' : self.match_prefix + r'INF \[NET\] PlayerConnected ' + \
#                                       r'EntityID=-1, PlayerID=\'\', OwnerID=\'\', PlayerName=\'\'$',
#                                       'to_call'  : [ ] },
#            'supply crate' : self.match_prefix + r'INF AIAirDrop: Spawned supply ' + \
#                                       r'crate @ \(' + self.match_string_pos + r'\)$',
#                                       'to_call'  : [ ] },
#            'supply plane' : r'[\d]+\. id=[\d]+, GameObject (EntitySupplyPlane), pos=' +\
#                                       self.match_string_pos + r', rot=' + self.match_string_pos + \
#                                       r', lifetime=float.Max, remote=False, dead=False,$',
#                                       'to_call'  : [ ] },
            'telnet closed' : self.match_prefix + r'INF Telnet connection closed: ' + self.match_string_ip + r':[\d]+$',
#            'wave spawn' : r'^' + self.match_string_date + r' INF Spawning this wave:' +\
#                                       r' ([\d]+)',
#                                       'to_call'  : [ ] },
#            'wave start' : r'^' + self.match_string_date + r' INF Start a new wave ' + \
#                                       r'\'[\w]+\'\. timeout=[\d]+s$',
#                                       'to_call'  : [ ] },
#            'telnet conn block' : self.match_prefix + r'INF Telnet connection closed for too many login attempts: ' + self.match_string_ip + ':[\d]+$',
#                                       'to_call'  : [ ] },
            'telnet conn from' : self.match_prefix + r'INF Telnet connection from: ' + self.match_string_ip + ':[\d]+$',
            'telnet thread exit' : '^' + self.match_string_date + r' INF Exited thread TelnetClient[\w]+_' + self.match_string_ip + r':[\d]+$',
            'telnet thread start r' : '^' + self.match_string_date + r' INF Started thread TelnetClientReceive_' + self.match_string_ip + r':[\d]+$',
            'telnet thread start s' : '^' + self.match_string_date + r' INF Started thread TelnetClientSend_' + self.match_string_ip + r':[\d]+$',
            "telnet client send error" : self.match_prefix + r"ERR Error in TelnetClientSend_.*",
#            'token length' : self.match_prefix + r'INF Token length: [\d]+$',
#                                       'to_call'  : [ ] },
#            'tp command executing' : self.match_string_date + \
#                                       r' INF Executing command \'teleportplayer ([\d]+) ([+-]*[\d]+) ' + \
#                                       r'([+-]*[\d]+) ([+-]*[\d]+)\' by Telnet from ' + \
#                                       self.match_string_ip + ':([\d]+)',
#                                       'to_call'  : [ ] },
#            'version' : r'^' + self.match_string_date + r' INF Executing ' + \
#                                       r'command \'version\' by Telnet from ' + self.match_string_ip + r':[\d]+$',
#                                       'to_call'  : [ ] },
#            'exception sharing' : r'IOException: Sharing violation on path .*',
#                                       'to_call'  : [ self.framework.quiet_listener ] },
        }
        
        # must run after self.telnet_output_matchers is defined
        self.logger.debug("parser.init: compile telnet_output_matchers" )
        for key in self.telnet_output_matchers.keys ( ):
            self.matchers [ key ] = re.compile ( self.telnet_output_matchers [ key ] )

    def run ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.logger.info(prefix + " ( )" )
        
        while ( self.keep_running ):
            line = self.dequeue ( )
            if line [ "text" ]  == "":
                continue
            self.logger.debug(prefix + " line = {}".format ( line ) )
            if type ( line [ "text" ] ) != str:
                self.logger.debug(prefix + " type ( line [ 'text' ] ) = {}".format ( type ( line [ "text" ] ) ) )
                try:
                    line [ "text" ] = bytes ( line [ "text" ] )
                except Exception as e:
                    self.logger.error("Unable to cast to bytes." )
                    return
            any_match = False
            for key in self.matchers.keys ( ):
                match = self.matchers [ key ].search ( line [ 'text' ] )
                if match:
                    any_match = True
                    matched_key = key
                    match_timestamp = time.time ( )
                    self.logger.debug("key '{}', match.groups = '{}'.".format ( key, match.groups ( ) ) )
                    self.controller.dispatcher.call_registered_callbacks ( key, match.groups ( ) )

            if not any_match:
                try:
                    self.logger.info("Unparsed output: '{}'.".format ( line [ "text" ] ) )
                except UnicodeEncodeError as e:
                    self.logger.error("UnicodeEncodeError: {}".format ( e ) )
                continue

    def stop ( self ):
        self.keep_running = False

    # API

    def enqueue ( self, text ):
        self.lock_queue ( )
        self.queue.append ( { 'text'      : text,
                              'timestamp' : time.time ( ) } )
        self.unlock_queue ( )

    # \API

    def dequeue ( self ):
        while ( not self.controller.telnet_ongoing ):
            if not self.keep_running:
                return { 'text' : "", "timestamp" : time.time ( ) }
            time.sleep ( 1 )
        self.lock_queue ( )
        while len ( self.queue ) < 1:
            self.unlock_queue ( )
            if not self.keep_running:
                return { 'text' : "", "timestamp" : time.time ( ) }
            time.sleep ( 0.1 )
            self.lock_queue ( )
        popped = self.queue.pop ( 0 )
        self.unlock_queue ( )
        return popped
        
    def lock_queue ( self ):
        callee_class = inspect.stack ( ) [ 1 ] [ 0 ].f_locals [ 'self' ].__class__.__name__
        callee = inspect.stack ( ) [ 1 ] [ 0 ].f_code.co_name
        begin = time.time ( )
        while self.queue_lock:
            self.logger.debug("{}.{} wants parser queue lock from {}.".format (
                callee_class, callee, self.queue_lock ) )
            time.sleep ( 0.01 )
            if time.time ( ) - begin > 60:
                break
        self.queue_lock = callee_class + "." + callee
        #self.logger.debug("{:s} got parser queue lock.".format ( callee ) )

    def unlock_queue ( self ):
        callee = inspect.stack ( ) [ 1 ] [ 0 ].f_code.co_name
        self.queue_lock = None
        #self.logger.debug("{:s} unlocked the parser queue.".format ( callee ) )
        
