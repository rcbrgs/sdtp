# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import signal
import subprocess
import threading
import time

from sdtp.lkp_table import lkp_table

class BiomeLoadHang(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_biomeloadhang_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
            self.check_for_hangup()
        self.tear_down()
            
    def stop(self):
        self.logger.info("Stop.")
        self.keep_running = False

    def setup(self):
        self.countdown_start = 0
        self.in_countdown = False
        self.controller.dispatcher.register_callback(
            "loading biomes", self.start_countdown)
        self.controller.dispatcher.register_callback(
            'Steamworks.NET GameServer.Logon success', self.stop_countdown)

    def tear_down(self):
        self.controller.dispatcher.deregister_callback(
            "loading biomes", self.start_countdown)
        self.controller.dispatcher.deregister_callback(
            'Steamworks.NET GameServer.Logon success', self.stop_countdown)
        
    # Mod specific
    ##############
    
    def start_countdown(self, match_groups):
        self.countdown_start = time.time()
        self.in_countdown = True
        self.logger.info("Starting countdown to detect load biome hang-up.")

    def stop_countdown(self, match_groups):
        self.countdown_start = 0
        self.in_countdown = False
        self.logger.info("Stopping countdown to detect load biome hang-up.")

    def check_for_hangup(self):
        if not self.in_countdown:
            return
        if time.time() - self.countdown_start >= self.controller.config.values[
                "mod_biomeloadhang_countdown"]:
            self.controller.telnet.write("shutdown")
            self.logger.warning("Load biome hangup detected, shutdown initiated.")
            self.stop_countdown([])

            if not self.controller.config.values["mod_biomeloadhang_kill"]:
                return
            self.logger.info("Attempting to kill a local server that won't shutdown.")
            time.sleep(5)
            process = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
            out, err = process.communicate()
            for line in out.splitlines():
                if b"7DaysToDieServer" in line:
                    pid = int(line.split(None, 1)[0])
                    os.kill(pid, signal.SIGKILL)
                    self.logger.warning("Sent a signal.SIGKILL to pid {}.".format(pid))
