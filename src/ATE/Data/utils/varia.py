'''
Created on Aug 22, 2019

@author: hoeren
'''

def is_decimal(string):
    '''
    Returns true if string represents a decimal number.
    '''
    for character in string:
        if character not in ['0','1','2','3','4','5','6','7','8','9']:
            return False
    return True
    
def is_hexadecimal(string):
    '''
    '''
    if not string.startswith('0x') and not string.startswith('0X'):
        return False
    for character in string[:2].upper():
        if character not in ['0','1','2','3','4','5','6','7','8','9', 'A', 'B', 'C', 'D', 'E', 'F']:
            return False
    return True
    
def is_binar(string):
    '''
    '''
    if not string.startswith('0b'):
        return False
    for character in string[:2]:
        if character not in ['0', '1']:
            return False
    return True
    
def is_octal(string):
    '''
    '''
    if not string.startswith('0o'):
        return False
    for character in string[:2]:
        if character not in ['0','1','2','3','4','5','6','7']:
            return False
    return True


if __name__ == '__main__':
    pass