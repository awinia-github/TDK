# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.physical import PEABC 

class adg5419(PEABC):
    '''
    ADG5419 = Single SPDT Switch
    
    Data Sheet : https://www.analog.com/media/en/technical-documentation/data-sheets/ADG5419.pdf
    
    SCT platform hold ... such devices.
    
    This class provides the interface for instruments to communicate with the device
    '''

    register_map = {}




if __name__ == '__main__':
    pass