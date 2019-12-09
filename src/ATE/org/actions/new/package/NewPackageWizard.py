# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 18:18:41 2019

@author: hoeren
"""
from PyQt5 import QtWidgets, QtCore, QtGui, uic

import os, re, pickle

from ATE.org.validation import valid_package_name_regex, valid_integer_regex, is_ATE_project
from ATE.org.listings import list_packages, dict_project_paths

class NewPackageWizard(QtWidgets.QDialog):

    def __init__(self, parent):
        super(NewPackageWizard, self).__init__()
        
        my_ui = __file__.replace('.py', '.ui')
        if not os.path.exists(my_ui):
            raise Exception("can not find %s" % my_ui)
        uic.loadUi(my_ui, self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', os.path.basename(__file__).replace('.py', ''))))

        self.parent = parent
        self.project_directory = os.path.join(self.parent.workspace_path, self.parent.active_project)
        self.existing_packages = list_packages(self.project_directory)

        rxi = QtCore.QRegExp(valid_integer_regex)
        integer_validator = QtGui.QRegExpValidator(rxi, self)
        rxPackageName = QtCore.QRegExp(valid_package_name_regex)
        package_validator = QtGui.QRegExpValidator(rxPackageName, self)

        self.PackageName.setValidator(package_validator)
        self.PackageName.textChanged.connect(self.validate)

        self.Pins.setValidator(integer_validator)
        self.Pins.textChanged.connect(self.validate)

        # self.PinListTableView
        
        self.Feedback.setText("")
        self.Feedback.setStyleSheet('color: orange')

        self.OKButton.clicked.connect(self.OKButtonPressed)
        self.CancelButton.clicked.connect(self.CancelButtonPressed)
        
        self.validate()
        self.show()

    def validate(self):
        
        feedback = ""

        package_name = self.PackageName.text()
        if package_name == "":
            feedback = "invalid package name"
        else:
            if package_name in self.existing_packages:
                feedback = "maskset already defined"

        number_of_pins = self.Pins.text() 
        if number_of_pins == "" and feedback == "":
            feedback = "invalid number of pins"

        self.Feedback.setText(feedback)
        if feedback == "":
            self.OKButton.setEnabled(True)
        else:
            self.OKButton.setEnabled(False)

    def OKButtonPressed(self):
        
        package_setup = {'package_name'   : self.PackageName.text(),
                         'number_of_pins' : int(self.Pins.text()),
                         'Pins'           : {1:'VDD', 2:'OUT', 3: 'GND'}
                     }
        create_new_package(self.parent.active_project_path, package_setup)
        self.accept()

    def CancelButtonPressed(self):
        self.accept()

def create_new_package(project_path, package_data):
    '''
    given a project_path, a package_name (in package_data),
    create the appropriate definition file for this new package.
    
        package_data = {'defines' : 'package',
                        'package_name' : str,
                        'number_of_pins' : int,
                        'Pins'           : dict{1:'VDD', 2:'OUT', 3: 'GND'}}
    '''
    if is_ATE_project(project_path):
        package_root = dict_project_paths(project_path)['package_root']
        package_name = package_data['package_name']
        package_path = os.path.join(package_root, "%s.pickle" % package_name)
        pickle.dump(package_data, open(package_path, 'wb'), protocol=4) # fixing the protocol guarantees compatibility

def new_package_dialog(parent):
    newPackageWizard = NewPackageWizard(parent)
    newPackageWizard.exec_()
    del(newPackageWizard) 

if __name__ == '__main__':
    import sys, qdarkstyle
    from ATE.org.actions.dummy_main import DummyMainWindow
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
    dummyMainWindow = DummyMainWindow()
    dialog = NewPackageWizard(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())
