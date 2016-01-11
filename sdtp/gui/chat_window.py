# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
#from PySide import QtCore, QtGui
#from time import sleep, strftime
import sys

class chat_window ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = None ):
        super ( self.__class__, self ).__init__ ( )

        self.controller = controller
        self.title = title
        
        self.init_GUI ( )
        self.show ( )

        self.controller.config.verify ( "show_chat_window" )
        
    def init_GUI ( self ):
               
        self.chat_log_widget = QtGui.QListWidget ( self )
        self.controller.dispatcher.register_callback ( "chat message", self.add_chat )

        self.input_chat = QtGui.QLineEdit ( self )
        self.input_chat.returnPressed.connect ( self.send_chat )
        
        close_button = QtGui.QPushButton ( "Close", self )
        close_button.clicked.connect ( self.close )

        main_layout = QtGui.QVBoxLayout ( )
        main_layout.addWidget ( self.chat_log_widget )
        input_layout = QtGui.QHBoxLayout ( )
        input_layout.addWidget ( self.input_chat )
        main_layout.addLayout ( input_layout )
        main_layout.addWidget ( close_button )
        self.setLayout ( main_layout )

        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        
        if self.title != None:
            self.setWindowTitle ( self.title )

    def add_chat ( self, match_group ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( {} )".format ( match_group ) )

        #now = strftime ( "%Y-%m-%d %H:%M:%S" )
        message_time = "{}-{}-{} {}:{}:{}".format ( match_group [ 0 ], match_group [ 1 ], match_group [ 2 ], match_group [ 3 ], match_group [ 4 ], match_group [ 5 ] )
        try:
            #self.chat_log_widget.insertItem ( 0, "{} {}".format ( message_time, str ( match_group [ 7 ] ).encode ( "utf-8" ) ) )
            #self.chat_log_widget.addItem ( "{} {}".format ( message_time, str ( match_group [ 7 ] ).encode ( "utf-8" ) ) )
            self.chat_log_widget.addItem ( "{} {}".format ( message_time, match_group [ 7 ] ) )
        except Exception as e:
            self.controller.log ( "debug", prefix + " type ( match_group [ 7 ] ) == {}, exception: {}".format ( type ( match_group [ 7 ] ), e ) )
            try:
                #self.chat_log_widget.addItem ( "{} {}".format ( message_time, match_group [ 7 ].decode ( "latin-1", "replace" ) ) )
                self.chat_log_widget.addItem ( "{} {}".format ( message_time, match_group [ 7 ].encode ( "utf-8", "replace" ) ) )
            except Exception as e:
                self.controller.log ( "error", prefix + " latin-1" )
                return

        self.chat_log_widget.scrollToBottom ( )
        
    def close ( self ):
        self.controller.config.values [ "show_log_window" ] = False
        super ( self.__class__, self ).close ( )

    def send_chat ( self ):
        prefix = "{}.{}".format ( self.__class__.__name__, sys._getframe().f_code.co_name )
        self.controller.log ( "debug", prefix + " ( )".format ( ) )

        self.controller.log ( "debug", "gui.chat_window.send_chat ( )" )
        try:
            #message = str ( self.input_chat.text ( ).toUtf8 ( ) ).encode ( "utf-8" )
            #message = str ( self.input_chat.text ( ).toUtf8 ( ) ).decode ( "utf-8" )
            message_qstring = self.input_chat.text ( )
            self.controller.log ( "info", prefix + " qstring obtained" )
            message = str ( message_qstring )
            self.controller.log ( "info", prefix + " unicode obtained" )
            self.controller.telnet.write ( 'say "{}"'.format ( message ) )
        except Exception as e:
            self.controller.log ( "warning", " exception: {}".format ( e ) )
            self.controller.telnet.write ( 'say "{}"'.format ( message.encode ( "latin-1" ) ) )
            #self.controller.log ( "error", " type ( message ) ==  {}".format ( type ( message ) ) )
            
        self.input_chat.clear ( )
