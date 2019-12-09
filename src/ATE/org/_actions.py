'''
Created on Nov 19, 2019

@author: hoeren
'''
import os, pickle

from ATE.org.validation import is_ATE_project, is_valid_pcb_name
from ATE.org.listings import list_hardware, dict_project_paths

  
    
# def Create_new_maskset(maskset_root, maskset_data):
#     if not os.path.exists(maskset_root):
#         os.makedirs(maskset_root)
#     maskset_file = os.path.join(maskset_root, "%s.pickle" % maskset_data['maskset_name'])
#     pickle.dump(maskset_data, open(maskset_file, 'wb'), protocol=4) # fixing the protocol guarantees compatibility



def new_probecard(project_path, probecard_name):
    '''
    given a project_path and a probecard_name, create the directory (and the structure inside ... templating)
    '''
    if not is_ATE_project(project_path):
        raise Exception("not an ATE project")
    #TODO: add the structure (templating)
    

        




        
        
if __name__ == '__main__':
    from SpyderMockUp.SpyderMockUp import workspace
    trial_project = os.path.join(workspace, 'TrIaL')
    Create_ATE_Project(trial_project)
    
    