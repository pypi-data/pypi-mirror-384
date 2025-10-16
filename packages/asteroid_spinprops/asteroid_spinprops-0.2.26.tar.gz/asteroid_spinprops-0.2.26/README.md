# asteroid_spinprops

## Name
asteroid-spinprops

## Description
A collection of tools for fitting sHG1G2 and ssHG1G2 photometric models to sparse asteroid photometry

## Installation
```
pip install asteroid_spinprops
```
## Usage
```
import asteroid_spinprops.ssolib.utils as utils
import asteroid_spinprops.ssolib.modelfit as mfit
import asteroid_spinprops.ssolib.periodest as pest
import asteroid_spinprops.ssolib.dataprep as dprep
import os

data_path = os.path.join(project_path, "data") # Path to collection of .parquet files containing your asteroid data (FINK x ATLAS for example)

pqload = utils.pq_foler_to_dictionary(data_path, save=True)

ephem_path = os.path.join(data_path, "ephem_cache") # Path to your cached sso ephemerides (optional)

path_args = [data_path, pqload, ephem_path]


name = "Oloosson" # Object name
data = dprep.prepare_sso_data(name, *path_args) # Complement asteroid data with ephemerides/query the IMCCE Miriade service
cdata, rejects = dprep.filter_sso_data(name, *path_args) # Implement object filtering suite 
dprep.plot_filtering(cdata, rejects) # Inspect filtering


mparams = mfit.get_fit_params(cdata, "SHG1G2") # Get parameters from an sHG1G2 model
shg1g2_resids = mfit.make_residuals_df(cdata, mparams) # Get sHG1G2 model residuals
singnal, window, noise = pest.get_period_estimate(shg1g2_resids) # Get a period estimate from the sHG1G2 residuals
pest.plot_periodograms(singnal, window, name) # Inspect periodogram

# Combine all of the above to a single ssHG1G2 model fit & plot
mfit.plot_model(cdata, "SSHG1G2", shg1g2_constrained=True, alt_spin=True, resolution=400, x_axis="Phase")
```

## Models
Photometric models from Carry et al.(2024) {2024A&A...687A..38C}
and https://github.com/astrolabsoftware

## Project status
Under development
