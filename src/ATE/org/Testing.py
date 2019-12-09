'''
Created on 24 Oct 2016

@author: tho
'''
import os,copy
import inspect, imp
import re
import logging
import random

Pass = 1
Fail = 0
Undetermined = -1
Unknown = -1


#TODO: import ABC ... make it a real Abstract Base Class !

class testABC(object):
    '''
    This class is the prototype class for all tests.
    '''
    start_state = None
    end_state = None
    input_parameters = {}
    output_parameters = {}
    extra_output_parameters = {}
    patterns = []
    tester_states = []
    test_dependencies = [] 
    tester = None
    ran_before = False
    is_self_reentrant = False
    is_post_reentrant = False
    is_pre_reentrant = False
    is_reentrant = 0
    is_stand_alone_capable = True

    def __init__(self):
        self.name = str(self.__class__).split('main__.')[1].split("'")[0]
        tmp = str(inspect.getmodule(self)).split("from '")[1].replace("'", '').replace('>', '').split('/')
        self.test_dir = os.sep.join(tmp[0:-1])
        self.file_name = tmp[-1]
        self.file_name_and_path = os.sep.join(tmp)
        self.project_path = os.sep.join(tmp[0:-3])
        self.project_name = tmp[-3]
        
        logging.debug("Initializing test '%s' in module '%s'" % (self.name, self.file_name_and_path))

        #self._add_setup_states_to_start_state()
        #self._add_teardown_states_to_end_state()
        self._extract_patterns()
        self._extract_tester_states()
        
        
        
        
        self._extract_tester()
        self.sanity_check()
        
    def __call__(self, start_state, end_state, input_parameters, output_parameters, extra_output_parameters, data_manager):
        '''
        This method is how the test will be called from a higher level
        '''
        self.setup(start_state)
        retval = self.do(input_parameters, output_parameters, extra_output_parameters, data_manager)
        #TODO: implement functional test (based on the return value of do not being None
        self.teardown(end_state)
    
    def __del__(self):
        pass

    def _extract_patterns(self):
        '''
        This method will extract the patterns it finds in the test class methods 'pre_do', 'do' and 'post_do' as well as in all *functions* in the definitions module and adds them to self.patterns
        format : {'pattern_file' : [(start_label, end_label), ...]}
        '''
        patterns = {} # {'pattern_name' : ['label1', 'label2', ...]}
        #TODO: Implement pattern extraction from setup
        #TODO: Implement pattern extraction from do
        #TODO: Implement pattern extraction from teardown
        #TODO: Implement pattern extraction from functions in module definitions (definitions.py in the tests directory)
        self.patterns += patterns
        self.patterns = sorted(set(self.patterns)) # no duplications, sorted alphabetically
        
    def _extract_tester_states(self): 
        '''
        This method will extract the used tester-states it finds in the test class methods 'setup', 'do' and 'teardown' as well as all *functions* in the definitions module and adds them to self.tester_states
        '''
        tester_states = []
        #TODO: Implement tester-state extraction from setup
        #TODO: Implement tester-state extraction from do
        #TODO: Implement tester-state extraction from teardown
        #TODO: Implement tester-state extraction from functions in module definitions (definitions.py in the tests directory)
        self.tester_states += tester_states
        self.tester_states = sorted(set(self.tester_states)) # no duplications, sorted alphabetically

    def _extract_test_dependencies(self):
        '''
        This method will analyze the do method, and extract all the test dependencies (by looking what is accessed in the DataManager (dm) and add them to self.test_dependencies
        '''
        test_dependencies = []
        #TODO: Implement test dependency extraction from do
        self.test_dependencies += test_dependencies
        self.test_dependencies = sorted(set(self.test_dependencies)) # no duplications, sorted alphabetically

    def _extract_tester(self):
        '''
        This method will extract the used tester (firmware) self.tester accordingly.
        '''
        fp, pathname, description = imp.find_module(self.name, [self.test_dir])
        module = imp.load_module(self.name, fp, pathname, description)
        for member in inspect.getmembers(module, inspect.isclass):
            if 'ATE.Tester.' in str(member[1]):
                self.tester = (str(member[1]).split('<class')[1].strip().replace('>', '').replace("'", ''), member[0])
        
    def _get_imports(self):
        '''
        This method will return a list of all imports of this (test) module.
        Each import is a tuple formatted as follows (from, what, as) 
            'from bla.bla.bla import foo as bar" --> ('bla.bla.bla', 'foo', 'bar')
            'import os' --> ('', os, '')
        '''
        fp, pathname, description = imp.find_module(self.name, [self.test_dir])
        module = imp.load_module(self.name, fp, pathname, description)
        for member in inspect.getmembers(module):
            print member
    
    
    def _get_method_source(self, method):
        '''
        This method will return the source code of the named method of the test class
        '''
        fp, pathname, description = imp.find_module(self.name, [self.test_dir])
        module = imp.load_module(self.name, fp, pathname, description)
        class_of_interest = None
        retval = ''
        for member in inspect.getmembers(module, inspect.isclass):
            if member[0] == self.name:
                class_of_interest = member[1]
        print method
        print class_of_interest
        if class_of_interest is not None:
            method_of_interest = None
            for member in inspect.getmembers(class_of_interest, inspect.ismethod):
                print member
                if member[0] == method:
                    method_of_interest = member[1]
            print method_of_interest
            retval = inspect.getsource(method_of_interest)        
        return retval                    
    
    def _get_if_elif_structure(self, method):
        '''
        This method will return the if/elif structure from the named method in the form of a dictionary.
        It will choke on a else statement! 
        '''
        if method == 'pre_do' or method == 'post_do':
            code_lines = self._get_method_source(method).split('\n')
            def_regex = "\s*(?:def)\s+(?P<function_name>\w+)\s*\(\s*self\s*,\s*(?P<switch>\w+)\):"
            def_pattern = re.compile(def_regex)
            if_regex = '''\s*if\s+(?P<switch>[^ =]+)\s*==\s*(?P<quoting>['"])(?P<state>\w+)(?P=quoting):'''
            if_pattern = re.compile(if_regex)
            elif_regex = '''\s*elif\s+(?P<switch>[^ =]+)\s*==\s*(?P<quoting>['"])(?P<state>\w+)(?P=quoting)\s*:'''
            elif_pattern = re.compile(if_regex)
            go_from_regex = "\s*go_from_(?P<from_state>\w+)_to_(?P<to_state>\w+)_state()"
            go_from_pattern = re.compile(go_from_regex)
            split_pattern = "\s*(?:el)+?if\s+(?P<switch>%s.upper())\s+(?:==)"
            base_indent = len(code_lines[0]) - len(code_lines[0].lstrip())
            retval = {0:None}
            chunk = 0
            for code_line in code_lines:
                if code_line.strip() == '': continue
                indent = (len(code_line) - len(code_line.lstrip()) - base_indent)/base_indent
                if chunk == 0: # in function definition or pre-switch config
                    if indent == 0: # in function definition
                        def_match = def_pattern.match(code_line)
                        if not def_match:
                            raise Exception("Couldn't match '%s'" % code_line)
                        else:
                            switch = def_match.group('switch')
                            if method != def_match.group('function_name'):
                                raise Exception("Unexpected method naming ('%s'<->'%s')" % (method, def_match.group('function_name')))
                            retval[0] = (method, switch) # is always chunk 0 !
                    elif indent == 1:
                        if code_line.stip().startswith('if'):
                            pass
                        else:
                            pass
                    else:
                        pass
                else: # in switch definition
                    if indent == 0: # can only be comment !!!
                        pass
                    elif indent == 1: # can only be if/elif statement
                        if code_line.strip().startswith('else'):
                            raise Exception("'%s' can not contain a general else statement !" % method)
                        if code_line.strip().startswith('if') or code_line.strip().startswith('elif'):
                            chunk += 1
                            retval[chunk]=[]
                            if_match = if_pattern.match(code_line)
                            if not if_match:
                                raise Exception("Couldn't match '%s'" % code_line)
                            else:
                                
                                pass
                        else:
                            retval[chunk].append(code_line)
                        
                    elif indent == 2: # switch block code
                        pass
                    else: # switch block code
                        pass
                    
                    
                    print "%d : %s" % (indent, code_line)
        else:
            raise Exception("'_get_if_elif_structure' only applies to 'pre_do' and 'post_do'")    


            
        
    def _set_method_source(self, method, source):
        '''
        
        '''
        pass    

        
    def _add_pre_do_states_to_start_state(self):
        '''
        self.start_state is a string prior to class instantization.
        The __init__ method will call this function to transform the start state in a 2 element tuple,
        the first element being the start state of the do function (=initial assignment to start_state)
        and the second element is a list of all the from_states defined in setup. 
        '''
        if type(self.start_state) == tuple:
            self.start_state = self.start_state[0] 
        setup_states = []
        code_lines = self._get_method_source('setup').split('\n')
        switch = code_lines[0].strip().split(',')[1].strip().replace(',', ')').split(')')[0].strip()
        for code_line in code_lines:
            if 'if' in code_line:
                code_line = code_line.split('if')[1]
                if switch in code_line:
                    code_line = code_line.split(switch)[1].replace(' ','').replace('==', '').replace(':', '')
                    if code_line.startswith("'"):
                        code_line = code_line.replace("'", '')
                    if code_line.startswith('"'):
                        code_line = code_line.replace('"', '')
                    setup_states.append(code_line)
        self.start_state = (self.start_state, setup_states) 
    
    def _add_post_do_states_to_end_state(self):
        '''
        self.end_state is a string prior to class instantization.
        The __init__ method will call this function to transform the start state in a 2 element tuple,
        the first element being the end state of the do function (=initial assignment to end_state)
        and the second element is a list of all the to_states defined in teardown. 
        '''
        if type(self.end_state) == tuple:
            self.end_state = self.end_state[0] 
        setup_states = []
        print 
        
        code_lines = self._get_method_source('teardown').split('\n')
        switch = code_lines[0].strip().split(',')[1].strip().replace(',', ')').split(')')[0].strip()
        for code_line in code_lines:
            if 'if' in code_line:
                code_line = code_line.split('if')[1]
                if switch in code_line:
                    code_line = code_line.split(switch)[1].replace(' ','').replace('==', '').replace(':', '')
                    if code_line.startswith("'"):
                        code_line = code_line.replace("'", '')
                    if code_line.startswith('"'):
                        code_line = code_line.replace('"', '')
                    setup_states.append(code_line)
        self.end_state = (self.end_state, setup_states) 
        
    def sanity_check(self):
        if not self.ran_before:
            # sanity check on the (test) class name and module
            if self.name != self.file_name.split('.py')[0]:
                msg = "The class '%s' doesn't live in a module with the name '%s.py', instead the module name is '%s', please correct this." % (self.name, self.name, self.file_name)
                logging.critical(msg)
                raise Exception()
            
            
            # sanity check on pre_do for the state names
            
            # sanity check on the post_do for the state names
            
            # sanity check on the start_state
