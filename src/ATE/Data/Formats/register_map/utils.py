'''
Created on Aug 19, 2019

@author: hoeren
'''

def register_map_config_manager():
    '''
    graphical tool to configure register maps.
    '''
    pass

def register_map_save(Filename, regmap):
    '''
    Given a register_map dictionary (regmap) and a file, save (pickle) the dictionary.
    complain if the FileName ends with anything else then '.regmap'
    '''
    

def register_map_load(FileName):
    '''
    this function will load the register_map from FileName, and return the dictionary to be used in subclasses of register_map_abc
    '''
    retval = {}
    return retval

if __name__ == '__main__':
    pass