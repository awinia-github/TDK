'''
Created on Nov 20, 2019

@author: hoeren
'''
import os, sqlite3
from ATE.org.validation import is_ATE_project
from ATE.org.Templates import project_structure

class listings(object):
    
    def __init__(self, project_path):
        self.conn = None
        self.__call__(project_path)        

    def __call__(self, project_path):
        if self.conn != None:
            self.conn.close()
        db_file = "%s.sqlite3" % os.path.basename(project_path)
        self.db_path = os.path.join(project_path, db_file)
        if not os.path.exists(self.db_path):
            raise Exception("Couldn't find '%s'" % self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def __del__(self):
        if self.conn != None:
            self.conn.close()
    
    def insert(self, insert_sql_statement):
        if 'INSERT' not in insert_sql_statement.upper():
            raise Exception("I don't find the 'INSERT' keyword in '%s'" % insert_sql_statement)
        self.cursor.execute(insert_sql_statement)
        self.conn.commit()
    
    def select(self, select_sql_statement):
        if 'SELECT' not in select_sql_statement.upper():
            raise Exception("I don't find the 'SELECT' keyword in '%s'" % select_sql_statement)
        
    def list_hardwaresetups(self):
        retval = []
        sql_statement = "SELECT Name FROM hardwaresetups ORDER BY Name ASC"
        for row in self.cursor.execute(sql_statement):
            retval.append("HWR%s" % row[0])
        return retval
        
    def dict_hardwaresetups(self):
        pass
    
    def get_hardwaresetup(self, hardwaresetup):
        pass
    


def dict_projects(workspace_path):
    '''
    given a workspace_path, create a list with projects as key, and their
    project_path as value
    '''
    retval = {}
    for directory in os.listdir(workspace_path):
        full_directory = os.path.join(workspace_path, directory)
        if os.path.isdir(full_directory):
            retval[directory] = full_directory
    return retval
    
def list_projects(workspace_path):
    '''
    given a workspace_path, extract a list of all projects
    '''
    return list(dict_projects(workspace_path))

def dict_ATE_projects(workspace_path):
    '''
    given a workspace_path, create a dictionary with all ATE projects as key,
    and the project_path as value.
    '''
    retval = {}
    all_projects = dict_projects(workspace_path)
    for candidate in all_projects:
        possible_ATE_project = all_projects[candidate]
        if is_ATE_project(possible_ATE_project):
            retval[candidate] = possible_ATE_project
    return retval

def list_ATE_projects(workspace_path):
    '''
    given a workspace_path, extract a list of all ATE projects
    '''
    return list(dict_ATE_projects(workspace_path))

def dict_hardwaresetups(project_path):
    '''
    given a project_path, create a dictionary with as keys the hardware versions,
    and as value the path to the defintition file.
    '''
    retval = {}
    if is_ATE_project(project_path):
        hwr_root = dict_project_paths(project_path)['hwr_root']
        for candidate in os.listdir(hwr_root):
            candidate_path = os.path.join(hwr_root, candidate)
            if os.path.isfile(candidate_path) and candidate_path.endswith('.pickle'):
                hardwaresetup = candidate.replace('.pickle', '')
                retval[hardwaresetup] = candidate_path
    return retval

def list_hardwaresetups(project_path):
    return list(dict_hardwaresetups(project_path))
    
def dict_pcbs_for_hardware_setup(project_path, hardware_version):
    import pickle
    
    hwr_root = dict_project_paths(project_path)['hwr_root']
    hwr_setup_path = os.path.join(hwr_root, hardware_version)
    hwr_setup_path = os.path.join(hwr_setup_path, 'definition.pickle')
    hwr_setup = pickle.load(open(hwr_setup_path, 'rb'))
    return hwr_setup

def dict_masksets(project_path):
    '''
    given an (ATE) project_path, extract a dictionary with the maskset names
    as key and the masket definition file as value.
    '''
    retval = {}
    if is_ATE_project(project_path):
        maskset_root = dict_project_paths(project_path)['maskset_root']
        for element in os.listdir(maskset_root):
            if element.endswith('.pickle'):
                maskset_file = os.path.join(maskset_root, element)
                maskset_name = element.replace('.pickle', '')
                retval[maskset_name] = maskset_file
    return retval

def list_masksets(project_path):
    '''
    given an (ATE) project_path, extract a list of all masksets
    '''
    return list(dict_masksets(project_path))

def dict_packages(project_path):
    '''
    given an (ATE) project_path, construct a dictionary where the keys are
    all packages defined, and the value is the path to the definition file.
    '''
    retval = {}
    if is_ATE_project(project_path):
        package_root = dict_project_paths(project_path)['package_root']
        for candidate in os.listdir(package_root):
            if candidate.endswith('.pickle'):
                candidate_name = candidate.replace('.pickle', '')
                candidate_path = os.path.join(package_root, candidate)
                retval[candidate_name] = candidate_path
    return retval

def list_packages(project_path):
    return list(dict_packages(project_path))


def dict_devices(project_path):
    '''
    given an (ATE) project_path, construct a dictionary where the keys are all
    devices in the project, and the value is the path tot the definition file.
    '''
    retval = {}
    if is_ATE_project(project_path):
        device_root = dict_project_paths(project_path)['device_root']
        for candidate in os.listdir(device_root):
            if candidate.endswith('.pickle'):
                candidate_name = candidate.replace('.pickle', '')
                candidate_path = os.path.join(device_root, candidate)
                retval[candidate_name] = candidate_path
    return retval
 

def list_devices(project_path):
    '''
    given an (ATE) project_path, extract a list of all devices
    '''
    return list(dict_devices(project_path))

def dict_dies(project_path):
    '''
    given an (ATE) project_path, create a dictionary with the dies as keys,
    and the die_path as value.
    die_path is the absolute path to the location where the definition.pickle
    file is located (including the definition.pickle file itself)
    '''
    retval = {}
    if is_ATE_project(project_path):
        die_root = dict_project_paths(project_path)['die_root']
        for rel_die_path in os.listdir(die_root):
            if rel_die_path.endswith('.pickle'):
                die_name = rel_die_path.replace('.pickle', '')
                retval[die_name] = os.path.join(die_root, rel_die_path) 
    return retval

def list_dies(project_path):
    '''
    given an (ATE) project_path, extract a list of all dies
    '''
    return list(dict_dies(project_path))

def list_products(project_path):
    '''
    given an (ATE) project_path, extract a list of all products
    '''
    retval = []
    if is_ATE_project(project_path):
        # find path to products from project_structure
        products_path = ''
        for branch in project_structure:
            if 'PRODUCTS' in branch.upper():
                products_path = os.path.normpath(os.path.join(project_path, branch))
        # find devices
        if products_path != '':
            for product in os.listdir(products_path):
                if os.path.isdir(os.path.join(products_path, product)):
                    retval.append(product)
    return retval, products_path

def dict_tests(project_path):
    retval = {}
    if is_ATE_project(project_path):
        test_root = dict_project_paths(project_path)['test_product_root']
        for candidate in os.listdir(test_root):
            if candidate.endswith('FT'):
                retval[candidate.replace('.py', '')] = os.path.join(test_root, candidate)
        test_root = dict_project_paths(project_path)['test_die_root']
        for candidate in os.listdir(test_root):
            if candidate.endswith('PR'):
                retval[candidate.replace('.py', '')] = os.path.join(test_root, candidate)
    return retval

def list_tests(project_path):
    '''
    given an (ATE) project_path, extract a list of all tests (read: Final test tests *AND* probe tests)
    '''
    retval = []
    for candidate in dict_tests(project_path):
        if candidate.endswith('PR') or candidate.endswith('FT'):
            retval.append(candidate)
    return retval

def list_product_tests(project_path):
    '''
    given an (ATE) project_path, extract a list of all product tests (read: Final test tests)
    '''
    retval = []
    for candidate in dict_tests(project_path):
        if candidate.endswith('FT'):
            retval.append(candidate)
    return retval

def list_die_tests(project_path):
    '''
    given an (ATE) project_path, extract a list of all die tests (read: probing tests)
    '''
    retval = []
    for candidate in dict_tests(project_path):
        if candidate.endswith('PR'):
            retval.append(candidate)
    return retval    

def list_product_flows(project_path):
    '''
    given an (ATE) project_path, extract a list of all product flows (read: Final test flows)
    '''
    retval = []
    if is_ATE_project(project_path):
        pass
    
    return retval, 

def list_die_flows(project_path):
    '''
    given an (ATE) project_path, extract a list of all die flows (read: probing flows)
    '''
    retval = []
    if is_ATE_project(project_path):
        pass
    
    return retval

def dict_single_site_loadboards(project_path):
    '''
    This function creates a dictionary of all single site loadboards in project_path
    
    return looks like : {'HWR1' : 'U33301', 'HWR2' : '', 'HWR3' : 'U44547'}
    Note : if not available for a hardware version, then it equals ''
    '''
    retval = {}
    if is_ATE_project(project_path):
        hardware_versions = list_hardwaresetups(project_path)
        for hardware_version in hardware_versions:
            pcbs = dict_pcbs_for_hardware_setup(project_path, hardware_version)
            retval[hardware_version] = pcbs['SingeSiteLoadboard']
    return retval

def dict_probe_cards(project_path):
    '''
    This function creates a dictionary of all probe cards in project_path
    
    return looks like : {'V1' : 'U33301', 'V2' : '', 'V3' : 'U44547'}
    Note : if not available for a hardware version, then it equals ''
    '''
    retval = {}
    if is_ATE_project(project_path):
        hardware_versions = list_hardwaresetups(project_path)
        for hardware_version in hardware_versions:
            pcbs = dict_pcbs_for_hardware_setup(project_path, hardware_version)
            retval[hardware_version] = pcbs['ProbeCard']
    return retval

def dict_Single_site_DIBs(project_path):
    '''
    This function creates a dictionary of all single site DIB's in project_path
    
    return looks like : {'V1' : 'U33301', 'V2' : '', 'V3' : 'U44547'}
    Note : if not available for a hardware version, then it equals ''
    '''
    retval = {}
    if is_ATE_project(project_path):
        hardware_versions = list_hardwaresetups(project_path)
        for hardware_version in hardware_versions:
            pcbs = dict_pcbs_for_hardware_setup(project_path, hardware_version)
            retval[hardware_version] = pcbs['SingleSiteDIB']
    return retval

def dict_multi_site_loadboards(project_path):
    '''
    This function creates a dictionary of all multi site loadboards in project_path
    
    return looks like : {'V1' : 'U33301', 'V2' : '', 'V3' : 'U44547'}
    Note : if not available for a hardware version, then it equals ''
    '''
    retval = {}
    if is_ATE_project(project_path):
        hardware_versions = list_hardwaresetups(project_path)
        for hardware_version in hardware_versions:
            pcbs = dict_pcbs_for_hardware_setup(project_path, hardware_version)
            retval[hardware_version] = pcbs['MultiSiteLoadboard']
    return retval
    
def dict_multi_site_DIBs(project_path):
    '''
    This function creates a dictionary of all multi site DIBs in project_path
    
    return looks like : {'V1' : 'U33301', 'V2' : '', 'V3' : 'U44547'}
    Note : if not available for a hardware version, then it equals ''
    '''
    retval = {}
    if is_ATE_project(project_path):
        hardware_versions = list_hardwaresetups(project_path)
        for hardware_version in hardware_versions:
            pcbs = dict_pcbs_for_hardware_setup(project_path, hardware_version)
            retval[hardware_version] = pcbs['MultiSiteDIB']
    return retval
  
def dict_project_paths(project_path):
    '''
    This function will create a dictionary of all paths in the project.
    '''
    from ATE.org.Templates import project_structure
    retval = {}
    if is_ATE_project(project_path):
        for branch in project_structure:
            path = os.path.normpath(os.path.join(project_path, branch))
            retval[project_structure[branch][0]] = path
    return retval

def list_MiniSCTs():
    retval = ["Tom's MiniSCT", "Rudie's MiniSCT", "Achim's MiniSCT", "Siegfried's MiniSCT"]
    return retval


def unpickle(path):
    '''
    given a 'path' to a pickle file (the extension *MUST* be .pickle),
    return the object inside.
    '''
    retval = None
    if os.path.basename(path).endswith('.pickle'):
        retval = pickle.load(open(path, "rb" ))
    return retval
     
def print_lists(workspace_path, project_path=None):
    print()
    print("dict_projects(workspace_path) = %s" % dict_projects(workspace_path))
    print("list_projects(workspace_path) = %s" % list_projects(workspace_path))
    print("dict_ATE_projects(workspace_path) = %s" % dict_ATE_projects(workspace_path))
    print("list_ATE_projects(workspace_path) = %s" % list_ATE_projects(workspace_path))
    print()
    if project_path != None:
        print("dict_hardwaresetups(project_path) = %s" % dict_hardwaresetups(project_path))
        print("list_hardwaresetups(project_path) = %s" % list_hardwaresetups(project_path))
        print("dict_masksets(project_path) = %s" % dict_masksets(project_path))
        print("list_masksets(project_path) = %s" % list_masksets(project_path))
        print("dict_dies(project_path) = %s" % dict_dies(project_path))
        print("list_dies(project_path) = %s" % list_dies(project_path))
        print("dict_packages(project_path) = %s" % dict_packages(project_path))
        print("list_packages(project_path) = %s" % list_packages(project_path))
        print("dict_devices(project_path) = %s" % dict_devices(project_path))
        print("list_devices(project_path) = %s" % list_devices(project_path))

if __name__ == '__main__':
    workspace_path = r'C:\Users\hoeren\Desktop\TDK\__spyder_workspace__'
    project_path = os.path.join(workspace_path, "CTCA")
    db = lc(project_path)
    print(db.list_hardwaresetups())
