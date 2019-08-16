'''
Created on Jun 14, 2014

@author: $Author: tho $

This Library implements Date and Time manipulations in a convenient way.

License : GPL    
'''

import os, time, datetime
from PyQt5.QtCore import QDate

def is_date(stamp):
    '''
    This function will return True or False, depending if the supplied stamp
    can be interpreted as a date string of format DDMMYYYY
    '''
    if type(stamp) == str:
        if len(stamp) == 8:
            if stamp.isdigit():
                DD = int(stamp[:2])
                MM = int(stamp[2:4])
                YYYY = int(stamp[4:])
                if DD > 31 : return False
                if MM > 12 : return False
                return True
            else:
                return False
        else:
            return False
    else:
        return False
    

def is_datecode(stamp):
    '''
    This function will return True or False, depending if the supplied stamp 
    can be interpreted as a date-code string of the format YYWWD
    '''
    if type(stamp) == str:
        if len(stamp) == 5:
            year = stamp[0:2]
            if not year.isdigit():
                return False
            week = stamp[2:4]
            if week.isdigit():
                week = int(week)
                if (week < 1) or (week > 53):
                    return False
            else:
                return False
            day = stamp[4]
            if day.isdigit():
                day = int(day)
                if (day < 1) or (day >7):
                    return False
                else:
                    return True
            else:
                return False
        else:
            return False
    else:
        return False
    
def iso_year_start(iso_year):
    "The gregorian calendar date of the first day of the given ISO year"
    fourth_jan = datetime.date(iso_year, 1, 4)
    delta = datetime.timedelta(fourth_jan.isoweekday()-1)
    return fourth_jan - delta 

def iso_to_gregorian(iso_year, iso_week, iso_day):
    "Gregorian calendar date for the given ISO year, week and day"
    year_start = iso_year_start(iso_year)
    return year_start + datetime.timedelta(days=iso_day-1, weeks=iso_week-1)

def url_datetime_string_to_epoch(url_datetime):
    retval = url_datetime
    print(retval)
    retval = retval.split(',')[1].strip()
    retval = retval.replace('GMT', '').strip()
    retval = datetime.datetime.strptime(retval, "%d %b %Y %H:%M:%S")
    return int((retval - datetime.datetime(1970,1,1)).total_seconds())



class DTOerror(RuntimeError):
    '''
    module exception
    '''
    def __init__(self, arg):
        self.args = arg

    def __str__(self):
        return ''.join(self.args)
    
    def __repr__(self):
        return ''.join(self.args)        


class DT(object):
    '''
    Date and Time Object
    '''
    def __init__(self, stamp=None):
        loct = int(time.time())
        self.tz = (time.mktime(time.gmtime(loct)) - loct) / 3600 
        self.dst = time.localtime()[8] 
        self.__call__(stamp)
    
    def __call__(self, stamp=None):
        if stamp == None:
            self.epoch = int(time.time())
        elif isinstance(stamp, int) or isinstance(stamp, float):
            self.epoch = int(stamp)
        elif isinstance(stamp, str):
            if is_datecode(stamp):
                # set epoch to the beginning of the datecode
                # http://stackoverflow.com/questions/5882405/get-date-from-iso-week-number-in-python
                iso_year = int(stamp[:2])
                if iso_year > 70: # epoch = 1 Jan 1970 ;-)
                    iso_year += 1900
                else:
                    iso_year += 2000
                iso_week = int(stamp[2:4])
                iso_day = int(stamp[4])
                temp = iso_to_gregorian(iso_year, iso_week, iso_day)    
                self.epoch = int((datetime.datetime(temp.year,temp.month,temp.day) - datetime.datetime(1970,1,1)).total_seconds())
            elif is_date(stamp):
                DD = int(stamp[:2])
                MM = int(stamp[2:4])
                YYYY = int(stamp[4:])
                self.epoch = int((datetime.datetime(YYYY, MM, DD) - datetime.datetime(1970,1,1)).total_seconds())        
            elif os.path.exists(stamp):
                self.epoch =  os.stat(stamp)[6]
