'''
Created on %DT%
Platform : %PLATFORM%

This is the main entry point for the %PROJECT% (zip) project

@author: %USER%
'''

import argparse

parser = argparse.ArgumentParser(description="Entry point selector for all %PROJECT% test programs")
parser.add_argument("--info", action="store_true", help="prints out information of this project package")

args = parser.parse_args()

if args.info:
    print("info")


