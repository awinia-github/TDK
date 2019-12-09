#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created on Fri Nov 29 10:46:57 2019

@author: hoeren

this module is just there so we can test our individual dialogs whithout
the full mockup (or later spyder) attached to it.
"""

import sys, os, re

from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication

from SpyderMockUp import workspace_path
# from SpyderMockUp.SpyderMockUp import workspace_path
active_project = 'HATB'

class DummyMainWindow(QWidget):
    
    def __init__(self):
        super().__init__()
        self.workspace_path = workspace_path
        self.active_project = active_project
        self.active_project_path = os.path.join(workspace_path, active_project)

        self.button = QPushButton('Button', self)
        self.button.resize(self.button.sizeHint())
        self.button.move(50, 33)  
        self.button.setMinimumSize(QtCore.QSize(200,33))
        
        self.setGeometry(300, 300, 300, 100)
        self.setWindowTitle('Dummy Main Widget')    
        self.show()

    def register_dialog(self, some_dialog):
        self.dialog = some_dialog
        self.button.blockSignals(True)
        self.button.clicked.connect(self.run_dialog)
        self.button.setText(' '.join(re.findall('.[^A-Z]*', self.dialog.__class__.__name__)))
        self.button.blockSignals(False)

    def run_dialog(self):
        print("run dialog ... ", end='')
        self.dialog.show()
        self.dialog.exec_()
        print("done.")

class SomeDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        self.parent = parent
        super().__init__()  

        my_ui = os.path.join(os.path.dirname(__file__), "%s.ui" % self.__class__.__name__)
        print(my_ui)
        
        if not os.path.exists(my_ui):
            raise Exception("can not find %s" % my_ui)
        uic.loadUi(my_ui, self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', self.__class__.__name__)))
 
        self.workspace_path = parent.workspace_path
        self.active_project = parent.active_project
        self.active_project_path = parent.active_project_path
    
        self.CancelButton.clicked.connect(self.CancelButtonPressed)    
        self.OKButton.clicked.connect(self.OKButtonPressed)

    def CancelButtonPressed(self):
        print("cancel button pressed ... ", end='')
        self.accept()
    
    def OKButtonPressed(self):
        print("OK button pressed ... ", end='')
        self.accept()        
        
if __name__ == '__main__':
    import qdarkstyle
    
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    dummyMainWindow = DummyMainWindow()
    dialog = SomeDialog(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())