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

<!-- Use environment.yml file to create a Conda virtual environment:
```bash
conda env create --file=environment.yml
```

After setting up the Conda virtual environment, activate it with:
```bash
conda activate cloudbandpy
``` -->

Then install the package with:
```bash
pip install -e .
```

## Usage
Change configuration file as needed. Eg. directories where the input data are located, where the figures will be saved, where the output files will be saved, then in the cloudbandPy directory.

```python
python ./src/cloudbandpy/run.py ./config/config_cbworkflow_southPacific.yml
```
<!-- TODO change for the runscript directory  -->

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

# cloudbandpy
Todo
# cloudbanddetection texting version
todo

# Notes
This package contains modified ERA5 data
Copernicus Climate Change Service (C3S) (2023): ERA5 hourly data on single levels from 1940 to present. Copernicus Climate Change Service (C3S) Climate Data Store (CDS). 10.24381/cds.adbb2d47