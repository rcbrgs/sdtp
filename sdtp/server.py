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
        self.normal_zombies = [4, 8, 11, 14, 17, 20, 27, 30, 33, 36, 41,
                               44, 46, 49, 50, 52, 57, 58, 61, 64, 67, 70,
                               73, 76, 78]
        self.special_zombies = [7, 24, 54]
        self.feral_zombies = [2, 5, 9, 12, 15, 18, 21, 25, 28, 31, 34, 37, 40,
                              42, 45, 47, 51, 53, 55, 59, 62, 65, 68, 71, 74,
                              77, 79, 87]
        self.radiated_zombies = [3, 6, 10, 13, 16, 19, 22, 26, 29, 32, 35, 38,
                                 43, 48, 56, 60, 66, 69, 72, 75]

    
    def tear_down(self):
        pass
    
    # Component specific
    ####################

    def give(self, player, what, quantity, quality = ""):
        if not self.controller.telnet.ready:
            self.logger.error("Telnet not ready when trying to give.")
            return
        self.controller.telnet.write('give {} {} {} {}'.format(
            player["steamid"], what, quantity, quality))
        self.logger.info('gave {} {} {} of quality \'{}\'.'.format(
            player["name"], quantity, what, quality))        
    
    def pm(self, player, message):
        if not self.controller.telnet.ready:
            self.logger.error("Telnet not ready when trying to PM.")
            return
        self.controller.telnet.write('pm {} "{}"'.format(
            player["steamid"], message))
        self.logger.info('pm {} "{}"'.format(
            player["name"], message))

    def say(self, message):
        if not self.controller.telnet.ready:
            self.logger.error("Telnet not ready when trying to say.")
            return
        self.controller.telnet.write('say "{}"'.format(message))

    def se(self, player, zombie):
        if not self.controller.telnet.ready:
            self.logger.error("Telnet not ready when trying to se.")
            return
        self.controller.telnet.write(
            'se {} {}'.format(player["player_id"], zombie))
        self.logger.info("se {} {}".format(player["name"], zombie))
