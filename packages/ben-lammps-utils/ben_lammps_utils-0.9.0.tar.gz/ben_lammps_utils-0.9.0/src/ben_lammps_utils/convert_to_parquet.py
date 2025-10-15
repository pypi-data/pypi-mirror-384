from .read_lammps_out import read_species_out
from glob import glob
from tqdm import tqdm

def convert_to_parquet(input_file_name:str="species.out",output_file_name:str="species.parquet") -> None:
    """ converts a species out file to a parquet file

    Parameters
    ----------
    input_file_name (str): The name that matches the species file.
    
    output_file_name (str): The name of the parquet file to output to.

    Returns
    -------
    None: creates a parquet file
    """
    species_file = read_species_out(input_file_name)
    species_file.to_parquet(output_file_name,index=False)

def convert_all_to_parquet(input_file_pattern="*.out") -> None:
    """ converts all species out files that match a pattern to a parquet of the same name

    Parameters
    ----------
    input_file_pattern (str): the pattern that matches the species files.

    Returns
    -------
    None: creates parquet files
    """
    for file in tqdm(glob(input_file_pattern)):
        out_file_name=file[:-3]+"out"
        convert_to_parquet(file,out_file_name)


def species_to_parquet_UI():
    """convert to parquet user interface script.
    """
    # Welcome the user and get initial options
    print("Welcome to the species out conversion, please choose an option:")
    print("1: Convert one species file to parquet")
    print("2: Convert a bunch of species files to parquet")
    available_choices = ["1","2"]
    option_choice = input("Choice: ")

    # Handling incorrect option selections
    while not option_choice in available_choices:
        print(f"{option_choice} is not an option, please select from available options:")
        print("1: Convert one species file to parquet")
        print("2: Convert a bunch of species files to parquet")

    # Handle the convert one species case

    if option_choice == "1":
        print("Option 1 selected.")
        print("Which file would you like to convert? Leave blank to select default (species.out).")
        input_file_choice = input("Choice: ")
        print("")
        print("What would you like the output file to be called? Leave blank to select default (species.parquet).")
        output_file_choice = input("Choice: ")
        if input_file_choice == "":
            input_file_choice = "species.out"
        if output_file_choice == "":
            output_file_choice = "species.parquet"
        convert_to_parquet(input_file_choice,output_file_choice)
        print(f"{input_file_choice} -> {output_file_choice} completed.")

    elif option_choice == "2":
        print("Option 2 selected.")
        print("CAUTION: species out files must end in .out extension.")
        print("Specify a file pattern to convert. Leave blank to select default (*.out).")
        input_pattern_choice = input("Choice: ")
        if input_pattern_choice == "":
            input_pattern_choice = "*.out"
        convert_all_to_parquet(input_pattern_choice)
        print(f"species file conversion completed.")