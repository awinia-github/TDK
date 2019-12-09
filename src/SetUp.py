# -*- coding: utf-8 -*-
"""
This small script creates the needed directories in your home directory.

Created on Mon Dec  9 17:26:01 2019

@author: hoeren
"""
import os

homedir = os.path.expanduser("~")

workspace_dir = os.path.join(homedir, r"__spyder_workspace__")
if not os.path.exists(workspace_dir):
    print("Creating '%s' ... " % workspace_dir, end='')
    os.mkdir(workspace_dir)
    print("Done.")

metis_dir = os.path.join(homedir, r"__metis__")
if not os.path.exists(metis_dir):
    print("Created '%s' ... " % metis_dir, end='')
    os.mkdir(metis_dir)
    print("Done.")