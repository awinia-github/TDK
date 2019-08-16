# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.logical import LEABC


class ad8330(LEABC):
    '''
    AD8330 = 1 (differential) channel Variable Gain Amplifier
    
    Data Sheet : https://www.analog.com/media/en/technical-documentation/data-sheets/AD8330.pdf
    
    SCT platform hold 2 such devices.
    
    The AD8330 is programmed by using some channels of the AD5372, it therefore is a 'logical' element
    
    This class provides the interface for instruments to communicate with the ADC's
    '''

    register_map = {}


    def __init__(self, configManager, channel):
        if not isinstance(channel, int) or channel not in [0, 1]:
            raise Exception("channel must be provided and in the range [0:1]")
        self.name = 'AD8330_%d' % channel
        self.fd = open('/dev/' % self.name, 'rw')
        self.configManager = configManager
        self.__call__()

if __name__ == '__main__':
    pass