'''
Created on Aug 8, 2019

@author: hoeren
'''
import sys, os

if sys.version_info < (3, 5):
    this_file = __file__.split(os.path.sep)[-1]
    this_python = "%s.%s.%s" % tuple(list(sys.version_info)[:3])
    raise Exception("'%s' needs a mature Python 3 engine, got %s" % \
                    (this_file, this_python))

if __name__ == '__main__':
    print("working")