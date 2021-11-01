'''This code determines whether a given float profile occurred during the day or 
night by incorporating position and date information into an astronomical model.
Please note that in order to use the code below, your data must have the same
variable names for latitude, longitude, and date, and the date must be in
Julian day. This code was written by PhD student Rosalind Echols by adapting
demo code from the Skyfield toolbox documation (https://rhodesmill.org/skyfield/).
'''


from skyfield import api
from skyfield import almanac
import numpy as np
import pandas as pd
import xarray as xr


def is_it_night(data,subset,ts,e):
    #determines whether it is nighttime at a particular location and time
    
    #format latitude and longitude
    night_time=[]
    day_time=[]
    
    for n in range(0,len(data['LATITUDE'][subset])):
        if n%1000==0:
            print('File #', n)
    #format latitude and longitude
        if data['LATITUDE'][subset][n]<0:
            lat = '%1.2f S' %data['LATITUDE'][subset][n]
        else:
            lat = '%1.2f N' %data['LATITUDE'][subset][n]
            
        if data['LONGITUDE'][subset][n]<0:
            lon = '%1.2f W' %data['LONGITUDE'][subset][n]
        else:
            lon = '%1.2f E' %data['LONGITUDE'][subset][n]
        
        location = api.Topos(lat,lon)
        
        #format time
        year = pd.to_datetime(data['JULD'].values[subset])[n].year
        month = pd.to_datetime(data['JULD'].values[subset])[n].month
        day = pd.to_datetime(data['JULD'].values[subset])[n].day
        hour = pd.to_datetime(data['JULD'].values[subset])[n].hour
        minute = pd.to_datetime(data['JULD'].values[subset])[n].minute
        
        #define window for searching for either a sunset or sunrise
        t0,t1=ts.utc(year,month,day,[hour-12,hour+12])
        #define UTC time of profile
        t2=ts.utc(year,month,day,hour,minute)
        
        #t=array of times; y = 0 for sun set, 1 for sun rise: look for a sunset
        #or sunrise within the window provided
        t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(e, location))
        #print(t.utc_iso())
       # print(y)
    
        count_polar_night=0
        count_polar_day=0
        #first figure out if sunrise/sunset is irrelevant (i.e. poles at certain
        #times of year, then determine day/night)
        if len(t)<=1:
            f=almanac.sunrise_sunset(e, location)
            t, y = almanac.find_discrete(t0, t1, f)
            if f(t2)==True:
                day_time.append(n)
                count_polar_day+=1
            else:
                night_time.append(n)
                count_polar_night+=1
        
        #if sunrise/sunset exists, figure out whether the profile occurred
        #before or sunset (sunrise). This depends on whether the t array is
        #ordered [0,1] or [1,0] and whether t2 (the actual profile time) is
        #before or after a 0 or 1. 
        else:
            if t.utc_iso()[0]<t2.utc_iso()<t.utc_iso()[1] and y[0]==1:
                day_time.append(n)
            elif t.utc_iso()[0]<t2.utc_iso()<t.utc_iso()[1] and y[0]==0:
                night_time.append(n)
            elif t2.utc_iso()>t.utc_iso()[1] and y[0]==0:
                day_time.append(n)
            elif t2.utc_iso()>t.utc_iso()[1] and y[0]==1:
                night_time.append(n)
            elif t2.utc_iso()<t.utc_iso()[0] and y[0]==1:
                night_time.append(n)
            else:
                day_time.append(n)
                
     #can ask the program to provide how many profiles occurred during polar
     #day or night
   # print(count_polar_day,count_polar_night)
   #returns lists of indices corresponding to night time and day time for the 
   #original array
    return night_time,day_time