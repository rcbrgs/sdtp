# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------80

import code
import logging
import threading
import time

class Interpreter(threading.Thread):
    def __init__(self, controller):
        super(self.__class__, self).__init__()
        self.controller = controller
        self.keep_running = True
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Start.")
        if not self.controller.config.values["mod_interpreter_enable"]:
            return
        self.setup()
        while(self.keep_running):
            time.sleep(0.1)
            self.run_eval_loop()
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

    def run_eval_loop(self):
        code.interact(local=locals())
