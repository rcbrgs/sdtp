# -*- coding: utf-8 -*-

#from PySide import QtCore, QtGui
from PyQt4 import QtCore, QtGui
import sys

class metronomer_window ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

        self.controller.config.verify ( "show_metronomer_window" )
        
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
                                              
        close_button = QtGui.QPushButton ( "Close", self )
        close_button.clicked.connect ( self.close )

        main_layout = QtGui.QVBoxLayout ( )
        lp_layout = QtGui.QHBoxLayout ( )
        lp_layout.addWidget ( enable_lp )
        lp_layout.addWidget ( self.lp_interval_label )
        lp_layout.addWidget ( self.interval_lp )
        main_layout.addLayout ( lp_layout )
        main_layout.addWidget ( close_button )

        self.setLayout ( main_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def close ( self ):
        self.controller.config.falsify ( "show_{}".format ( self.__class__.__name__ ) )
        super ( self.__class__, self ).close ( )

    # Specific
    ##########
        
    def set_lp_interval ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        self.controller.config.values [ "lp_interval" ] = int ( self.interval_lp.text ( ) ) 
        self.lp_interval_label.setText ( "every {} seconds.".format ( self.interval_lp.text ( ) ) )
        self.interval_lp.setText ( "" )
