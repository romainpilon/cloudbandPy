# CloudbandPy

cloudbandPy is a Python package for detecting and tracking atmospheric cloud bands.

The cloudbandPy package detect tropical-extratropical cloud bands. This software can use various regular grid datasets.

This is currently the development software used for research.

## Installation
Clone cloudbandPy:

```bash
git clone https://github.com/romainpilon/cloudbandPy.git
```

Go to the directory:
```bash
cd cloudbandPy
```

Then install the package with:
```bash
pip install -e .
```

### --- Alternative install
You can also set up a conda environment before installing the package.

With environment.yml file, create a Conda virtual environment:
```bash
conda env create --file=environment.yml
```

After setting up the Conda virtual environment, activate it with:
```bash
conda activate cloudbandpy
```

Then install the package
```bash
pip install -e .
```

## Input Data Requirements
cloudbandPy works with netCDF files using netCDF4's capability to handle 3-dimension arrays of gridded latitude/longitude data. Currently, cloudbandPy  supports ERA5 data on the regular grid.

The input data must contain at least 3 dimensions: time, latitude and longitude.
cloudbandPy only supports detection and tracking data on 2D arrays


## Usage
Before you run anything, make sure that the configuration file is set up the way you want it, i.e. setting up the input data directory.

To run the cloud band detection, run the following command:

```python
python ./runscripts/run.py ./config/config_cbworkflow_southPacific.yml
```

Default settings are:
- Input data are 3-hourly ERA5 OLR data with filenames written as such `top_net_thermal_radiation_yyyy.nc` where `yyyy` is the year.
- The detection period is 24 hours.
- Output files containing cloud bands are written in a specific directory that will be created in the current directory.
- Figures will be saved in a specific directory that will be created in the current directory.

Example run scripts are located in the `runscripts` directories.


## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.


# Notes
This package contains modified ERA5 data
Copernicus Climate Change Service (C3S) (2023): ERA5 hourly data on single levels from 1940 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). 10.24381/cds.adbb2d47