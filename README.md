# CloudbandPy

cloudbandPy is a Python package for detecting and tracking atmospheric cloud bands.

The cloudbandPy package detect tropical-extratropical cloud bands. This software can use various regular grid datasets.

This is currently the development software used for research.

## 1. Installation
To install, type:

```bash
pip install cloudbandpy
```

Additionnaly, you can clone cloudbandPy


```bash
git clone https://github.com/romainpilon/cloudbandPy.git
```

Go to the directory
```bash
cd cloudbandPy
```

Then install the package with
```bash
pip install -e .
```


Optionally, a conda environment.yml file is provided to create a conda virtual environment containing all librairies required. Before installing the package with pip, you may run

```bash
conda env create --file=environment.yml
```

Then you may activate it
```bash
conda activate cloudbandpy
```

## 2. Input Data Requirements
cloudbandPy works with netCDF files using netCDF4's capability to handle 3-dimension arrays of gridded latitude/longitude data. Currently, cloudbandPy  supports ERA5 data on its regular grid. Irregular grids must be regridded to a regular grid beforehand.

The input data must contain at least 3 dimensions: time, latitude and longitude, in this order.
cloudbandPy only supports detection and tracking data on 2D arrays.


## 3. Usage
Before you run anything, make sure that the configuration file is set up the way you want it, i.e. setting up the input data directory, all the paths of the files, and so on

To run the cloud band detection, run the following command:

```python
python ./cloudbandPy/runscripts/run.py ./cloudbandPy/config/config_cbworkflow_southPacific.yml
```

Default settings:
- Input data are 3-hourly ERA5 OLR data with filenames written as such `top_net_thermal_radiation_yyyy.nc` where `yyyy` is the year.
- The detection period is 24 hours.
- Output files containing cloud bands are written in a specific directory that will be created in the current directory.
- Cloud band masks and characteristics are written to netCDF4 files and stored in a user defined directory.
- Figures will be saved in a specific directory that will be created in the current directory.

Example run scripts are located in the `runscripts` directories.

To see specific use of the code, a set of notebooks are located in the `notebooks` directory.

## 4. Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.


## 5. Disclaimer
This package contains modified ERA5 data.
Copernicus Climate Change Service (C3S) (2023): ERA5 hourly data on single levels from 1959 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). 10.24381/cds.adbb2d47

Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data this code contains.