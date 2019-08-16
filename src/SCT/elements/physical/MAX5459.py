# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.physical import PEABC 

class max5459(PEABC):
    '''
    MAX5459 = 2 X 10bit Digital Potentiometer
    
    Data Sheet : https://datasheets.maximintegrated.com/en/ds/MAX5494-MAX5499.pdf

    It is a 'write only' SPI-like interface :
        RDIN    : Output to U815 (MAX5459) Data 
        RSCLK   : Output to U815 (MAX5459) Clock
        \RCS    : Output to U815 (MAX5459) Chip Select
    
    SCT platform hold 1 such device
    
    This class provides the interface for instruments to communicate with the ADC's
    '''

    register_map = {
        'REG1'   : {'offset' : 0x000, 'bytes' : 2, 'slice' : (9, 0), 'default' : 0x1FF, 'access' : 'W', 'value' : None, 'changed' : False},
        'REG2'   : {'offset' : 0x002, 'bytes' : 2, 'slice' : (9, 0), 'default' : 0x1FF, 'access' : 'W', 'value' : None, 'changed' : False},
        'REG2NV' : {'offset' : 0x004, 'bytes' : 1, 'slice' : (0,),   'default' : 0,     'access' : 'W', 'value' : None, 'changed' : False},
        'NV2REG' : {'offset' : 0x005, 'bytes' : 1, 'slice' : (0,),   'default' : 0,     'access' : 'W', 'value' : None, 'changed' : False},
    }
    
    

if __name__ == '__main__':
    MAX5459 = max5459()
    print(MAX5459)