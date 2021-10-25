'''This is code to download biogeochemical Argo data from the Argo FTP servers. 
The original code was written by PhD student Katy Christensen (katyc4@uw.edu)
with modifications by PhD student Rosalind Echols (rechols@uw.edu). With 
slight modifications, the user can use it to download the raw biogeochemical 
data or the core Argo data instead of the merged biogeochemical-physical 
profiles used for this project. This is the first in a series of files 
needed to recreate the results presented in Echols, Rocap, and Riser ().'''


import os
from ftplib import FTP
import numpy as np
from os.path import isfile, join
import shutil
from tqdm import tqdm

#Set the high-level storage location for the data
mypath = '/Volumes/RE_DATA/'


# Change the directory to your desired path
# You should already be here, but it is good to check
os.chdir(mypath)

# Create a folder to put the data into. Here, we are downloading
# the merged (Synthetic) BioArgo files, so we use that as a folder name.
# If the folder already exists, just use that. This makes sure that you
# don't try to store the data in a non-existent location
direc = mypath+'/SyntheticBioArgo/'
if not os.path.exists(direc):
	os.makedirs(direc)

os.chdir(mypath+'SyntheticBioArgo/')

# FTP into the GDAC
ftp = FTP('ftp.ifremer.fr')
ftp.login()
ftp.cwd('/ifremer/argo')

# Load in the greylist and the profile lists
print('Downloading Lists')

ftp.retrbinary('RETR ar_greylist.txt',open('ar_greylist.txt','wb').write)
#this is where you set which directory on the GDAC you will be downloading data
#from. If you want something other than the synthetic profiles, you'll need to 
#change the names of these text files.
ftp.retrbinary('RETR argo_synthetic-profile_index.txt',open('argo_synthetic-profile_index.txt','wb').write)

# Set up variables for greylist and profile files
# Look to see which files you have already downloaded
greylist = 'ar_greylist.txt'

named = 'argo_synthetic-profile_index.txt'
gotten = 'synthetic_namefile.txt'

# Find the greylisted floats (load as strings)
grey = np.genfromtxt(greylist,dtype='|S7',skip_header=1,delimiter=',',usecols=0)

# Retrieve all names (column0)
names = np.genfromtxt(named,dtype=None,skip_header=9,delimiter=',',usecols=0)
amounts = len(names)

if os.path.isfile(gotten):
	filesdone = np.genfromtxt(gotten,dtype=None,usecols=0)
else:
	filesdone = []


# Remove the floats that are on the greylist or that you have already downloaded
print('Collecting Downloads')
arnames =[]
for t in range(amounts):
	if names[t] not in filesdone:
		a = names[t].decode().split("/")
		if a[1] not in grey:
			arnames.append(names[t])
		del(a)

arnames = sorted(list(set(arnames)))

# Print out the total number of files to work with total
amounts2 = len(arnames)
print('Number of Files: ')
print(amounts2)

# Create a file with the names of all the floats
ff = open("synthetic_namefile.txt",'ab')
for n in range(amounts2):
	ff.write(arnames[n]+'\n'.encode('utf-8'))

ff.close()
del(ff)

#ftp.sendcmd('PASV')
ftp.cwd('dac')

# Go through the FTP selecting only the data files that are in the focus area
# for t in tqdm(range(amounts2)):
for t in tqdm(range(amounts2)):
	floaty = arnames[t].decode().split("/")
	filepaths = direc+floaty[3]
	ftp.retrbinary('RETR '+ arnames[t].decode() ,open(filepaths,'wb').write)

# End the connection
ftp.quit()

os.chdir(mypath)