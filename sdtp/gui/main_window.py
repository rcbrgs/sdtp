# -*- coding: utf-8 -*-
# 0.2.0

from ..auto_updater import fetch_update_confirm_dialog, fetch_update_execute_dialog, install_update_confirm_dialog, reinitialize_update_confirm_dialog
from ..chat import chat_widget
from ..controller import controller
from ..logger import log_widget
from ..telnet import telnet_widget
from ..version import api, feature, bug
#from .interpreter_widget import interpreter_widget
from ..metronomer import metronomer_widget
from ..players_control import players_control_widget
from .player_portals_window import player_portals_window

#from ..database.database_widget import database_widget
from ..mods.mods import mods_widget
#from ..mods.server_reboot import server_reboot_window

from PyQt4 import QtGui, QtCore
#from PySide import QtGui, QtCore
import sys
import time

class main_window ( QtGui.QMainWindow ):

    def __init__( self ):
        super ( main_window, self ).__init__ ( )
        self.children = [ ]
        
        self.subwindow_actions = { }
        
        self.init_GUI ( )
        
    def init_GUI ( self ):
        self.controller = controller ( self )
        self.controller.start ( )
        while ( not self.controller.ready_for_gui ( ) ):
            time.sleep ( 1 )

        self.controller.log ( )

        # mdi 
        self.mdi_area = QtGui.QMdiArea ( )
        chat_subwindow = chat_widget ( self, self.controller )
        self.mdi_area.addSubWindow ( chat_subwindow )
        log_subwindow = log_widget ( self.controller, self, title = "Log" )
        self.mdi_area.addSubWindow ( log_subwindow )
        metronomer_subwindow = metronomer_widget ( self, self.controller, "Metronomer configuration" )
        self.mdi_area.addSubWindow ( metronomer_subwindow )
        mods_subwindow = mods_widget ( self, self.controller )
        self.mdi_area.addSubWindow ( mods_subwindow )
        players_control_subwindow = players_control_widget ( self, self.controller )
        self.mdi_area.addSubWindow ( players_control_subwindow )
        telnet_subwindow = telnet_widget ( self, self.controller )
        self.mdi_area.addSubWindow ( telnet_subwindow )
        #interpreter_subwindow = interpreter_widget ( self.controller, self, title = "Python interpreter" )
        #self.mdi_area.addSubWindow ( interpreter_subwindow )
        #database_subwindow = database_widget ( self.controller, self, "Database" )
        #self.mdi_area.addSubWindow ( database_subwindow )
        # actions
        quit_program_action = QtGui.QAction ( '&Quit', self )
        quit_program_action.triggered.connect ( self.stop )
        quit_program_action.setToolTip ( 'Exits the program.' )
        # subwindow show actions
        chat_widget_show_action = QtGui.QAction ( "Show &Chat window", self )
        chat_widget_show_action.setCheckable ( True )
        chat_widget_show_action.setChecked ( self.controller.config.get ( "chat_widget_show" ) )
        chat_widget_show_action.toggled.connect ( lambda: ( self.toggle_subwindow ( chat_subwindow ), self.organize_subwindows ( ) ) )
        self.subwindow_actions [ "chat_widget_show_action" ] = chat_widget_show_action
        self.toggle_subwindow ( chat_subwindow )
        log_widget_show_action = QtGui.QAction ( "Show &Log window", self )
        log_widget_show_action.setCheckable ( True )
        log_widget_show_action.setChecked ( self.controller.config.get ( "log_widget_show" ) )
        log_widget_show_action.toggled.connect ( lambda: ( self.toggle_subwindow ( log_subwindow ), self.organize_subwindows ( ) ) )
        self.subwindow_actions [ "log_widget_show_action" ] = log_widget_show_action
        self.toggle_subwindow ( log_subwindow )
        metronomer_widget_show_action = QtGui.QAction ( "Show &Metronomer window", self )
        metronomer_widget_show_action.setCheckable ( True )
        metronomer_widget_show_action.setChecked ( self.controller.config.get ( "metronomer_widget_show" ) )
        metronomer_widget_show_action.toggled.connect ( lambda: ( self.toggle_subwindow ( metronomer_subwindow ), self.organize_subwindows ( ) ) )
        self.subwindow_actions [ "metronomer_widget_show_action" ] = metronomer_widget_show_action
        self.toggle_subwindow ( metronomer_subwindow )
        mods_widget_show_action = QtGui.QAction ( "Show &Mods window", self )
        mods_widget_show_action.setCheckable ( True )
        mods_widget_show_action.setChecked ( self.controller.config.get ( "mods_widget_show" ) )
        mods_widget_show_action.toggled.connect ( lambda: ( self.toggle_subwindow ( mods_subwindow ), self.organize_subwindows ( ) ) )
        self.subwindow_actions [ "mods_widget_show_action" ] = mods_widget_show_action
        self.toggle_subwindow ( mods_subwindow )
        players_control_widget_show_action = QtGui.QAction ( "Show &Players window", self )
        players_control_widget_show_action.setCheckable ( True )
        players_control_widget_show_action.setChecked ( self.controller.config.get ( "players_control_widget_show" ) )
        players_control_widget_show_action.toggled.connect ( lambda: ( self.toggle_subwindow ( players_control_subwindow ), self.organize_subwindows ( ) ) )
        self.subwindow_actions [ "players_control_widget_show_action" ] = players_control_widget_show_action
        self.toggle_subwindow ( players_control_subwindow )
        telnet_widget_show_action = QtGui.QAction ( "Show &Telnet window", self )
        telnet_widget_show_action.setCheckable ( True )
        telnet_widget_show_action.setChecked ( self.controller.config.get ( "telnet_widget_show" ) )
        telnet_widget_show_action.toggled.connect ( lambda: ( self.toggle_subwindow ( telnet_subwindow ), self.organize_subwindows ( ) ) )
        self.subwindow_actions [ "telnet_widget_show_action" ] = telnet_widget_show_action
        self.toggle_subwindow ( telnet_subwindow )
        #interpreter_widget_show_action = QtGui.QAction ( "Show &Python interpreter window", self )
        #interpreter_widget_show_action.setCheckable ( True )
        #interpreter_widget_show_action.setChecked ( self.controller.config.get ( "interpreter_widget_show" ) )
        #interpreter_widget_show_action.toggled.connect ( lambda: ( self.toggle_subwindow ( interpreter_subwindow ), self.organize_subwindows ( ) ) )
        #self.subwindow_actions [ "interpreter_widget_show_action" ] = interpreter_widget_show_action
        #self.toggle_subwindow ( interpreter_subwindow )
        #database_widget_show_action = QtGui.QAction ( "Show &Database window", self )
        #database_widget_show_action.setCheckable ( True )
        #database_widget_show_action.setChecked ( self.controller.config.get ( "database_widget_show" ) )
        #database_widget_show_action.triggered.connect ( lambda: ( self.toggle_subwindow ( database_subwindow ), self.organize_subwindows ( ) ) )
        #self.subwindow_actions [ "database_widget_show_action" ] = database_widget_show_action
        #self.toggle_subwindow ( database_subwindow )
        mdi_manual = QtGui.QAction ( "Do &not automatically organize windows", self )
        mdi_manual.setCheckable ( True )
        if self.controller.config.get ( "mdi_auto_organizing" ) == "manual":
            mdi_manual.setChecked ( True )
        mdi_manual.triggered.connect ( lambda: ( self.controller.config.set ( "mdi_auto_organizing", "manual" ), mdi_manual.setChecked ( True ) ) )
        mdi_cascading = QtGui.QAction ( "Automatically &cascade windows", self )
        mdi_cascading.setCheckable ( True )
        if self.controller.config.get ( "mdi_auto_organizing" ) == "cascading":
            mdi_cascading.setChecked ( True )
        mdi_cascading.triggered.connect ( lambda: ( self.controller.config.set ( "mdi_auto_organizing", "cascading" ), self.organize_subwindows ( ), mdi_cascading.setChecked ( True ) ) )
        mdi_tiling = QtGui.QAction ( "Automatically &tile windows", self )
        mdi_tiling.setCheckable ( True )
        if self.controller.config.get ( "mdi_auto_organizing" ) == "tiling":
            mdi_tiling.setChecked ( True )
        mdi_tiling.triggered.connect ( lambda: ( self.controller.config.set ( "mdi_auto_organizing", "tiling" ), self.organize_subwindows ( ), mdi_tiling.setChecked ( True ) ) )
        mdi_auto_organize_group = QtGui.QActionGroup ( self )
        mdi_auto_organize_group.addAction ( mdi_manual )
        mdi_auto_organize_group.addAction ( mdi_cascading )
        mdi_auto_organize_group.addAction ( mdi_tiling )
        mdi_auto_organize_group.setExclusive ( True )
        # menus
        file_menu = self.menuBar ( ).addMenu ( "&File" )
        file_menu.addAction ( quit_program_action )
        windows_menu = self.menuBar ( ).addMenu ( "&Windows" )
        windows_menu.addAction ( chat_widget_show_action )
        windows_menu.addAction ( log_widget_show_action )
        windows_menu.addAction ( metronomer_widget_show_action )
        windows_menu.addAction ( mods_widget_show_action )
        windows_menu.addAction ( players_control_widget_show_action )
        windows_menu.addAction ( telnet_widget_show_action )
        #windows_menu.addAction ( database_widget_show_action )
        #windows_menu.addAction ( interpreter_widget_show_action )
        windows_menu.addSeparator ( )
        windows_menu.addAction ( mdi_manual )
        windows_menu.addAction ( mdi_cascading )
        windows_menu.addAction ( mdi_tiling )
        # toolbar
        #toolbar = QtGui.QToolBar ( self )
        #toolbar.addAction ( open_FITS_file_action )
        #self.addToolBar ( toolbar )

        mainLayout = QtGui.QHBoxLayout ( )


        open_ping_limiter_window = QtGui.QPushButton ( "Configure ping limiter", self )
        open_ping_limiter_window.clicked.connect ( lambda: self.children.append ( ping_limiter_window ( self, self.controller, "Ping limiter configuration" ) ) )
        if self.controller.config.values [ "show_ping_limiter_window" ]:
            open_ping_limiter_window.clicked.emit ( True )

        show_player_portals_window = QtGui.QPushButton ( "Configure player portals", self )
        show_player_portals_window.clicked.connect ( lambda: self.children.append ( player_portals_window ( self, self.controller, "Player portals configuration" ) ) )
        if self.controller.config.values [ "show_player_portals_window" ]:
            show_player_portals_window.clicked.emit ( True )
            
        # Mods
        ######

        modsFrame = QtGui.QFrame ( self )
        modsFrame.setFrameShape ( QtGui.QFrame.StyledPanel )
        modsFrameLayout = QtGui.QVBoxLayout ( )
        modsFrame.setLayout ( modsFrameLayout )

        mainLayout.addWidget ( modsFrame )

        modsFrameLayout.addWidget ( open_ping_limiter_window )
        modsFrameLayout.addWidget ( show_player_portals_window )

        # assorted config
        QtGui.QToolTip.setFont ( QtGui.QFont ( 'SansSerif', 10 ) )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        self.setWindowTitle ( '{} v{}.{}.{}'.format ( self.controller.config.get ( "app_name" ), api, feature, bug ) )
        
        old_frame = QtGui.QFrame ( )
        old_frame.setLayout ( mainLayout )       
        self.mdi_area.addSubWindow ( old_frame )
        self.setCentralWidget ( self.mdi_area )
        
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        self.show ( )
        self.organize_subwindows ( )
        
    def stop ( self ):
        self.controller.log ( )
        
        self.controller.stop ( )
        while ( not self.controller.isFinished ( ) ):
            time.sleep ( 0.1 )
        QtCore.QCoreApplication.instance().quit ( )

    def force_repaint ( self ):
        # don't log here, or it will spam the log.

        QtGui.QApplication.processEvents ( )

    # subwindows
    ############

    def organize_subwindows ( self ):
        self.controller.log ( )
        
        if self.controller.config.get ( "mdi_auto_organizing" ) == "tiling":
            self.mdi_area.tileSubWindows ( )
        if self.controller.config.get ( "mdi_auto_organizing" ) == "cascading":
            self.mdi_area.cascadeSubWindows ( )
        
    def toggle_subwindow ( self, subwindow ):
        self.controller.log ( )

        checked = self.subwindow_actions [ "{}_show_action".format ( subwindow.__class__.__name__ ) ].isChecked ( )
        self.controller.config.values [ "{}_show".format ( subwindow.__class__.__name__ ) ] = checked
        subwindows_list = self.mdi_area.subWindowList ( )
        self.controller.log ( "debug", "subwindows_list == {}".format ( subwindows_list ) )
        for sub in subwindows_list:
            if sub.widget ( ) == subwindow:
                self.controller.log ( "debug", "match: {}".format ( sub ) )
                if checked:
                    sub.show ( )
                else:
                    sub.hide ( )
        self.organize_subwindows ( )

    # auto updater
    ##############
        
    def ask_about_fetching_update ( self ):
        self.controller.log ( )

        dialog = fetch_update_confirm_dialog ( self.controller, self )
        result = dialog.exec_ ( )
        if result:
            dialog = fetch_update_execute_dialog ( self.controller, self )
            dialog.exec_ ( )
            self.controller.auto_updater.to_install = self.controller.auto_updater.to_update
        self.controller.auto_updater.to_update = None

    def ask_about_installing_update ( self ):
        self.controller.log ( )

        dialog = install_update_confirm_dialog ( self.controller, self )
        result = dialog.exec_ ( )
        if result:
            self.controller.auto_updater.install_update ( )
            self.controller.auto_updater.to_install = None

    def ask_about_reinitialize_update ( self ):
        self.controller.log ( )

        dialog = reinitialize_update_confirm_dialog ( self.controller, self )
        result = dialog.exec_ ( )
        if result:
            self.controller.auto_updater.reinitialize ( )
            self.controller.auto_updater.to_reinitialize = None
            self.stop ( )
        
def run ( ):
    app = QtGui.QApplication ( sys.argv )
    main_window_object = main_window ( )
    app.exec_ ( )
    
if __name__ == '__main__':
    run ( )    
