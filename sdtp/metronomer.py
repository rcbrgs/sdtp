# -*- coding: utf-8 -*-

import logging
import sys
import threading
import time

from sdtp.lp_table import lp_table

class Metronomer(threading.Thread):
    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run ( self ):
        self.logger.info("Start.")
        now = time.time ( )
        latest_gt = now - self.controller.config.values ["gt_interval"] + 5
        latest_lp = now - self.controller.config.values ["lp_interval"] + 5
        latest_llp = now - self.controller.config.values["llp_interval"] / 2
        while ( self.keep_running ):
            time.sleep ( 0.1 )
            old = now
            now = time.time ( )
            if(now - latest_llp > self.controller.config.values["llp_interval"]):
                latest_llp = now
                if self.controller.telnet.ready:
                    self.controller.telnet.write("llp", lock_after_write = True)
                    # Lock will be released by mod claim_alarm.
            if(now - latest_lp > self.controller.config.values["lp_interval"]):
                latest_lp = now
                self.controller.worldstate.get_online_players()
                self.controller.database.delete(lp_table, [], print)
                if self.controller.telnet.ready:
                    self.controller.telnet.write("lp")
            if(now - latest_gt > self.controller.config.values["gt_interval"]):
                latest_gt = now
                if self.controller.telnet.ready:
                    self.controller.telnet.write ( "gt" )

    def stop ( self ):
        self.keep_running = False
        self.logger.info("Stop.")
