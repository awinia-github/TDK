'''
Created on Aug 16, 2019

@author: hoeren
'''

import os

from PyQt5 import QtWidgets, QtCore, QtGui

import qtawesome as qta

from SpyderMU.core import default_base_directory_name
from SpyderMU.core import default_workspace_directory_name
from SpyderMU.core import default_workspace_name
from SpyderMU.core import default_workspace_extension
from SpyderMU.core import active_workspace_file_name

#from SpyderMU.core import spyderWorkspacesDir
#from SpyderMU.core import default_workspace_directory_name
#from SpyderMU.core import default_workspace_config_directory_name


class explorerManager(object):

    def __init__(self, spyder=None):
        if spyder==None:
            raise Exception("Can not attach to None-type")
        self.spyder = spyder

        
        self.spyderBase = os.path.join(self.spyder.userManager.USER['HOME'], default_base_directory_name)
        self.workspacesRoot = os.path.join(self.spyderBase, default_workspace_directory_name)
        self.spyderDefaultWorkspaceFile = os.path.join(self.workspacesRoot, "%s%s" % (default_workspace_name, default_workspace_extension))
        self.activeWorkspaceFile = os.path.join(self.workspacesRoot, "%s%s" % (active_workspace_file_name, default_workspace_extension))
        
        self.__call__()
        
    def __call__(self):
        self.workspaceTreeviewModel = SpyderProjectsTreeModel()
        
        workspaceTreeview = QtWidgets.QTreeView()
        workspaceTreeview.setModel(self.workspaceTreeviewModel)
        workspaceTreeview.setObjectName("workspaceTreeview")
        workspaceTreeview.setRootIsDecorated(False)
        workspaceTreeview.setHeaderHidden(True)

        WorkspaceModel = QtGui.QStandardItemModel()
        workspaceTreeview.setModel(WorkspaceModel)

        root = WorkspaceModel.invisibleRootItem()

        projects = os.listdir(self.workspacesRoot)
        for project in projects:
            if project.startswith('__'):
                continue
            if project.startswith('.'):
                continue
            item = QtGui.QStandardItem(project)
            item.setIcon(qta.icon('mdi.folder-outline', color='black', scale_factor=1.5))
            item.setEditable(False)
            item.setToolTip('Closed Project')
            root.appendRow(item)
            
        self.spyder.workspaceTreeview = workspaceTreeview
        
    def __str__(self):
        retval = "%s\n" % str(__class__).split("'")[1]
        #TODO: put something usefull here
        retval += ''
        return retval
    
class SpyderProjectsTreeModel(QtCore.QAbstractItemModel):
    
    pass

if __name__ == '__main__':
    from SpyderMU.core.managers.userManager import userManager
    
    class dummySpyder(object):
        pass

    UserManager = userManager()
    DummySpyder = dummySpyder()
    DummySpyder.UserManager = UserManager
    