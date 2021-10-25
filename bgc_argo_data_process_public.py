'''This is the third in a series of short Python programs that can be used to
recreate the results in Echols, Rocap, and Riser (). It is important to note
that this program relies on a list of float numbers previously compiled in the
program "bgc_argo_float_list_public.py". This code was written by PhD student 
Rosalind Echols.
'''

import numpy as np
import os
import re
import xarray as xr
from scipy import ndimage
from scipy.interpolate import interp1d
import gsw
import matplotlib.pyplot as plt


''' Steps to prepare data for machine learning application described in Echols,
Rocap, and Riser ().

1. Import data files by float number (using file with list of float numbers)
2. Quality control
    a. Check QC flags in file: A, B, or "nan" with additional checks
    b. Remove empty profiles of T, S, and Chl (must have all 3 for some applications)
    c. Remove spurious data (need a clear definition here)
    d. Remove data with insufficient resolution/big gaps/unacceptable max/min pressure
3. Interpolate T, S, and Chl profiles to a 1-meter grid (also DO and Nitrate, if available)
    a. Smooth chlorophyll profiles with median filter 
    b. Store interpolated profiles in new array along with date, lat, lon, QC flag

'''
    
def file_list(chl_file):
    with open(chl_file) as numbers:
        floats=numbers.read()
        float_numbers=floats.split('\n')
    print(len(float_numbers))
    
    files=[]
    for number in float_numbers:
        if len(files)%5==0:
            print('Total files so far: ',len(files))
           
        for data_file in os.listdir(path):
            match = re.search(str(number), data_file)
            if match:
                file_path = path+data_file
                files= np.append(files,file_path)
            else:
                pass

        delete=[i for i,j in enumerate(files) if j[-4:]=='D.nc']    
        files=np.delete(files,delete)
        
        #find duplicate files: SD vs. SR; want to use SD if possible
        good_files,bad_files=find_dups(files)
    
        np.append(files,good_files,axis=0)

    print('Total number of files: ', len(files))
    
    return files

def func(x):

    return x[-14:]

def find_dups(L):
    #function to retain delayed mode files only when delayed mode and regular
    #mode are both available for a particular float and profile number
    new_L=sorted(L,key=func)
    good=[]
    bad=[]
    
    if len(new_L)==1:
        good=new_L
        return good, bad

    for n in range(0,len(new_L)):
        if new_L[n] in good:
            pass
        elif new_L[n][-14:]==new_L[n-1][-14:]:
            pass
        elif n==(len(new_L)-1) and new_L[n] not in good and new_L[n] not in bad:
            good.append(new_L[n])
        elif new_L[n][-14:]==new_L[n+1][-14:]:

            if new_L[n][-16:-14]=='SD':

                good.append(new_L[n])
                bad.append(new_L[n+1])

        else:
            good.append(new_L[n])

    return good,bad

def quality_control(data,variable):
    qc=0
   
    #In theory, we should just be able to check the QC flags in the file for an A or B 
    #classification. However, there are mismatches in the QC flags between indiividual
    #data points and the overall QC tag for the profile in the Synthetic profiles used
    #for this project. Therefore, we implement additional QC checks for all profiles
    #and keep track of the QC problems.
    
    #To retain only A/B profiles, uncomment the next 3 lines
    # if variable in ['CHLA','CHLA_ADJUSTED'] and data['PROFILE_CHLA_QC'].values[0] not in [b'A',b'B']:
        #qc=7
        #return qc,data
        #To retain A, B, and profiles missing QC, but discard C-F profiles, uncomment the following lines
        # try:
        #     if variable in ['CHLA','CHLA_ADJUSTED'] and np.isnan(data['PROFILE_CHLA_QC'].values[0]):
        #         qc=0
        #     else:
        #         qc=7
        #         return qc,data
        # except TypeError:
        #     #print('REALLY BAD')
        #     qc=7
        #     return qc,data
    
    #data without an identifiable lat/lon are not useable for geographic purposes
    if np.isnan(data['LATITUDE'].values[0]) or np.isnan(data['LONGITUDE'].values[0]):
        qc=1
        return qc,data
    #if the pressure conditions for any of the variables are unacceptable
    #stop working with this data (max(depths))
    nnans=[i for i,j in enumerate(data[variable].values[0]) if ~np.isnan(j)]
    if  (np.nanmax(data['PRES'].values[0,nnans])<200 or 
        np.nanmin(data['PRES'].values[0,nnans])>10):
#        print(np.nanmax(data['PRES'].values[0]),np.nanmin(data['PRES'].values[0]))
        qc=2
        return qc,data
    #If any pressure differences are larger than 20, don't use it; also deals with
    #profiles without enough total data points
    surf=next(i for i,j in enumerate(data['PRES'].values[0,nnans]) if j>=200)
    if any(np.diff(data['PRES'].values[0,nnans][0:surf])>20):
        qc=3
        return qc,data
    #if all of the data is nans except 2 or fewer, it's garbage
    
    if sum(~np.isnan(data[variable].values[0]))<=10:
