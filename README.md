# Alpha version of CloudbandPy

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

Use environment.yml file to create a Conda virtual environment:
```bash
conda env create --file=environment.yml
```

After setting up the Conda virtual environment, activate it with:
```bash
conda activate cloudbandpy
```

Then install the package with:
```bash
pip install -e .
```

## Usage
Run cloudbandPy after activating the conda enviromnent.

```python
python ./src/main.py ./config/config_cbworkflow_southPacific.yml
```

Example run scripts are included runscripts. These run scripts act as a drop-in replacement for src/main.py config/config.yml, and get executed in the same way, using bash:

```bash
bash ./runscripts/run_cloudbanddetection.bash
```


## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.
# CloudBandDetection
# cloudbanddetection texting version
