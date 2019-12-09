# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 10:41:27 2019

@author: hoeren

source: 
https://stackoverflow.com/questions/51459331/pyqt5-how-to-add-actions-menu-in-a-toolbar
https://www.learnpyqt.com/courses/start/actions-toolbars-menus/
"""
import sys
from PyQt5 import QtWidgets
import qtawesome as qta
import qdarkstyle

class Menu(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        toolbar = self.addToolBar('toolbar')
        toolbar.setMovable(False)

        tester_label = QtWidgets.QLabel("Tester:")
        tester_label.setStyleSheet("background-color: rgba(0,0,0,0%)")
        toolbar.addWidget(tester_label)
        
        tester_combo = QtWidgets.QComboBox()
        toolbar.addWidget(tester_combo)
        tester_combo.insertItems(1, ["Tom's MiniSCT", "Rudie's MiniSCT"])

        run_action = QtWidgets.QAction(qta.icon('mdi.play-circle-outline', color='orange'), "Run", self)
        run_action.setStatusTip("Run active module")
        run_action.triggered.connect(self.onRun)
        run_action.setCheckable(False)
        toolbar.addAction(run_action)
        
        project_label = QtWidgets.QLabel("Project:")
        project_label.setStyleSheet("background-color: rgba(0,0,0,0%)")
        toolbar.addWidget(project_label)
        
        project_combo = QtWidgets.QComboBox()
        toolbar.addWidget(project_combo)
        project_combo.insertItems(1, ['CTCA', 'HATB'])

        hw_label = QtWidgets.QLabel("Hardware:")
        hw_label.setStyleSheet("background-color: rgba(0,0,0,0%)")
        toolbar.addWidget(hw_label)
        
        hw_combo = QtWidgets.QComboBox()
        toolbar.addWidget(hw_combo)
        hw_combo.insertItems(1, ['V1', 'V2', 'V3'])



        settings_action = QtWidgets.QAction(qta.icon('mdi.wrench', color='orange'), "Settings", self)
        settings_action.setStatusTip("Settings")
        settings_action.triggered.connect(self.onSettings)
        settings_action.setCheckable(True)
        toolbar.addAction(settings_action)


    def closeEvent(self, event=None):
        self.close()

    def onRun(self):
        print("run")

    def onSettings(self):
        print("settings")
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    menu = Menu()
    menu.show()
    sys.exit(app.exec_())

