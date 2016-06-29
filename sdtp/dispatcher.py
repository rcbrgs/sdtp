# -*- coding: utf-8 -*-

from PyQt4 import QtCore
import sys
import threading
import time

class dispatcher ( QtCore.QThread ):

    # Boilerplate
    debug = QtCore.pyqtSignal ( str, str, str, str )

    def log ( self, level, message ):
        self.debug.emit ( message, level, self.__class__.__name__,
                          sys._getframe ( 1 ).f_code.co_name )

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        self.callback_registry = { }

    def run ( self ):
        while ( self.keep_running ):
            time.sleep ( 1 )

    def stop ( self ):
        self.keep_running = False

    def call_registered_callbacks ( self, key, match_groups ):
        self.log ( "debug", "dispatcher ( {}, {} )".format ( key, match_groups ) )
        if key not in list ( self.callback_registry.keys ( ) ):
            return
        for callback in self.callback_registry [ key ]:
            self.log ( "debug", "Dispatcher calling {} for key '{}' and match_groups {}.".format ( callback.__name__, key, match_groups ) ) 
            try:
                callback ( match_groups )
            except Exception as e:
                self.log ( "error", "dispatcher.call_registered_callbacks: exception in callback {}: {}.".format ( callback, e ) )

    def register_callback ( self, key, callback ):
        self.log ( "debug", "dispatcher.register_callback ( {}, {} )".format ( key, callback.__name__ ) )
        try:
            self.callback_registry [ key ].append ( callback )
        except KeyError:
            self.callback_registry [ key ] = [ callback ]

    def deregister_callback ( self, key, callback ):
        self.log ( "debug", "dispatcher.deregister_callback ( {}, {} )".format ( key, callback.__name__ ) )
        if key in list ( self.callback_registry.keys ( ) ):
            if callback in self.callback_registry [ key ]:
                self.callback_registry [ key ].remove ( callback )
            else:
                self.log ( "debug", "dispatcher.deregister_callback: callback not registered under key." )
        else:
            self.log ( "debug", "dispatcher.deregister_callback: no key in registry, ignoring." )
