from .read_lammps_out import read_species_out
import matplotlib.pyplot as plt
import pandas as pd

def read_in_data(file_name="species.out") -> pd.DataFrame:
    """ Reads in a data file from a species out file, csv, or parquet
    
    Parameters
    ----------
    
    file_name (str): the name of the file to read in
    
    Returns
    -------
    Pandas Dataframe"""
    if file_name[-4:] == ".csv":
        species_df = pd.read_csv(file_name)
        for column in species_df.columns:
            species_df[column] = pd.to_numeric(species_df[column])

    if file_name[-8:] == ".parquet":
        species_df = pd.read_parquet(file_name)
        for column in species_df.columns:
            species_df[column] = pd.to_numeric(species_df[column])
    else: 
        species_df = read_species_out(file_name)
    return species_df

def get_n_max(dataframe:pd.DataFrame,num_vals:int,ignore:list=[]) -> list[str]:
    """ Gets The N species that have maximum counts

    Parameters
    ----------
    dataframe (pandas.DataFrame): the data frame read in from a species out file.

    num_vals (int): The numberr of species to plot

    ignore (list[str]): A list of species to ignore for maximums

    Return
    ------
    list[str]: a list of N species that have maximum counts
    """
    vals = []
    for column in dataframe.columns:
        if column != "Timestep" and not column in ignore:
            vals.append((column,dataframe[column].max()))
    vals = sorted(vals,key=lambda x:x[1],reverse=True)
    return [i[0] for i in vals[:num_vals]]

def get_n_max_cycle(dataframe:pd.DataFrame,num_vals:int,ignore:list=[]) -> list[str]:
    """ Gets The N species that have maximum counts interactively

    Parameters
    ----------
    dataframe (pandas.DataFrame): the data frame read in from a species out file.

    num_vals (int): The numberr of species to plot

    ignore (list[str]): A list of species to ignore for maximums

    Return
    ------
    list[str]: a list of N species that have maximum counts
    """

    # Get the first set
    species_of_interest = get_n_max(dataframe,num_vals,ignore)
    print(f"Top {num_vals} species.")
    for species in species_of_interest:
        print(species)

    # Iteratevly remove species as needed
    print("If there are any you don't want included please type them below. You may specify multiple and seperate them by spaces. If you would not like to add species, leave it blank.")
    species_to_ignore = input("Species to ignore: ").strip().split()

    while species_to_ignore != []:
        for i in species_to_ignore:
            ignore.append(i)
        species_of_interest = get_n_max(dataframe,num_vals,ignore)

        for species in species_of_interest:
            print(species)

        print("If there are any you don't want included please type them below. You may specify multiple and seperate them by spaces. If you would not like to add species, leave it blank.")
        species_to_ignore = input("Species to ignore: ").strip().split()
    
    return species_of_interest


def species_vs_time_quickplot(dataframe:pd.DataFrame,keys_to_plot,time_step_lower=None,time_step_upper=None,is_transparent=False,outfile_name="species_vs_time.png",figure_title="Species over time"):
    """ Quickly plots species out.
    Parameters
    ----------
    dataframe (pandas.DataFrame): a dataframe containing information from the species out file.

    keys_to_plot (list[str]): a list of the species of interest.

    time_step_lower (int): the lower bound for time steps to plot

    time_step_upper (int): the upper bound of time steps to plot

    is_transparent (bool): Wether or not the background should be transparent

    outfile_name (str): The name of the file figure will be saved to.

    figure_title (str): The Title at the top of the figure.

    Returns
    -------

    The matplotlib figure and axis. Saves a figure.

    """
    temp_dataframe = dataframe.copy()
    if time_step_lower != None:
        temp_dataframe = temp_dataframe[temp_dataframe["Timestep"]>= time_step_lower]
    if time_step_upper != None:
        temp_dataframe = temp_dataframe[temp_dataframe["Timestep"]<= time_step_upper]
    
    fig, ax  =  plt.subplots(1,1)
    for key in keys_to_plot:
        if key in temp_dataframe.columns:
            print(f"plotting {key}")
            ax.plot(temp_dataframe["Timestep"],temp_dataframe[key],label=key)
    ax.set_title(figure_title)
    ax.set_xlabel("Time Step")
    ax.set_ylabel("Species Count")
    ax.legend()
    fig.savefig(outfile_name,bbox_inches="tight",transparent=is_transparent)
    print(f"{outfile_name} created")

    return fig, ax




