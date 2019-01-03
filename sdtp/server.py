# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import logging
import re
import threading
import time

import sdtp

class Server(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
        self.tear_down()
            
    def stop ( self ):
        self.keep_running = False
        self.logger.info("Stop.")

    def setup(self):
        pass
    
    def tear_down(self):
        pass
    
    # Component specific
    ####################

    def pm(self, player, message):
        if self.controller.telnet.ready:
            self.controller.telnet.write('pm {} "{}"'.format(
                player["steamid"], message))
            self.logger.info('pm {} "{}"'.format(
                player["name"], message))
        else:
            self.logger.error("Telnet not ready when trying to PM.")
