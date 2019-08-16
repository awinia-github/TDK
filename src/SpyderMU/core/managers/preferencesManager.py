'''

lowest level =  1 = spyder default preferences --> in the package
                2 = spyder dynamic preferences (from plugins) --> can we also put this in the package ?!? 
                3 = site preferences --> in the workspace directory under .spyder in a file --> init = empty file
                4 = user preferences --> in the user's home directory under .spyder in a file --> upon initialization for the first time this is an empty file
highest level = 5 = project preferences --> in the project directory under .spyder in a file --> upon initialization of a new project, this is an empty file
    
a higher level setting overwrites a lower level setting

hmmmm ... every setting should have a mask level ... a level from where overwriting is disabled ... 

    masklevel 5 --> all the way overwrite-able
    masklevel 1 --> not at all overwrite-able
    makslevel 3 --> user & project can not overwrite anymore

hmmmm ... how (and for all where) to set these masklevels ?
    
'''
class preferencesManager(object):
    
    def __init__(self, spyder=None):
        if spyder==None:
            raise Exception("Can not attach to None-type")
        self.spyder = spyder
        if 'userManager' not in dir(self.spyder):
            raise Exception("SpyderPreferenceManager depends on the UserManager, but that one can't be found.")


    def editPreferences(self):
        print('edit preferences')

    def __str__(self):
        retval = "%s\n" % str(__class__).split("'")[1]
        #TODO: put something usefull in here
        retval += ''
        return retval

if __name__ == '__main__':
    pass