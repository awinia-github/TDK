# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.physical import PEABC 

class ad7770(PEABC):
    '''
    AD7770 = 8 channels x 24 bit ADC
    
    Data Sheet : https://www.analog.com/media/en/technical-documentation/data-sheets/ad7770.pdf
    
    SCT platform hold 1 such device
    
    This class provides the interface for instruments to communicate with the ADC's
    '''

    register_map = {
        # CH0_CONFIG
        'CH0_GAIN'            : {'offset' : 0x000, 'bytes' : 1, 'slice' : (7, 6), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH0_REF_MONITOR'     : {'offset' : 0x000, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH0_RX'              : {'offset' : 0x000, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH1_CONFIG
        'CH1_GAIN'            : {'offset' : 0x001, 'bytes' : 1, 'slice' : (7, 6), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH1_REF_MONITOR'     : {'offset' : 0x001, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH1_RX'              : {'offset' : 0x001, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH2_CONFIG
        'CH2_GAIN'            : {'offset' : 0x002, 'bytes' : 1, 'slice' : (7, 6), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH2_REF_MONITOR'     : {'offset' : 0x002, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH2_RX'              : {'offset' : 0x002, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH3_CONFIG
        'CH3_GAIN'            : {'offset' : 0x003, 'bytes' : 1, 'slice' : (7, 6), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH3_REF_MONITOR'     : {'offset' : 0x003, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH3_RX'              : {'offset' : 0x003, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH4_CONFIG
        'CH4_GAIN'            : {'offset' : 0x004, 'bytes' : 1, 'slice' : (7, 6), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH4_REF_MONITOR'     : {'offset' : 0x004, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH4_RX'              : {'offset' : 0x004, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH5_CONFIG
        'CH5_GAIN'            : {'offset' : 0x005, 'bytes' : 1, 'slice' : (7, 6), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH5_REF_MONITOR'     : {'offset' : 0x005, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH5_RX'              : {'offset' : 0x005, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH6_CONFIG
        'CH6_GAIN'            : {'offset' : 0x006, 'bytes' : 1, 'slice' : (7, 6), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH6_REF_MONITOR'     : {'offset' : 0x006, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH6_RX'              : {'offset' : 0x006, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH7_CONFIG
        'CH7_GAIN'            : {'offset' : 0x007, 'bytes' : 1, 'slice' : (7, 6), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH7_REF_MONITOR'     : {'offset' : 0x007, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH7_RX'              : {'offset' : 0x007, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH_DISABLE
        'CH0_DISABLE'         : {'offset' : 0x008, 'bytes' : 1, 'slice' : (0,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH1_DISABLE'         : {'offset' : 0x008, 'bytes' : 1, 'slice' : (1,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH2_DISABLE'         : {'offset' : 0x008, 'bytes' : 1, 'slice' : (2,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH3_DISABLE'         : {'offset' : 0x008, 'bytes' : 1, 'slice' : (3,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH4_DISABLE'         : {'offset' : 0x008, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH5_DISABLE'         : {'offset' : 0x008, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH6_DISABLE'         : {'offset' : 0x008, 'bytes' : 1, 'slice' : (6,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH7_DISABLE'         : {'offset' : 0x008, 'bytes' : 1, 'slice' : (7,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # CH_SYNC
        'CH0_SYNC_OFFSET'     : {'offset' : 0x009, 'bytes' : 1, 'slice' : (7,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH1_SYNC_OFFSET'     : {'offset' : 0x00A, 'bytes' : 1, 'slice' : (7,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH2_SYNC_OFFSET'     : {'offset' : 0x00B, 'bytes' : 1, 'slice' : (7,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH3_SYNC_OFFSET'     : {'offset' : 0x00C, 'bytes' : 1, 'slice' : (7,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH4_SYNC_OFFSET'     : {'offset' : 0x00D, 'bytes' : 1, 'slice' : (7,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH5_SYNC_OFFSET'     : {'offset' : 0x00E, 'bytes' : 1, 'slice' : (7,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH6_SYNC_OFFSET'     : {'offset' : 0x00F, 'bytes' : 1, 'slice' : (7,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH7_SYNC_OFFSET'     : {'offset' : 0x010, 'bytes' : 1, 'slice' : (7,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # GENERAL_USER_CONFIG_1
        'ALL_CH_DIS_MCLK_EN'  : {'offset' : 0x011, 'bytes' : 1, 'slice' : (7,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'POWERMODE'           : {'offset' : 0x011, 'bytes' : 1, 'slice' : (6,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'PDB_VCM'             : {'offset' : 0x011, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'PDB_REFOUT_BUF'      : {'offset' : 0x011, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'PDB_SAR'             : {'offset' : 0x011, 'bytes' : 1, 'slice' : (3,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'PDB_RC_OSC'          : {'offset' : 0x011, 'bytes' : 1, 'slice' : (2,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'SOFT_RESET'          : {'offset' : 0x011, 'bytes' : 1, 'slice' : (1,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # GENERAL_USER_CONFIG_2
        'SAR_DIAG_MODE_EN'    : {'offset' : 0x012, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'SDO_DRIVE_STR'       : {'offset' : 0x012, 'bytes' : 1, 'slice' : (4,3),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'DOUT_DRIVE_STR'      : {'offset' : 0x012, 'bytes' : 1, 'slice' : (2,1),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'SPI_SYNC'            : {'offset' : 0x012, 'bytes' : 1, 'slice' : (0,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # GENERAL_USER_CONFIG_3
        'CONVST_DEGLITCH_DIS' : {'offset' : 0x013, 'bytes' : 1, 'slice' : (7,6),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'SPI_SLAVE_MODE_EN'   : {'offset' : 0x013, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CLK_QUAL_DIS'        : {'offset' : 0x013, 'bytes' : 1, 'slice' : (0,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # DOUT_FORMAT
        'DOUT_FORMAT'         : {'offset' : 0x014, 'bytes' : 1, 'slice' : (7,6),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'DOUT_HEADER_FORMAT'  : {'offset' : 0x014, 'bytes' : 1, 'slice' : (5,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'DCLK_CLK_DIV'        : {'offset' : 0x014, 'bytes' : 1, 'slice' : (3,1),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # ADC_MUX_CONFIG
        'REF_MUX_CTRL'        : {'offset' : 0x015, 'bytes' : 1, 'slice' : (7,6),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'MTR_MUX_CTRL'        : {'offset' : 0x015, 'bytes' : 1, 'slice' : (5,2),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # GLOBAL_MUX_CONFIG
        'GLOBAL_MUX_CTRL'     : {'offset' : 0x016, 'bytes' : 1, 'slice' : (7,3),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # GPIO_CONFIG  
        'GPIO_OP_EN'          : {'offset' : 0x017, 'bytes' : 1, 'slice' : (2,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # GPIO_DATA
        'GPIO_READ_DATA'      : {'offset' : 0x018, 'bytes' : 1, 'slice' : (5,3),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'GPIO_WRITE_DATA'     : {'offset' : 0x018, 'bytes' : 1, 'slice' : (2,0),  'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # BUFFER_CONFIG_1
        'REF_BUF_POS_EN'      : {'offset' : 0x019, 'bytes' : 1, 'slice' : (4,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'REF_BUF_NEG_EN'      : {'offset' : 0x019, 'bytes' : 1, 'slice' : (3,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # BUFFER_CONFIG_2
        'REF-BUFP_PREQ'       : {'offset' : 0x01A, 'bytes' : 1, 'slice' : (7,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'REF-BUFN_PREQ'       : {'offset' : 0x01A, 'bytes' : 1, 'slice' : (6,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'PDB_ALDO1_OVRDRV'    : {'offset' : 0x01A, 'bytes' : 1, 'slice' : (2,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'PDB_ALDO2_OVRDRV'    : {'offset' : 0x01A, 'bytes' : 1, 'slice' : (1,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'PDB_DLDO_OVRDRV'     : {'offset' : 0x01A, 'bytes' : 1, 'slice' : (0,),   'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        # OFFSET & GAIN
        'CH0_OFFSET'          : {'offset' : 0x01C, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH0_GAIN'            : {'offset' : 0x01F, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH1_OFFSET'          : {'offset' : 0x022, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH1_GAIN'            : {'offset' : 0x025, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH2_OFFSET'          : {'offset' : 0x028, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH2_GAIN'            : {'offset' : 0x02B, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH3_OFFSET'          : {'offset' : 0x02E, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH3_GAIN'            : {'offset' : 0x031, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH4_OFFSET'          : {'offset' : 0x034, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH4_GAIN'            : {'offset' : 0x037, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH5_OFFSET'          : {'offset' : 0x03A, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH5_GAIN'            : {'offset' : 0x03D, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH6_OFFSET'          : {'offset' : 0x040, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH6_GAIN'            : {'offset' : 0x043, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH7_OFFSET'          : {'offset' : 0x046, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        'CH7_GAIN'            : {'offset' : 0x049, 'bytes' : 3, 'slice' : (23,0), 'default' : None, 'access' : 'RW', 'value' : None, 'changed' : False},
        }

if __name__ == '__main__':
    pass