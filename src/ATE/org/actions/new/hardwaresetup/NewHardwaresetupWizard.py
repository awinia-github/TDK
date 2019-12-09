'''
Created on Nov 18, 2019

@author: hoeren
'''
from PyQt5 import QtCore, QtWidgets, uic

import os, re

from ATE.org.listings import list_hardwaresetups, dict_project_paths
from ATE.org.validation import is_valid_pcb_name, is_ATE_project

class NewHardwaresetupWizard(QtWidgets.QDialog):

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

        existing_hardwaresetups = list_hardwaresetups(self.active_project_path)
        new_hardwaresetup_number = 1
        for hardwaresetup in existing_hardwaresetups:
            existing_hardwaresetup_number = int(hardwaresetup.replace('HWR', ''))
            if existing_hardwaresetup_number >= new_hardwaresetup_number:
                new_hardwaresetup_number+=1
        new_hardwaresetup_name = "HWR%s" % new_hardwaresetup_number

        self.blockSignals(True)

        self.HardwareSetup.setText(new_hardwaresetup_name)
        self.HardwareSetup.setEnabled(False)
        
        self.SingleSiteLoadboard.setText("")
        self.SingleSiteLoadboard.textChanged.connect(self.verify)

        self.MultiSiteLoadboard.setText("")
        self.MultiSiteLoadboard.textChanged.connect(self.verify)
        self.MultiSiteLoadboard.setEnabled(False)
        
        self.ProbeCard.setText("")
        self.ProbeCard.textChanged.connect(self.verify)
        
        self.SingleSiteDIB.setText("")
        self.SingleSiteDIB.textChanged.connect(self.verify)
        
        self.MultiSiteDIB.setText("")
        self.MultiSiteDIB.textChanged.connect(self.verify)
        self.MultiSiteDIB.setEnabled(False)
        
        self.Parallelism.clear()
        self.Parallelism.addItems(['%s'%(i+1) for i in range(16)])
        self.Parallelism.setCurrentIndex(0) # conforms to '1'
        self.Parallelism.currentTextChanged.connect(self.ParallelismChanged)
        self.parallelism = int(self.Parallelism.currentText())
        
        self.Feedback.setText("")
        self.Feedback.setStyleSheet('color: orange')
        
        self.OKButton.setEnabled(False)
        self.OKButton.clicked.connect(self.OKButtonPressed)
        
        self.CancelButton.setEnabled(True)
        self.CancelButton.clicked.connect(self.CancelButtonPressed)

        self.blockSignals(False)

        self.verify()
        self.show()

    def verify(self):
        if self.parallelism == 1:
            SingleSiteDIB = self.SingleSiteDIB.text()
            if is_valid_pcb_name(SingleSiteDIB):
                self.Feedback.setText("")
            else:
                self.Feedback.setText("invalid Singel Site DIB Name")
            ProbeCardName = self.ProbeCard.text()
            if is_valid_pcb_name(ProbeCardName):
                self.Feedback.setText("")
            else:
                self.Feedback.setText("invalid ProbeCard Name")
            SingleSiteLoadboardName = self.SingleSiteLoadboard.text()
            if is_valid_pcb_name(SingleSiteLoadboardName):
                self.Feedback.setText("")
            else:
                self.Feedback.setText("invalid Singel Site LoadBoard Name")
        else:
            MultiSiteDIB = self.MultiSiteDIB.text()
            if is_valid_pcb_name(MultiSiteDIB):
                self.Feedback.setText("")
            else:
                self.Feedback.setText("invalid Singel Site DIB Name")
            MultiSiteLoadboardName = self.MultiSiteLoadboard.text()
            if is_valid_pcb_name(MultiSiteLoadboardName):
                self.Feedback.setText("")
            else:
                self.Feedback.setText("invalid Singel Site DIB Name")
            SingleSiteDIB = self.SingleSiteDIB.text()
            if is_valid_pcb_name(SingleSiteDIB):
                self.Feedback.setText("")
            else:
                self.Feedback.setText("invalid Singel Site DIB Name")
            ProbeCardName = self.ProbeCard.text()
            if is_valid_pcb_name(ProbeCardName):
                self.Feedback.setText("")
            else:
                self.Feedback.setText("invalid ProbeCard Name")
            SingleSiteLoadboardName = self.SingleSiteLoadboard.text()
            if is_valid_pcb_name(SingleSiteLoadboardName):
                self.Feedback.setText("")
            else:
                self.Feedback.setText("invalid Singel Site LoadBoard Name")

        if self.Feedback.text()=="":
            if SingleSiteLoadboardName!="":
                self.OKButton.setEnabled(True)
            else:
                self.OKButton.setEnabled(False)

    def ParallelismChanged(self):
        self.parallelism = int(self.Parallelism.currentText())
        if self.parallelism == 1:
            self.MultiSiteLoadboard.setEnabled(False)
            self.MultiSiteDIB.setEnabled(False)
        else:
            self.MultiSiteLoadboard.setEnabled(True)
            self.MultiSiteDIB.setEnabled(True)
        self.update()

    def OKButtonPressed(self):
        #project_path, hardware_setup_version, hardware_data
        
        hwr_setup = {'defines' : 'hardwaresetup',
                     'hardwaresetup_name' : self.HardwareSetup.text(),
                     'parallelism' : self.parallelism,
                     'SingeSiteLoadboard' : self.SingleSiteLoadboard.text(),
                     'ProbeCard' : self.ProbeCard.text(),
                     'SingleSiteDIB' : self.SingleSiteDIB.text(),
                     'MultiSiteLoadboard' : self.MultiSiteLoadboard.text(),
                     'MultiSiteDIB' : self.MultiSiteDIB.text()
                     }
        create_new_hardwaresetup(self.active_project_path, hwr_setup)
        self.parent.active_hw = hwr_setup['hardwaresetup_name']
        self.accept()

    def CancelButtonPressed(self):
        self.accept()

def create_new_hardwaresetup(project_path, hardwaresetup_data):
    '''
    given a project_path, a hardwaresetup_name (in hardwaresetup_data),
    create the appropriate definition file for this new device.
    
    ps: hardwaresetup_name is for example HWR1, it is kind of a version too ;-)
    '''

    if is_ATE_project(project_path):
        hardwaresetup_name = hardwaresetup_data['hardwaresetup_name']
        hardwaresetup_root = dict_project_paths(project_path)['hwr_root']
        hardwaresetup_path =os.path.join(hardwaresetup_root, "%s.pickle" % hardwaresetup_name)
        pickle.dump(hardwaresetup_data, open(hardwaresetup_path, 'wb'), protocol=4) # fixing the protocol guarantees compatibility

def new_hardwaresetup_dialog(parent):
    newHardwaresetupWizard = NewHardwaresetupWizard(parent)
    newHardwaresetupWizard.exec_()
    del(newHardwaresetupWizard)        

if __name__ == '__main__':
    import sys, qdarkstyle
    from ATE.org.actions.dummy_main import DummyMainWindow
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
    dummyMainWindow = DummyMainWindow()
    dialog = NewHardwaresetupWizard(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())