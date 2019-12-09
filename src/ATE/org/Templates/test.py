#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on %DT%

@author: %USER%
'''

from ATE.org.Testing import testABC
#from common import *

#from definitions.protocols.bi_phase import my_bi_phase

class %TSTCLASS%(testABC):
    '''
    Description: 
        This test ... 
    '''
    run_time = 13.56327 #ms (automatically set)

    start_state = 'UNDETERMINED'
    end_state = 'CONTACT_TEST'

    input_parameters = {'T' : {'Min' : -40, 'Max' : 170, 'Default' : 25,  'Unit' : '°C'}, # Obligatory !
                        'i' : {'Min' : 0.1, 'Max' : 2.5, 'Default' : 1.0, 'Unit' : 'mA'}}
    
    output_parameters = {'parameter1_name' : {'LSL' : None, 'USL' : 5,    'Nom' : 2.5, 'Unit' : 'Ω'}, # maybe add SBIN group ? - NO, auto assign testnumbers
                         'parameter2_name' : {'LSL' : 0,    'USL' : None, 'Nom' : 2.5, 'Unit' : 'mV'},
                         'R_vdd_contact'   : {'LSL' : None, 'USL' : 5,    'Nom' : 2,   'Unit' : 'Ω'}}

    def do(self, ip, op, gp, dm):
        print("Doing %s test ..." % self.__class__.__name__.split("_")[0])
        #the_value = SCT.protocol.my_bi_phase.read('adc')
        #SCT.protocol.my_bi_phase.write('dac', 0xAA)
        
    
    def target(self, ip, op, gp, dm):
        return self.do(ip, op, gp, dm)

    
    def flow(self, ip, op, gp, dm):
        return self.target(ip, op, gp, dm)
        
    
    
    
    
if __name__ == '__main__':
    from ATE.org.Sequencers import development_sequencer
    from ATE.Data.Loggers import Console

    sequencer = development_sequencer(__file__)
    sequencer.register_logger(Console)
    sequencer.register_test(%TSTCLASS%)

    #sequencer.print_run_modes()    
    sequencer.run(10)
    #sequencer.run("Time")
    #sequencer.run("Corners")
    #sequencer.run("Shmoo")
    #sequencer.run("Audit")
