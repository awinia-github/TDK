'''
Created on Aug 16, 2019

@author: hoeren
'''

class editorManager(object):
    '''
    The SpyderEditorManager interacts with the other managers :
        - SpyderUserManager --> not so much interaction
        - SpyderPreferencesManager --> to get settings from the plugins
        - SpyderPlutinManager --> to know what editors are available [service = 'EDIT' serviceType = 'LSP' for example]
        - SpyderWorkspaceManager --> to open/close/save... files
    It is thus imperative that all other managers are found, but on __init__ all other managers can never be there,
    that's why the __call__ is used (with keyword argument 'validate=True' to validate if the manager can find the others.
    '''
    def __init__(self, spyder):
        if spyder==None:
            raise Exception("Can not attach to None-type")
        self.spyder = spyder
        self.__call__()

    def __call__(self, *args, **kwargs):
        '''
        This method is called after system setup, to make sure that all the managers find eachother.
        '''
        if 'validate' in kwargs:
            if kwargs['validate'] == True:
                print('Validating')
        else:
            pass # normal setup

    def saveAndCloseAllFiles(self):
        '''
        This method is called from outside of this class to save and close all files curently open.
        (this is for when one switches workspaces)
        '''
        pass

    def __str__(self):
        retval = "report from '%s':" % str(__class__).split("'")[1]
        #TODO: put something usefull here
        retval += ''
        return retval


if __name__ == '__main__':
    pass