#       Need a minimum of 10 data points; might overlap with the last one
        #this is almost irrelevant, but not quite
        qc=4
        return qc,data
    
    #profiles with large values at depth (not the Black Sea) are problematic
    d200=next(i for i,j in enumerate(data['PRES'].values[0]) if j>200)
    if np.nanmean(data['CHLA'].values[0,d200:])>0.3:
        qc=5
        return qc,data
    
    #if almost all "data" is either negative or nans, remove
    #This does not apply when other checks are in place
    nans=len([i for i,j in enumerate(data[variable].values[0]) if np.isnan(j)])
    negative=len([i for i,j in enumerate(data[variable].values[0]) if j<0])
    if abs((nans+negative)-len(data[variable].values[0]))<=10:
        qc=6
        return qc,data   
    
    return qc, data

def interpolate_data(data,var,depths,mask):
    if len(data[var].values[0,mask])<2:
        interp_data=np.nan*np.ones(len(depths))
        return(interp_data)
    if var=='CHLA':
        #use 5-point median filter; reduces some peak size, but also much more
        #effective at removing erratic data
        temp=ndimage.median_filter(data[var].values[0,mask],size=5)
        p_intp = interp1d(data['DEPTH'].values[mask], temp, axis=0,fill_value='extrapolate')
        chl=p_intp(depths)
        #subtract smallest deepwater value to account for other fluorescence contributions, Carranza et al 2018
        #except in the Black Sea, where deep sea red fluorescence is a known issue
        if 27.5<data['LONGITUDE'].values[0]<42.5 and 41<data['LATITUDE'].values[0]<47:
            pass
        else:
            interp_data = chl-np.nanmin(chl[-10:])
        #remove infinite zero values (artifact of extrapolation)
        if np.isinf(interp_data[0]):
            interp_data[0]=interp_data[1]
        #replace negative near-surface values with nearest non-negative value
        if interp_data[0]<0:
            try:
                pos=next(i for i,j in enumerate(interp_data) if j>0)
                interp_data[0:pos]=interp_data[pos]
                #if all the values are negative, it's garbage and we don't want it
            except StopIteration:
                interp_data=np.nan
    else:
        #non-CHLA data typically do not exhibit the same potential interpolation issues
        p_intp = interp1d(data['DEPTH'].values[mask], data[var].values[0,mask], axis=0,fill_value="extrapolate")            
        interp_data = p_intp(depths)
    
    return interp_data


def export_data(int_data,all_vars,sfpath):
    '''Example of formatting for dictionary to dataset
        d = {'t': {'dims': ('t'), 'data': t},
             'a': {'dims': ('t'), 'data': x},
             'b': {'dims': ('t'), 'data': y}}
        
        d = {'coords': {'t': {'dims': 't', 'data': t,
                      'attrs': {'units':'s'}}},
         'attrs': {'title': 'air temperature'},
         'dims': 't',
         'data_vars': {'a': {'dims': 't', 'data': x, },
                       'b': {'dims': 't', 'data': y}}}
    '''
    
    dict_data={}
    for v in all_vars:
        dict_data[v]={'dims':('time','z'),'data':int_data[v]}
    
    for v in ['LATITUDE','LONGITUDE','JULD']:
        dict_data[v]={'dims':('time'),'data':int_data[v]}
    
    for v in ['PRES','DEPTH']:
        dict_data[v]={'dims':('time','z'),'data':int_data[v]}
    
    ds=xr.Dataset.from_dict(dict_data)
    print(ds.keys())
    
    ds.to_netcdf(sfpath)
    
    return ds


###MAIN FILE###
#filepath for float data:
path='/Volumes/RE_DATA/SyntheticBioArgo/'

sfpath='/Users/rosalindechols/Documents/Generals/Self_Shading_Research/Data/Argo_Merged/CHL_Data/'

#make a list of all of the files with chlorophyll data in them. If you do
#this step once and want to re-run the code later, set make_file_list to 
#False so you don't have to repeat this step
make_file_list=True

if make_file_list==True:
    #filename and location from bgc_argo_float_list_public.py
    chl_file='/Users/rosalindechols/Documents/Generals/Self_Shading_Research/Data/argo_CHL_float_list_synthetic.txt'
    print('Make file list')
    #This routine checks to make sure that profiles have a chlorophyll variable
    #in them and that realtime and delayed mode profiles are not duplicated in the analysis
    all_files=file_list(chl_file)
    
    print('Save files')   
    save_file='/Users/rosalindechols/Documents/Generals/Self_Shading_Research/argo_CHL_file_list_synthetic.txt'
    files = open(save_file,'w')
    
#for f in file_list:
    for f in all_files:
        files.write(f)
        files.write('\n')
    
    print('Close file list')
    files.close()

else:
    chl_file='/Users/rosalindechols/Documents/Generals/Self_Shading_Research/Data/argo_CHL_file_list_synthetic.txt'
    print('Open file list')
    with open(chl_file) as numbers:
        files=numbers.read()
        all_files=files.split('\n')

