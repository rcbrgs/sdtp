# -*- coding: utf-8 -*-
__version__ = "0.0.0"
__changelog__ = {
    "0.0.0" : "Initial commit."
    }

from PyQt4 import QtGui

class children_window ( QtGui.QDialog ):
    def __init__ ( self, parent ):
        QtGui.QDialog.__init__ ( self, parent )
