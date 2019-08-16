'''
Created on Aug 8, 2019

@author: hoeren
'''

def argskwargs(*args, **kwargs):
    print("Type(%s)=%s" % (args, type(args)))
    print("Type(%s)=%s" % (kwargs, type(kwargs)))

if __name__ == '__main__':
    argskwargs(5, 6, 7, foo='bar')