print(len(all_files))
print('Initialize arrays')
all_data={}
depths=np.arange(0,251,5)
var_all=['TEMP','PSAL','DOXY','NITRATE','CHLA']
#want to initialize these with nans, so that if not all the profiles end
#up being used, the blank ones can be easily identified and removed. This
#is more efficient than appending tens of thousands of values to empty
#arrays.
for var in var_all:
    all_data[var]=np.nan*np.ones((len(all_files),len(depths)))
for var in ['LATITUDE','LONGITUDE']:
    all_data[var]=np.nan*np.ones(len(all_files))
all_data['JULD']=np.empty(len(all_files),dtype='datetime64[ns]')
all_data['PRES']=np.nan*np.ones((len(all_files),len(depths)))
all_data['DEPTH']=np.nan*np.ones((len(all_files),len(depths)))
#keep track of QC for comparing various effects
all_data['QC']=np.nan*np.ones(len(all_files))

#because some files have adjusted values and some do not, we need to be able
#to check for both and then ultimately store them in a single variable name
#for analysis purposes. 
key_dict={'TEMP':'TEMP','PSAL':'PSAL','DOXY':'DOXY','NITRATE':'NITRATE','CHLA':'CHLA',
          'TEMP_ADJUSTED':'TEMP','PSAL_ADJUSTED':'PSAL','DOXY_ADJUSTED':'DOXY',
          'NITRATE_ADJUSTED':'NITRATE','CHLA_ADJUSTED':'CHLA'}

count=0
qc_all=[]
qc_good=[]

print('Import data')
for f in all_files:
    #defective file that makes the program crash
    if f=='/Volumes/RE_DATA/SyntheticBioArgo/SR5904855_122.nc':
        continue
    #print counts to keep track of progress
    if count%1000==0:
        print('Number of completed files: ', count)
    data=xr.open_dataset(f) 
    
    #even if a float collected CHLA data at some point, not all files for
    #that float may have CHLA. Skip those. 
    if 'CHLA' not in data.keys():
        continue
    elif np.isnan(data['CHLA']).all():
        continue
    
    var_list=[]
    #need to use adjusted data if possible, but if not, use the regular
    for var in var_all:
        if var+'_ADJUSTED' in data.keys():
            for i in range(0,len(data['PRES'])):
                #need to check to see if adjusted data is all nans before using
                if ~np.isnan(data[var+'_ADJUSTED'][i]).all():
                   # print(var,i)
                    var_list.append(var+'_ADJUSTED')
                    break
                elif np.isnan(data[var+'_ADJUSTED'][i]).all() and i==len(data['PRES'])-1:
                    var_list.append(var)
                    break
        elif var not in data.keys() and var+'_ADJUSTED' not in data.keys():
            pass
        else:
            var_list.append(var)
                 
    qc,data=quality_control(data,'CHLA')
    qc_all.append(qc)
    if qc!=0:
        continue    
    
    qc_good.append(qc)
    all_data['QC'][count]=qc
    
    data['DEPTH']=abs(gsw.z_from_p(data['PRES'].values[0],data['LATITUDE'].values[0]))


    for var in var_list:
        #need to only use the real values because of the weird synthetic profiles
        mask=[i for i,j in enumerate(data[var].values[0]) if ~np.isnan(j)]
        all_data[key_dict[var]][count]=interpolate_data(data,var,depths,mask)
    
    #do one more QC check after interpolation to make sure there are no extreme problems:
    if all(~np.isnan(all_data['CHLA'][count])) and abs(all_data['CHLA'][count,50])<=0.5 and \
                abs(all_data['CHLA'][count,-1])<=0.5:
        if any(np.isinf(all_data['CHLA'][count])) or any(abs(all_data['CHLA'][count])>50) or \
                    any(all_data['CHLA'][count]<-0.02):
            bad=True
        else:
            bad=False
    else:
        bad=True
    
    if bad==True:
        continue
    
    all_data['DEPTH'][count]=depths
    all_data['PRES'][count]=gsw.p_from_z(-1*all_data['DEPTH'][count],data['LATITUDE'][0])
    
    for var in ['LATITUDE','LONGITUDE','JULD']:
        all_data[var][count]=data[var].values[0]
    if np.isnan(all_data['CHLA'][count]).all():
        continue
    
    
    data.close()
    count+=1


#remove extra placeholder values from the data arrays
for var in ['LATITUDE','LONGITUDE','JULD','TEMP','PSAL','CHLA','DOXY','NITRATE','DEPTH','PRES']:
    all_data[var]=np.delete(all_data[var],np.s_[count:],0)

all_data['PDENSITY']=gsw.rho(all_data['PSAL'],all_data['TEMP'],0)

print(count)
    
print('Export data to a file')
var_all=['TEMP','PSAL','DOXY','NITRATE','CHLA','PDENSITY']
print(all_data.keys())
export_data(all_data,var_all,sfpath+'all_chla_argo_250_5m.nc')

print("Total number of files:", len(qc_all))
print("Total number of files passing QC checks:", len(qc_good))
print("Total number of files with realistic values after interpolation:", len(all_data['QC']))