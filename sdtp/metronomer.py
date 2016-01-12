# -*- coding: utf-8 -*-
# 0.1.0

from PyQt4 import QtCore, QtGui
#from PySide import QtCore
import sys
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

class metronomer_widget ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.parent = parent
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

        self.controller.config.verify ( "{}_show".format ( self.__class__.__name__ ) )
        
    def init_GUI ( self ):

        enable_lp = QtGui.QCheckBox ( "Enable lp command", self )
        if self.controller.config.values [ "enable_lp" ]:
            enable_lp.setChecked ( True )
        else:
            enable_lp.setChecked ( False )
        enable_lp.stateChanged.connect ( lambda: self.controller.config.toggle ( "enable_lp" ) )

        self.lp_interval_label = QtGui.QLabel ( "every {} seconds.".format ( self.controller.config.values [ "lp_interval" ] ), self )
        
        self.interval_lp = QtGui.QLineEdit ( self )
        self.interval_lp.returnPressed.connect ( self.set_lp_interval )
                                              
        main_layout = QtGui.QVBoxLayout ( )
        lp_layout = QtGui.QHBoxLayout ( )
        lp_layout.addWidget ( enable_lp )
        lp_layout.addWidget ( self.lp_interval_label )
        lp_layout.addWidget ( self.interval_lp )
        main_layout.addLayout ( lp_layout )

        self.setLayout ( main_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def close ( self ):
        self.controller.config.falsify ( "show_{}".format ( self.__class__.__name__ ) )
        super ( self.__class__, self ).close ( )
        
    def closeEvent ( self, event ):
        self.controller.log ( )
        
        event.ignore ( )
        self.parent.subwindow_actions [ "{}_show_action".format ( self.__class__.__name__ ) ].setChecked ( False )
            

    # Specific
    ##########
        
    def set_lp_interval ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        self.controller.config.values [ "lp_interval" ] = int ( self.interval_lp.text ( ) ) 
        self.lp_interval_label.setText ( "every {} seconds.".format ( self.interval_lp.text ( ) ) )
        self.interval_lp.setText ( "" )
