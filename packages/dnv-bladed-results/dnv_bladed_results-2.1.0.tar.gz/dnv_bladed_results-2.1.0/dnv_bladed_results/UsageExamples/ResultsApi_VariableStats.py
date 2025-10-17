from dnv_bladed_results import ResultsApi, UsageExamples
import dnv_bladed_results as dnvres
import os

############   Bladed Results API: Get basic statistics from variables   ############

# Demonstrates how to get basic statistics from:
# - 1D variables (dependent variables with one independent variable)
# - 2D variables (dependent variables with two independent variables)


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Gets 1D and 2D variables from an example run.
    - Prints basic statistics to the console, including min, max, mean, and contemporaneous values.
    """

    run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")
    run_name = "powprod5mw"

    # Print max value of 1D variable data
    display_1d_variable_basic_stats(run_directory, run_name, "Rotating hub Mx", "Rotating hub My")

    # Print max value of 2D variable data
    display_2d_variable_basic_stats(run_directory, run_name, "Tower Mx", "Tower My")

    # Clear the cache
    ResultsApi.clear_runs()


def display_1d_variable_basic_stats(run_directory, run_name, variable_name, variable_name_for_contemporaneous_stats):

    ################################
    #  Get a specific run by name  #
    ################################

    run = ResultsApi.get_run(run_directory, run_name)
    
    try:
        ##############################
        #  Get 1D variable from run  #
        ##############################

        var_1d = run.get_variable_1d(variable_name)
        print("\nStats for variable '" + var_1d.name + "':")

        ##########################################################
        #  Get independent variables for the dependent variable  #
        ##########################################################
        
        # Primary independent variable
        primary_independent_variable = var_1d.get_independent_variable()
        print("Primary independent variable: Name: " + primary_independent_variable.name + "; unit: " + primary_independent_variable.si_unit)

        #######################
        #  Print basic stats  #
        #######################

        print("Minimum value:", var_1d.get_minimum())
        print("Maximum value:", var_1d.get_maximum())
        print("Mean value:", var_1d.get_mean())

        # Get min and max contemporaneous values
        print("Minimum contemporaneous value for variable '" + variable_name_for_contemporaneous_stats + "':", var_1d.get_minimum_contemporaneous(variable_name_for_contemporaneous_stats))
        print("Maximum contemporaneous value for variable '" + variable_name_for_contemporaneous_stats + "':", var_1d.get_maximum_contemporaneous(variable_name_for_contemporaneous_stats))
        
        # Data is returned as a NumPy array allowing use of any NumPy function, e.g.:
        min = var_1d.get_data().min()

    except RuntimeError as e:
        print(e)


def display_2d_variable_basic_stats(run_directory, run_name, variable_name, variable_name_for_contemporaneous_stats):

    ################################
    #  Get a specific run by name  #
    ################################

    run = ResultsApi.get_run(run_directory, run_name)
    
    try:
        ##############################
        #  Get 2D variable from run  #
        ##############################

        var_2d = run.get_variable_2d(variable_name)
        print("\nStats for variable '" + var_2d.name + "':")

        ##########################################################
        #  Get independent variables for the dependent variable  #
        ##########################################################

        # Primary independent variable
        # Get an independent variable using the INDEPENDENT_VARIABLE_ID key
        primary_independent_variable = var_2d.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_PRIMARY)

        # Note: we can also get an independent variable using the name, for example:
        # primary_independent_variable = var_2d.get_independent_variable("time")

        print("Primary independent variable: Name: " + primary_independent_variable.name + "; unit: " + primary_independent_variable.si_unit)

        # Secondary independent variable
        # Get an independent variable using the INDEPENDENT_VARIABLE_ID key
        secondary_independent_variable = var_2d.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY)

        # Note: we can also get an independent variable using the name, for example:
        # secondary_independent_variable = var_2d.get_independent_variable("location")

        print("Secondary independent variable: Name: " + secondary_independent_variable.name + "; unit: " + secondary_independent_variable.si_unit)
    
        # Get the independent variable values
        secondary_independent_variable_values = secondary_independent_variable.get_values_as_string()

        #################################################################
        #  Print basic stats for each independent variable data series  #
        #################################################################

        for secondary_independent_variable_value in secondary_independent_variable_values:
            print("Minimum value @ " + secondary_independent_variable_value + ":", var_2d.get_minimum_at_value(secondary_independent_variable_value))
            print("Maximum value @ " + secondary_independent_variable_value + ":", var_2d.get_maximum_at_value(secondary_independent_variable_value))
            print("Mean value @ " + secondary_independent_variable_value + ":", var_2d.get_mean_at_value(secondary_independent_variable_value))
            
            # Get min and max contemporaneous values
            print("Minimum contemporaneous value for variable '" + variable_name_for_contemporaneous_stats + "' @ " + secondary_independent_variable_value + ":", var_2d.get_minimum_contemporaneous_at_value(variable_name_for_contemporaneous_stats, secondary_independent_variable_value))
            print("Maximum contemporaneous value for variable '" + variable_name_for_contemporaneous_stats + "' @ " + secondary_independent_variable_value + ":", var_2d.get_maximum_contemporaneous_at_value(variable_name_for_contemporaneous_stats, secondary_independent_variable_value))
            print()

            # Data is returned as a NumPy array allowing use of any NumPy function, e.g.:
            min = var_2d.get_data_at_value(secondary_independent_variable_value).min()
            
    except RuntimeError as e:
        print(e)


if __name__ == "__main__":
    run_script()
