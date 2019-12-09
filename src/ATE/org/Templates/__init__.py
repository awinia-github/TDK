import os, shutil

project_structure = {
    '.'                               : ('project_root',      [('dot_spyder', '.spyder', 'text'), 
                                                               ('database.sqlite3', "%PROJECT%.sqlite3", 'binary')]),
    './documentation'                 : ('docs_root',         []),
    './documentation/standards'       : ('standards_root',    [('AEC_Q100_Rev_G_Base_Document.pdf', 'AEC_Q100_Rev_G_Base_Document.pdf', 'binary'),
                                                               ('STDF V4.pdf', 'STDF V4.pdf', 'binary')]),
    './sources'                       : ('sources_root',      [('dunder_init.py', '__init__.py', 'text'),
                                                               ('dunder_main.py', '__main__.py', 'text')]),
    './sources/definitions'           : ('definitions_root',  [('dunder_init.py', '__init__.py', 'text')]),
    './sources/definitions/states'    : ('states_root',       [('dunder_init.py', '__init__.py', 'text'),
                                                               ('init_harware.py', 'init_hardware.py', 'text')]),
    './sources/definitions/protocols' : ('protocols_root',    [('dunder_init.py', '__init__.py', 'text')]),
    './sources/definitions/tests'     : ('tests_root',        [('dunder_init.py', '__init__.py', 'text')]),
    './sources/definitions/programs'  : ('programs_root',     [('dunder_init.py', '__init__.py', 'text')]),
    './sources/definitions/patterns'  : ('patterns_root',     [('dunder_init.py', '__init__.py', 'text')]),
    }

def translation_template(project_path):
    '''
    given the project_path, this function will return a translation_template,
    dynamically filled in with USER, DT, DATE, PROJECT, 
    '''
    from ATE.utils.DT import DT
    from ATE.utils.varia import sys_platform
    import getpass
    
    retval = {}
    now = DT()
    retval['DT'] = str(DT(now.local()))
    retval['PATH'], retval['PROJECT'] = os.path.split(project_path) 
    retval['PLATFORM'] = sys_platform()
    retval['USER'] = getpass.getuser()
    return retval

def templating(source, destination, mode, translation):
    '''
    source is a file in this directory
    destination is an absolute path (ending in a filename!) 
    translation is a dictionary with the translations
    
    in source there are words encapsulated in % (eg: %NAME%), 
    NAME has to be a key in the tranlation dictionary, and the 
    value is what %NAME% will be replaced with.
    '''
    if mode not in ['text', 'binary']:
        raise Exception("Mode must be 'text' or 'binary', not '%s'" % mode)
    
    source = os.path.join(os.path.dirname(__file__), source)
    if not os.path.exists(source):
        raise Exception("Template '%s' doesn't exist" % source)
    
    if os.path.exists(destination):
        raise Exception("Templating '%s' to '%s', but the destination exists!" % (source, destination))

    destination_base = os.path.dirname(destination)
    if not os.path.exists(destination_base):
        os.makedirs(destination_base)

    if mode == 'text':
        with open(source, 'r') as src:
            with open(destination, 'w') as dst:
                for line in src:
                    for item in translation:
                        look_for = "%%%s%%" % item
                        replace_with = translation[item]
                        if look_for in line:
                            line = line.replace(look_for, replace_with)
                    dst.write(line)
    else:
        shutil.copyfile(source, destination)
                    
if __name__ == '__main__':
    from SpyderMockUp.SpyderMockUp import workspace
    from ATE.org.listings import list_ATE_projects
    ATE_projects = list_ATE_projects(workspace)
    if ATE_projects: # ATE projects found
        translation_base = translation_template(os.path.join(workspace, ATE_projects[0]))
        print(translation_base)
        other_translation = {'foo' : 'bar', 'USER' : 'tom'}
        translation_base.update(other_translation)
        print(translation_base)