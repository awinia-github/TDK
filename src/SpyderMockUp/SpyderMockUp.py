'''
Created on Nov 18, 2019

@author: hoeren (horen.tom@micronas.com)


https://www.google.com

file://./documentation/STDF_V4.pdf

'''
from PyQt5 import QtWidgets, QtCore, QtGui, uic

import qdarkstyle
import qtawesome as qta

import os, sys
import re
import shutil
import sqlite3
import importlib

from ATE.org.listings import list_projects, list_ATE_projects, list_MiniSCTs, list_hardwaresetups, listings, dict_project_paths

workspace_path = os.path.normpath(os.path.join(os.path.dirname(__file__), r"./../__spyder_workspace__"))

class screenCast(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()
    rightClicked = QtCore.pyqtSignal()
    
    def __init(self, parent):
        super().__init__(parent)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            self.rightClicked.emit()
        else:
            self.clicked.emit()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
    # get the appropriate .ui file and load it.
        my_ui = __file__.replace('.py', '.ui')
        if not os.path.exists(my_ui):
            raise Exception("'%s' doesn't exist" % my_ui)
        uic.loadUi(my_ui, self)
        
    # Initialize the main window        
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle(' '.join(re.findall('.[^A-Z]*', os.path.basename(__file__).replace('.py', ''))))

    # Check if OpenCV is available (without loading it !)
        spec = importlib.util.find_spec('cv2')
        self.open_cv_available = spec is not None
        
    # setup initial paths    
        self.workspace_path = workspace_path
        if not os.path.exists(self.workspace_path):
            os.makedirs(self.workspace_path)

        self.tester_list = list_MiniSCTs()
        self.active_tester = self.tester_list[0] # start with the first in the list
        print("active_tester =", self.active_tester)

        self.ATE_projects = list_ATE_projects(workspace_path) + ['']
        self.active_project = self.ATE_projects[0] # there is always something
        if self.active_project != '':
            self.active_project_path = os.path.join(self.workspace_path, self.active_project)
            self.project_info = listings(self.active_project_path)
        else:
            self.active_project_path = None
            self.project_info = None
        print("active_project =", self.active_project)
            
        if self.project_info != None:
            self.hw_list = self.project_info.list_hardwaresetups()
            if self.hw_list != []:
                self.active_hw = self.hw_list[-1] # take the most recent hardware setup
            else:
                self.active_hw = ''
        else:
            self.active_hw = ''
        print("active_hw =", self.active_hw)


        if self.project_info != None:
            self.active_base = 'Product' # or 'Die'
            pass
        else:
            self.active_base = ''

    # connect the File/New/Project menu
        self.action_new_project.triggered.connect(self.new_project)

    # setup the project explorer
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.context_menu_manager)


    # setup the screencaster
        self.screencast = screenCast()
        self.screencast.setPixmap(qta.icon('mdi.video', color='orange').pixmap(16,16))   
        self.screencast_state = 'idle'
        self.screencast.clicked.connect(self.screencast_start_stop)
        self.screencast.rightClicked.connect(self.screencast_settings)

        self.statusBar().addPermanentWidget(self.screencast)

    # setup the toolbar
        self.toolbar = self.create_toolbar() # sets active_tester, active_project, hwr (and base if necessary)



        self.update_toolbar()


        self.update_testers()
        self.update_projects()        
        self.update_hardware()

        self.tree_update()
        #self.update_project_list()
        self.update_menu()
        self.show()

    def closeEvent(self, event=None):
        self.close()

    def create_toolbar(self):
        '''
        This method will create the toolbar (once, like etention of __init__)
        '''        
        toolbar = self.addToolBar('toolbar')
        toolbar.setMovable(False)

        tester_label = QtWidgets.QLabel("Tester:")
        tester_label.setStyleSheet("background-color: rgba(0,0,0,0%)")
        toolbar.addWidget(tester_label)
        
        self.tester_combo = QtWidgets.QComboBox()
        self.tester_combo.clear()
        toolbar.addWidget(self.tester_combo)

        refreshTesters = QtWidgets.QAction(qta.icon('mdi.refresh', color='orange'), "Refresh Testers", self)
        refreshTesters.setStatusTip("Refresh the tester list")
        refreshTesters.triggered.connect(self.update_testers)
        refreshTesters.setCheckable(False)
        toolbar.addAction(refreshTesters)        

        run_action = QtWidgets.QAction(qta.icon('mdi.play-circle-outline', color='orange'), "Run", self)
        run_action.setStatusTip("Run active module")
        run_action.triggered.connect(self.onRun)
        run_action.setCheckable(False)
        toolbar.addAction(run_action)
        
        project_label = QtWidgets.QLabel("Project:")
        project_label.setStyleSheet("background-color: rgba(0,0,0,0%)")
        toolbar.addWidget(project_label)
        
        self.project_combo = QtWidgets.QComboBox()
        self.project_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.project_combo.currentTextChanged.connect(self.projectChanged)
        self.project_combo.clear()
        toolbar.addWidget(self.project_combo)
        
        project_refresh = QtWidgets.QAction(qta.icon('mdi.refresh', color='orange'), "Refresh Projects", self)
        project_refresh.setStatusTip("Refresh the project list")
        project_refresh.triggered.connect(self.update_projects)
        project_refresh.setCheckable(False)
        toolbar.addAction(project_refresh)        
        
        hw_label = QtWidgets.QLabel("Hardware:")
        hw_label.setStyleSheet("background-color: rgba(0,0,0,0%)")
        toolbar.addWidget(hw_label)
        
        self.hw_combo = QtWidgets.QComboBox()
        self.hw_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.hw_combo.currentTextChanged.connect(self.hardwareChanged)
        self.hw_combo.clear()
        toolbar.addWidget(self.hw_combo)
        
        base_label = QtWidgets.QLabel("Base:")
        base_label.setStyleSheet("background-color: rgba(0,0,0,0%)")
        toolbar.addWidget(base_label)
        
        self.base_combo = QtWidgets.QComboBox()
        self.base_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.base_combo.clear()
        toolbar.addWidget(self.base_combo)

        info_action = QtWidgets.QAction(qta.icon('mdi.information-outline', color='orange'), "Information", self)
        info_action.setStatusTip("print current information")
        info_action.triggered.connect(self.printInfo)
        info_action.setCheckable(False)
        toolbar.addAction(info_action)

        settings_action = QtWidgets.QAction(qta.icon('mdi.wrench', color='orange'), "Settings", self)
        settings_action.setStatusTip("Settings")
        settings_action.triggered.connect(self.onSettings)
        settings_action.setCheckable(False)
        toolbar.addAction(settings_action)

        return toolbar
    
    def update_toolbar(self):
        '''
        This method will update the toolbar.
        '''
        pass

    def context_menu_manager(self, point):
        #https://riverbankcomputing.com/pipermail/pyqt/2009-April/022668.html
        #https://doc.qt.io/qt-5/qtreewidget-members.html
        #https://www.qtcentre.org/threads/18929-QTreeWidgetItem-have-contextMenu
        index = self.tree.indexAt(point)
        if not index.isValid():
            return
        item = self.tree.itemAt(point)
        self.node_name = item.text(0)
        self.node_type = item.text(1)
        self.node_data = item.text(2)

        if self.node_type == 'project':
            menu = QtWidgets.QMenu(self)
            audit = menu.addAction(qta.icon("mdi.incognito", color='orange') ,"audit")
            audit.triggered.connect(self.placeholder)
            pack = menu.addAction(qta.icon("mdi.gift-outline", color='orange'), "pack")
            menu.exec_(QtGui.QCursor.pos())
        elif self.node_type == 'docs_root' :
            menu = QtWidgets.QMenu(self)
            new_folder = menu.addAction(qta.icon("mdi.folder-plus-outline", color='orange'), "New Folder")
            new_folder.triggered.connect(self.new_folder)
            rename_folder = menu.addAction(qta.icon("mdi.folder-edit-outline", color='orange'), "Rename Folder")
            import_document = menu.addAction(qta.icon("mdi.folder-download-outline", color='orange'), "Import Document")
            menu.exec_(QtGui.QCursor.pos())
        elif self.node_type == 'docs':
            menu = QtWidgets.QMenu(self)
            new_folder = menu.addAction(qta.icon("mdi.folder-plus-outline", color='orange'), "New Folder")
            rename_folder = menu.addAction(qta.icon("mdi.folder-edit-outline", color='orange'), "Rename Folder")
            import_document = menu.addAction(qta.icon("mdi.folder-download-outline", color='orange'), "Import Document")
            menu.addSeparator()
            delete_folder = menu.addAction(qta.icon("mdi.folder-remove-outline", color='orange'), "Delete Folder")
            menu.exec_(QtGui.QCursor.pos())
        elif self.node_type == 'doc':
            menu = QtWidgets.QMenu(self)
            open_file = menu.addAction(qta.icon("mdi.file-edit-outline", color='orange'), "Open")
            rename_file = menu.addAction(qta.icon("mdi.lead-pencil", color='orange'), "Rename")
            menu.addSeparator()
            delete_file = menu.addAction(qta.icon("mdi.eraser", color='orange'), "Delete")
            menu.exec_(QtGui.QCursor.pos())
        
        
        



    def update_testers(self):
        tester_list = list_MiniSCTs()
        old_tester_list = [self.tester_combo.itemText(i) for i in range(self.tester_combo.count())]
        if set(tester_list) != set(old_tester_list): 
            self.tester_combo.blockSignals(True)
            self.tester_combo.clear()
            self.tester_combo.addItems(tester_list)
            if self.active_tester in tester_list:
                self.tester_combo.setCurrentIndex(self.tester_list.index(self.active_tester))
            else:
                self.tester_combo.setCurrentIndex(0)
            self.active_tester = self.tester_combo.currentText()
            self.tester_combo.blockSignals(False)

    def update_projects(self):
        print("update_projects")
        all_projects = list_projects(self.workspace_path)
        ATE_projects = list_ATE_projects(workspace_path)
        old_projects = [self.project_combo.itemText(i) for i in range(self.project_combo.count())]

        if len(ATE_projects) == 0:
            ATE_projects.append('')
            all_projects.append('')
            self.active_project = ''

        if self.active_project not in ATE_projects:
            self.active_project = ATE_projects[0]
            
        if set(all_projects) != set(old_projects):
            self.project_combo.blockSignals(True)
            self.project_combo.clear()
            for index, project in enumerate(all_projects):
                self.project_combo.addItem(project)
                if project not in ATE_projects:
                    self.project_combo.model().item(index).setEnabled(False)
                if project == self.active_project:
                    self.project_combo.setCurrentIndex(index)
            self.project_combo.blockSignals(False)
        
        self.active_project_path = os.path.join(self.workspace_path, self.active_project)
        self.update_hardware()
        
    def update_hardware(self):
        print("update_hardware (%s)" % self.active_project)
        hw_list = self.project_info.list_hardwaresetups()
        old_hw_list = [self.hw_combo.itemText(i) for i in range(self.hw_combo.count())]
        
        if len(hw_list) == 0:
            hw_list.append('')
            self.active_hw = ''
            
        if self.active_hw not in hw_list:
            self.active_hw = hw_list[0]

        if set(hw_list) != set(old_hw_list):
            self.hw_combo.blockSignals(True)
            self.hw_combo.clear()
            for index, hw in enumerate(hw_list):
                self.hw_combo.addItem(hw)
                if hw == self.active_hw:
                    self.hw_combo.setCurrentIndex(index)
            self.hw_combo.blockSignals(False)
        
    def update_menu(self):
        if self.active_project == None: # no active project
            self.active_project_path = None
        else: # we have an active project
            self.active_project_path = os.path.join(self.workspace_path, self.active_project)
           
    def testerChanged(self):
        self.active_tester = self.tester_combo.currentText()
        
            
    def projectChanged(self):
        self.active_project = self.project_combo.currentText()
        self.active_project_path = os.path.join(self.workspace_path, self.active_project)
        print("active_project = '%s' (%s)" % (self.active_project, self.active_project_path))
        self.update_hardware()
    
    def hardwareChanged(self):
        self.active_hw = self.hw_combo.currentText()
        print("active_hw = '%s'" % self.active_hw)
    
    def active_project_changed(self):
        self.active_project = self.comboBox.currentText()
        self.active_project_path = os.path.join(self.workspace_path, self.active_project)
        self.setWindowTitle("Spyder MockUp (%s)" % self.active_project_path)

    def workspace_setup(self):
        self.workspace_path = workspace_path
        if not os.path.exists(self.workspace_path):
            os.makedirs(self.workspace_path)
        for project in self.list_projects_in_workspace():
            print(project)

    def list_projects_in_workspace(self):
        retval = []
        for possible_project_dir in os.listdir(self.workspace_path):
            if os.path.isdir(possible_project_dir):
                retval.append(possible_project_dir)
                #TODO: look in the directories
        return retval

    def tree_update(self):
        self.tree.setHeaderHidden(True)
        # self.project_info        



        
        project = QtWidgets.QTreeWidgetItem(self.tree)
        project.setText(0, "HATC")
        project.setText(1, 'project')
        font = project.font(0)
        font.setWeight(QtGui.QFont.Bold)
        project.setFont(0, font)
        project.setForeground(0, QtGui.QBrush(QtGui.QColor("#FFFF00")))
        
        
        
        documentation = QtWidgets.QTreeWidgetItem(project)
        documentation.setText(0, 'documentation')
        documentation.setText(1, 'documentation')
        doc_root = os.path.join(self.active_project_path, 'documentation')
        #TODO: cycle the directory structure, and add the documents

        sources = QtWidgets.QTreeWidgetItem(project, documentation)
        sources.setText(0, 'sources')
        sources.setText(1, 'sources')
                
        definitions = QtWidgets.QTreeWidgetItem(sources)
        definitions.setText(0, 'definitions')
        definitions.setText(1, 'definitions')
        
        states = QtWidgets.QTreeWidgetItem(definitions)
        states.setText(0, 'states')
        states.setText(1, 'states')
        states_root = dict_project_paths(self.active_project_path)['states_root']
        previous = None
        for state_file in os.listdir(states_root):
            if state_file.startswith('__'): continue
            if not state_file.endswith('.py'): continue
            state = QtWidgets.QTreeWidgetItem(states, previous)
            state.setIcon(0, qta.icon('mdi.shoe-print', color='orange'))
            state.setText(0, state_file)
            state.setText(1, 'state')
            state.setText(2, os.path.join(states_root, state_file))
            previous = state
        
        protocols = QtWidgets.QTreeWidgetItem(definitions, states)
        protocols.setText(0, 'protocols')
        protocols.setText(1, 'protocols')
        #TODO: cycle through the directory and add the protocols
        
        registermap = QtWidgets.QTreeWidgetItem(definitions, protocols)
        registermap.setText(0, 'register maps')
        registermap.setText(1, 'registermaps')
        #TODO: cycle through the directory and add the registermaps
        
        flows = QtWidgets.QTreeWidgetItem(definitions, registermap)
        flows.setText(0, 'flows')
        flows.setText(1, 'flows')
        #TODO: insert the right flows from the database
        
        products = QtWidgets.QTreeWidgetItem(definitions, flows)
        products.setText(0, 'products')
        products.setText(1, 'products')
        #TODO: insert the right products from the database
        
        devices = QtWidgets.QTreeWidgetItem(definitions, products)
        devices.setText(0, 'devices')
        devices.setText(1, 'devices')
        #TODO: insert the right devices from the database
        
        packages = QtWidgets.QTreeWidgetItem(definitions, devices)
        packages.setText(0, 'packages')
        packages.setText(1, 'packages')
        #TODO: insert the right packages from the database
        
        dies = QtWidgets.QTreeWidgetItem(definitions, packages)
        dies.setText(0, 'dies')
        dies.setText(1, 'dies')
        #TODO: inset the right dies from the database
        
        masksets = QtWidgets.QTreeWidgetItem(definitions, dies)
        masksets.setText(0, 'masksets')
        masksets.setText(1, 'masksets')
        #TODO: insert the right masksets from the database
        
        hardwaresetups = QtWidgets.QTreeWidgetItem(definitions, masksets)
        hardwaresetups.setText(0, 'hardwaresetups')
        hardwaresetups.setText(1, 'hardwaresetups')
        previous = None
        for hwsetup in self.project_info.list_hardwaresetups():
            setup = QtWidgets.QTreeWidgetItem(hardwaresetups, previous)
            setup.setText(0, hwsetup)
            setup.setText(1, 'hardwaresetup')
            previous = setup
            
        
        #TODO: insert the right hardwaresetups from the database
        
        tests = QtWidgets.QTreeWidgetItem(sources)
        tests.setText(0, 'tests')
        tests.setText(1, 'tests')
        #TODO: insert the appropriate test names from /sources/tests, based on HWR and base (read: die- or product-based or probing/final test)
                
        progs = QtWidgets.QTreeWidgetItem(sources, tests)
        progs.setText(0, 'programs')
        progs.setText(1, 'programs')
        #TODO: insert the appropriate programs from /sources/programs, based on HWR and base 
        
        patterns = QtWidgets.QTreeWidgetItem(sources, progs)
        patterns.setText(0, 'patterns')
        patterns.setText(1, 'patterns')
        #TODO: insert the appropriate patterns from /sources/patterns, based on HWR and Base

                
    def new_test(self):
        from ATE.org.actions.new.test.NewTestWizard import new_test_dialog
        new_test_dialog(self)
        
    def new_testprogram(self):
        print("new_testprogram")    
        
    def new_flow(self):
        print("new_flow")    
        
    def new_protocol(self):
        print("new_protocol")    
        
    def new_registermap(self):
        print("new_registermap")    
        
    def new_product(self):
        from ATE.org.actions.new.product.NewProductWizard import new_product_dialog
        new_product_dialog(self)
        
    def new_device(self):
        from ATE.org.actions.new.device.NewDeviceWizard import new_device_dialog
        new_device_dialog(self)
        
    def new_package(self):
        from ATE.org.actions.new.package.NewPackageWizard import new_package_dialog
        new_package_dialog(self)
        
    def new_die(self):
        from ATE.org.actions.new.die.NewDieWizard import new_die_dialog
        new_die_dialog(self)
        
    def new_maskset(self):
        from ATE.org.actions.new.maskset.NewMasksetWizard import new_maskset_dialog
        new_maskset_dialog(self)
        
    def new_hardwaresetup(self):
        from ATE.org.actions.new.hardwaresetup.NewHardwaresetupWizard import new_hardwaresetup_dialog
        new_hardwaresetup_dialog(self)
        self.update_hardware()
        
    def new_project(self):
        from ATE.org.actions.new.project.NewProjectWizard import new_project_dialog
        new_project_dialog(self)
        self.update_projects()
        
    def clone_test(self):
        print("clone_test")    
        
    def clone_testprogram(self):
        print("clone_testprogram")    
        
    def clone_flow(self):
        print("clone_flow")    
        
    def clone_protocol(self):
        print("clone_protocol")    
        
    def clone_registermap(self):
        print("clone_registermap")    
        
    def clone_product(self):
        print("clone_product")    
        
    def clone_device(self):
        print("clone_device")    
        
    def clone_package(self):
        print("clone_package")    
        
    def clone_die(self):
        print("clone_die")    
        
    def clone_maskset(self):
        print("clone_maskset")    



    def import_registermap(self):
        print("import_registermap")    
        
    def import_product(self):
        print("import_product")    
        
    def import_package(self):
        print("import_package")    
        
    def import_maskset(self):
        print("import_maskset")    



    def edit_test(self):
        print("edit_test")    
        
    def edit_testprogram(self):
        print("edit_testprogram")    
        
    def edit_flow(self):
        print("edit_flow")    
        
    def edit_protocol(self):
        print("edit_protocol")    
        
    def edit_registermap(self):
        print("edit_registermap")    
        
    def edit_product(self):
        print("edit_product")    
        
    def edit_device(self):
        print("edit_device")    
        
    def edit_package(self):
        print("edit_package")    
        
    def edit_die(self):
        print("edit_die")    
        
    def edit_maskset(self):
        print("edit_maskset")    
        
    def edit_hardwaresetup(self):
        print("actionhardware_setup")    



    def rename_test(self):
        print("rename_test")    
        
    def rename_maskset(self):
        print("rename_maskset")    
        
    def rename_device(self):
        print("rename_device")    
        
    def rename_die(self):
        print("rename_die")    
        
    def rename_product(self):
        print("rename_product")    
        
    def rename_package(self):
        print("rename_package")    

        
        
    def display_tests(self):
        print("display_tests")    
        
    def display_testprograms(self):
        print("display_testprograms")    
        
    def display_flows(self):
        print("display_flows")    
        
    def display_protocols(self):
        print("display_protocols")    
        
    def display_registermaps(self):
        print("display_registermaps")    
        
    def display_products(self):
        print("display_products")    
        
    def display_devices(self):
        print("display_devices")    
        
    def display_packages(self):
        print("display_packages")    
        
    def display_dies(self):
        print("display_dies")    
        
    def display_masksets(self):
        print("display_masksets")    
        
    def display_hardwaresetups(self):
        print("display_hardwaresetups")    
        
    def display_activeproject(self):
        print("display_activeproject")    
        
    def display_allprojects(self):
        print("display_allprojects")  
        from ATE.org.listings import list_projects
        for project in list_projects(self.workspace_path):
            print("   ", project)
        
    def display_ateprojects(self):
        print("display_ateprojects")  
        from ATE.org.listings import list_ATE_projects
        for project in list_ATE_projects(self.workspace_path):
            print("   ", project)
        
    def display_workspace(self):
        print("display_workspace = '%s'" % self.workspace_path)
        



    def delete_test(self):
        print("delete_test")    
        
    def delete_testprogram(self):
        print("delete_testprogram")    

    def delete_flow(self):
        print("delete_flow")    
    
    def delete_protocol(self):
        print("delete_protocol")    
        
    def delete_registermap(self):
        print("delete_registermap")    
        
    def delete_product(self):
        print("delete_product")    
        
    def delete_device(self):
        print("delete_device")    
        
    def delete_package(self):
        print("delete_package")    
        
    def delete_die(self):
        print("delete_die")    
        
    def delete_maskset(self):
        print("delete_maskset")    
        
    def delete_hardwaresetup(self):
        print("delete_hardwaresetup")    
    
    def delete_project(self):
        print("delete_project", end='')
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        directory_to_delete = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", workspace_path, options=options))
        print(" : %s" % directory_to_delete, end='')
        shutil.rmtree(directory_to_delete)
        print(" Done.")



    def onRun(self):
        print("run")

    def onSettings(self):
        print("settings")

    def screencast_settings(self):
        print("start screencast settings")
        from ScreenCastSettings import ScreenCastSettings
        screenCastSettings = ScreenCastSettings(self)       
        screenCastSettings.exec_() 
        del(screenCastSettings)
        print("end screencast settings")
        
    def screencast_start_stop(self):
        if self.screencast_state == 'recording':
            
            print("recording stopped")
            self.screencast_state = 'idle'
            self.screencast.setPixmap(qta.icon('mdi.video', color='orange').pixmap(16,16))   
        else:
            
            print("recording started")
            self.screencast_state = 'recording'
            self.screencast.setPixmap(qta.icon('mdi.video', 'fa5s.ban', options=[{'color' : 'orange'},{'color' : 'red'}]).pixmap(16,16))
        
    def printInfo(self):
        from ATE.org.listings import print_lists
        print("-----")
        print_lists(self.workspace_path, self.active_project_path)
    

    def placeholder(self, event):
        print(type(event))
        print(event)

    
if __name__ == '__main__':
    import sys
    print(workspace_path)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window.show()
    sys.exit(app.exec_())

        




        
        
        
        
