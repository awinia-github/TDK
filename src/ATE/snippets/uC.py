'''
Created on Oct 2, 2019

--> time structure of Micronas ...

@author: hoeren
'''
import struct
from ATE.utils import DT

#                                      Type                 Bytes            Note
SyncCode = b'MN'                     # byte array      2s   2             
PlatinenNr = 33100                   # unsigned short  H    2  
VersionNr = 200                      # unsinged short  H    2                shifted >> 2
ModulCharakter = 0                   # unsinged short  H    2
Datum = 0x26DC                       # unsinged short  H    2                (14.12.19) 'Achim format'
Uhrzeit = 0x173B                     # unsinded short  H    2                (23:59)
Abgleicher = b'TH'                   # byte array      2s   2         
Operationen = 0                      # unsined int     I    4 
SerienNr = 12345                     # unsined short   H    2
CheckerDatum = 0x26DC                # unsinged short  H    2                (14.12.19) 'Achim format'
CheckerUhrzeit = 0x173B              # unsinded short  H    2                (23:59)
KalibrationDatum = 0x26DC            # unsinged short  H    2                (14.12.19) 'Achim format'
KalibrationUhrzeit = 0x173B          # unsinded short  H    2                (23:59)
PlatinenKennung = b'MiniPower-Board' # byte array      21s  21
PMNummer = 0                         # unsinged short  H    2
HerstellerNr = b'180284438'          # byte array      21s  21
Frei = b''                           # byte array      29s  29

fmt = "<2sHHHHH2sIHHHHH21sH21s29s"

def micronas_time_structure_to_epoch(Datum=0, Uhrzeit=0):
    year = (Datum & (0b111111 << 10)) >> 10
    month = (Datum & (0b1111 << 6)) >> 6
    day = (Datum & (0b11111 << 1)) >> 1
    hour = (Uhrzeit & (0b11111111 << 8)) >> 8
    minutes = Uhrzeit & 0b11111111
    dt = DT("%2s%2s%4s" % (day, month+1, year+2000))
    return dt.epoch+(hour*60*60)+(minutes*60)
    
if __name__ == '__main__':
    raw_data = struct.pack(fmt,    
                           SyncCode,           
                           PlatinenNr,
                           VersionNr,
                           ModulCharakter,
                           Datum,
                           Uhrzeit,
                           Abgleicher,
                           Operationen,
                           SerienNr,
                           CheckerDatum,
                           CheckerUhrzeit,
                           KalibrationDatum,
                           KalibrationUhrzeit,
                           PlatinenKennung,
                           PMNummer,
                           HerstellerNr,
                           Frei)
    (SyncCode_,           
    PlatinenNr_,
    VersionNr_,
    ModulCharakter_,
    Datum_,
    Uhrzeit_,
    Abgleicher_,
    Operationen_,
    SerienNr_,
    CheckerDatum_,
    CheckerUhrzeit_,
    KalibrationDatum_,
    KalibrationUhrzeit_,
    PlatinenKennung_,
    PMNummer_,
    HerstellerNr_,
    Frei_) = struct.unpack(fmt, raw_data)
    
    inbetriebnahme = DT(micronas_time_structure_to_epoch(Datum_, Uhrzeit_))
    checker = DT(micronas_time_structure_to_epoch(CheckerDatum_, CheckerUhrzeit_))
    kalibration = DT(micronas_time_structure_to_epoch(KalibrationDatum_, KalibrationUhrzeit_))
    
    print(DT()-kalibration)
    