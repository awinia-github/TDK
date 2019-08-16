'''
Created on Aug 5, 2019

@author: hoeren
'''

import re

names = ["blablabla.stdf.gz", 'bla.GZ', 'xyz.gZ', 'xyz.stdf', 'bla.zip', 'blah.std']
patterns = {'gz' : r'stdf?\.gz$', 'zip' : r'stdf?\.zip$', 'stdf' : r'\.stdf?'}


if __name__ == '__main__':
    for name in names:
        print(name)
        for pattern in patterns:
            print("\t r'%s' : " % patterns[pattern], end='')
            if re.search(patterns[pattern], name, re.IGNORECASE): # bullshit error from eclipse !!!
                print("match")
            else:
                print("no match")