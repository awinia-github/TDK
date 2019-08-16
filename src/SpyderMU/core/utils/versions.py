'''
Created on Aug 16, 2019

@author: hoeren
'''
import os, sys, platform
import inspect

from PyQt5 import Qt

class OpenCVinfo(object):
    
    def __init__(self):
        if 'cv2' in dir():
            self.__version__ = cv2.__version__ # eclipse gets confused ;-) no error, is correct
        else:
            try:
                import cv2
            except (ImportError, ModuleNotFoundError) as e:
                self.__version__ = ''
            else:
                self.__version__ = cv2.__version__ 
        if self.__version__ != '':
            # image write formats available
            self.elements = dir(cv2)
            self.image_write_formats = []
            tmp = [e for e in self.elements if 'IMWRITE' in e]
            for element in tmp:
                if element.split('_')[1].lower() not in self.image_write_formats:
                    self.image_write_formats.append(element.split('_')[1].lower())
            # video write formats available
            for element in self.elements:
                if 'fourcc' in element:
                    print(element)
    
        

def version_numbers():
    '''
    returns a bunch of version numbers.
    '''
    retval = {}
    # Machine
    retval['Machine'] = {'processor' : platform.uname().processor,
                         'node' : platform.uname().node}

    # Operating System 
    #TODO: implement OS section further (https://docs.python.org/3.7/library/platform.html)
    retval['OS'] = {'system' : platform.system(),
                    'version' : platform.version}
  
    # Python
    retval['python'] = {'version' : platform.python_version(),
                        'build' : platform.python_build(),
                        'implementation' : platform.python_implementation()}
    
    # Qt & PyQt
    vers = ['%s = %s' % (k,v) for k,v in vars(Qt).items() if k.lower().find('version') >= 0 and not inspect.isbuiltin(v)]
    print('\n'.join(sorted(vers)))
    
    
    
    # OpenCV
    



    #TODO: access the python console welcome message for python/anaconda stuff

    
    # Anaconda
    if 'CONDA' in sys.executable.upper(): # still possible that anaconda is installed, but not active (on my mac) ...
        # reference : https://stackoverflow.com/questions/48342098/how-to-check-python-anaconda-version-installed-on-windows-10-pc
        executable_path_elements = sys.executable.split(os.path.sep)
        conda_root_elements = []
        for element in executable_path_elements:
            if 'CONDA' not in element.upper():
                conda_root_elements.append(element)
            else:
                conda_root_elements.append(element)
                break
        conda_root = os.path.sep.join(conda_root_elements)
        print("Conda root = %s" % conda_root)
        for root,dirs, files in os.walk(conda_root):
            for file in files:
                file_root, file_ext = os.path.splitext(file)
                if file_ext == '.json' and file.startswith('anaconda'):
                    print(os.path.join(root,file))
                    # returns :
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\conda-meta\anaconda-client-1.7.2-py36_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\conda-meta\anaconda-custom-py36h363777c_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\conda-meta\anaconda-navigator-1.9.6-py36_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\conda-meta\anaconda-project-0.8.2-py36_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py27\conda-meta\anaconda-5.0.1-py27hdb50712_1.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py27\conda-meta\anaconda-client-1.6.5-py27h9642776_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py27\conda-meta\anaconda-navigator-1.6.9-py27hd588ecf_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py27\conda-meta\anaconda-project-0.8.0-py27h56b7296_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py27\Menu\anaconda-navigator.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py36\conda-meta\anaconda-5.0.1-py36h8316230_2.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py36\conda-meta\anaconda-client-1.6.5-py36hd36550c_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py36\conda-meta\anaconda-navigator-1.6.9-py36hc720852_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py36\conda-meta\anaconda-project-0.8.0-py36h8b3bf89_0.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\envs\py36\Menu\anaconda-navigator.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\Menu\anaconda-navigator.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\pkgs\anaconda-navigator-1.6.9-py27hd588ecf_0\Menu\anaconda-navigator.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\pkgs\anaconda-navigator-1.6.9-py36hc720852_0\Menu\anaconda-navigator.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\pkgs\anaconda-navigator-1.8.4-py36_0\Menu\anaconda-navigator.json
                    # C:\Users\hoeren\AppData\Local\Continuum\anaconda3\pkgs\anaconda-navigator-1.9.6-py36_0\Menu\anaconda-navigator.json
                    # which json to use ?!? (see reference at top of section)
    
    else:
        print("bommer, we don't have conda")

    return retval

if __name__ == '__main__':
    pass