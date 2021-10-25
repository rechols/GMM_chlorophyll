'''This is the second in a series of short Python programs that can be used to
recreate the results in Echols, Rocap, and Riser (). It is important to note
that this program relies on a directory containing BGC Argo data downloaded
using the program "bgc_argo_download_public.py". This code was written by 
PhD student Rosalind Echols.
'''

from netCDF4 import Dataset
import os
import re
import numpy as np
import itertools
import xarray as xr

#Compile a list of data files (can vary the search criteria depending on file source)
def float_list_with_keyword(path,search_crit,keyword):
    float_list=[]
    bad_floats=[]
    count=0
    for data_file in os.listdir(path):
        if data_file[-14:-7] in float_list or data_file[-15:-8] in float_list:
            pass
        elif data_file[-14:-7] in bad_floats or data_file[-15:-8] in bad_floats:
            pass
        else:
            match = re.search(search_crit, data_file)
            if match:
                file_path = path+data_file
                try:
                    with xr.open_dataset(file_path) as ds:
                        if keyword in ds.keys():
                            float_list= np.append(float_list,data_file[-14:-7])
                            count+=1
                            if count%10==0:
                                print(count)
                        else:
                            bad_floats=np.append(bad_floats,data_file[-14:-7])
                except OSError:
                    pass
                
            else:
                pass
            
    return float_list


#Main program
folder='/Volumes/RE_DATA/SyntheticBioArgo/'
path=folder


print('Find files')
float_list = float_list_with_keyword(path, '.nc','CHLA')


print('Save files')   
save_file='' #set filename/location for saving file list, ending with .txt
files = open(save_file,'w')
    
for f in float_list:
    files.write(f)
    files.write('\n')

print('Close file list')    
files.close()