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
        self.setup()
        now = time.time ( )
        latest_gt = now - self.controller.config.values ["interval_gt"] / 2
        latest_lp = now - self.controller.config.values ["interval_lp"] / 2
        latest_lkp = now - self.controller.config.values["interval_lkp"] / 2
        latest_llp = now - self.controller.config.values["interval_llp"] / 2
        latest_tick = now - self.controller.config.values["interval_tick"] / 2
        while(self.keep_running):
            time.sleep(0.1)
            old = now
            now = time.time()
            if(now - latest_gt > self.controller.config.values["interval_gt"]):
                latest_gt = now
                if self.controller.telnet.ready:
                    self.controller.telnet.write("gt")
            if(now - latest_lkp > self.controller.config.values["interval_lkp"]):
                latest_lkp = now
                if self.controller.telnet.ready:
                    self.controller.telnet.write("lkp")
            if(now - latest_llp > self.controller.config.values["interval_llp"]):
                latest_llp = now
                if self.controller.telnet.ready:
                    self.controller.telnet.write("llp", lock_after_write = True)
                    # Lock will be released by mod claim_alarm.
            if(now - latest_lp > self.controller.config.values["interval_lp"]):
                latest_lp = now
                if self.controller.telnet.ready:
                    self.controller.telnet.write("lp")
            if(now - latest_tick > self.controller.config.values["interval_tick"]):
                latest_tick = now
                if self.controller.worldstate.server_empty:
                    if self.controller.telnet.ready:
                        self.controller.telnet.write('say "Tick"')
        self.tear_down()

    def stop(self):
        self.keep_running = False
        self.logger.info("Stop.")

    def setup(self):
        pass

    def tear_down(self):
        pass
