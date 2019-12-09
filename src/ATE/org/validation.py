'''
Created on Nov 19, 2019

@author: hoeren
'''
import os, re

valid_python_class_name_regex = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
valid_die_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_product_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_maskset_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_device_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_package_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_test_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_testprogram_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_project_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_pcb_name_regex = r"^[a-zA-Z][a-zA-Z0-9]*$"
valid_integer_regex = r"^\d*"

def is_ATE_project(project_path):
    ATE_file = os.path.join(project_path, '.spyder')
    if os.path.exists(ATE_file) and os.path.isfile(ATE_file):
        with open(ATE_file, 'r') as fd:
            for line in fd:
                if line.upper().startswith('TYPE'):
                    if 'ATE' in line.upper():
                        return True
    return False

def is_valid_python_class_name(name):
    pattern = re.compile(valid_python_class_name_regex)
    if pattern.match(name):
        return True
    else:
        return False
    
def is_valid_die_name(name):
    '''
    Check if the supplied name is a valid name for a 'die'
    
    Note: in the end this will be the name of a directory ...
    '''
    pattern = re.compile(valid_die_name_regex)
    if pattern.match(name):
        return True
    else:
        return False
    
def is_valid_product_name(name):
    '''
    Check if the supplied name is a valid name for a 'product'
    
    Note: should be the same as for the die !
    '''
    pattern = re.compile(valid_product_name_regex)
    if pattern.match(name):
        return True
    else:
        return False

def is_valid_maskset_name(name):
    '''
    Check if the supplied name is a valid name for a 'maskset'
    '''
    pattern = re.compile(valid_maskset_name_regex)
    if pattern.match(name):
        return True
    else:
        return False

def is_valid_device_name(name):
    '''
    Check if the supplied name is a valid name for a 'device'
    '''
    pattern = re.compile(valid_device_name_regex)
    if pattern.match(name):
        return True
    else:
        return False

def is_valid_package_name(name):
    '''
    Check if the supplied name is a valid name for a 'package'
    '''
    pattern = re.compile(valid_package_name_regex)
    if pattern.match(name):
        return True
    else:
        return False

def is_valid_test_name(name):
    '''
    Check if the supplied name is a valid name for a 'test'
    
    As a test is a .py file, and in the .py file the class will be the same name, 
    this reverts to 'is_valid_python_class_name', however, we don't want the word
    'test' in any capitalisations in this name (it is always a test, so let's skip it) !!!
    '''
    if 'TEST' in name.upper():
        return False
    pattern = re.compile(valid_test_name_regex)
    if pattern.match(name):
        return True
    else:
        return False

def is_valid_project_name(name):
    '''
    Check if the supplied name is a valid name for a 'project'
    '''
    if 'TEST' in name.upper():
        return False
    pattern = re.compile(valid_project_name_regex)
    if pattern.match(name):
        return True
    else:
        return False

def is_valid_pcb_name(name):
    pattern = re.compile(valid_pcb_name_regex)
    if pattern.match(name):
        return True
    else:
        return False

def has_single_site_loadboard(project_path, hardware_version):
    from ATE.org.listings import dict_pcbs_for_hardware_setup
    from ATE.org.listings import list_hardware_setups
    
    if is_ATE_project(project_path):
        if hardware_version in list_hardware_setups(project_path):
            pcbs = dict_pcbs_for_hardware_setup(project_path, hardware_version)
            if pcbs['SingeSiteLoadboard'] != "":
                return True
    return False

def has_probe_card(project_path, hardware_version):
    from ATE.org.listings import dict_pcbs_for_hardware_setup
    from ATE.org.listings import list_hardware_setups
    
    if is_ATE_project(project_path):
        if hardware_version in list_hardware_setups(project_path):
            pcbs = dict_pcbs_for_hardware_setup(project_path, hardware_version)
            if pcbs['ProbeCard'] != "":
                return True
    return False

def has_single_site_DIB(project_path, hardware_version):
    pass

if __name__ == '__main__':
    from SpyderMockUp.SpyderMockUp import workspace
    from ATE.org.listings import list_ATE_projects
    
    for project in list_ATE_projects(workspace):
        print(project)