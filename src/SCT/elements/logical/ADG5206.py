# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.logical import LEABC 

class adg5206(LEABC):
    '''
    ADG5206 = 16 channel multiplexer
    
    Data Sheet : https://www.analog.com/media/en/technical-documentation/data-sheets/ADG5206_5207.pdf
    
    SCT platform hold 1 such devices.
    
    Notes: 
        * This devices is so simple that it hasn't got a physical register map.
        * This device is steered by the following semi-static outputs from the ZU:
            - MUX_EN
            - MUX_A3
            - MUX_A2
            - MUX_A1
            - MUX_A0
          The firmware people consider these singals to be 'gpio'
    
    This class provides the interface for the ADG5206
    '''

    register_map = {}

if __name__ == '__main__':
    pass