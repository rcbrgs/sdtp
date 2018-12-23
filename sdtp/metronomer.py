# -*- coding: utf-8 -*-

import logging
import sys
import threading
import time

class Metronomer(threading.Thread):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

    def run ( self ):
        now = time.time ( )
        latest_lp = now - self.controller.config.values [ "lp_interval" ] + 5
        while ( self.keep_running ):
            time.sleep ( 0.1 )
            old = now
            now = time.time ( )
            if ( now - latest_lp > self.controller.config.values [ "lp_interval" ] ):
                latest_lp = now
                if self.controller.telnet.ready:
                    self.controller.telnet.write ( "lp" )
                    self.controller.world_state.get_online_players()

    def stop ( self ):
        self.keep_running = False
