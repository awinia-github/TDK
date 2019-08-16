'''
Created on Aug 16, 2019

@author: hoeren
'''
import os, platform

from ATE.utils import DT

class userManager(object):
    
    USER = {}
    
    def __init__(self, spyder=None):
        if spyder==None:
            raise Exception("Can not attach to None-type")
        self.spyder = spyder
        
        self.USER = {}
        self.USER['NAME'] = self.getUserName()
        self.USER['HOME'] = self.getUserHomeDir()
        self.USER['TMPDIR'] = self.getUserTempDir()
        self.USER['DESKTOP'] = self.getUserDesktopDir()
        
    def getUserName(self):
        '''
        This method will return the username from the environment, based on the platform.
        '''
        if platform.system() == 'Darwin':
            if 'USER' not in os.environ and 'USERNAME' not in os.environ:
                raise Exception("you must have a 'USER' or 'USERNAME' environment variable set!")
            if 'USER' in os.environ:
                retval = os.environ['USER']
            else:
                retval = os.environ['USERNAME']
        elif platform.system() == 'Windows':
            if 'USER' not in os.environ and 'USERNAME' not in os.environ:
                raise Exception("you must have a 'USER' or 'USERNAME' environment variable set!")
            if 'USER' in os.environ:
                retval = os.environ['USER']
            else:
                retval = os.environ['USERNAME']
        elif platform.system() == 'Linux':
            raise NotImplementedError("woops, 'USER' for platform '%s' not implemented, implement now." % platform.system())
        else:
            raise NotImplementedError("woops, 'USER' for platform '%s' not implemented, implement now." % platform.system())
        return retval
    
    def getUserHomeDir(self):
        if platform.system() == 'Darwin':
            if 'HOME' not in os.environ:
                raise Exception("you must have a 'HOME' environment variable set!")       
            if not os.path.exists(os.environ['HOME']):
                try:
                    os.makedirs(os.environ['HOME'])
                except:
                    raise Exception("The 'HOME' environment variable is set to '%s', but it does't point to an existing directory, the attempt to create this directory failed!" % os.environ['HOME'])
                else:
                    retval = os.environ['HOME']
            else:
                if os.path.isdir(os.environ['HOME']):
                    retval = os.environ['HOME']
                else:
                    raise Exception("The 'HOME' environment variable is set to '%s', but it doens't point to a directory!"% os.environ['HOME'])
        elif platform.system() == 'Windows':
            if 'HOMEDRIVE' not in os.environ:
                raise Exception("you must have a 'HOMEDRIVE' environment variable set!")
            if 'HOMEPATH' not in os.environ:
                raise Exception("you must have a 'HOMEPATH' environment variable set!")
            tmp = os.path.normpath(os.path.join(os.environ['HOMEDRIVE'], os.environ['HOMEPATH']))
            if not os.path.exists(tmp):
                try:
                    os.makedirs(tmp)
                except:
                    raise Exception("your 'home' (%s) doesn't exist, and something went wrong in creating it." % tmp)
            elif not os.path.isdir(tmp):
                raise Exception("your 'home' (%s) doesn't point to a directory!" % tmp)
            retval = tmp
        elif platform.system() == 'Linux':
            raise NotImplementedError("woops, 'HOME' for platform '%s' not implemented, implement now." % platform.system())
        else:
            raise NotImplementedError("woops, 'HOME' for platform '%s' not implemented, implement now." % platform.system())
        return retval

    def getUserTempDir(self):
        '''
        depends on:
            self.USER['NAME']
            self.USER
            
            
            
        TIP : Use the tempfile module!!!
        '''
        
        H = str(abs(hash(str(os.getpid())+str(DT()))))
        if platform.system()=='Darwin':
            if 'TMPDIR' not in os.environ:
                raise Exception("Couldn't find the 'TMPDIR' environment variable ...")
            else: # so we have a system temp dir, now create the spyder temp dir inside it.
                raise NotImplemented("correct this on a mac")
#                 root_temp_dir = os.path.join(os.path.sep.join(os.environ['TMPDIR'].split(os.path.sep)[:-2]), "Cleanup At Startup")
#                 if os.path.exists(root_temp_dir) and os.path.isdir(root_temp_dir):
# 
#                         try:
#                             os.makedirs(user_temp_dir)
#                         except:
#                             raise Exception("Couldn't create '%s', something went wrong." % user_temp_dir)
#                         retval = user_temp_dir
#                 else:
#                     raise Exception("The directory '%s' doesn't exist, or is a file" % root_temp_dir)
        elif platform.system()=='Windows':
            # is the temp dir in windows cleaned up after reboot ?!?
            if 'TMP' not in os.environ and 'TEMP' not in os.environ:
                raise Exception("On Windows, either the 'TMP' or 'TEMP' environment variables should be set and pointing to a directory")
            if 'TMP' in os.environ:
                retval = os.path.join(os.environ['TMP'], H)
                os.makedirs(retval)
            else:
                retval = os.path.join(os.environ['TEMP'], H)
                os.makedirs(retval)
        elif platform.system()=='Linux':
            raise NotImplementedError("woops, 'TMPDIR' for platform '%s' not implemented, implement now." % platform.system())
        else:
            raise NotImplementedError("woops, 'TMPDIR' for platform '%s' not implemented, implement now." % platform.system())
        return retval
    
    def getUserDesktopDir(self):
        '''
        depends on:
            self.USER['HOME']
        '''
        if platform.system() == 'Darwin' or platform.system() == 'Windows':
            desktop = os.path.join(self.USER['HOME'], 'Desktop')
            if os.path.exists(desktop):
                if os.path.isdir(desktop):
                    retval = desktop
                else:
                    raise Exception("your desktop '%s' points to a file rather than a directory ..." % desktop)
            else:
                raise Exception("where is the desktop? For sure not in '%s' as it doesn't exist!" % desktop)
        elif platform.system() == 'Linux':
            raise NotImplementedError("woops, 'TMPDIR' for platform '%s' not implemented, implement now." % platform.system())
        else:
            raise NotImplementedError("woops, 'TMPDIR' for platform '%s' not implemented, implement now." % platform.system())
        return retval

    def change_user(self):
        if platform.system() == 'Darwin':
            raise NotImplementedError("woops, su for platform '%s' not implemented, implement now!" % platform.system())
        elif platform.system() == 'Windows':
            raise NotImplementedError("woops, su for platform '%s' not implemented, implement now!" % platform.system())
        elif platform.system() == 'Linux':
            raise NotImplementedError("woops, su for platform '%s' not implemented, implement now!" % platform.system())
        else:
            raise NotImplementedError("woops, su for platform '%s' not implemented, implement now!" % platform.system())
        self.USER = self.setup()
        self.spyder.USER = self.USER

    def __str__(self):
        retval = "%s\n" % str(__class__).split("'")[1]
        for key in self.USER:
            retval += "\tUSER[%s] = %s\n" % (key, self.USER[key])
        return retval


if __name__ == '__main__':
    pass