# -*- coding: utf-8 -*-

import googletrans
import logging
import threading
import time

class ChatTranslator(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

        self.abort = False
        self.start ( )

    def run(self):
        if not self.controller.config.values["mod_chat_translator_enable"]:
            return
        self.setup()
        while ( self.keep_running ):
            time.sleep ( 0.1 )
        self.tear_down()
            
    def stop ( self ):
        self.keep_running = False

    # Mod specific
    ##############

    def setup(self):
        self.controller.dispatcher.register_callback("chat message", self.parse_chat_message)
        self.translator = googletrans.Translator()

    def tear_down(self):
        pass
        
    def parse_chat_message(self, match_groups):
        reconstructed_message = "[{}] {}: {}".format(
            match_groups[9], match_groups[10], match_groups[11])
        if match_groups[10] == "Server":
            return
        message = match_groups[11]
        detect = self.translator.detect(message)
        self.logger.info("Detected language: {}".format(detect.lang))
        if detect.lang != "en":
            translation = self.translator.translate(message, dest="en")
            self.logger.info("Translation: {}".format(translation))
            self.controller.telnet.write('say "{}: {}"'.format(match_groups[10], translation.text))
