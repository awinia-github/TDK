'''
Created on Aug 16, 2019

@author: hoeren
'''
'''
Created on 22 Jul 2019

@author: tho
ABC : https://www.youtube.com/watch?v=PDMe3wgAsWg
Meta : https://stackoverflow.com/questions/100003/what-are-metaclasses-in-python
non-conflicting types : http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/
'''
import os

from abc import ABC#, abstractmethod, abstractproperty

class SpyderPluginABC(ABC):
    '''
    Abstract Base Class for the spyder plugins.
    '''
    
    service = None
    service_type = None

    plugin_source = None
    project_path = None
    project_name = None
    plugin_logo = None

    toolbar = None
    settings = None

    variable_explorer = None
    project_explorer = None
        
    
    def __init__(self, spyder=None):
        self.spyder = spyder
        self.__set_enabled(False)

    def __get_enabled(self):
        return self.__enabled
    
    def __set_enabled(self, val):
        if not isinstance(val, bool):
            raise TypeError("expected a boolean")
        if self.__enabled != val:
            if val==True :
                self.__enabled = True
                self.enable_action()
            else:
                self.__enabled = False
                self.disable_action()
        return self.__enabled
            
    def enable_action(self):
        pass
    
    def disable_action(self):
        pass

    def load_project(self, project_path, project_name):
        '''
        given the project_path and project_name, load the project in the plugin.
        '''
        pass

    def import_project_dialog(self):
        '''
        optional method, used if service is a language
        '''
        pass
    
    def import_project(self, project_path, project_name, project_source):
        '''
        This method will import a (non spyder-plugin) project from project_source for the given language & type in project_path with project_name and load the project.
        '''
        pass

    
    def create_new_project_dialog(self):
        pass


    #@abstractmethod
    def create_new_project(self, project_path, project_name):
        '''
        This method creates a new plugin-type project from location 'workspacepath'
        '''
        self.project_path = os.path.normpath(project_path)
        self.project_name = project_name

if __name__ == '__main__':
    pass