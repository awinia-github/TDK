# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.physical import PEABC 

class gpio(PEABC):
    '''
    GPIO = General Purpose Inputs and Outputs, semi-static levels, thus a physical element.
    
    The GPIO element drives the following signals 
    
    From the ADIO bus :

        \VFBWL  : Output to Q816; Voltage Force BandWidth Limit
        \VFSS   : Output to U835B (ADG5419); Voltage Force Source Select --> LO means that Vsource drives RLCF
                                                                             HI means that the DAC21 drives RLCF
        
        \A0FEN  : Output to drive Q800 (AWG) --> LO means that the output of the AWG on Abus 0 is enabled
        \A0FBWL : Output to drive Q804 (AWG) --> LO means that the bandwith of AWG on Abus 0  is limimited to 30MHz

        A0SEN   : Output to enable U816A (DIG/ADC-driver)\  
                                   U817 (DIG/Switch)     +--> HI means that the input of the Digitizer on Abus 0 is enabled
        \A0SBWL : Output to drive Q810 (DIG/BUF634) --> LO means that the bandwidth of the Digitizer on Abus 0 is limited to 30MHz 
                                                        HI means that the bandwidth of the Digitizer on Abus 0 is limited to 180MHz
        A0SSS   : Output to U817B (DIG/Switch) --> Abus 0 Sense Source Select : HI --> Isense is brought to the ADC0
                                                                                LO --> Abus 0 is brought to the ADC0

        \A1FEN  : Output to drive Q801 (AWG) --> LO means that the output of the AWG on Abus 1 is enabled
        \A1FBWL : Output to drive Q807 (AWG) --> LO means that the bandwith of AWG on Abus 1  is limimited to 30MHz

        A1SEN   : Output to enable U816B (DIG/ADC-driver)\  
                                   U824 (DIG/Switch)     +--> HI means that the input of the Digitizer on Abus 1 is enabled
        \A1SBWL : Output to drive Q813 (DIG/BUF634) --> LO means that the bandwidth of the Digitizer on Abus 1 is limited to 30MHz 
                                                        HI means that the bandwidth of the Digitizer on Abus 1 is limited to 180MHz
        A1SSS   : Output to U824B (DIG/Switch) --> Abus 1 Sense Source Select : HI --> Vsense is brought to the ADC1
                                                                                LO --> Abus 1 is brought to the ADC1

    SCT platform hold 1 such interface
    
    This class provides the interface to the AWG/DIG
    '''

    register_map = {
        'RLC'     : ['VFBWLn', 'VFSSn'],
        'VFBWLn'  : {'offset' : 0x000, 'bytes' : 1, 'slice' : (0,),  'default' : 1,    'access' : 'W', 'value' : None, 'changed' : False}, 
        'VFSSn'   : {'offset' : 0x000, 'bytes' : 1, 'slice' : (1,),  'default' : 1,    'access' : 'W', 'value' : None, 'changed' : False},

        'AWG'    : ['A0FENn', 'A0FBWLn', 'A0FENn', 'A0FBWLn', ],
        'A0FENn'  : {'offset' : 0x001, 'bytes' : 1, 'slice' : (0,),  'default' : 1,    'access' : 'W', 'value' : None, 'changed' : False},
        'A0FBWLn' : {'offset' : 0x001, 'bytes' : 1, 'slice' : (1,),  'default' : 1,    'access' : 'W', 'value' : None, 'changed' : False},
        'A0FENn'  : {'offset' : 0x001, 'bytes' : 1, 'slice' : (4,),  'default' : 1,    'access' : 'W', 'value' : None, 'changed' : False},
        'A0FBWLn' : {'offset' : 0x001, 'bytes' : 1, 'slice' : (5,),  'default' : 1,    'access' : 'W', 'value' : None, 'changed' : False},

        'DIG'     : ['A0SEN', 'A0SBWLn', 'A0SSS', 'A1SEN', 'A1SBWLn', 'A1SSS'],
        'A0SEN'   : {'offset' : 0x002, 'bytes' : 1, 'slice' : (0,),  'default' : 0,    'access' : 'W', 'value' : None, 'changed' : False},
        'A0SBWLn' : {'offset' : 0x002, 'bytes' : 1, 'slice' : (1,),  'default' : 0,    'access' : 'W', 'value' : None, 'changed' : False},
        'A0SSS'   : {'offset' : 0x002, 'bytes' : 1, 'slice' : (2,),  'default' : 0,    'access' : 'W', 'value' : None, 'changed' : False},
        'A0SEN'   : {'offset' : 0x002, 'bytes' : 1, 'slice' : (4,),  'default' : 0,    'access' : 'W', 'value' : None, 'changed' : False},
        'A0SBWLn' : {'offset' : 0x002, 'bytes' : 1, 'slice' : (5,),  'default' : 0,    'access' : 'W', 'value' : None, 'changed' : False},
        'A0SSS'   : {'offset' : 0x002, 'bytes' : 1, 'slice' : (6,),  'default' : 0,    'access' : 'W', 'value' : None, 'changed' : False},
    }

if __name__ == '__main__':
    pass