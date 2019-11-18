'''
Created on Nov 18, 2019

@author: hoeren
'''
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileSystemModel, QTreeView, QWidget, QVBoxLayout, QDialog
from PyQt5.Qt import QFileDialog

import qdarkstyle
import qtawesome as qta

from ui.Ui_MainWindow import Ui_MainWindow

import os
import Ui_NewProjectDialog

workspace = r"C:\__spyder_workspace__"

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self) # setup from Designer (layout)
        self.workspace_setup()
        self.initUI()         # setup from below (handlers)
        self.show()

    def initUI(self):
        self.setWindowTitle("Spyder MockUp")

        self.ui.action_new_test.triggered.connect(self.new_test)
        self.ui.action_new_test.setEnabled(False)
        self.ui.action_new_maskset.triggered.connect(self.new_maskset)
        self.ui.action_new_maskset.setEnabled(False)
        self.ui.action_new_device.triggered.connect(self.new_device)
        self.ui.action_new_device.setEnabled(False)
        self.ui.action_new_die.triggered.connect(self.new_die)
        self.ui.action_new_die.setEnabled(False)
        self.ui.action_new_product.triggered.connect(self.new_product)
        self.ui.action_new_product.setEnabled(False)
        self.ui.action_new_project.triggered.connect(self.new_project)
        self.ui.action_new_project.setEnabled(True)
        
        self.ui.action_edit_test.triggered.connect(self.edit_test)
        self.ui.action_edit_test.setEnabled(False)
        self.ui.action_edit_maskset.triggered.connect(self.edit_maskset)
        self.ui.action_edit_maskset.setEnabled(False)
        self.ui.action_edit_device.triggered.connect(self.edit_device)
        self.ui.action_edit_device.setEnabled(False)
        self.ui.action_edit_die.triggered.connect(self.edit_die)
        self.ui.action_edit_die.setEnabled(False)
        self.ui.action_edit_product.triggered.connect(self.edit_product)
        self.ui.action_edit_product.setEnabled(False)
        self.ui.action_edit_flow.triggered.connect(self.edit_flow)
        self.ui.action_edit_flow.setEnabled(False)
        self.ui.action_edit_project.triggered.connect(self.edit_project)
        self.ui.action_edit_project.setEnabled(True)
        
        self.ui.action_display_test.triggered.connect(self.display_test)
        self.ui.action_display_test.setEnabled(False)
        self.ui.action_display_maskset.triggered.connect(self.display_maskset)
        self.ui.action_display_maskset.setEnabled(False)
        self.ui.action_display_device.triggered.connect(self.display_device)
        self.ui.action_display_device.setEnabled(False)
        self.ui.action_display_die.triggered.connect(self.display_die)
        self.ui.action_display_die.setEnabled(False)
        self.ui.action_display_product.triggered.connect(self.display_product)
        self.ui.action_display_product.setEnabled(False)
        self.ui.action_display_flow.triggered.connect(self.display_flow)
        self.ui.action_display_flow.setEnabled(False)

        self.ui.action_delete_test.triggered.connect(self.delete_test)
        self.ui.action_delete_test.setEnabled(False)
        self.ui.action_delete_maskset.triggered.connect(self.delete_maskset)
        self.ui.action_delete_maskset.setEnabled(False)
        self.ui.action_delete_device.triggered.connect(self.delete_device)
        self.ui.action_delete_device.setEnabled(False)
        self.ui.action_delete_die.triggered.connect(self.delete_die)
        self.ui.action_delete_die.setEnabled(False)
        self.ui.action_delete_product.triggered.connect(self.delete_product)
        self.ui.action_delete_product.setEnabled(False)
        self.ui.action_delete_flow.triggered.connect(self.delete_flow)
        self.ui.action_delete_flow.setEnabled(False)
        self.ui.action_delete_project.triggered.connect(self.delete_project)
        self.ui.action_delete_project.setEnabled(True)
        
        self.show()

    def workspace_setup(self):
        self.workspace = workspace
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        for project in self.list_projects_in_workspace():
            print(project)

    def list_projects_in_workspace(self):
        retval = []
        for possible_project_dir in os.listdir(self.workspace):
            if os.path.isdir(possible_project_dir):
                retval.append(possible_project_dir)
                #TODO: look in the directories
        return retval

    def tree_update(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(self.project_root)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(False)
        self.tree.setWindowTitle("Dir view")
#         self.tree.resize(640, 480)
        windowLayout = QVBoxLayout()
        windowLayout.addWidget(self.tree)
        self.setLayout(windowLayout)
        
    def new_device(self):
        print("new device")
        
    def new_die(self):
        print("new die")
        
    def new_maskset(self):
        print("new maskset")
        
    def new_product(self):
        print("new product")
        
    def new_test(self):
        print("new test")
        
    def new_project(self):
        from NewProjectDialog import NewProjectDialog
        newProjectDialog = NewProjectDialog(self)       
        newProjectDialog.exec_() 
        del(newProjectDialog)
        
    def edit_device(self):
        print("edit device")
        
    def edit_die(self):
        print("edit die")
        
    def edit_maskset(self):
        print("edit maskset")
        
    def edit_product(self):
        print("edit product")
        
    def edit_test(self):
        print("edit test")
        
    def edit_project(self):
        print("edit project")

    def edit_flow(self):
        print("edit flow")
    
    def display_device(self):
        print("display device")
        
    def display_die(self):
        print("display die")
        
    def display_flow(self):
        print("display flow")
        
    def display_maskset(self):
        print("display maskset")
        
    def display_product(self):
        print("display product")
        
    def display_test(self):
        print("display test")
        
    def delete_device(self):
        print("delete device")
        
    def delete_die(self):
        print("delete die")
        
    def delete_flow(self):
        print("delete flow")
    
    def delete_maskset(self):
        print("delete maskset")
        
    def delete_product(self):
        print("delete product")
        
    def delete_test(self):
        print("delete test")
        
    def delete_project(self):
        print("delete project")

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window.show()
    sys.exit(app.exec_())
