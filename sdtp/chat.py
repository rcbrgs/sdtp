# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
#from PySide import QtCore, QtGui
import sys

class chat_widget ( QtGui.QWidget ):

    def __init__ ( self, parent = None, controller = None, title = "Chat" ):
        super ( self.__class__, self ).__init__ ( )
        self.controller = controller
        self.parent = parent
        self.title = title
        self.init_GUI ( )
        self.show ( )

    def init_GUI ( self ):
        self.chat_log_widget = QtGui.QListWidget ( self )
        self.controller.dispatcher.register_callback ( "chat message", self.add_chat )
        self.chat_input_name = QtGui.QLineEdit ( )
        #self.chat_input_name.sizePolicy ( ).setHorizontalPolicy ( QtGui.QSizePolicy.Fixed )
        my_name = self.controller.config.get ( "chat_input_name" )
        if my_name != None:
            self.chat_input_name.setText ( my_name )
        self.input_chat = QtGui.QLineEdit ( self )
        self.input_chat.returnPressed.connect ( self.send_chat )
        input_layout = QtGui.QHBoxLayout ( )
        input_layout.addWidget ( self.chat_input_name, 10 )
        input_layout.addWidget ( self.input_chat, 90 )
        main_layout = QtGui.QVBoxLayout ( )
        main_layout.addWidget ( self.chat_log_widget )
        main_layout.addLayout ( input_layout )
        self.setLayout ( main_layout )
        QtGui.QApplication.setStyle ( QtGui.QStyleFactory.create ( 'Cleanlooks' ) )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def add_chat ( self, match_group ):
        self.controller.log ( )
        message_time = "{}-{}-{} {}:{}:{}".format ( match_group [ 0 ], match_group [ 1 ], match_group [ 2 ], match_group [ 3 ], match_group [ 4 ], match_group [ 5 ] )
        item = QtGui.QListWidgetItem ( "{} {}".format ( message_time, match_group [ 7 ] ) )
        try:
            self.chat_log_widget.addItem ( item )
        except Exception as e:
            self.controller.log ( "debug", prefix + " type ( match_group [ 7 ] ) == {}, exception: {}".format ( type ( match_group [ 7 ] ), e ) )
            try:
                self.chat_log_widget.addItem ( "{} {}".format ( message_time, match_group [ 7 ].encode ( "utf-8", "replace" ) ) )
            except Exception as e:
                self.controller.log ( "error", prefix + " latin-1" )
                return
        #self.chat_log_widget.scrollToItem ( item )
        self.chat_log_widget.scrollToBottom ( )

    def send_chat ( self ):
        self.controller.log ( )

        self.controller.config.set ( "chat_input_name", str ( self.chat_input_name.text ( ) ) )
        my_name = "{}".format ( str ( self.chat_input_name.text ( ) ) )
        if my_name == "() ":
            my_name = ""
        try:
            message_qstring = self.input_chat.text ( )
            self.controller.log ( "info", "qstring obtained: {}".format ( message_qstring ) )
            message = str ( message_qstring )
            self.controller.log ( "info", "unicode obtained: {}".format ( message ) )
            self.controller.telnet.write ( 'say "({}): {}"'.format ( my_name, message ) )
        except Exception as e:
            self.controller.log ( "warning", "exception: {}".format ( e ) )
            self.controller.telnet.write ( 'say "({}): {}"'.format ( my_name, message.encode ( "latin-1" ) ) )
            
        self.input_chat.clear ( )

    def closeEvent ( self, event ):
        self.controller.log ( )
        
        event.ignore ( )
        self.parent.subwindow_actions [ "{}_show_action".format ( self.__class__.__name__ ) ].setChecked ( False )

    def close ( self ):
        self.controller.config.set ( "{}_show".format ( self.__class__.__name__ ), False )
        super ( self.__class__, self ).close ( )