def plot_species_UI():
    """ Interactive prompt for plotting species."""

    print("What is the location of the data you would like to plot?:")
    data_frame = read_in_data(input("File Name: "))

    print("Welcome to species out quick plotting, please choose an option:")
    print("1: Plotting N maximum species.")
    print("2: Plotting specified species.")


    available_choices = ["1","2"]

    option_choice = input("Choice: ")

    # Handling incorrect option selections
    while not option_choice in available_choices:
        print(f"{option_choice} is not an option, please select from available options:")
        print("1: Plotting N maximum species.")
        print("2: Plotting specified species.")
        option_choice = input("Choice: ")

    if option_choice == "1":
        N_Species = int(input("How many species would you like to plot?: "))
        species_to_plot = get_n_max_cycle(data_frame,N_Species,["No_Moles","No_Specs"])
        # lower_time_step
        print("What is the lower bound for time steps to plot (leave blank to allow all)")
        lower_time = input("lowest time step: ")
        if lower_time == "":
            lower_time =None
        else: lower_time = float(lower_time)


        # Upper_time_step
        print("What is the lower bound for time steps to plot (leave blank to allow all)")
        highest_time = input("highest time step: ")
        if highest_time == "":
            highest_time = None
        else: highest_time = float(highest_time)
        # transparent_value
        print("Would you like the background to be tansparent (default is no), type 'yes' confirm")
        transparent_value = (input("Transparent?: ")).lower().strip()
        transparent_value = transparent_value == "yes"
        # outfile_name
        print("What would you like the file to be named (leave blank for default species_vs_time.png)")
        file_name = input("file name: ")
        if file_name == "":
            file_name = "species_vs_time.png"
        # Figure Title
        print("What would you like the figure title to be. (leave blank for 'Species over Time')")
        plot_title = input("plot title: ")
        if plot_title == "":
            plot_title = "Species over Time"

        species_vs_time_quickplot(data_frame,species_to_plot,lower_time,highest_time,transparent_value,file_name,plot_title)

    if option_choice == "2":
        print("Which species would you like to plot? Please seperate them by spaces.")
        species_to_plot = input("Species to plot: ")
        species_to_plot = species_to_plot.strip().split()
        # lower_time_step
        print("What is the lower bound for time steps to plot (leave blank to allow all)")
        lower_time = input("lowest time step: ")
        if lower_time == "":
            lower_time =None
        else: lower_time = float(lower_time)


        # Upper_time_step
        print("What is the lower bound for time steps to plot (leave blank to allow all)")
        highest_time = input("highest time step: ")
        if highest_time == "":
            highest_time = None
        else: highest_time = float(highest_time)
        # transparent_value
        print("Would you like the background to be tansparent (default is no), type 'yes' confirm")
        transparent_value = (input("Transparent?: ")).lower().strip()
        transparent_value = transparent_value == "yes"
        # outfile_name
        print("What would you like the file to be named (leave blank for default species_vs_time.png)")
        file_name = input("file name: ")
        if file_name == "":
            file_name = "species_vs_time.png"
        # Figure Title
        print("What would you like the figure title to be. (leave blank for 'Species over Time')")
        plot_title = input("plot title: ")
        if plot_title == "":
            plot_title = "Species over Time"

        species_vs_time_quickplot(data_frame,species_to_plot,lower_time,highest_time,transparent_value,file_name,plot_title)


if __name__ == "__main__":
    plot_species_UI()
