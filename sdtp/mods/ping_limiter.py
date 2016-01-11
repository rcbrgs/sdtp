# -*- coding: utf-8 -*-

from PyQt4 import QtCore
#from PySide import QtCore
import threading
import time

class ping_limiter ( QtCore.QThread ):

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

        self.controller.dispatcher.register_callback ( "lp output", self.check_ping )
        self.start ( )

    def run ( self ):
        while ( self.keep_running ):
            time.sleep ( 0.1 )

    def stop ( self ):
        self.keep_running = False

    def check_ping ( self, match_group ):
        self.controller.log ( "debug", "mods.ping_limiter.check_ping ( {} )".format ( match_group ) )
        if not self.controller.config.values [ "enable_ping_limiter" ]:
            return
        if int ( match_group [ 17 ] ) > self.controller.config.values [ "max_ping" ]:
            self.controller.telnet.write ( 'kick {} "Ping too high (max is {})."'.format ( match_group [ 15 ], self.controller.config.values [ "max_ping" ] ) )
