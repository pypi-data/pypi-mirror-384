from dnv_bladed_results import ResultsApi, Variable2D, IndependentVariable, UsageExamples
import dnv_bladed_results as dnvres
import numpy as np
import os
from matplotlib import pyplot
import matplotlib.ticker as mtick
from matplotlib import cm

############   Bladed Results API: Plot Bladed results (3D surface chart)   ############

# This example requires the matplotlib library, available via pip.  It has been tested with matplotlib >= 3.9.4.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Reads time series data for every independent variable value of a 2D variable (blade 1 fx for all blade stations).
    - Creates a 3D surface plot of the data using matplotlib.
    """

    run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")
    run_name = "powprod5MW"
    variable_name = "blade 1 fx (principal elastic axes)"

    # Get the data using the Results API
    time_independent_variable, blade_stations_independent_variable, blade_variable = read_bladed_results(variable_name, run_directory, run_name)

    # Plot the data using the matplotlib library
    plot_bladed_results_surface(time_independent_variable, blade_stations_independent_variable, blade_variable)

    # Clear the cache
    ResultsApi.clear_runs()


def read_bladed_results(variable_name, run_directory, run_name):

    ################################
    #  Get a specific run by name  #
    ################################

    run = ResultsApi.get_run(run_directory, run_name)
    
    ################################
    #  Get variables from the run  #
    ################################

    # Dependent variable
    variable_2d: Variable2D
    variable_2d = run.get_variable_2d(variable_name)

    # Independent variables
    primary_independent_variable = variable_2d.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_PRIMARY)
    secondary_independent_variable = variable_2d.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY)

    # Note: we can also get an independent variable using the name, for example:
    # primary_independent_variable = variable_2d.get_independent_variable("time")
    # secondary_independent_variable = variable_2d.get_independent_variable("distance along blade")

    return primary_independent_variable, secondary_independent_variable, variable_2d


def plot_bladed_results_surface(
        primary_independent_variable: IndependentVariable, 
        secondary_independent_variable: IndependentVariable, 
        variable_2d: Variable2D):
    
    #########################################
    #  Get data arrays for the 3 plot axes  #
    #########################################

    # Get the time values as numeric array
    x_values = primary_independent_variable.get_values_as_number()

    # Get a 2D array of time series data (dependent variable)
    y_values = variable_2d.get_data()

    # Get the secondary independent variable values (e.g. blade stations)
    z_values = secondary_independent_variable.get_values_as_number()

    ####################################
    #  Plot the data using matplotlib  #
    ####################################

    # Set up axes
    fig = pyplot.figure(figsize=(12, 8), constrained_layout=True)
    ax = pyplot.axes(projection="3d")

    # Set up co-ordinate matrix and surface co-ordinates
    (x_values,z_values) = np.meshgrid(x_values,z_values)
    ax.plot_surface(x_values,y_values,z_values,cmap=cm.coolwarm,cstride=1,rstride=1)

    # Set axis labels
    ax.set_xlabel(primary_independent_variable.name + " [" + primary_independent_variable.si_unit + "]")
    ax.set_ylabel(variable_2d.si_unit)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))
    ax.set_zlabel(secondary_independent_variable.name + " [" + secondary_independent_variable.si_unit + "]")
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))

    # Render plot
    pyplot.title(variable_2d.parent_group_name + " - all blade stations")
    pyplot.show()


if __name__ == "__main__":
    run_script()