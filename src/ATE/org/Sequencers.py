'''
Created on 11 Feb 2017

@author: tho
'''
from ATE.Data.DM import data_manager
from ATE.Testing import isEmptyFunction

import logging, logging.handlers
import os
import inspect

default_run_mode = '1'
default_test_number_separation = 50
default_loop_number = 1000

class development_sequencer(object):
    '''
    This is a simple sequencer for testing individual tests interactively.
    '''
    run_modes = {'1'       : "Single mode : starts with 'off' state and end with whatever state using the default input parameters." ,
                 'N'       : "Loop mode : starts and end with 'off' state using the default input parameters N times if N is omitted (empty string) %s is used" % default_loop_number,
                 'TIME[N]' : "Time mode : like the loop mode but times the do method (and appends the runtime to the test class code) if N is omitted %s is used" % default_loop_number,
                 'AUDIT'   : "Audit mode : a GUI is brought up to do corner and/or schmoo investigation (varying the input parameters)"
                 }
    sequence = {}
    
    def __init__(self, main_module, log_level=logging.NOTSET+1):
        main_module_elements = main_module.split(os.sep)
        self.event_log_file = os.sep.join(main_module_elements[0:-2])+os.sep+'log'+os.sep+main_module_elements[-1].split('.py')[0]+'.log'
        self.project = main_module_elements[-3]
        self.project_directory = os.sep.join(main_module_elements[0:-2])

        fh = logging.handlers.RotatingFileHandler(self.event_log_file, maxBytes=1000000, backupCount=10)
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(module)s:%(lineno)d - %(levelname)s - %(message)s'))
        root = logging.getLogger()
        root.setLevel(log_level)
        root.addHandler(fh)

        self.dm = data_manager() 

        self.iteration = 0
        self.run_mode = None

        logging.info("--------------------Sequencer Start--------------------")
    
    def __call__(self):
        pass
    
    def __del__(self):
        logging.info("--------------------Sequencer Stop--------------------")
    
    
    def register_test(self, test_class, test_number=None):
        '''
        With this method one can add a test to the sequencer.
        if the test_number is None, the test will be appended at the end, if not it will be registered under that number
        '''
        import inspect

        #TODO: verify that the test_class is a child from ATE.Testing.test        
        tmp = test_class()
        test_name = tmp.name
        test_module = tmp.file_name_and_path
        project = tmp.project_name
        del(tmp)
        
        if self.project==None: # no project defined yet
            self.project=project
        else:
            if self.project!=project:
                msg = "We can not mix test_classes from two different projects ('%s' & '%s')" % (self.project, project)
                logging.critical(msg)
                raise Exception(msg)

        test_sequence_list = self.sequence.keys()
        if test_number==None: # append the test at the end
            if test_sequence_list == []: # empty list
                test_number = default_test_number_separation
            else:
                test_number = max(test_sequence_list) + default_test_number_separation
        else:
            if test_number in test_sequence_list:
                msg = "Test number '%s' is already been occupied by test_class '%s' " % (test_number, self.sequence[test_number][0])
                logging.critical(msg)
                raise Exception(msg)
        
        self.sequence[test_number] = test_class()
        logging.debug("Registered '%s' under test number '%s' for project '%s'" % (test_name, test_number, self.project))
        
    def register_logger(self, logger):
        pass
        
    def can_run(self, mode="SINGLE"):
        '''
        This method will determine if the current sequencer has enough info to run in the provided mode.
        
        '''
        if type(mode)==str:
            if mode.upper() in run_modes:
                if mode.upper()=='CORNERS':
                    retval = False
                elif mode.upper()=='SCHMOO':
                    retval = False
                elif mode.upper()=='LOOP':
                    retval = False
                elif mode.upper()=='TIME':
                    retval = False
                elif mode.upper()=='SINGLE':
                    retval = True
                else:
                    print "run mode '%s' is defined, but not yet implemented" % mode.upper()
            else:
                retval = False
        else:
            retval = False
        return retval

    def propose_resolution(self, mode=default_run_mode):
        pass
    
    def print_run_modes(self):
        '''
        This method will report the different run modes.
        '''
        print "Run Modes :"
        print "-----------"
        for run_mode in run_modes:
            if run_mode == default_run_mode:
                print "   * %-7s -> %s" % (run_mode, run_modes[run_mode]) 
            else:
                print "     %-7s -> %s" % (run_mode, run_modes[run_mode])
        print 
        
    def print_sequence(self):
        '''
        This method will print the current test sequence
        '''
        pass    
        
    def get_run_mode(self):
        '''
        This method will return the current run mode.
        '''
        return self.run_mode
        
    def cycle(self):
        print "---> Start iteration %d" % self.iteration
        for test in self.sequence:
            self.sequence[test].run(None, None, None, None, None)
        print "<--- Done with iteration %d" % self.iteration
        self.iteration+=1
        
    def run(self, mode=default_run_mode, number=100, test_class=None):
        if type(mode)==str:
            if mode.upper() in run_modes:
                self.run_mode = mode
                if mode.upper()=='CORNERS':
                    pass
                elif mode.upper()=='SCHMOO':
                    pass
                elif mode.upper()=='LOOP':
                    for _ in range(number):
                        self.cycle()
                elif mode.upper()=='TIME':
                    import inspect
                    if test_class==None: # no test_class provided
                        if len(self.sequence)==1: # but only one test_class in the sequencer
                            msg = "No test_class provided but only one test_class in the sequencer, using that one (%s)" % "TODO"
                            logging.warn(msg)

                        else: # and multiple tests in the sequencer
                            msg = "No test_calss provided and multiple test_calss-es in the sequencer. Define which test to time!"
                            logging.critical(msg)
                            raise Exception(msg)
                    else: # test_class provided
                        pass
#                         msg = "No test class provided to time"
#                         logging.critical(msg)
#                         raise Exception(msg)
                    #TODO test if the test_class can be found (for insertion)
                    print "Doing Timing of test class '%s'" % test_class #TODO: implement console progress feedback
                    print inspect.getmodule(test_class)
                    pass
                elif mode.upper()=='SINGLE':
                    self.cycle()
                else:
                    print "run mode '%s' is defined, but not yet implemented" % mode.upper()
            else:
                msg = "Atempted to start the sequencer with run mode '%s' ... unknown mode" % mode
                logging.critical(msg)
                raise Exception(msg)
        else:
            msg = "Atempted to start the sequencer without a run mode name"
            logging.critical(msg)
            raise Exception(msg)
        
    def brol(self):
        return build_state_change_table(self.project_directory)

def build_state_change_table(project_dir):
    retval = {}
    if os.path.isdir(project_dir):
        if os.path.isdir(os.path.join(project_dir, 'tests')):
            test_dir = os.path.join(project_dir, 'tests')
            test_list = os.listdir(test_dir)
            for test in test_list:
                print inspect.getmoduleinfo(os.path.join(test_dir, test))

        
        
        else:
            msg = "'%s' is not a directory"
            logging.critical(msg)
            raise Exception(msg)
    else:
        msg = "'%s' is not a directory, let alone a project directory"
        logging.critical(msg)
        raise Exception(msg)
    

if __name__ == '__main__':
    pass