#             try:
#                 self.start_state
#             except NameError: # was not defined
#                 self.start_state = 'pre_%s' % self.name
#                 msg = "test '%s' did not define a start_state, it was added as '%s'" % (self.name, self.start_state) 
#                 logging.warn(msg)
#             else: # was defined
#                 if type(self.start_state) == tuple:
#                     if len(self.start_state)!=2:
#                         msg = "The start_state for test '%s' is to be a 2-element tuple, not a %d element tuple" % (self.name, len(self.start_state))
#                         logging.critical(msg)
#                         raise Exception(msg)
#                 else:
#                     msg = "The start_state for test '%s' is to be a tuple not '%s'" % (self.name, type(self.start_state))
#                     logging.critical(msg)
#                     raise Exception(msg)
#             # sanity check on the end_state
#             try:
#                 self.end_state
#             except NameError: # was not defined
#                 self.end_state = self.name
#                 msg = "test '%s' did not define an end_state, it was added as '%s'" % (self.name, self.end_state)
#                 logging.warn(msg)
#             else: # was defined
#                 if type(self.end_state) == tuple:
#                     if len(self.end_state)!=2:
#                         msg = "The end_state for test '%s' is to be a 2-element tuple, not a %d element tuple" % (self.name, len(self.end_state))
#                         logging.critical(msg)
#                         raise Exception(msg)
#                 else:
#                     msg = "The end_state for test '%s' is to be a tuple, not a '%s'" % (self.name, type(self.end_state))
#                     logging.critical(msg)
#                     raise Exception(msg)
            # sanity check on the input_parameters format  : {'parmeter' : {'Min' : 1.4, 'Max' : 12, 'Default' : 5, 'Unit' : 'V'}}
            try:
                self.input_parameters
            except NameError: # was not defined
                self.input_parameters = {}
                msg = "input_parameters was not defined, added as '{}'" % self.start_state 
                logging.warn(msg)
            else: # was defined
                if type(self.input_parameters) == dict:
                    for input_parameter in self.input_parameters:
                        if type(input_parameter)!=str:
                            msg = "input_parameters contains the key '%s' that is not a string!" % input_parameter
                            logging.critical(msg)
                            raise Exception(msg)
                        if type(self.input_parameters[input_parameter]) != dict:
                            msg = "input_parameters contains the key '%s' that doesn't point to a dictionary " % (input_parameter, self.input_parameters[input_parameter])
                            logging.critical(msg)
                            raise Exception(msg)
                        else:
                            if 'Min' not in self.input_parameters[input_parameter]:
                                msg = "No minimum defined for input_parameter '%s' (Key is to be 'Min')" % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            elif type(self.input_parameters[input_parameter]['Min']) not in [int, float]:
                                msg = "The minimum defined for input_parameter '%s' is not of type int or float" % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            if 'Max' not in self.input_parameters[input_parameter]:
                                msg = "No maximum defined for input_parameter '%s' (Key is to be 'Max')" % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            elif type(self.input_parameters[input_parameter]['Max']) not in [int, float]:
                                msg = "The maximum defined for input_parameter '%s' is not of type int or float" % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            if self.input_parameters[input_parameter]['Min'] > self.input_parameters[input_parameter]['Max']:
                                msg = "The minimum defined for input_parameter '%s' is bigger than the defined maximum" % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            if self.input_parameters[input_parameter]['Min'] == self.input_parameters[input_parameter]['Max']:
                                msg = "The defined minimum and maximum for input_parameter '%s' are equal." % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            if 'Default' not in self.input_parameters[input_parameter]:
                                msg = "No default defined for input_parameter '%s' (Key is to be 'Default')" % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            elif type(self.input_parameters[input_parameter]['Default'])!=int and type(self.input_parameters[input_parameter]['Default'])!=float:
                                msg = "The default defined for test '%s' input_parameter '%s' is not of type int or float" % (self.name, input_parameter)
                                logging.critical(msg)
                                raise Exception(msg)
                            if self.input_parameters[input_parameter]['Default'] > self.input_parameters[input_parameter]['Max'] or self.input_parameters[input_parameter]['Default'] < self.input_parameters[input_parameter]['Min']:
                                msg = "The default defined for input_parameter '%s' is not in the domain [Min .. Max]" % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            if self.input_parameters[input_parameter]['Default'] == self.input_parameters[input_parameter]['Max']:
                                logging.warn("The default defined for input_parameter '%s' is equal to the maximum" % input_parameter)
                            if self.input_parameters[input_parameter]['Default'] == self.input_parameters[input_parameter]['Min']:
                                logging.warn("The default defined for input_parameter '%s' is equal to the minimum" % input_parameter)
                            if 'Unit' not in self.input_parameters[input_parameter]:
                                msg = "No unit defined for input_parameter '%s' (Key is to be 'Unit')" % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                            elif type(self.input_parameters[input_parameter]['Unit'])!=str:
                                msg = "The unit defined for input_parameter '%s' should be of type str." % input_parameter
                                logging.critical(msg)
                                raise Exception(msg)
                else:
                    msg = "input_parameters should be a dictionary !"
                    logging.critical(msg)
                    raise Exception(msg)
            # sanity check on the output_parameters format : {'parameter' : {'LSL' : None, 'USL' : 200, 'Nom' : 100, 'Unit' : 'mA'}}
            try:
                self.output_parameters
            except NameError: # was not defined
                self.output_parameters = {}
                msg = "test '%s' output_parameters was not defined, added as '{}'" % self.name 
                logging.warn(msg)
            else: # was defined
                if type(self.output_parameters) == dict:
                    for output_parameter in self.output_parameters:
                        if type(output_parameter)!=str:
                            msg = "output_parameters contains the key '%s' that is not a string!" % output_parameter
                            logging.critical(msg)
                            raise Exception(msg)
                        if type(self.output_parameters[output_parameter]) != dict:
                            msg = "output_parameters contains the key '%s' that doesn't point to a dictionary " % (output_parameter, self.output_parameters[output_parameter])
                            logging.critical(msg)
                            raise Exception(msg)
                        else:
                            if 'LSL' not in self.output_parameters[output_parameter] and 'USL' not in self.output_parameters[output_parameter]:
                                msg = "The test '%s' output_parameter '%s' does not define either spec limits (LSL/USL) at least one is needed" % (self.name, output_parameter)
                                logging.critical(msg)
                                raise Exception(msg)
                            if 'LSL' not in self.output_parameters[output_parameter]:
                                self.output_parameters[output_parameter]['LSL'] = None
                                msg = "No lower spec limit (LSL) defined for test '%s' output_parameter '%s' it is added as a 'None'" % (self.name, output_parameter)
                                logging.info(msg)
                            elif type(self.output_parameters[output_parameter]['LSL']) not in [int, float, type(None)]:
                                msg = "The defined lower spec limit (LSL) for test '%s' output_parameter '%s' is not of type int, float or None" % (self.name, output_parameter)
                                logging.critical(msg)
                                raise Exception(msg)
                            if 'USL' not in self.output_parameters[output_parameter]:
                                self.output_parameters[output_parameter]['USL'] = None
                                msg = "No upper spec limit (USL) defined for test '%s' output_parameter '%s' it is added as a 'None'" % (self.name, output_parameter)
                                logging.info(msg)
                            elif type(self.output_parameters[output_parameter]['USL']) not in [int, float, None]:
                                msg = "The defined upper spec limit (USL) for test '%s' output_parameter '%s' is not of type int, float or None" % (self.name, output_parameter)
                                logging.critical(msg)
                                raise Exception(msg)         
                            if 'Nom' not in self.output_parameters[output_parameter]:
                                self.output_parameters[output_parameter]['Nom'] = None
                                msg = "No nominal defined for test '%s' output_parameter '%s', it is added as 'None'" % (self.name, output_parameter)
                                logging.info(msg)
                            elif type(self.output_parameters[output_parameter]['Nom']) not in [int, float, None]:
                                msg = "The nominal defined for test '%s' output_parameter '%s' is not of type int, float or None" % (self.name, output_parameter)
                                logging.critical(msg)
                                raise Exception(msg)
                            if type(self.output_parameters[output_parameter]['LSL'])!=None and type(self.output_parameters[output_parameter]['USL'])!=None:           
                                if self.output_parameters[output_parameter]['LSL'] > self.output_parameters[output_parameter]['USL']:
                                    msg = "The defined lower spec limit (LSL) defined for test '%s' output_parameter '%s' is bigger than the defined upper spec limit (USL)" % (self.name, output_parameter)
                                    logging.critical(msg)
                                    raise Exception(msg)
                                if self.output_parameters[output_parameter]['LSL'] == self.output_parameters[output_parameter]['USL']:
                                    msg = "The defined lower spec limit (LSL) and upper spec limit (USL) for test '%s' output_parameter '%s' are equal.If a functional test (aka go-no-go-test) is intended, use the return statement" % (self.name, output_parameter)
                                    logging.critical(msg)
                                    raise Exception(msg)
                                if self.output_parameters[output_parameter]['Nom'] > self.output_parameters[output_parameter]['USL'] or self.output_parameters[output_parameter]['Nom'] < self.output_parameters[output_parameter]['LSL']:
                                    print self.output_parameters[output_parameter]['Nom']
                                    print self.output_parameters[output_parameter]['USL']
                                    print self.output_parameters[output_parameter]['LSL']
                                    msg = "The defined nominal for test '%s' output_parameter '%s' is not in the domain [LSL .. USL]" % (self.name, output_parameter)
                                    logging.critical(msg)
                                    raise Exception(msg)
                                if self.output_parameters[output_parameter]['Nom'] == self.output_parameters[output_parameter]['USL']:
                                    logging.warn("The defined nominal for test '%s' output_parameter '%s' is equal to the USL !!!" % (self.name, output_parameter))
                                if self.output_parameters[output_parameter]['Nom'] == self.output_parameters[output_parameter]['LSL']:
                                    logging.warn("The defined nominal for test '%s' output_parameter '%s' is equal to the LSL !!!" % (self.name, output_parameter))
                            if 'Unit' not in self.output_parameters[output_parameter]:
                                msg = "No unit defined for test '%s' output_parameter '%s' (Key is to be 'Unit')" % (self.name, output_parameter)
                                logging.critical(msg)
                                raise Exception(msg)
                            elif type(self.output_parameters[output_parameter]['Unit']) != str:
                                msg = "The unit defined for test '%s' output_parameter '%s' should be of type str" % (self.name, output_parameter)
                                logging.critical(msg)
                                raise Exception(msg)
                else:
                    msg = "output_parameters should be a dictionary !"
                    logging.critical(msg)
                    raise Exception(msg)
            # sanity check on the extra_output_parameters
            try:
                self.extra_output_parameters
            except NameError: # was not defined
                self.extra_output_parameters = {}
                msg = "extra_output_parameters was not defined, added as '{}'" % self.start_state 
                logging.warn(msg)
            else: # was defined
                pass
            # sanity check on the patterns
            for pattern in self.patterns:
                pattern_file = pattern + '.tp'
                pattern_path = os.path.join(self.project_path, 'patterns')
                pattern_path_to_file = os.path.join(pattern_path, pattern_file)
                if not os.path.isfile(pattern_path_to_file):
                    msg = "pattern file '%s' does not exist in location '%s'" % (pattern_file, pattern_path)
                    logging.critical(msg)
                    raise Exception(msg)
                else:
                    found_labels = get_labels_from_pattern(pattern_path_to_file)
                    for start_label, stop_label in self.patterns[pattern]:
                        # check if labels are present in the file
                        if start_label not in found_labels or stop_label not in found_labels:
                            if start_label not in found_labels and stop_label not in found_labels:
                                msg = "start label '%s' and stop label '%s' not found in '%s'" % (start_label, stop_label, pattern_file)
                                logging.critical(msg)
                                raise Exception(msg)
                            elif start_label not in found_labels:
                                msg = "start label '%s' not found in '%s'" (start_label, pattern_file) 
                                logging.critical(msg)
                                raise Exception(msg)
                            else:
                                msg = "stop label '%s' not found in '%s'" (stop_label, pattern_file)
                                logging.critical(msg)
                                raise Exception(msg)
                        # check if start label comes before stop label in the pattern file
                        if found_labels[start_label] > found_labels[stop_label]:
                            msg = "start label '%s' comes after stop label '%s' in pattern file" % (start_label, stop_label, pattern_file)
                            logging.critical(msg)
                            raise Exception(msg)
            
            # sanity check on the tester_states (reentrant / stand_alone_capable)
            if self.start_state[0] == self.end_state[0]:
                self.is_self_reentrant = True
            if self.start_state[0] in self.end_state[1]:
                self.is_post_reentrant = True
            if self.end_state[0] in self.start_state[0]:
                self.is_pre_reentrant = True
            if self.start_state[0] in self.start_state[1]:
                msg = "the do method of test '%s' starts with the '%s' state, yet '%s' is also defined in pre_do method ... please remove it from the pre_do method" % (self.name, self.start_state[0], self.start_state[0])
                logging.critical(msg)
                raise Exception(msg)
            if self.end_state[0] in self.end_state[1]:
                msg = "the do method of test '%s' ends with the '%s' state, yet '%s' is also defined in the post_do method ... please remove it from the post_do method" % (self.name, self.end_state[0], self.end_state[0])
                logging.critical(msg)
                raise Exception(msg)
            self.is_reentrant = len(set(self.start_state[1])&set(self.end_state[1]))+int(self.is_pre_reentrant)+int(self.is_post_reentrant)+int(self.is_self_reentrant)
            if self.is_reentrant == 0:
                msg = "the test '%s' is not reentrant" % self.name
                logging.critical(msg)
                raise Exception(msg)
            else:
                msg = "the test '%s' is %d times reentrant" % (self.name, self.is_reentrant)
                logging.info(msg)
            if not self.is_stand_alone_capable:
                msg = "test '%s' is not stand alone capable, add a the 'off' state switch to the pre_do routine or make the test run from 'off' state" % self.name
                logging.critical(msg)
                raise Exception(msg)
            else:
                msg = "test '%s' is stand alone capable" % self.name
                logging.info(msg)
            
            # sanity check on the test_dependency 
            #TODO: implement the test_dependency
            
            # sanity check on the tester
            if self.tester is None:
                msg = "Test '%s' does not seem to be written for a tester ..." % self.name
                logging.critical(msg)
                raise Exception(msg)
            if type(self.tester)==tuple:
                if len(self.tester)==2:
                    msg = "Test '%s' uses tester '%s' referenced as '%s'" % (self.name, self.tester[0], self.tester[1])
                    logging.debug(msg)
                else:
                    msg = "I don't understand what tester test '%s' is written for" % self.name
                    logging.critical(msg)
                    raise Exception(msg)
            else:
                msg = "I don't understand what tester test '%s' is written for" % self.name 
                logging.critical(msg)
                raise Exception(msg)
    
            # check if the test's doc string is implemented
            if self.__doc__ == '':
                msg = "Please implement a good doc string for test '%s'" % self.name
                logging.warn(msg)

    def switch_extraction(self, method):
        print type(method)
        exit()
        if type(method) == str:
            if method.upper() == 'PRE':
                
                
                pass
            elif method.upper() == 'POST':
                pass
            else:
                msg = "method should be 'pre' for pre-do or 'post' for post-do, not '%s'" % method
                logging.critical(msg)
                raise Exception(msg)
        else:
            msg = "method should be the string 'pre' or 'post'"
            logging.critical(msg)
            raise Exception(msg)



    def can_refactor(self):
        '''
        This method will return True/False depending if a refactoring can be made from the pre_do/post_do definitions (regardless if it will lead to conflicts at refactoring time)
        '''
        pass
    
    def has_refactor_conflict(self):
        '''
        This method will return True/False depending if a re-factoring already has an entry in definitions.py
        '''
        pass
                
    def refactor(self):
        '''
        This method will take the code-blocks in the if-elif-else block of pre_do and post_do, and re-factor them as functions in definitions.py for the benefit of other tests.
        If a state-change already exists (self.has_refactro_conflict() will return True) the code block will be appended as comment to the previously defined code-block.
        Each re-factored code block has a comment stating from what test(and place) if was re-factored.
        '''
        pass
        
    def pre_do(self, from_state):
        pass
    
    def do(self, ip, op, ep, dm):
        pass
    
    def post_do(self, to_state):
        pass
    
    def run(self, from_state, to_state, ip, op, eop=None, dm=None):
        logging.debug("Running test '%s' from start_state '%s' to end_state '%s' with parameters '%s'" % (self.name, from_state, to_state, ip))
        if from_state != self.start_state[0]:
            if from_state in self.start_state[1]:
                logging.debug("   Executing setup(%s)" % from_state)
                self.pre_do(from_state)
            else:
                msg = "Test '%s' doesn't support running from '%s' state" % (self.name, from_state)
                logging.critical(msg)
                raise Exception(msg)
        else:
            logging.debug("   Skipping pre_do")
        logging.debug("   Executing do(%s, %s, %s, %s)" % (ip, op, eop, dm))
        retval = self.do(ip, op, eop, dm)
        logging.debug("   do returned '%s'" % retval)
        if to_state != self.end_state[0]:
            if to_state in self.end_state[1]:
                logging.debug("   Executing teardown(%s)" % to_state)
                self.post_do(to_state)
            else:
                msg = "Test '%s' doesn't support running to '%s' state" % (self.name, to_state)
                logging.critical(msg)
                raise Exception(msg)
        else:
            logging.debug("   Skipping post_do")    
        bin_code = int(random.uniform(0, 100)) #TODO: pass op & eop to the data manager and get a bincode back.
        logging.debug("   data manager returned (soft) bincode '%s'" % bin_code)
        if not self.ran_before:
            self.ran_fefore = True
               
