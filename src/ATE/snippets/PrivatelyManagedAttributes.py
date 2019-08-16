# -*- coding: utf-8 -*-
import sys, os
from builtins import AttributeError, NameError

if sys.version_info < (3, 5):
    this_file = __file__.split(os.path.sep)[-1]
    this_python = "%s.%s.%s" % tuple(list(sys.version_info)[:3])
    raise Exception("'%s' needs a mature Python 3 engine, got %s" % \
                    (this_file, this_python))

class PMA(object):

    _pma = {} # works with and without this pre-definition
    
    def __init__(self):
        self.FOO = 1 # becomes unreachable after next line
        self._pma = {'FOO' : 2,
                     'BAR' : 3}
        self.FOO = 4

    def __getattribute__(self, attr):
        retval = object.__getattribute__(self, attr)
        if not attr.startswith('_') and attr in self._pma:
            return self._pma[attr]
        return retval

    def __getattr__(self, attr):
        if hasattr(self.__dict__, '_pma'):
            if hasattr(self._pma, attr):
                return self._pma[attr]
            
    def __setattr__(self, attr, value):
        if hasattr(self, '__dict__'):
            if hasattr(self.__dict__, '_pma'):
                if hasattr(self.__dict__._pma, attr):
                    self._pma[attr] = value
                    return
        object.__setattr__(self, attr, value)
    
    def __delattr__(self, attr):
        if hasattr(self._pma, attr):
            del self._pma[attr]
        else:
            object.__delattr__(self, attr)
    
    def __str__(self):
        retval = '-' * 79 + '\n' 
        retval += str(__class__).split('.')[-1].replace("'>", '') + '\n'
        for attr in self.__dict__:
            if attr == '_pma':
                retval += "   _pma\n"
                for field in self._pma:
                    retval += "      %s = %s\n" % (field, self._pma[field])
            elif not attr.startswith('__'):
                retval += "   %s = %s\n" % (attr, self.__getattribute__(attr))
        return retval           

if __name__ == '__main__':    
    pma = PMA();       print("after: pma=PMA()");              print(pma)
    pma.BARZ=5;        print("after: pma.BARZ=5");             print(pma)
    foo = pma.Zever;   print("after: foo=pma.zever (%s)"%foo); print(pma)
    pma.FOO=6;         print("after: pma.FOO=6");              print(pma)
    pma._pma['new']=7; print("after: pma._pma['new']=7");      print(pma)
    pma.new ='world';  print("after: pma.new = 'world");       print(pma)
    del pma.BARZ;      print("after: del pma.BARZ");           print(pma)
    pma.FOO=8;         print("after: pma.FOO=8");              print(pma)
    foo = pma.FOO;     print("after: foo = pma.FOO (%s)"%foo); print(pma)
    del pma.FOO;       print("after: del pma.FOO");            print(pma)
    pma.FOO=9;         print("after: pma.FOO=9");              print(pma)
    del pma.new;       print("after: del pma.new");            print(pma)
    