#!/usr/bin/env python
# -*- coding: utf-8 -*-

default_history_depth = 20 # retain bin-code info for the last N test runs.
default_test_sites = 1 

class data_manager(object):
    '''
    This is the data manager
    '''
    
    data = {}
    
    data_loggers = {}
    
    def __init__(self, lot_number=None, test_sites=default_test_sites, history_depth=default_history_depth):
        
        
        pass
    
    def __call__(self):
        '''
        This call returns a read-only version of the data present in the data manager.
        '''
        pass
    
    def __del__(self):
        '''
        The destructor of this class will see to it that all data is written to the data_loggers, and that the file handles are cleanly closed.
        '''
        pass
    
    def set_lot(self, lot_number):
        '''
        This method will set the lot-number in the data manager.
        If the given lot_number is different from the current one, open data loggers will be cleanly written and shut down
        then the lot_number is changed, and , and new ones will be opened 
        '''
        pass
    
    def register_data_logger(self, data_logger):
        '''
        With this method one can register data logger(s) to the data manager. 
        '''
        pass
    
    def register_test(self, test_name):
        '''
        By feeding this method a test_name, it will figure out where the test is located, and create the structure for the output_parameters and extra_output_parameters
        '''
        pass

    def clear(self):
        '''
        This method will clear all the 'Values' by setting them to None to prepare for the next test cycle.
        '''
        pass
    
    def write_loggings(self):
        '''
        This method will write the current content of the datamanager to all registered data_loggers
        '''
        pass
    
    def close_data_loggers(self):
        '''
        This method will close all registered data loggers (regardless wether the last data is written to file)
        '''
        pass
    
    def open_data_loggers(self):
        '''
        This method will open all registered data loggers with current self.lot_number for self.test_sites
        '''
        pass
    
    def add_data(self, test_name, test_site, output_parameters, extra_output_parameters):
        '''
        This method will take the output_parameters and extra_output_parameters from test_name and file them in self.data for test_site.
        '''
        pass

if __name__ == '__main__':
    pass