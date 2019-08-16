#!/usr/bin/env python

import os, sys, platform

from PyQt5 import QtCore, QtGui, QtWidgets
import qtawesome as qta

from SpyderMU.core.managers import editorManager, pluginManager, preferencesManager, userManager, explorerManager

class Spyder(QtWidgets.QMainWindow):
    
    debug = True
    def __init__(self):
        super().__init__()

        self.userManager = userManager(self)
        if self.debug: print(self.userManager)

        self.preferencesManager = preferencesManager(self)
        if self.debug: print(self.preferencesManager)

        self.pluginManager = pluginManager(self)
        if self.debug: print(self.pluginManager)
        
        self.explorerManager = explorerManager(self)
        if self.debug: print(self.explorerManager)
        
        self.editorManager = editorManager(self)
        if self.debug: print(self.editorManager)
        
        self.setupUI() #TODO: during the UI setup, the preferences in the preference manager should be used.

    def setupUI(self):
        self.setWindowTitle('Spyder MockUp')
        self.resize(1000, 800)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.setSizePolicy(sizePolicy)

        self.setupMenubar()
        self.setupStatusbar()
        self.setupCentralWidget()
        self.setupBaseStyle()
        
    def setupMenubar(self):
        menu_bar = self.menuBar()
        if platform.system()=='Darwin':
            menu_bar.setNativeMenuBar(False)
            
        file_menu = menu_bar.addMenu('File')
        actionNewProject = QtWidgets.QAction(qta.icon('mdi.folder-plus-outline', color='black', scale_factor=1), '&New Project', self)
        actionNewProject.triggered.connect(self.pluginManager.createNewProject)
        actionPreferences = QtWidgets.QAction(qta.icon('mdi.cogs', color='black', scale_factor=1), '&Preferences', self)
        actionPreferences.triggered.connect(self.preferencesManager.editPreferences)
        file_menu.addAction(actionNewProject)
        file_menu.addAction(actionPreferences)

    def setupStatusbar(self):
        statusbar = QtWidgets.QStatusBar(self)
        statusbar.setObjectName("statusbar")
        self.setStatusBar(statusbar)
    
    def setupCentralWidget(self):
        centralwidget = QtWidgets.QWidget()
        centralwidget.setObjectName("centralwidget")
        centralwidgetLayout = QtWidgets.QHBoxLayout(centralwidget)
        centralwidgetLayout.setObjectName("horizontalLayout")
        # Workspace Explorer
        workspaceGroupbox = QtWidgets.QGroupBox(centralwidget)
        workspaceGroupbox.setTitle('Workspace Explorer')
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(workspaceGroupbox.sizePolicy().hasHeightForWidth())
        workspaceGroupbox.setSizePolicy(sizePolicy)
        workspaceGroupbox.setObjectName("workspaceGroupbox")
        workspaceBox = QtWidgets.QVBoxLayout(workspaceGroupbox)
        workspaceBox.setObjectName("workspaceBox")
        workspaceLayout = QtWidgets.QVBoxLayout()
        workspaceLayout.setObjectName("workspaceLayout")
        workspaceLayout.addWidget(self.workspaceTreeview)  # self.workspaceTreeView is present and created prior by the workspace manager
        workspaceBox.addLayout(workspaceLayout)
        centralwidgetLayout.addWidget(workspaceGroupbox)

        # Editorspace
        editorsGroupbox = QtWidgets.QGroupBox(centralwidget)
        editorsGroupbox.setTitle("Editors")
        editorsGroupbox.setVisible(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(editorsGroupbox.sizePolicy().hasHeightForWidth())
        sizePolicy.setRetainSizeWhenHidden(True)
        editorsGroupbox.setSizePolicy(sizePolicy)
        editorsGroupbox.setObjectName("editorsGroupbox")
        editorsLayout = QtWidgets.QVBoxLayout(editorsGroupbox)
        editorsLayout.setObjectName("editorsLayout")
        editorsTabwidget = QtWidgets.QTabWidget(editorsGroupbox)
        editorsTabwidget.setObjectName("editorsTabwidget")
        editor1Tab = QtWidgets.QWidget()
        editor1Tab.setObjectName("editor1Tab")
        editorsTabwidget.addTab(editor1Tab, "File1")
        editor2Tab = QtWidgets.QWidget()
        editor2Tab.setObjectName("editor2Tab")
        editorsTabwidget.addTab(editor2Tab, "File2")
        editorsLayout.addWidget(editorsTabwidget)
        centralwidgetLayout.addWidget(editorsGroupbox)

        # Variable Explorer
        variableExplorerGroupbox = QtWidgets.QGroupBox(centralwidget)
        variableExplorerGroupbox.setTitle("Variable Explorer")
        variableExplorerGroupbox.setVisible(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(variableExplorerGroupbox.sizePolicy().hasHeightForWidth())
        sizePolicy.setRetainSizeWhenHidden(True)
        variableExplorerGroupbox.setSizePolicy(sizePolicy)
        variableExplorerGroupbox.setObjectName("variableExplorerGroupbox")
        variablesLayout = QtWidgets.QVBoxLayout(variableExplorerGroupbox)
        variablesLayout.setObjectName("variablesLayout")
        variablesTreeView = QtWidgets.QTreeView(variableExplorerGroupbox)
        variablesTreeView.setObjectName("variablesTreeView")
        variablesLayout.addWidget(variablesTreeView)
        centralwidgetLayout.addWidget(variableExplorerGroupbox)
        
        self.setCentralWidget(centralwidget)

    def setupBaseStyle(self):
        self.setStyleSheet('')


if __name__ == '__main__':
    if sys.version_info.major < 3:
        raise Exception("Must be using Python 3")
    if sys.version_info.minor < 6:
        raise Exception("Must be using Python 3.6 or newer (using %s.%s.%s)" % (sys.version_info.major, sys.version_info.minor, sys.version_info.micro) )
    
    app = QtWidgets.QApplication(sys.argv)
    spyder = Spyder()
    spyder.show()
    sys.exit(app.exec_())
