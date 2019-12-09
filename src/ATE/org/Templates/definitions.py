#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Tester/tets definition
from ATE.Tester.Micronas import SCT8 as DUT
from ATE.Testing import test

# Constant Definitions 
from ATE.Testing import Pass
from ATE.Testing import Fail
from ATE.Testing import Undetermined
from ATE.Testing import Unknown

# Channel Definitions
VDD = 5

 
# State Definitions
def go_from_UNDETERMINED_to_ANY_state():
    # auto generated, not re-factored 
    DUT.init_hardware()

def go_from_HELLO_to_OFF_state():
    # re-factored from contact_test.pre_do
    pass

def go_from_WORLD_to_OFF_state():
    # re-factroed from contact_test.pre_do
    pass



def from_ANY_to_Idle():
    pass

state_timing = {
    ('ANY', 'Idle') : 0.0001
}

if __name__ == '__main__':
    print("Pass : %s" % Pass)
    print("Fail : %s" % Fail)
    print("Undetermined : %s" % Undetermined)
    print("Unknown : %s" % Unknown)