#         elif type(stamp) == time.struct_time: # intende for time.strptime so that it can be converted into UTC
#             self.epoch = int((datetime.datetime(stamp.tm_year, stamp.tm_mon, stamp.tm_mday, stamp.tm_hour, stamp.tm_min, stamp.tm_sec) - datetime.datetime(1970, 1, 1)).total_seconds()) - (self.tz * 3600) + (abs(self.dst) * 3600)
        else:
            raise Exception("Don't now how to handle type(%s)=%s" % (stamp, type(stamp)))
#             print(stamp)
#             print(type(stamp))
#             print(float(stamp))
#             self.epoch = float((datetime.datetime.fromtimestamp(float(stamp)) - datetime.datetime(1970,1,1)).total_seconds())
        self._populate()
        
    def _populate(self):
        t = time.gmtime(self.epoch)
        d = datetime.date(t.tm_year, t.tm_mon, t.tm_mday)
        self.datecode = "%4d%02d%1d" % (d.isocalendar()[0], d.isocalendar()[1], d.isocalendar()[2]) # YYYYWWD
        self.datecode = self.datecode[2:] # YYWWD
        self.min = t.tm_min # minute of the hour [0 .. 59]
        if self.min < 15:
            self.qhour = 1
        elif self.min < 30:
            self.qhour = 2
        elif self.min < 45:
            self.qhour = 3
        else:
            self.qhour = 4
        self.hour = t.tm_hour # hour of the day [0 .. 23]
        self.sec = t.tm_sec # seconds of the min [0..59]
        self.wday = d.isocalendar()[2]
        if self.wday == 1:
            self.wday_name = 'Monday'
        elif self.wday == 2:
            self.wday_name = 'Tuesday'
        elif self.wday == 3:
            self.wday_name = 'Wednesday'
        elif self.wday == 4:
            self.wday_name = 'Thursday'
        elif self.wday == 5:
            self.wday_name = 'Friday'
        elif self.wday == 6:
            self.wday_name = 'Saturday'
        elif self.wday == 7:
            self.wday_name = 'Sunday'
        else: # should never reach this point
            raise DTOerror
        self.mday = t.tm_mday # day of the month [1 .. 31]
        self.yday = t.tm_yday # day of the year [1 .. 365/366] depending on leap year
        self.week = d.isocalendar()[1] # week of the year [1 .. 52/53] aka 'Work Week'
        self.month = t.tm_mon # month of the year [1 .. 12]
        if self.month == 1:   
            self.month_name = 'January'
        elif self.month == 2:
            self.month_name = 'February'
        elif self.month == 3:
            self.month_name = 'March'
        elif self.month == 4:
            self.month_name = 'April'
        elif self.month == 5:
            self.month_name = 'May'
        elif self.month == 6:
            self.month_name = 'June'
        elif self.month == 7:
            self.month_name = 'July'
        elif self.month == 8:
            self.month_name = 'August'
        elif self.month == 9:
            self.month_name = 'September'
        elif self.month == 10:
            self.month_name = 'October'
        elif self.month == 11:
            self.month_name = 'November'
        elif self.month == 12:
            self.month_name = 'December'
        else: # should never reach this point
            raise DTOerror
        if self.month in [1, 2, 3]: self.quarter = 1
        elif self.month in [4, 5, 6]: self.quarter = 2
        elif self.month in [7, 8, 9]: self.quarter = 3
        else: self.quarter = 4
        self.year = t.tm_year # year
        self.datetime = datetime.datetime(self.year, self.month, self.mday, self.hour, self.min, self.sec)
        self.date = datetime.date(self.year, self.month, self.mday)
        self.QDate = QDate(self.year, self.month, self.mday)
        self.time = datetime.time(self.hour, self.min, self.sec)

    def bod(self):
        '''
        Returns the epoch (is thus gmt based) for the Begin Of the Day from the underlaying epoch.
        The epoch of the object remains unchanged.
        '''
        return int((datetime.datetime(self.year, self.month, self.mday) - datetime.datetime(1970,1,1)).total_seconds())
    
    def eod(self):
        '''
        Returns the epoch (is thus gmt based) for the End Of the Day from the underlaying epoch.
        The underlaying epoch of the object remains unchanged.
        '''
        return self.bod() + (24*60*60)

    def bow(self):
        '''
        Returns the epoch (is thus gmt based) for the Begin Of the Week from the underlaying epoch.
        The underlaying epoch of the object remains unchanged.
        '''
        temp = iso_to_gregorian(self.year, self.week, 1)    
        return int((datetime.datetime(temp.year,temp.month,temp.day) - datetime.datetime(1970,1,1)).total_seconds())

    def eow(self):
        '''
        Returns the epoch (is thus gmt based) for the End Of the Week from the underlaying epoch.
        The underlaying epoch of the object remains unchanged.
        '''
        return self.bow() + (7*24*60*60)

    def bom(self):
        '''
        Returns the epoch (is thus gmt based) of the Begin Of the Month from the undelaying epoch.
        The underlying epoch of the object remains unchanged.
        '''
        
    def eom(self):
        '''
        Returns the epoch (is thus gmt based) of the End Of the Month from the undelaying epoch.
        The underlying epoch of the object remains unchanged.
        '''
        
    def boy(self):
        '''
        Returns the epoch (is thus gmt based) of the Begin Of the Year from the underlaying epoch. 
        The underlying epoch of the object remains unchanged.
        '''


    def local(self):
        '''
        Returns the epoch (is thus gmt based) for the LOCAL time.
        The underlaying epoch remains unchanged.
        '''
        return self.epoch - (self.tz * 3600) + (abs(self.dst) * 3600)

    def __sub__(self, other):
        if self.__class__.__name__ == other.__class__.__name__:
            return self.epoch - other.epoch
        return NotImplemented
        
        
    def __lt__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False
        if self.epoch < other.epoch:
            return True
        else:
            return False
    
    def __le__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False
        if self.epoch <= other.epoch:
            return True
        else:
            return False
    
    def __eq__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False
        if self.epoch == other.epoch:
            return True
        else:
            return False
    
    def __ne__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False
        if self.epoch != other.epoch:
            return True
        else:
            return False
    
    def __gt__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False
        if self.epoch > other.epoch:
            return True
        else:
            return False
    
    def __ge__(self, other):
        if self.__class__.__name__ != other.__class__.__name__:
            return False
        if self.epoch >= other.epoch:
            return True
        else:
            return False
    
    def __str__(self):    
        #Monday, January 6 2014 @ 13:22:11 (Q1 2014)
        return "%s, %s %s %s @ %02d:%02d:%02d" % (self.wday_name, self.month_name, self.mday, self.year, self.hour, self.min, self.sec)
        
    def __repr__(self):
        #Monday, January 6 2014 @ 13:22:11 (Q1 2014)
        return "%s, %s %s %s @ %02d:%02d:%02d (Q%s %s)" % (self.wday_name, self.month_name, self.mday, self.year, self.hour, self.min, self.sec, self.quarter, self.datecode)
    
