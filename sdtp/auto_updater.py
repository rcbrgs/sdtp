# -*- coding: utf-8 -*-

import esky
from PyQt4 import QtCore, QtGui
import sys
import time

class auto_updater ( QtCore.QThread ):

    update_available = QtCore.pyqtSignal ( )
    install_available = QtCore.pyqtSignal ( )
    reinitialization_available = QtCore.pyqtSignal ( )
    
    def __init__ ( self, controller = None ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.keep_running = True
        
        self.esky_app = None
        self.to_install = None
        self.to_reinitialize = None
        self.to_update = None

        self.start ( )

    def run ( self ):
        self.controller.log ( )

        self.latest_update_check = time.time ( ) - 3599
        if getattr ( sys, "frozen", False ):
            self.esky_app = esky.Esky ( sys.executable, self.controller.config.get ( "auto_updater_url" ) )
            self.cleanup ( )
            while self.keep_running:
                time.sleep ( 0.1 )
                self.check_for_updates ( )
                self.check_for_installs ( )
                self.check_for_reinitializations ( )
        else:
            while self.keep_running:
                time.sleep ( 0.1 )
            
    # domain specific
    #################

    def check_for_updates ( self ):
        if time.time ( ) - self.latest_update_check < 3600:
            return

        self.controller.log ( )
        
        self.to_update = None
        self.latest_update_check = time.time ( )
        if self.esky_app == None:
            self.controller.log ( "warning", "This is not an updateable version of {}.".format ( self.controller.config.get ( "app_name" ) ) )
            return 
        self.to_update = self.esky_app.find_update ( )
        if self.to_update != None:
            self.controller.log ( "info", "updated version of {} is available ({}).".format ( self.controller.config.get ( "app_name" ), self.to_update ) )
        else:
            self.controller.log ( "info", "there are no updates available for {}.".format ( self.controller.config.get ( "app_name" ) ) )
            return 
        if self.to_update == self.esky_app.active_version:
            self.controller.log ( "info", "current running executable is the latest version, no update necessary." )
            return 
        self.update_available.emit ( )

    def check_for_installs ( self ):
        if self.to_install == None:
            return

        self.controller.log ( )

        self.to_install = None
        self.install_available.emit ( )

    def check_for_reinitializations ( self ):
        if self.to_reinitialize == None:
            return

        self.controller.log ( )

        self.to_reinitialize = None
        self.reinitialization_available.emit ( )

    def install_update ( self ):
        self.controller.log ( )

        print ( "Installing latest version." )
        self.esky_app.install_version ( self.esky_app.find_update ( ) )
        self.to_reinitialize = self.esky_app.find_update ( )
        print ( "Installation complete." )

    def reinitialize ( self ):
        self.controller.log ( )

        print ( "Reinitializing SDTP with latest version." )
        self.esky_app.reinitialize ( )
        print ( "Reinitialization complete." )

    def cleanup ( self ):
        self.controller.log ( )

        self.esky_app.cleanup ( )

class fetch_update_confirm_dialog ( QtGui.QDialog ):
    def __init__ ( self, controller = None, parent = None ):
        super ( self.__class__, self ).__init__ ( parent )
        self.controller = controller
        self.parent = parent
        
        self.init_GUI ( )

    def init_GUI ( self ):
        self.controller.log ( )

        message = QtGui.QLabel ( "A new version of {} is available. Would you like to download it now?".format ( self.controller.config.get ( "app_name" ) ) )
        yes = QtGui.QPushButton ( "&Yes", self )
        yes.clicked.connect ( self.accept )
        no = QtGui.QPushButton ( "&No", self )
        no.clicked.connect ( self.reject )
        
        layout = QtGui.QVBoxLayout ( )
        layout.addWidget ( message )
        button_layout = QtGui.QHBoxLayout ( )
        button_layout.addWidget ( yes )
        button_layout.addWidget ( no )
        layout.addLayout ( button_layout )
        self.setLayout ( layout )
        
        self.setWindowTitle ( "{} update available for download".format ( self.controller.config.get ( "app_name" ) ) )

class fetch_update_execute_dialog ( QtGui.QDialog ):
    def __init__ ( self, controller = None, parent = None ):
        super ( self.__class__, self ).__init__ ( parent )
        self.controller = controller
        self.parent = parent
        
        self.init_GUI ( )

    def init_GUI ( self ):
        self.controller.log ( )

        message = QtGui.QLabel ( "{} is being updated. Please wait.".format ( self.controller.config.get ( "app_name" ) ) )
        self.progress_bar = QtGui.QProgressBar ( self )
        self.progress_bar.setMinimum ( 0 )
        self.status = QtGui.QLabel ( "Status: process not started" )
        self.data_transfer = QtGui.QLabel ( "0 of 0 MB received." )
        self.close_button = QtGui.QPushButton ( "&Close" )
        self.close_button.clicked.connect ( self.accept )
        
        layout = QtGui.QVBoxLayout ( )
        layout.addWidget ( message )
        layout.addWidget ( self.progress_bar )
        layout.addWidget ( self.status )
        layout.addWidget ( self.data_transfer )
        layout.addWidget ( self.close_button )
        self.setLayout ( layout )
        
        self.setWindowTitle ( "Updating {}".format ( self.controller.config.get ( "app_name" ) ) )
        self.show ( )

        self.esky_app = esky.Esky ( sys.executable, self.controller.config.get ( "auto_updater_url" ) )
        self.esky_app.fetch_version ( self.esky_app.find_update ( ), callback = self.set_progress )
        
    def set_progress ( self, value_dict ):
        prefix = "{}.{} ".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        try:
            if int ( 100 * value_dict [ "received" ] / value_dict [ "size" ] ) % 10 == 0:
                self.controller.log ( "debug", "status = {}, size = {}, received = {}".format ( value_dict [ "status" ], value_dict [ "size" ], value_dict [ "received" ] ) )
        except:
            self.controller.log ( "debug", "value_dict = {}".format ( value_dict ) )

        try:
            self.progress_bar.setMaximum ( value_dict [ "size" ] )
            self.progress_bar.setValue ( value_dict [ "received" ] )
            self.data_transfer.setText ( "{:.1f} of {:.1f} MB received.".format ( value_dict [ "received" ] / 1000000, value_dict [ "size" ] / 1000000 ) )
        except:
            pass
        try:
            self.status.setText ( "Status: {}".format ( value_dict [ "status" ] ) )
        except:
            print ( "err status" )

        if value_dict [ "status" ] == "ready":
            self.progress_bar.setValue ( self.progress_bar.maximum ( ) )
            self.data_transfer.setText ( "{:.1f} of {:.1f} MB received.".format ( self.progress_bar.maximum ( ) / 1000000, self.progress_bar.maximum ( ) / 1000000 ) )
            self.accept ( )
            self.close ( )

        QtGui.QApplication.processEvents ( )
        self.parent.force_repaint ( )

class install_update_confirm_dialog ( QtGui.QDialog ):
    def __init__ ( self, controller = None, parent = None ):
        super ( self.__class__, self ).__init__ ( parent )
        self.controller = controller
        self.init_GUI ( )

    def init_GUI ( self ):
        self.controller.log ( )

        message = QtGui.QLabel ( "Would you like to install the updated {} version now?".format ( self.controller.config.get ( "app_name" ) ) )
        yes = QtGui.QPushButton ( "&Yes", self )
        yes.clicked.connect ( self.accept )
        no = QtGui.QPushButton ( "&No", self )
        no.clicked.connect ( self.reject )
        
        layout = QtGui.QVBoxLayout ( )
        layout.addWidget ( message )
        button_layout = QtGui.QHBoxLayout ( )
        button_layout.addWidget ( yes )
        button_layout.addWidget ( no )
        layout.addLayout ( button_layout )
        self.setLayout ( layout )
        
        self.setWindowTitle ( "{} update available for install".format ( self.controller.config.get ( "app_name" ) ) )

class reinitialize_update_confirm_dialog ( QtGui.QDialog ):
    def __init__ ( self, controller = None, parent = None ):
        super ( self.__class__, self ).__init__ ( parent )
        self.controller = controller
        self.init_GUI ( )

    def init_GUI ( self ):
        self.controller.log ( )

        message = QtGui.QLabel ( "Would you like to reinitialize {} with the new version now?".format ( self.controller.config.get ( "app_name" ) ) )
        yes = QtGui.QPushButton ( "&Yes", self )
        yes.clicked.connect ( self.accept )
        no = QtGui.QPushButton ( "&No", self )
        no.clicked.connect ( self.reject )
        
        layout = QtGui.QVBoxLayout ( )
        layout.addWidget ( message )
        button_layout = QtGui.QHBoxLayout ( )
        button_layout.addWidget ( yes )
        button_layout.addWidget ( no )
        layout.addLayout ( button_layout )
        self.setLayout ( layout )
        
        self.setWindowTitle ( "{} reinitialization into new version available".format ( self.controller.config.get ( "app_name" ) ) )
