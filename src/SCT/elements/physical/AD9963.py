# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.physical import PEABC 

class ad9963(PEABC):
    '''
    AD9963 = 2 channel x 12bit ADC + 12bit DAC @ 100MSPS
    
    Data Sheet : https://www.analog.com/media/en/technical-documentation/data-sheets/AD9961_9963.pdf
    
    SCT platform hold 1 such devices.
    
    This class provides the interface for instruments to communicate with the device
    '''

    register_map = {}

if __name__ == '__main__':
    pass