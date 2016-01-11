# -*- coding: utf-8 -*-
__version__ = "0.0.0"
__changelog__ = {
    "0.0.0" : "Initial commit."
    }

from PyQt4 import QtCore
#from PySide import QtCore
import threading
import time

class metronomer ( QtCore.QThread ):

    #log = QtCore.Signal ( object, object )
    #lp_sent = QtCore.Signal ( )
    log = QtCore.pyqtSignal ( object, object )
    lp_sent = QtCore.pyqtSignal ( )
    
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
                self.controller.telnet.write ( "lp" )
                self.lp_sent.emit ( )

    def stop ( self ):
        self.keep_running = False
