This repository contains several Python programs and notebooks that allow users to reproduce the results presented in Echols, Rocap, and Riser (in prep, 2021), beginning with initial data download. 

To perform the initial data download and cleaning, users should run the following programs in order:
1. Download Data: bgc_argo_download_public.py
2. Compile list of float numbers with critical variable (in this case, 'CHLA'): bgc_argo_float_list_public.py
3. Quality control, smooth, and interpolate all available profiles, then store in a single netCDF file: bgc_argo_data_process_public.py

After completing these three steps, users will have a single file containing all available profiles of chlorophyll (mg m^-3) from BGC Argo floats interpolated to a 5m grid. This file constitutes the input for the first of two python notebooks, "GMM_chlorophyll_public.ipynb". This notebook allows users to tinker with the methods used in the paper referenced above and produce some of the figures shown in the paper. Users can either use to complete the steps exactly as described in the paper or explore how adjusting different features (number of principal components, for example), affects the results. 

Many of the remaining figures can be reproduced using the output from "GMM_chlorophyll_public.ipynb" (which can be saved as a netCDF file) by using the notebook "GMM_figures.ipynb".

Finally, the methods and figures relating to the curve fitting work done in the paper can be reproduced using the notebook "GMM_curve_fit.ipynb". This notebook requires both the output from Step 3 above as well as the output from "GMM_chlorophyll_public.ipynb".

This notebook reflects work done by Rosalind Echols as a PhD candidate at the University of Washington School of Oceanography. Please direct questions to rechols@uw.edu. 
