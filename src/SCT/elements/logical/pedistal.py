# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.logical import LEABC


class pedistal(LEABC):
    '''
    pedistal = a DAC that come out (buffered) to the user.
    
    infact the AD5372 is used for this, this element is thus a logical one.
    
    SCT platform hold 2 such devices.
        DAC0 of the AD5372 = PD0
        DAC1 of the AD5372 = PD1
    
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