class ChronoMeter(object):
    
    def __init__(self):
        self.reset()
                
    def __repr__(self):
        print(self.__str__())
    
    def __str__(self):
        return "Timed %f sec for %d laps (%f sec per lap)" % (self.time(), self.laps(), self.laptime())
        
    def reset(self):
        self.TotalTime = 0
        self.Laps = 0
    
    def start(self):
        self.TimeStart = time.time()
    
    def stop(self):
        self.TimeStop = time.time()
        self.last_lap_time = self.TimeStop - self.TimeStart
        self.TotalTime += self.last_lap_time
        self.TimeStart = 0
        self.Laps += 1
    
    def laps(self):
        return self.Laps
    
    def time(self):
        return self.TotalTime
    
    def laptime(self):
        if self.Laps == 0:
            return 0.0
        else:
            return self.TotalTime / self.Laps
        
if __name__ == "__main__":
    now = DT()
    print("now (UTC) = %s" % now)
    print("now (local) = %s" % DT(now.local()))
    print("now tz = %s" % now.tz)
    print("now dst = %s" % now.dst)
    
    
    print("begin of week = %s" % DT(now.bow()))
    print("end of week = %s" % DT(now.eow()))
    print("begin of day = %s" % DT(now.bod()))
    print("end of day = %s" % DT(now.eod()))
    print(DT(time.strptime("Monday, September 22 2014 @ 10:26:26", "%A, %B %d %Y @ %H:%M:%S")))
    