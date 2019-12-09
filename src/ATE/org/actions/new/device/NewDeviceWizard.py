# -*- coding: utf-8 -*-
"""
Created on Wed Nov 27 15:09:41 2019

@author: hoeren
"""
from PyQt5 import QtGui, QtCore, QtWidgets, uic

import os, re, pickle

from ATE.org.listings import list_devices, list_dies, list_packages, dict_project_paths
from ATE.org.validation import valid_device_name_regex, is_ATE_project

import qtawesome as qta

class NewDeviceWizard(QtWidgets.QDialog):

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        
        my_ui = __file__.replace('.py', '.ui')
        if not os.path.exists(my_ui):
            raise Exception("can not find %s" % my_ui)
        uic.loadUi(my_ui, self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', os.path.basename(__file__).replace('.py', ''))))
 
        self.workspace_path = parent.workspace_path
        self.active_project = parent.active_project
        self.active_project_path = parent.active_project_path
    
        self.existing_devices = list_devices(self.active_project_path)
        self.DeviceName.setText("")        
        rxDeviceName = QtCore.QRegExp(valid_device_name_regex)
        DeviceName_validator = QtGui.QRegExpValidator(rxDeviceName, self)
        self.DeviceName.setValidator(DeviceName_validator)
        self.DeviceName.textChanged.connect(self.verify)
        
        self.existing_packages = list_packages(self.active_project_path)
        self.Package.blockSignals(True)
        self.Package.clear()
        self.Package.addItems(['', 'None'] + self.existing_packages)
        self.Package.setCurrentIndex(0) # this is the empty string !
        self.Package.currentIndexChanged.connect(self.verify)
        self.Package.blockSignals(False)

        self.existing_dies = list_dies(self.active_project_path)
        self.AvailableDies.blockSignals(True)
        self.AvailableDies.clear()
        self.AvailableDies.addItems(self.existing_dies)
        self.AvailableDies.clearSelection()
        self.AvailableDies.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.AvailableDies.blockSignals(False)
        
        self.AddDie.setEnabled(True)
        self.AddDie.setIcon(qta.icon('mdi.arrow-right-bold-outline', color='orange'))
        self.AddDie.clicked.connect(self.add_dies)
        
        self.RemoveDie.setEnabled(True)
        self.RemoveDie.setIcon(qta.icon('mdi.arrow-left-bold-outline', color='orange'))
        self.RemoveDie.clicked.connect(self.remove_dies)
        
        self.dies_in_device = []
        self.DiesInDevice.blockSignals(True)
        self.DiesInDevice.clear()
        self.DiesInDevice.addItems(self.dies_in_device)
        self.DiesInDevice.clearSelection()
        self.DiesInDevice.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.DiesInDevice.blockSignals(False)
        
        self.Feedback.setStyleSheet('color: orange')
        
        self.CancelButton.clicked.connect(self.CancelButtonPressed)    
        self.OKButton.clicked.connect(self.OKButtonPressed)

        self.verify()
        self.show()

    def add_dies(self):
        self.DiesInDevice.blockSignals(True)
        for die_to_add in self.AvailableDies.selectedItems():
            self.DiesInDevice.insertItem(self.DiesInDevice.count(), die_to_add.text())
        self.DiesInDevice.clearSelection()
        self.AvailableDies.clearSelection()
        self.DiesInDevice.blockSignals(False)
        self.verify()

    def remove_dies(self):
        self.DiesInDevice.blockSignals(True)
        self.DiesInDevice.takeItem(self.DiesInDevice.selectedIndexes()[0].row()) # DiesInDevice set to SingleSelection ;-)
        self.DiesInDevice.clearSelection()
        self.AvailableDies.clearSelection()
        self.DiesInDevice.blockSignals(False)
        self.verify()

    def verify(self):
        feedback = ""

        device_name = self.DeviceName.text()
        if device_name == "":
            feedback = "Invalid device name"
        elif device_name in self.existing_devices:
            feedback = "device already defined"
        else:
            package_name = self.Package.currentText()
            if package_name == '':
                feedback = "No package selected"
            elif package_name == 'None':
                number_of_dies_in_device = self.DiesInDevice.count()
                if number_of_dies_in_device != 1:
                    feedback = "Naked die device needs exactly 1 die"
            else:
                number_of_dies_in_device = self.DiesInDevice.count()
                if number_of_dies_in_device < 1:
                    feedback = "device needs minimal 1 die"

        self.Feedback.setText(feedback)

        if feedback == "":
            self.OKButton.setEnabled(True)
        else:
            self.OKButton.setEnabled(False)

    def CancelButtonPressed(self):
        self.accept()
    
    def OKButtonPressed(self):
        device_data = {}
        device_data['defines'] = 'device'
        device_data['device_name'] = self.DeviceName.text()
        device_data['package_name'] = self.Package.currentText()
        device_data['dies_in_package'] = [] 
        for die_obj in self.DiesInDevice.findItems('*', QtCore.Qt.MatchWrap | QtCore.Qt.MatchWildcard):
            device_data['dies_in_package'].append(die_obj.text())
        create_new_device(self.parent.active_project_path, device_data)
        self.accept()

def create_new_device(project_path, device_data):
    '''
    given a project_path, a device_name (in device_data),
    create the appropriate definition file for this new device.
    
        device_data = {'defines' : 'device'
                       'device_name' : str
                       'package' : str
                       'dies_in_package' : list[die_names]}
    '''
    if is_ATE_project(project_path):
        device_root = dict_project_paths(project_path)['device_root']
        device_name = device_data['device_name']
        device_path = os.path.join(device_root, "%s.pickle" % device_name)
        pickle.dump(device_data, open(device_path, 'wb'), protocol=4) # fixing the protocol guarantees compatibility

def new_device_dialog(parent):
    newDeviceWizard = NewDeviceWizard(parent)
    newDeviceWizard.exec_()
    del(newDeviceWizard)        

if __name__ == '__main__':
    import sys, qdarkstyle
    from ATE.org.actions.dummy_main import DummyMainWindow
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
    dummyMainWindow = DummyMainWindow()
    dialog = NewDeviceWizard(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())
