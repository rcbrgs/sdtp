# -*- coding: utf-8 -*-

import logging
import threading
import time

class ChatLogger(threading.Thread):
    def __init__(self, controller):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.abort = False
        self.start ( )

    def run ( self ):
        self.setup()
        while ( self.keep_running ):
            time.sleep ( 0.1 )
            
    def stop ( self ):
        self.keep_running = False

    # Mod specific
    ##############

    def setup(self):
        self.controller.dispatcher.register_callback("chat message", self.parse_chat_message)

    def parse_chat_message(self, match_groups):
        reconstructed_message = "[{}] {}: {}".format(
            match_groups[9], match_groups[10], match_groups[11])
        self.logger.info(" " + reconstructed_message)
