'''
Created on Aug 12, 2019

@author: hoeren
'''


class config_flo(object):
    '''
    '''
    def __init__(self, FileName, mode='rb', raw=False, roi=None):
        pass
    
    def __del__(self):
        self.fd.close()
    
    def __iter__(self):
        pass
    
    def __next__(self): # reference = https://docs.python.org/3/library/stdtypes.html#iterator-types
        pass
    
    def __enter__(self): # reference = https://docs.python.org/3/library/stdtypes.html#iterator-types
        pass
    
    def __exit__(self):
        self.__del__()
    
    def read(self, n):
        pass
    
    def write(self, n):
        pass
    
    def seek(self):
        pass
    



class ConfigManager(object):
    '''
    '''

    def __init__(self, ConfigFile='/etc/sct.pconf'):
        '''
        '''
        
    def open(self, ConfigFile):
        '''
        '''
        
    def read(self, Section=None):
        '''
        This method will read (and return) the Section of ConfigFile.
    
        If Section == None, all sections will be returned.
        '''
        
    def write(self, Section):
        '''
        This function will (over)write Section to the ConfigFile.
        '''
    
    def load(self, ConfigFile):
        '''
        '''
    
    def save(self, ConfigFile):
        '''
        '''
    
    def create(self, ConfigFile):
        '''
        '''
    
    def __repr__(self):
        '''
        '''
    
    def __str__(self):
        '''
        '''


if __name__ == '__main__':
    pass