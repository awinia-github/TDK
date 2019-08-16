'''
Created on Aug 9, 2019

@author: hoeren
'''

def call_by_reference(index):
    index['C'] = 3
    

if __name__ == '__main__':
    index = {'A' : 1, 'B' : 2}
    print(index)
    call_by_reference(index)
    print(index)