import pandas as pd

def read_species_out(file_name:str):
    ''' Reads a reaxff formatted species out file and gives a pandas dataframe
    
    Parameters
    ----------
    file_name (str): The Path to the species out file


    Returns
    -------
    a pandas dataframe holding all of the data
    
    '''
    # Lists to hold useful values
    species_lines = []
    number_lines = []
    
    # opens a file and turns it into a list
    with open(file_name,"r") as file:
        file_list = file.readlines()

    # seperates lines into their respective lists
    for line in file_list:
        line_list = line.strip("\n #").split()
        if line_list[0] == "Timestep":
            species_lines.append(line_list)
        else:
            number_lines.append(line_list)


    #Final dictionary that will hold data and be in a dataframe
    data_dict = {}
    # Going through each line in the species output
    for line_index, species_values in enumerate(species_lines):
        # going through each item in the species line
        for value_index, value in enumerate(species_values):
            # If a species in the species line is already in the dictionary then append the number line value
            if value in data_dict.keys():
                data_dict[value].append(int(number_lines[line_index][value_index]))

            # If a species is not already in the dictionary add it as an empty list and catch up to 1- the length of other items then add the value
            else:
                data_dict[value] = []
                for i in range(line_index-1):
                    data_dict[value].append(0)
                data_dict[value].append(int(number_lines[line_index][value_index]))

        # catch up the rest of the species
        for key in data_dict.keys():
            while len(data_dict[key]) < line_index+1:
                data_dict[key].append(0)
                
    df = pd.DataFrame(data_dict)
    return df



def read_in_stdout(file_name:str):
    ''' Reads a Lammps formatted standardout file and gives a list of pandas dataframes for each run section thermo data
    
    Parameters
    ----------
    file_name (str): The Path to the species out file


    Returns
    -------
    a list of pandas dataframes holding all of the thermo data
    
    '''
    final_data = []
    collecting_data = False
    with open(file_name,"r") as file:
        lines = [i.strip() for i in file.readlines()]

    for line in lines:
        if "Loop time of" in line:
            collecting_data = False
            final_data.append(pd.DataFrame(current_data))

        if collecting_data and line.split()[0] == "Step":
            conserved_keys = line.split().copy()
            for i in conserved_keys:
                current_data[i] = []

        if collecting_data and line.split()[0] != "Step":
            vals = [float(i) for i in line.split()]
            for key, value in zip(conserved_keys,vals):
                current_data[key].append(value)

        if "Per MPI rank" in line:
            collecting_data = True
            current_data = {}

    return final_data
