'''
Created on Aug 16, 2019

@author: hoeren
'''
from SpyderMU.core.ABC.plugin import SpyderPluginABC

class ATE(SpyderPluginABC):
    
    service = 'Python'
    service_type = 'ATE'
    
    def __str__(self):
        return "Python ATE plugin"

if __name__ == '__main__':
    pass