# Installation

For the core CLI tools to be installed as scripts it is reccomended that you install them using uv.
This can be done by running the command:
```bash
uv tool install ben-lammps-utils
```
The tools can also be installed using the standart pip installation in a conda or venv environment:
```bash
pip install ben-lammps-utils
```

To use the package in your own applications the ben-lammps-utils functions can be imported afer pip installation, or using `uv add` functionality.

# Use and Features
## CLI Tools
ben-lammps-utils comes with two built in CLI tools that can be installed and used system wide.

### spec2csv
The spec2csv command can be used to convert ReaxFF species out files to
a more human readable csv format. It can be used on one species out file,
or a range of species out files that match a pattern.
### spec_qp
The spec_qp command can be used to generate a quick plot of species from species out data using either the species out file or a csv. It has built in functionality to either plot specified species, or plot N species that have a maximum count.

## Package Functions

### read_species_out()
Reads a reaxff formatted species out file and gives a pandas dataframe

**Parameters**

file_name (str): The Path to the species out file


**Returns**

pandas dataframe holding all of the data

### read_in_stdout()

Reads a Lammps formatted standardout file and gives a list of pandas dataframes for each run section thermo data

**Parameters**

file_name (str): The Path to the species out file

**Returns**

a list of pandas dataframes holding all of the thermo data

### convert_to_csv()

converts a species out file to a csv file

**Parameters**

input_file_name (str): The name that matches the species file.
    
output_file_name (str): The name of the csv file to output to.

**Returns**

None: creates a csv file

### convert_all_to_csv()
converts all species out files that match a pattern to a csv of the same name

**Parameters**

input_file_pattern (str): the pattern that matches the species files.

**Returns**

None: creates csv files

### species_to_csv_UI()
Identical to using the `spec2csv`

### read_in_data()

Reads in a data file from a species out file or csv
    
**Parameters**

file_name (str): the name of the file to read in
    
**Returns**

Pandas Dataframe

### get_n_max()
Gets The N species that have maximum counts

**Parameters**

dataframe (pandas.DataFrame): the data frame read in from a species out file.

num_vals (int): The numberr of species to plot

ignore (list[str]): A list of species to ignore for maximums

**Returns**

list[str]: a list of N species that have maximum counts

### get_n_max_cycle()
Gets The N species that have maximum counts interactively

**Parameters**

dataframe (pandas.DataFrame): the data frame read in from a species out file.

num_vals (int): The numberr of species to plot

ignore (list[str]): A list of species to ignore for maximums

**Returns**

list[str]: a list of N species that have maximum counts

### species_vs_time_quickplot()
Quickly plots species out.
**Parameters**

dataframe (pandas.DataFrame): a dataframe containing information from the species out file.

keys_to_plot (list[str]): a list of the species of interest.

time_step_lower (int): the lower bound for time steps to plot

time_step_upper (int): the upper bound of time steps to plot

is_transparent (bool): Wether or not the background should be transparent

outfile_name (str): The name of the file figure will be saved to.

figure_title (str): The Title at the top of the figure.

**Returns**

The matplotlib figure and axis. Saves a figure.

### plot_species_UI()

Identical to calling spec_qp command

