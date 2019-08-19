'''
Created on Aug 13, 2019

@author: hoeren
'''

def set_bit(n, var, to=1):
    '''
    set bit n in var to
    n can be an integer for a single bit or a tuple for a bit-slice.
    to is an integer (1/0 for a single bit or something else for a bit-slice)
    '''
    mask = 1 << n
    if to == 0:
        mask = ~mask
        return var & mask
    elif to == 1:
        return var | mask
    else:
        raise Exception("WTF")

def get_bit(n, var):
    '''
    return bit n from var
    n can be an integer for one bit or a tuple for a bit-slice
    '''
    mask = 1 << n
    return (var & mask) >> n

if __name__ == '__main__':
    variable = 0x00; print(variable)
    variable = set_bit(0, variable, 1); print(variable)
    variable = set_bit(1, variable, 1); print(variable)
    variable = set_bit(2, variable, 1); print(variable)
    variable = set_bit(1, variable, 0); print(variable)
    print(get_bit(0, variable))
    print(get_bit(1, variable))
    print(get_bit(2, variable))
    variable = set_bit(15, 0x00, 1)
    print(variable)
    