from dnv_bladed_results import ResultsApi, Variable2D, IndependentVariable, UsageExamples
import dnv_bladed_results as dnvres
import os
from matplotlib import pyplot
import matplotlib.ticker as mtick

############   Bladed Results API: Plot Bladed results (2D line chart)   ############

# This example requires the matplotlib library, available via pip.  It has been tested with matplotlib >= 3.9.4.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Reads time series data for every independent variable value of a 2D variable (e.g. blade 1 fx for all blade stations).
    - Creates a 2D line plot of the data using matplotlib.
    """

    run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")
    run_name = "powprod5MW"
    variable_name = "blade 1 fx (principal elastic axes)"

    # Get the data using the Results API
    time_independent_variable, blade_stations_independent_variable, blade_variable = read_bladed_results(variable_name, run_directory, run_name)

    # Plot the data using the matplotlib library
    plot_bladed_results(time_independent_variable, blade_stations_independent_variable, blade_variable)

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
    var_2d: Variable2D
    var_2d = run.get_variable_2d(variable_name)

    # Independent variables
    primary_independent_variable = var_2d.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_PRIMARY)
    secondary_independent_variable = var_2d.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY)

    # Note: we can also get an independent variable using the name, for example:
    # primary_independent_variable = var_2d.get_independent_variable("time")
    # secondary_independent_variable = var_2d.get_independent_variable("distance along blade")

    return primary_independent_variable, secondary_independent_variable, var_2d


def plot_bladed_results(
        primary_independent_variable: IndependentVariable, 
        secondary_independent_variable: IndependentVariable, 
        variable: Variable2D):

    #####################################
    #  Create plot and add series data  #
    #####################################

    # Get the time values as numeric array
    x_values = primary_independent_variable.get_values_as_number()

    # Get the secondary independent variable values (e.g. blade stations)
    secondary_independent_variable_values = secondary_independent_variable.get_values_as_number()

    fig, ax = pyplot.subplots(figsize=(12, 8), constrained_layout=True)

    for value in secondary_independent_variable_values:
        # Get the time series data (dependent variable) for the secondary independent variable at the value indicated
        y_values = variable.get_data_at_value(value)
        ax.plot(x_values, y_values, label=variable.name + " at " + str(value) + "m")

    ####################################
    #  Plot the data using matplotlib  #
    ####################################

    # Set up axes
    ax.set_xlim(0, x_values.max())
    ax.grid()

    # Set axis labels
    plot_x_label = primary_independent_variable.name + " [" + primary_independent_variable.si_unit + "]"
    plot_y_label = variable.si_unit
    ax.set_xlabel(plot_x_label)
    ax.set_ylabel(plot_y_label, color='black')
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))

    # Add legend
    pyplot.title(variable.parent_group_name)
    pyplot.legend(bbox_to_anchor=(1.04, 0.5), loc="center left", borderaxespad=0)

    # Render plot
    pyplot.show()


if __name__ == "__main__":
    run_script()