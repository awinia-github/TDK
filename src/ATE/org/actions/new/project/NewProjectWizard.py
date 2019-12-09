'''
Created on Nov 18, 2019

@author: hoeren
'''
from PyQt5 import QtGui, QtCore, QtWidgets, uic

import os, re

from ATE.org.listings import list_ATE_projects
from ATE.org.validation import valid_project_name_regex, is_valid_project_name

class NewProjectWizard(QtWidgets.QDialog):

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        
        my_ui = __file__.replace('.py', '.ui')
        if not os.path.exists(my_ui):
            raise Exception("can not find %s" % my_ui)
        uic.loadUi(my_ui, self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', os.path.basename(__file__).replace('.py', ''))))


        rxProjectName = QtCore.QRegExp(valid_project_name_regex)
        ProjectName_validator = QtGui.QRegExpValidator(rxProjectName, self)
        self.ProjectName.setValidator(ProjectName_validator)
        self.ProjectName.setText("")
        self.ProjectName.textChanged.connect(self.verify)
        # self.ProjectName.returnPressed.connect(self.PressedEnter)

        self.existing_projects = list_ATE_projects(self.parent.workspace_path)
    
        self.Feedback.setStyleSheet('color: orange')

        self.OKButton.clicked.connect(self.OKButtonPressed)
        self.CancelButton.clicked.connect(self.CancelButtonPressed)

        self.verify()
        self.show()

    def verify(self):
        feedback = ""

        project_name = self.ProjectName.text()
        if project_name == "":
            feedback = "Invalid project name"
        elif project_name in self.existing_projects:
            feedback = "project already defined"
        else:
            if not is_valid_project_name(project_name):
                feedback = "Invalid project name"

        self.Feedback.setText(feedback)

        if feedback == "":
            self.OKButton.setEnabled(True)
        else:
            self.OKButton.setEnabled(False)

    # def PressedEnter(self):
    #     if self.Feedback.text() == "": # no feedback means that the name is ok
    #         self.OKButtonPressed()
    #     else:
    #         self.CancelButtonPressed()
    
    def OKButtonPressed(self):
        project_name = self.ProjectName.text()
        create_ATE_project(self.parent.workspace_path, project_name)
        #switch the parent to this new project
        self.parent.active_project = project_name
        self.parent.active_project_path = os.path.join(self.parent.workspace_path, self.parent.active_project)
        self.accept()
        
    def CancelButtonPressed(self):
        self.accept()

def create_ATE_project(workspace_path, project_name):
    '''
    create a new (empty) ATE project named project_name in 'workspace_path'

    project_name directory in workspace_path shouldn't exist prior to this
    call.
    '''
    from ATE.org.Templates import templating, project_structure, translation_template
    
    if not os.path.exists(workspace_path):
        raise Exception("workspace '%s' doesn't exist" % workspace_path)
    
    project_path = os.path.join(workspace_path, project_name)
    if os.path.exists(project_path):
        raise Exception("'%s' already exists" % project_path)

    translations = translation_template(project_path)

    for branch in project_structure:
        branch_path = os.path.normpath(os.path.join(project_path, branch.replace('/', os.path.sep))) # always a directory
        print(branch_path)
        if not os.path.exists(branch_path):
            os.makedirs(branch_path, exist_ok = True)
        _, branch_templates = project_structure[branch] # branch_templates is a list of tuples (source, destination, mode)
        for template in branch_templates: # template is a tuple(source, destination, mode)
            source = template[0]
            destination = os.path.join(branch_path, template[1])
            mode = template[2]
            
            if '%' in destination: # do translation in the name!
                for translation in translations:
                    replacement = "%%%s%%" % translation
                    if replacement in destination:
                        destination = destination.replace(replacement, translations[translation])
            
            templating(source, destination, mode, translations)

def new_project_dialog(parent):
    newProjectWizard = NewProjectWizard(parent)
    newProjectWizard.exec_()
    del(newProjectWizard)  

if __name__ == '__main__':
    import sys, qdarkstyle
    from ATE.org.actions.dummy_main import DummyMainWindow
    
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
    dummyMainWindow = DummyMainWindow()
    dialog = NewProjectWizard(dummyMainWindow)
    dummyMainWindow.register_dialog(dialog)
    sys.exit(app.exec_())    