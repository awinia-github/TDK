'''
Created on Aug 14, 2019

@author: hoeren
'''
import os

project_root = str.join(os.path.sep, os.path.split(__file__)[0].split(os.path.sep)[:-1]) 

project = os.path.join(project_root, 'src')
resources = os.path.join(project_root, 'resources')
stdf_resources = os.path.join(resources, 'stdf')
metis_path = os.path.join(resources, 'metis')
our_license = os.path.join(project_root, 'license')
doc = os.path.join(project_root, 'doc')

ATE_scripts = os.path.join(project, str.join(os.path.sep, ['ATE', 'scripts']))
SCT_scripts = os.path.join(project, str.join(os.path.sep, ['SCT', 'scripts']))
metis_scripts = os.path.join(project, str.join(os.path.sep, ['metis', 'scripts']))


# good place to see the size of the whole tree
def disk_size(start_path = '.'):
    if start_path == '.':
        start_path = os.getcwd()
    else:
        if not os.path.exists(start_path) or not os.path.isdir(start_path):
            raise Exception("'%s' is not an (existing) directory" % start_path)
    total_size = 0
    for root, _, files in os.walk(start_path):
        if '.git' not in root.split(os.path.sep): # exclude .git!
            for file in files:
                FileName = os.path.join(root, file)
                total_size += os.path.getsize(FileName)
    return total_size

if __name__ == '__main__':
    print("#\n# Project disk usage :")
    print("#    %6.2f MB sources" % round((disk_size(project)/1000000), 2))
    print("#    %6.2f MB resources" % round((disk_size(resources)/1000000), 2))
    print("#    %6.2f MB doc & co" % round((disk_size(doc) + disk_size(our_license))/1000000, 2))
    print("#  ", "-"*11)
    print("#    %6.2f MB total" % round((disk_size(project_root)/1000000), 2))
    print("#\n# Copy the below text to your (i)python console to get access to the project\n#")
    print("import sys, os")
    print("project = r'%s'" % project)
#     print("ATE_scripts = r'%s'" % ATE_scripts)
#     print("SCT_scripts = r'%s'" % SCT_scripts)
#     print("metis_scripts = r'%s'" % metis_scripts)
    print("sys.path.insert(0, project)")
#     print("sys.path.append(ATE_scripts)")
#     print("sys.path.append(SCT_scripts)")
#     print("sys.path.append(metis_scripts)")
#    print("stdf_resources = r'%s'" % stdf_resources)
    print("os.environ['METIS'] = r'%s'" % metis_path)