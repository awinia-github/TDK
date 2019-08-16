# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.physical import PEABC 


class ad7766(PEABC):
    '''
    AD7766 = 1 channel x 24 bit ADC
    
    Data Sheet : https://www.analog.com/media/en/technical-documentation/data-sheets/AD7766.pdf
    
    SCT platform hold 3 such device (model=AD7766-2, cfr 'channel')
    
    This class provides the interface for instruments to communicate with the ADC's
    '''

    register_map = {}

    def __init__(self, configManager, channel):
        if not isinstance(channel, int) or channel not in [0, 1, 2]:
            raise Exception("channel must be provided and in the range [0:2]")
        self.name = 'AD7766_%d' % channel
        self.fd = open('/dev/' % self.name, 'rw')
        self.configManager = configManager
        self.__call__()

if __name__ == '__main__':
    pass