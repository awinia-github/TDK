# -*- coding: utf-8 -*-
'''
Created on Aug 5, 2019

@author: hoeren
'''

from SCT.elements.physical import PEABC 


class elevate(PEABC):
    '''
    ElevATE = an SPI-like interface with 6 chip selects.

    Chip Select |
      aka:STB   | Device
    ------------+--------------------- 
         0      | SaturnA (CH0 & CH1)
         1      | SaturnB (CH2 & CH3) 
         2      | SaturnC (CH4 & CH5) 
         3      | SaturnD (CH6 & CH7) 
         4      | Jupiter 
         5      | ARTIX (Relay Driver)  
    
    Data Sheet : https://www.analog.com/media/en/technical-documentation/data-sheets/AD5372_5373.pdf
    
    SCT platform hold 1 such interface
    
    As it is a 'gateway' to talk to any of 6 devices, this is a physical element, whereas
    the devices themselves are 'logical'. This interface also has *NO* register_map.
    
    This class provides the interface for instruments to communicate with the DAC's
    '''
    register_map = {} # keep it here

    devices = {0:None, 1:None, 2:None, 3:None, 4:None, 5:None}
    device_pointers = {0:None, 1:None, 2:None, 3:None, 4:None, 5:None}

    def read(self, CS, n):
        '''
        This method will read n bytes from device on ChipSelect CS.
        
        Note: we keep track of the current positions in self.file_poiters
        '''
        
        
    def write(self, CS, buff):
        '''
        This method will write buff to the device on ChipSelect CS.
        
        Note: we keep track of the current positions in self.file_pointers
        '''

    def tell(self, CS):
        '''
        This method will return the file object's current position for the device on ChipSelect CS.
        '''
        return(self.file_pointers[CS])

    def stat(self, CS):
        '''
        This method will return the size in bytes of the device on ChipSelect CS.
        '''
        return self.devices[CS].stat()

    def seek(self, CS, offset, from_what=0):
        '''
        This method will set the file object's current position for the device on ChipSelect CS.
        
        from_what = 0 --> beginning of the file
                    1 --> from the current file position
                    2 --> from the end of the file (offset should thus be *NEGATIVE*)
                    
        Note : if offset = -1 and from_what = 0, the object's current position will be at the end!
        '''
        if from_what == 0: # from beginning of the file
            self.file_pointers[CS] = offset
        elif from_what == 1: # from the current file position
            self.file_pointers[CS] += offset
        elif from_what == 2: # from the end of the file
            size = self.stat(CS)
            if offset > 0: # offset needs to be negative!!!
                raise Exception("seek offset needs to be negative!!!")
                #TODO: think about this ... can't we support posetive values ?!?
            self.file_pointers[CS] = size + offset
        else:
            raise Exception("WTF!")

    def register(self, CS, device):
        '''
        This method will register a logical device to this physical interface
        '''
        #TODO: some checking ...
        self.devices[CS] = device
        
    def __str__(self):
        '''
        needs other implementation ...
        '''

if __name__ == '__main__':
    ElevATE = elevate()
    ElevATE.read(5,10) # read 5 bytes from the current position of the device on ChipSelect=5 (=ATRIX)
    ElevATE.seek(4, 0) # set the current position of the device on ChipSelect=4 (=Jupiter) to 0
    ElevATE.write(4, b'\x05') # write the buffer to the device on ChipSelect=4 (=Jupiter)