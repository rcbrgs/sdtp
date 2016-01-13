# -*- coding: utf-8 -*-

from sdtp.lp_table import lp_table

from PyQt4 import QtCore, QtGui
#from PySide import QtCore
import sys
import time

class server_reboots ( QtCore.QThread ):

    def __init__ ( self, controller ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True

        self.abort = False
        self.alarm_triggered = False
        self.uptime_triggered = False
        self.latest_uptime_announcement = -1
        
        self.start ( )

    def run ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        self.controller.dispatcher.register_callback ( "executing command", self.announce_server_uptime )
        while ( self.keep_running ):
            time.sleep ( 1 )
            if self.alarm_triggered or self.uptime_triggered:
                self.try_to_reboot ( )

        self.controller.dispatcher.deregister_callback ( "executing command", self.announce_server_uptime )

        self.controller.log ( "info", prefix + " return." )
            
    def stop ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )

        self.keep_running = False

    # Mod specific
    ##############

    def abort_shutdown ( self ):
        self.abort = True

    def announce_server_uptime ( self, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        uptime_string = match_group [ 6 ]
        self.controller.log ( "debug", prefix + " uptime_string = {}".format ( uptime_string ) )

        uptime = int ( float ( uptime_string ) / 3600 )
        self.controller.log ( "debug", prefix + " uptime = {} hours".format ( uptime ) )
        
        if uptime > self.latest_uptime_announcement:
            if self.latest_uptime_announcement != -1:
                self.controller.log ( "info", prefix + " Server online for {} hours.".format ( uptime ) )
                self.controller.telnet.write ( 'say "Server online for {} hours.".'.format ( uptime ) )
                
            self.latest_uptime_announcement = uptime

        self.check_for_reboot ( uptime, match_group )

    def check_for_reboot ( self, uptime, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )
        
        if self.controller.config.values [ "enable_frequency_reboots" ]:
            if uptime > int ( self.controller.config.values [ "frequency_reboots_interval" ] ):
                self.controller.log ( "info", prefix + " reboot triggered by uptime." )
                #self.try_to_reboot ( )
                self.uptime_triggered = True
                return
        if self.controller.config.values [ "enable_alarm_reboots" ]:
            if ( int ( match_group [ 3 ] ) == self.controller.config.values [ "alarm_reboots_time" ] ):
                self.alarm_triggered = True
            if self.alarm_triggered:
                self.controller.log ( "info", prefix + " reboot triggered by alarm." )
                #self.try_to_reboot ( )

    def try_to_reboot ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "info", prefix + " ( )" )
        
        if self.controller.config.values [ "server_empty_condition" ]:
            if not self.controller.world_state.server_empty:
                return

        if time.time ( ) < self.controller.config.values [ "latest_reboot" ] + 3601:
            return
            
        self.controller.log ( "info", prefix + " shutting down server for automatic reboot." )

        countdown = 600
        
        while countdown > 0:
            if self.abort:
                self.abort = False
                return
            if countdown % 60 == 0 or ( countdown < 60 and countdown % 5 == 0 ):
                self.controller.telnet.write ( 'say "Shutdown in {} seconds."'.format ( countdown ) )
            time.sleep ( 1 )
            countdown -= 1
        
        self.controller.telnet.write ( "kickall" ) 
        self.controller.telnet.write ( "saveworld" )
        self.controller.telnet.write ( "shutdown" )
        self.controller.config.values [ "latest_reboot" ] = time.time ( )
        self.uptime_triggered = False
        self.alarm_triggered = False

class server_reboots_widget ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.parent = parent
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

        self.controller.config.verify ( "show_{}".format ( self.__class__.__name__ ) )
        
    def init_GUI ( self ):

        enable_reboots = QtGui.QCheckBox ( "Enable server reboots", self )
        if self.controller.config.values [ "enable_frequency_reboots" ]:
            enable_reboots.setChecked ( True )
        else:
            enable_reboots.setChecked ( False )
        enable_reboots.stateChanged.connect ( lambda: self.controller.config.toggle ( "enable_frequency_reboots" ) )

        self.reboots_interval_label = QtGui.QLabel ( "every {} hours.".format ( self.controller.config.values [ "frequency_reboots_interval" ] ), self )
        
        self.interval_reboots = QtGui.QLineEdit ( self )
        self.interval_reboots.returnPressed.connect ( self.set_reboots_interval )

        alarm_reboots = QtGui.QCheckBox ( "Enable server reboots", self )
        if self.controller.config.values [ "enable_alarm_reboots" ]:
            alarm_reboots.setChecked ( True )
        else:
            alarm_reboots.setChecked ( False )
        alarm_reboots.stateChanged.connect ( lambda: self.controller.config.toggle ( "enable_alarm_reboots" ) )

        self.reboots_alarm_label = QtGui.QLabel ( "everyday at {} (24 hour notation).".format ( self.controller.config.values [ "alarm_reboots_time" ] ), self )
        
        self.alarm_reboots = QtGui.QLineEdit ( self )
        self.alarm_reboots.returnPressed.connect ( self.set_alarm_time )

        server_empty_condition = QtGui.QCheckBox ( "Server must be empty to reboot.", self )
        if self.controller.config.values [ "server_empty_condition" ]:
            server_empty_condition.setChecked ( True )
        else:
            server_empty_condition.setChecked ( False )
        server_empty_condition.stateChanged.connect ( lambda: self.controller.config.toggle ( "server_empty_condition" ) )

        abort = QtGui.QPushButton ( "Abort current shutdown", self )
        abort.clicked.connect ( self.controller.server_reboots.abort_shutdown )
        
        main_layout = QtGui.QVBoxLayout ( )
        reboot_layout = QtGui.QHBoxLayout ( )
        reboot_layout.addWidget ( enable_reboots )
        reboot_layout.addWidget ( self.reboots_interval_label )
        reboot_layout.addWidget ( self.interval_reboots )
        alarm_layout = QtGui.QHBoxLayout ( )
        alarm_layout.addWidget ( alarm_reboots )
        alarm_layout.addWidget ( self.reboots_alarm_label )
        alarm_layout.addWidget ( self.alarm_reboots )

        main_layout.addLayout ( reboot_layout )
        main_layout.addLayout ( alarm_layout )
        main_layout.addWidget ( server_empty_condition )

        control_layout = QtGui.QHBoxLayout ( )
        control_layout.addWidget ( abort )

        main_layout.addLayout ( control_layout )

        self.setLayout ( main_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def close ( self ):
        self.controller.config.falsify ( "show_{}".format ( self.__class__.__name__ ) )
        super ( self.__class__, self ).close ( )

    def closeEvent ( self, event ):
        self.controller.log ( )
        
        self.parent.mdi_area.removeSubWindow ( self )

    # Specific
    ##########
        
    def set_reboots_interval ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        self.controller.config.values [ "frequency_reboots_interval" ] = int ( self.interval_reboots.text ( ) ) 
        self.reboots_interval_label.setText ( "every {} hours.".format ( self.interval_reboots.text ( ) ) )
        self.interval_reboots.setText ( "" )

    def set_alarm_time ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )" )

        self.controller.config.values [ "alarm_reboots_time" ] = int ( self.alarm_reboots.text ( ) ) 
        self.reboots_alarm_label.setText ( "everyday at {} (24 hour notation).".format ( self.alarm_reboots.text ( ) ) )
        self.alarm_reboots.setText ( "" )

