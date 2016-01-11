# -*- coding: utf-8 -*-

#from PySide import QtCore, QtGui
from PyQt4 import QtCore, QtGui

class progress_dialog ( QtGui.QDialog ):

    def __init__ ( self, controller, parent = None, title = None ):
        super ( self.__class__, self ).__init__ ( parent )

        self.controller = controller
        self.title = title
        
        self.init_GUI ( )

        self.show ( )

    def init_GUI ( self ):

        layout = QtGui.QHBoxLayout ( )
        self.progress_bar = QtGui.QProgressBar ( self )
        layout.addWidget ( self.progress_bar )
        self.setLayout ( layout )
        if self.title != None:
            self.setWindowTitle ( self.title )

    def setValue ( self, value ):
        self.progress_bar.setValue ( value ) 
