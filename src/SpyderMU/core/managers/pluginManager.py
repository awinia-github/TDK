'''
Created on Aug 16, 2019

@author: hoeren
'''
import os
import pkgutil, importlib, pyclbr

class pluginManager(object):
    '''
    '''
    plugins = {}

    non_language_services = ['RCS',     # --> Revision Control System (eg git, cvs, mercurial ...)
                             'PKG',     # --> Packing System (eg: anaconda, pip, ... )
                             'CORE',    # --> Plugin for spyder functionality (eg: snapshot, screencast, ...)
                             'STYLE',  # --> styles
                             'TICKET',  # --> ticketing system plugins (Bugzilla/Jira/...)
                             'GUI'      # --> GUI support plugins (Qt/Tk/curses/...)
                             ]  # --> Plugin for spyder styles (eg: qdark, qlight, ...)
    #TODO: non-language-services should always be capitalized in service
    def __init__(self, spyder=None):
        '''
        The constructor will walk trough all python packages, and search for a '__spyder__' directory.
        Under such a '__spyder__' directory, we will locate all .py files (not including __init__.py and __pycache__ directories)
        Then we will search in those files for all classes that inherit from 'SpyderPluginABC', those calsses are the plugins!
        The spyder plugins are instantenated an placed in the self.plugins dictonary with as keys service and service_type.
        '''
        if spyder==None:
            raise Exception("Can not attach to None-type")
            
        spyder_modules = {}
        # find all possible spydermodules
        for module in pkgutil.iter_modules():
            if module.name.startswith('__'):
                continue
            if module.ispkg:
                if module.name not in spyder_modules:
                    spec = importlib.util._find_spec_from_path(module.name)
                    module_root = os.path.sep.join(spec.origin.split(os.path.sep)[:-1])
                    spyder_modules[module.name] = []
                    for root, _, files in os.walk(module_root):
                        root_elements = root.split(os.path.sep)
                        if root_elements[-1] == '__pycache__':
                            continue
                        for file in files:
                            file_name, file_ext = os.path.splitext(file)
                            if '__spyder__' in root_elements and file_ext == '.py' and not file_name.startswith('.') and file_name != '__init__':
                                module_fake_root = os.path.sep.join(module_root.split(os.path.sep)[:-1])
                                delta = os.path.join(root, file_name).replace(module_fake_root,'').replace(os.path.sep, '.')[1:]
                                spyder_modules[module.name].append(delta)
                else:
                    raise Exception("Woops %s is used double !!!" % module.name)
        # determine which one of the spydermodules holds a spyderplugin, and instantenate them in self.plugins
        for package in spyder_modules:
            for module in spyder_modules[package]:
                module_data = pyclbr.readmodule(module)
                for name, class_data in module_data.items():
                    if 'SpyderPluginABC' in class_data.super:
                        spec = importlib.util.spec_from_file_location(name, class_data.file)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        _ = getattr(module, name)
                        if _.service!=None and _.service_type!=None:
                            if _.service not in self.plugins:
                                self.plugins[_.service]={}
                            if _.service_type != None: 
                                if _.service_type not in self.plugins[_.service]:
                                    self.plugins[_.service][_.service_type] = _
                                    _.plugin_source = class_data.file
                                else: #wooow, it already seems to exist ... ok, give it a new name
#                                     print(_.service, _.service_type)
                                    i = 1
                                    new_service_type = "%s_%s" % (_.service_type, i)
                                    while new_service_type in self.plugins[_.service]:
                                        i+=1
                                        new_service_type = "%s_%s" % (_.service_type, i)
                                    self.plugins[_.service][new_service_type] = _
                                    _.plugin_source = class_data.file

    def languages(self):
        '''
        This method will return a list of languages in the services
        '''
        retval = []
        for service in self.plugins:
            if service not in self.non_language_services:
                retval.append(service)
        return retval
    
    def project_types(self, language=None):
        '''
        This method will return a list of project_types for the given language.
        '''
        if language==None:
            return []
        else:
            if language in self.plugins:
                return list(self.plugins[language].keys())
            else:
                return []

    def plugin(self, service=None, service_type=None):
        '''
        This method wil return the object (instantenated plugin) for a given service and service_type. (also language and project_type)
        '''
        if service!=None and service_type!=None:
            if service in self.plugins and service_type in self.plugins[service]:
                    return self.plugins[service][service_type]
        return None

    def createNewProject(self):
        '''
        This method implements the functionality to create a project using the style from spyder. 
        '''
        print("create new project")

    def __str__(self):
        retval = "%s\n" % str(__class__).split("'")[1]
        for service in self.plugins:
            retval += "\t%s\n" % service
            for service_type in self.plugins[service]:
                retval += "\t\t%s --> %s\n" % (service_type, id(self.plugins[service][service_type]))
        return retval


if __name__ == '__main__':
    from SpyderMU.core.utils.printers import pprint
    SPM = pluginManager()
    pprint(SPM.plugins)
    print('\n-------------')
    print('languages = %s' % SPM.languages())
