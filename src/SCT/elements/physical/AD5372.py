# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.physical import PEABC 


class ad5372(PEABC):
    '''
    AD5372 = 32 channel x 16 bit static DAC's
    
    Data Sheet : https://www.analog.com/media/en/technical-documentation/data-sheets/AD5372_5373.pdf
    
    SCT platform hold 1 such devices.
    
    This class provides the interface for instruments to communicate with the DAC's
    '''
    register_map = {}

if __name__ == '__main__':
    AD5372 = ad5372()
    print(AD5372)