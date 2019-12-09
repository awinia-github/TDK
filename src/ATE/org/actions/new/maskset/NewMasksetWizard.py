'''
Created on Nov 20, 2019

@author: hoeren
'''
from PyQt5 import QtWidgets, QtCore, QtGui, uic

import os, re, pickle

from ATE.org.validation import is_valid_maskset_name, is_ATE_project
from ATE.org.listings import list_masksets, dict_project_paths

class NewMasksetWizard(QtWidgets.QDialog):

    def __init__(self, parent):
        super().__init__()
        
        my_ui = __file__.replace('.py', '.ui')
        if not os.path.exists(my_ui):
            raise Exception("can not find %s" % my_ui)
        uic.loadUi(my_ui, self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', os.path.basename(__file__).replace('.py', ''))))

        self.parent = parent
        self.project_directory = os.path.join(self.parent.workspace_path, self.parent.active_project)
        self.existing_masksets = list_masksets(self.project_directory)

        from ATE.org.validation import valid_integer_regex
        rxi = QtCore.QRegExp(valid_integer_regex)
        integer_validator = QtGui.QRegExpValidator(rxi, self)
        from ATE.org.validation import valid_maskset_name_regex
        rxMaskSetName = QtCore.QRegExp(valid_maskset_name_regex)
        MasksetName_validator = QtGui.QRegExpValidator(rxMaskSetName, self)

        self.MasksetName.setText("")        
        self.MasksetName.setValidator(MasksetName_validator)
        self.MasksetName.textChanged.connect(self.validate)
        
        self.WaferDiameter.setText("200")
        self.WaferDiameter.setValidator(integer_validator)
        self.WaferDiameter.textChanged.connect(self.validate)
        
        self.Bondpads.setValidator(integer_validator)
        self.Bondpads.textChanged.connect(self.validate)

        self.DieSizeX.setValidator(integer_validator)
        self.DieSizeX.textChanged.connect(self.validate)

        self.DieSizeY.setValidator(integer_validator)
        self.DieSizeY.textChanged.connect(self.validate)

        self.ScribeX.setValidator(integer_validator)
        self.ScribeX.textChanged.connect(self.validate)

        self.ScribeY.setValidator(integer_validator)
        self.ScribeY.textChanged.connect(self.validate)

        #TODO: self.NewMasksetTableView
        
        self.Feedback.setText("")
        self.Feedback.setStyleSheet('color: orange')

        self.OKButton.clicked.connect(self.OKButtonPressed)
        self.CancelButton.clicked.connect(self.CancelButtonPressed)
        
        self.validate()
        self.show()

    def validate(self):
        
        feedback = ""

        maskset_name = self.MasksetName.text()
        if maskset_name == "":
            feedback = "Invalid maskset name"
        else:
            if maskset_name in self.existing_masksets:
                feedback = "maskset already defined"
            if not is_valid_maskset_name(maskset_name):
                feedback = "Invalid maskset name"

        number_of_bond_pads = self.Bondpads.text() 
        if number_of_bond_pads == "" and feedback == "":
            feedback = "No valid number of bond pads"

        die_size_x = self.DieSizeX.text() 
        if die_size_x == ""  and feedback == "":
            feedback = "No valid die size X"

        die_size_y = self.DieSizeY.text()
        if die_size_y == ""  and feedback == "":
            feedback = "No valid die size Y"

        scribe_x = self.ScribeX.text()
        if scribe_x == "" and feedback == "":
            feedback = "No valid scribe X"

        scribe_y = self.ScribeY.text()
        if scribe_y == "" and feedback == "":
            feedback = "No valid scribe Y"

        self.Feedback.setText(feedback)
        if feedback == "":
            self.OKButton.setEnabled(True)
        else:
            self.OKButton.setEnabled(False)

    def OKButtonPressed(self):
        maskset_data = {
            'defines'             : 'maskset',
            'maskset_name'        : self.MasksetName.text(),
            'number_of_bond_pads' : int(self.Bondpads.text()),
            'die_size_x'          : int(self.DieSizeX.text()),
            'die_size_y'          : int(self.DieSizeY.text()),
            'scribe_x'            : int(self.ScribeX.text()),
            'scribe_y'            : int(self.ScribeY.text()),
            #            pinNr  Name           xcoord    ycoord     xsize    ysize
            'bond_pads' : {1: ('bondpad1name', 100,      100,       90,      90),
                           2: ('bondpad2name', -100,     -100,      90,      90)
                          #TODO: recuperate above info from wizard
                           },
            'rotation_to_flat' : 0
            #TODO: add the rotation (0, 90, 180, 270) to the ui
            }

        create_new_maskset(self.parent.active_project_path, maskset_data)
        self.accept()
    
    def CancelButtonPressed(self):
        self.accept()

def create_new_maskset(project_path, maskset_data):
    '''
    given a project_path, a maskset_name (in maskset_data),
    create the appropriate definition file for this new maskset.
    
    maskset_data = {'defines' : 'maskset'
                    'maskset_name' : str,
                    'number_of_bond_pads' : int, # in μm
                    'die_size_x' : int, # in μm
                    'die_size_y' : int, # in μm
                    'scribe_x' : int, # in μm
                    'scribe_y' : int, # in μm
                    'bond_pads' : dict{int'padNr' : tuple(str'Name', int'xcoord', int'ycoord', int'xsize', int'ysize')}, # in μm
                    'rotation_to_flat' : int # = 0/90/180/270}
    '''
    if is_ATE_project(project_path):
        maskset_root = dict_project_paths(project_path)['maskset_root']
        maskset_name = maskset_data['maskset_name']
        maskset_path = os.path.join(maskset_root, "%s.pickle" % maskset_name)
        print(maskset_path)
        pickle.dump(maskset_data, open(maskset_path, 'wb'), protocol=4) # fixing the protocol guarantees compatibility

def new_maskset_dialog(parent):
    newMasksetWizard = NewMasksetWizard(parent)
    newMasksetWizard.exec_()
    del(newMasksetWizard)     

if __name__ == '__main__':
    import sys, qdarkstyle
    from ATE.org.actions.dummy_main import DummyMainWindow
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
    dummyMainWindow = DummyMainWindow()
    dialog = NewMasksetWizard(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())