def isEmptyFunction(func):
    '''
    This function will determine if the passed func (or method) is empty or not.
    A doc-string may be present but doesn't influence this function, nor does multiple pass statements.
    '''
    def empty_func():
        pass

    def empty_func_with_doc():
        """Empty function with docstring."""
        pass

    return func.__code__.co_code == empty_func.__code__.co_code or func.__code__.co_code == empty_func_with_doc.__code__.co_code
                
                
def project_state_changes():
    '''
    This method will return a list of form [(start_state, end_state), ...] from the definition functions in 'definitions.py'
    '''
    pass                        
                
def new_ate_project(ProjectName, Workspace):
    '''
    This function will create 'ProjectName' in directory 'Workspace' and populate it with the necessary files.
    '''
    # doc dir
    # patterns dir
    # programs dir
    # tests dir
    # programs/Configurations.py file
    # programs/specs.xlsx file
    # tests/POR.py file
    # tests/IDD.py file
    # tests/ctest.py file
    # tests/definitions.py file (empty)
    pass


def get_labels_from_pattern(pattern_path_to_file):
    '''
    This function will return a dictionary of labels pointing to the line number in the pattern file
    something like {'label1' : 15, 'label2' : 1034}
    '''
    retval = {}
    #TODO: Implement 'get_labels_from_pattern'
    return retval
    
if __name__ == '__main__':
    pass
    #TODO: Implement the unit tests here ...    
    