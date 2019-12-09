'''
Created on Sep 13, 2019

@author: hoeren
'''
import sys

if __name__ == '__main__':
    if sys.platform == "linux" or sys.platform == "linux2":
        print("Linux")
    elif sys.platform == "Darwin":
        print("Mac OS")
    elif sys.platform == "win32": # and what with windows64?!?
        print("Windows")
    else:
        print("Unknown OS : ", sys.platform)
        
