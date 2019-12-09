# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 14:32:40 2019

@author: hoeren
"""
from PyQt5 import QtGui, QtCore, QtWidgets, uic

import os, re

import pickle

from ATE.org.listings import list_dies, list_masksets, dict_project_paths
from ATE.org.validation import valid_die_name_regex, is_ATE_project


class NewDieWizard(QtWidgets.QDialog):

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        
        my_ui = __file__.replace('.py', '.ui')
        if not os.path.exists(my_ui):
            raise Exception("can not find %s" % my_ui)
        uic.loadUi(my_ui, self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', os.path.basename(__file__).replace('.py', ''))))
 
        self.parent = parent
        self.project_path = os.path.join(self.parent.workspace_path, self.parent.active_project)

        self.existing_masksets = [''] + list_masksets(self.project_path)
        self.existing_dies = list_dies(self.project_path)

        rxDieName = QtCore.QRegExp(valid_die_name_regex)
        DieName_validator = QtGui.QRegExpValidator(rxDieName, self)
        self.NewDieName.setText("")        
        self.NewDieName.setValidator(DieName_validator)
        self.NewDieName.textChanged.connect(self.verify)

        self.FromMaskset.blockSignals(True)
        self.FromMaskset.clear()
        self.FromMaskset.addItems(self.existing_masksets)
        self.FromMaskset.setCurrentIndex(0) # this is the empty string !
        self.FromMaskset.currentIndexChanged.connect(self.verify)
        self.FromMaskset.blockSignals(False)

        self.Feedback.setText("No die name")
        self.Feedback.setStyleSheet('color: orange')
    
        self.CancelButton.clicked.connect(self.CancelButtonPressed)    
        self.OKButton.clicked.connect(self.OKButtonPressed)
        self.OKButton.setEnabled(False)
        
        self.verify()
        self.show()

    def verify(self):
        if self.NewDieName.text() in self.existing_dies:
            self.Feedback.setText("Die name already exists !")
            self.OKButton.setEnabled(False)
        else:
            if self.FromMaskset.currentText() == "":
                self.Feedback.setText("No maskset selected")
                self.OKButton.setEnabled(False)
            else:
                self.Feedback.setText("")
                self.OKButton.setEnabled(True)

    def CancelButtonPressed(self):
        self.accept()
    
    def OKButtonPressed(self):
        die_data = {}
        die_data['defines'] = 'die'
        die_data['die_name'] = self.NewDieName.text()
        die_data['maskset_name'] = self.FromMaskset.currentText()
        create_new_die(self.parent.active_project_path, die_data)
        self.accept()
        
def create_new_die(project_path, die_data):
    '''
    given a project_path, a die_name (in die_data), 
    create the appropriate definition file for this new die.

    die_data = {'defines' : 'die'
                'die_name' : str,
                'maskset_name' : str}
    '''
    if is_ATE_project(project_path):
        die_root = dict_project_paths(project_path)['die_root']
        die_name = die_data['die_name']
        die_path = os.path.join(die_root, "%s.pickle" % die_name)
        pickle.dump(die_data, open(die_path, 'wb'), protocol=4) # fixing the protocol guarantees compatibility

def new_die_dialog(parent):
    newDieWizard = NewDieWizard(parent)
    newDieWizard.exec_()
    del(newDieWizard)            
        
if __name__ == '__main__':
    import sys, qdarkstyle
    from ATE.org.actions.dummy_main import DummyMainWindow
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
    dummyMainWindow = DummyMainWindow()
    dialog = NewDieWizard(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())
