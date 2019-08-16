'''
Created on Aug 14, 2019

@author: hoeren
'''
import os

project_root = str.join(os.path.sep, os.path.split(__file__)[0].split(os.path.sep)[:-3]) 
project = os.path.join(project_root, 'src')
resources_path = os.path.join(project_root, 'resources')
stdf_resources = os.path.join(resources_path, 'stdf')
stdf_files = [os.path.join(stdf_resources, i) for i in os.listdir(stdf_resources) if i.endswith('std') or i.endswith('stdf')]
stdf_gz_files = [os.path.join(stdf_resources, i) for i in os.listdir(stdf_resources) if i.endswith('std.gz') or i.endswith('stdf.gz')]
stdf_bz2_files = [os.path.join(stdf_resources, i) for i in os.listdir(stdf_resources) if i.endswith('std.bz2') or i.endswith('stdf.bz2')]
stdf_xz_files = [os.path.join(stdf_resources, i) for i in os.listdir(stdf_resources) if i.endswith('std.xz') or i.endswith('stdf.xz')]

if __name__ == '__main__':
    print("import sys, os")
    print("project = r'%s'" % project)
    print("sys.path.insert(0, project)")
    print("resources_path = r'%s'" % resources_path)
    print("stdf_resources = r'%s'" % stdf_resources)
    print("stdf_files = %s" % stdf_files)
    print("stdf_gz_files = %s" % stdf_gz_files)
    print("stdf_bz2_files = %s" % stdf_bz2_files)
    print("stdf_xz_files = %s" % stdf_xz_files)
