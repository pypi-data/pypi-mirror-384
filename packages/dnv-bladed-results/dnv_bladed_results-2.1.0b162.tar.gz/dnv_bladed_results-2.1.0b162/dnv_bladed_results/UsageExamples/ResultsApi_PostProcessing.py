from __future__ import annotations
from dnv_bladed_results import ResultsApi, Variable, IndependentVariable, UsageExamples
import dnv_bladed_results as dnvres
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

############   Bladed Results API: Post-Processing   ############

# Contains examples of post-processing Bladed results data into different data structures and plots.

# This example requires the pandas library, available via pip.  It has been tested with pandas >= 2.3.0.


def run_script(run_directory : str = None, run_name: str = None, variable_name: str = None):
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Loads an example run and fetches a specific variable from that run.
    - Prints the data to the console, and writes it both to a text file and to a CSV file.
    - Demonstrates how to post-process the data into a Matlab-like data structure, and into a Pandas DataFrame.
    - Plots data using the Pandas DataFrame plotting functions.
    """

    # Get the run directory location
    if run_directory is None: 
        run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")

    # Note that we do not need to provide run or variable names with the correct case
    if run_name is None:
        run_name = "powprod5mw"

    if variable_name is None :
        variable_name = "Blade 1 Fx (Principal elastic axes)"

    # Create output directory
    output_directory = "./Output"
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    # Set the file path for writing the processed data
    file_name = os.path.join(output_directory, "example_timeseries").replace("\\","/")

    # Get the target run outputs
    run = ResultsApi.get_run(run_directory, run_name)

    if run.contains_variable_2d(variable_name):
        # Get 2D variable 
        dependent_variable = run.get_variable_2d(variable_name)
    elif run.contains_variable_1d(variable_name):
        # Get 1D variable
        dependent_variable = run.get_variable_1d(variable_name)
    else:
        raise Exception("Run data does not contain the variable " + variable_name)

    # Create a data structure to handle the output data
    data = DataStructureClass(dependent_variable)

    # Print data to console
    to_console(data)

    # Print data to an ASCII file
    to_ascii(data, file_name)

    # Transform data into a Pandas DataFrame
    data_frame = to_data_frame(data)

    # Print data to an ASCII file
    to_csv(data_frame, file_name)

    # Plot time series at a defined span index
    if data.dependent_variable.ndim == 2:
        plot_section(data, data_frame, 1)

    # Plots a specific time step index of a Pandas DataFrame of a 2D variable.
    plot_time_step(data, data_frame, 1)

    # Show figures
    plt.show()  

class DataStructureClass():
    # Class to create a matlab like data structure for dnv_bladed_results ResultsAPI_Python.Variable types

    class VariableClass():
        # Inner class representing the second level of the structure
        def __init__(self, variable: Variable | IndependentVariable):
            
            # Assign variable metadata
            self.si_unit = variable.si_unit
            self.name = variable.name

            self.values = []
            self.ndim = None

            if (type(variable) == IndependentVariable):
                # Assign Independent variable numerical data whether it is a string or a number
                if variable.has_numeric_values:
                    self.values = variable.get_values_as_number()
                else:      
                    self.values = variable.get_values_as_string()
            
            else:
                # assign Dependent variable numerical data as a 1D or 2D array
                self.values = variable.get_data()

            # Store the number of dimensions of the array
            self.ndim = self.values.ndim

    def __init__(self, dependent_variable: Variable):

        # Assert that we have a ResultsAPI variable type
        if hasattr(dependent_variable, "number_of_independent_variables"):

            # Assign dependent variable data
            self.dependent_variable = self.VariableClass(dependent_variable)

            # Check whether it is a 1D or a 2D variable
            if(dependent_variable.is_one_dimensional):

                # Assign independent variable data
                primary_independent_variable = dependent_variable.get_independent_variable()
                self.primary_independent_variable = self.VariableClass(primary_independent_variable)

            elif(dependent_variable.is_two_dimensional):

                # Assign independent variable data
                primary_independent_variable = dependent_variable.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_PRIMARY)
                self.primary_independent_variable = self.VariableClass(primary_independent_variable)
                
                # Assign independent variable data
                secondary_independent_variable = dependent_variable.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY)
                self.secondary_independent_variable = self.VariableClass(secondary_independent_variable)

        else:
            raise TypeError("DataStructureClass expected a ResultsAPI_Python.Variable1D* or ResultsAPI_Python.Variable2D* type variables")


def to_console(data: DataStructureClass):
    r"""
    Prints all data from a specific dependent variable to the console.

    Parameters
    ----------
    data : DataStructureClass
        Data structure containing the dependent variable data to write.
    """

    # Print dependent variable data
    print("Name: " + data.dependent_variable.name)
    print("unit: " + data.dependent_variable.si_unit)
    print("Dimensions: " + str(data.dependent_variable.ndim))
    print(data.dependent_variable.values)

    # Print all timestep values to the console
    print("Name: " + data.primary_independent_variable.name)
    print("unit: " + data.primary_independent_variable.si_unit)
    print("Dimensions: " + str(data.primary_independent_variable.ndim))
    print(data.primary_independent_variable.values)

    if data.dependent_variable.ndim == 2:
        # Print all secondary independent variable value locations to the console
        print("Name: " + data.secondary_independent_variable.name)
        print("unit: " + data.secondary_independent_variable.si_unit)
        print("Dimensions: " + str(data.secondary_independent_variable.ndim))
        print(data.secondary_independent_variable.values)


def to_ascii(data: DataStructureClass, file_name: str):
    r"""
    Prints the dependent variable data into an ASCII file separated by tabs.

    Parameters
    ----------
    data : DataStructureClass
        Data structure containing the dependent variable data.
    file_name : str
        The name of the file to write.
    """ 

    with open(file_name + '.txt', 'w') as file:

        file.write("\n" + data.primary_independent_variable.name + " [" + data.primary_independent_variable.si_unit + "]")
        for primary_independent_variable_value in data.primary_independent_variable.values:
            file.write("\t" + str(primary_independent_variable_value))
        
        if data.dependent_variable.ndim == 2:
            file.write(str("\n" + data.secondary_independent_variable.name + " [" + data.secondary_independent_variable.si_unit + "]"))
        for primary_independent_variable_value in data.primary_independent_variable.values:
            file.write("\t" + data.dependent_variable.name + " [" + data.dependent_variable.si_unit + "]")

        if data.dependent_variable.ndim == 2:
            for secondary_index,distance in enumerate(data.secondary_independent_variable.values):
                file.write("\n" + str(distance))
                for primary_index, primary_independent_variable_value in enumerate(data.primary_independent_variable.values):
                    # Write load value:
                    file.write("\t" + str(data.dependent_variable.values[secondary_index][primary_index]))


def to_data_frame(data: DataStructureClass) -> pd.DataFrame:
    r"""
    Builds a Pandas data frame from a data structure object.

    Parameters
    ----------
    data : DataStructureClass
        Data structure containing the dependent variable data.
    
    Returns
    -------
    pd.DataFrame
        A Pandas DataFrame.
    """

    if data.dependent_variable.ndim == 2:
        data_frame = pd.DataFrame(data.dependent_variable.values, columns = data.primary_independent_variable.values, index = data.secondary_independent_variable.values)
        data_frame.index.name = data.secondary_independent_variable.name + " [" + data.secondary_independent_variable.si_unit + "]"
        data_frame.columns.name = data.primary_independent_variable.name + " [" + data.primary_independent_variable.si_unit + "]"
    elif data.dependent_variable.ndim == 1:
        data_frame = pd.DataFrame(data.dependent_variable.values, index = data.primary_independent_variable.values,\
                                   columns = [data.dependent_variable.name + " [" + data.dependent_variable.si_unit + "]"])
        data_frame.index.name = data.primary_independent_variable.name + " [" + data.primary_independent_variable.si_unit + "]"
 

    return data_frame


def plot_section(data: DataStructureClass, data_frame: pd.DataFrame, section_number: int):
    r"""
    Plots a specific section of a Pandas DataFrame of a 2D variable.

    Parameters
    ----------
    data : DataStructureClass
        Data structure containing the dependent variable data.
    data_frame : pd.DataFrame
        The DataFrame to plot.
    section_number : int
        The specific section to plot.
    """

    plt.figure()
    ax= data_frame.loc[data_frame.index[section_number]].plot()
    ax.set_ylabel(data.dependent_variable.name + " [" + data.dependent_variable.si_unit + "]")
    ax.set_title(data_frame.index.name + "=" + str(data_frame.index[section_number]))


def plot_time_step(data: DataStructureClass, data_frame: pd.DataFrame, time_step: int):
    r"""
    Plots a specific time step index of a Pandas DataFrame of a 2D variable.

    Parameters
    ----------
    data : DataStructureClass
        Data structure containing the dependent variable data.
    data_frame : pd.DataFrame
        The DataFrame to plot.
    time_step : int
        The timestep index to plot.
    """
    
    if data.dependent_variable.ndim==2:
        plt.figure()
        ax= data_frame[data_frame.columns[time_step]].plot()
        ax.set_ylabel(data.dependent_variable.name + " [" + data.dependent_variable.si_unit + "]")
        ax.set_title(data_frame.columns.name + "=" + str(data_frame.columns[time_step]))
    elif data.dependent_variable.ndim==1:
        ax= data_frame.plot()
        ax.set_ylabel(data.dependent_variable.name + " [" + data.dependent_variable.si_unit + "]")

def to_csv(data_frame: pd.DataFrame, file_name: str):
    r"""
    Prints the dependent variable data into a CSV file.

    Parameters
    ----------
    data_frame : pd.DataFrame
        The DataFrame to print.
    file_name : str
        The name of the file to write.
    """

    data_frame.to_csv(file_name + ".csv")


if __name__ == "__main__":
    run_script()
