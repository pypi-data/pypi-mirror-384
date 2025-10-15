#  Introduction 

EBM is a model used by the Norwegian Water Resources and Energy Directorates (NVE) to forecast energy use in the 
building stock. EBM is an open-source model developed and managed by NVE. The model allows the user to analyze how 
demographic trends and policy instruments impact the yearly energy use on a national and regional level. Energy use is 
estimated by a bottom- up approach, based on the building stock floor area, energy need and distribution of heating 
systems. The mathematical model is implemented in Python, with input and output files in excel or csv.


# Getting Started

## More information


 - [Full documentation found here](https://nve.github.io/ebm-docs/index.html)
   - [Model description](https://nve.github.io/ebm-docs/model_description/index.html)
   - [Limitations](https://nve.github.io/ebm-docs/limitations.html)
   - [User guide](https://nve.github.io/ebm-docs/user_guide/index.html)
   - [Troubleshooting](https://nve.github.io/ebm-docs/user_guide/troubleshooting.html)


## Setting up virtual environment
It is recommended that you use ebm in a python virtual environment (venv).

For detailed instructions, see
[How to create and activate a virtual environment](docs/source/env_setup.md)


## 1. Installation process 

<!-- Open a terminal application and navigate to wherever you want to do work. -->
 
<!-- Please refer to [getting started](https://nve.github.io/ebm-docs/user_guide/getting_started.html) for information on 
how ti install EBM as a user. -->

You can install the package in two main ways, depending on your needs:

**Option 1: Install from PyPI (recommended for most users)**

This is the simplest and most stable way to get the latest released version:

`python -m pip install ebm`


**Option 2: Install from source (for development or contributions)**

If you plan to modify the code or contribute to the project, clone the repository and install it in editable mode:

`git clone https://github.com/NVE/ebm`

`cd ebm`

Make sure your current working directory is the EBM root. 

`python -m pip install -e .`


The command will install install all dependencies and ebm as an editable module.
    
    
## 2. Software dependencies
  - pandas
  - loguru
  - openpyxl
  - pandera
   
  Dependecies will be automatically installed when you install the package as described under Installation process.
  See also [requirements.txt](requirements.txt)


## 3. Create an input directory
Before running the model you need to create a directory with the necessary input files:

`python -m ebm create --input`



## 4. Run the model

There are multiple ways to run the program. Listed bellow is running as a standalone program and running as a module. If 
running as a program fails due to security restriction, you might be able to use the module approach instead. 

See also [Running as code](#running-as-code)


### Running as a module

```cmd
python3 -m ebm
```

By default, the results will be written to the subdirectory `output`

For more information use `--help`

`python -m ebm --help`

```shell
usage: ebm [-h] [--version] [--debug] [--categories [CATEGORIES ...]] [--input [INPUT]] [--force] [--open]
           [--csv-delimiter CSV_DELIMITER] [--create-input] [--horizontal-years]
           [{area-forecast,energy-requirements,heating-systems,energy-use}] [output_file]

Calculate EBM energy use 1.2.15

positional arguments:
  {area-forecast,energy-requirements,heating-systems,energy-use}

                        The calculation step you want to run. The steps are sequential. Any prerequisite to the chosen step will run
                            automatically.
  output_file           The location of the file you want to be written. default: output\ebm_output.xlsx
                            If the file already exists the program will terminate without overwriting.
                            Use "-" to output to the console instead

options:
  -h, --help            show this help message and exit
  --version, -v         show program's version number and exit
  --debug               Run in debug mode. (Extra information written to stdout)
  --categories [CATEGORIES ...], --building-categories [CATEGORIES ...], -c [CATEGORIES ...]

                        One or more of the following building categories:
                            house, apartment_block, kindergarten, school, university, office, retail, hotel, hospital, nursing_home, culture, sports, storage_repairs.
                            The default is to use all categories.
  --input [INPUT], --input-directory [INPUT], -i [INPUT]
                        path to the directory with input files
  --force, -f           Write to <filename> even if it already exists
  --open, -o            Open output file(s) automatically when finished writing. (Usually Excel)
  --csv-delimiter CSV_DELIMITER, --delimiter CSV_DELIMITER, -e CSV_DELIMITER
                        A single character to be used for separating columns when writing csv. Default: "," Special characters like ; should be quoted ";"
  --create-input
                        Create input directory containing all required files in the current working directory
  --horizontal-years, --horizontal, --horisontal
                        Show years horizontal (left to right)
```


### Running as code
```python

from ebm.temp_calc import calculate_energy_use_wide
from ebm.model.file_handler import FileHandler

fh = FileHandler()
fh.create_missing_input_files()

df = calculate_energy_use_wide(ebm_input=fh.input_directory)
print(df)

```

## License
This project is licensed under the MIT License. You are free to use, modify, and distribute the software with proper attribution.

## Contributing
We welcome contributions! Please refer to the Contributing Guide (CONTRIBUTING.md) for details on how to get started.

## Documentation
Full documentation is available at the EBM User Guide: https://nve.github.io/ebm-docs/



