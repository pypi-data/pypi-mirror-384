from dnv_bladed_results import ResultsApi, Variable1D, Variable2D, UsageExamples
import dnv_bladed_results as dnvres
import numpy as np
import os

############   Bladed Results API: Get variable data (basic)   ############

# Demonstrates how to get data for:
# - 1D variables (dependent variables with one independent variable)
# - 2D variables (dependent variables with two independent variables)


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Gets data for a 1D or 2D variable without specifying the group.
    - Gets data for a 1D or 2D variable from a specific group (useful when two or more variables have the same name in a run).
    - Gets data for all 1D or 2D variables from a specific group.
    - Prints to the console the first, last, minimum, maximum, and mean value for the data sets returned above.
    """

    run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")

    # Note that we do not need to provide run or variable names with the correct case
    run_name = "powprod5mw"

    #######################
    #  1D variable tests  #
    #######################

    # Get data for one 1D variable from run
    get_data_for_1d_variable(run_directory, run_name, "rotating hub mx")

    # Get data for one 1D variable from a specific group within run
    get_data_for_1d_variable_from_specific_group(run_directory, run_name, "rotating hub mx", "hub loads: rotating gl coordinates")

    # Get data for all 1D variables from a specific group within run
    get_data_for_all_1d_variables_from_specific_group(run_directory, run_name, "hub loads: rotating gl coordinates")

    #######################
    #  2D variable tests  #
    #######################

    # Get data for one 2D variable from run
    get_data_for_2d_variable(run_directory, run_name, "tower mx", "mbr 15 end 1")

    # Get data for one 2D variable from a specific group within run
    get_data_for_2d_variable_from_specific_group(run_directory, run_name, "tower mx", "mbr 15 end 1", "tower member loads - local coordinates")

    # Get data for all 2D variables from a specific group within run
    get_data_for_all_2d_variables_from_specific_group(run_directory, run_name, "tower member loads - local coordinates")

    # Clear the cache
    ResultsApi.clear_runs()


def get_data_for_1d_variable(run_directory, run_name, variable_name):

    print("Getting data for a single 1D variable from run '" + run_name + "':")

    try:
        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)

        ############################
        #  Get data (NumPy array)  #
        ############################
   
        variable_data = run.get_variable_1d(variable_name).get_data()

        #######################
        #  Print some values  #
        #######################

        print_data(variable_data, variable_name)

    except RuntimeError as e:
        print(e)

    print()


def get_data_for_2d_variable(run_directory, run_name, variable_name, independent_variable_value):

    print("Getting data for a single 2D variable from run '" + run_name + "':")

    try:
        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)
   
        ############################
        #  Get data (NumPy array)  #
        ############################
   
        variable_data = run.get_variable_2d(variable_name).get_data_at_value(independent_variable_value)

        #######################
        #  Print some values  #
        #######################
        
        print_data(variable_data, variable_name, independent_variable_value)

    except RuntimeError as e:
        print(e)

    print()


def get_data_for_1d_variable_from_specific_group(run_directory, run_name, variable_name, group_name):

    print("Getting data for a single 1D variable from group '" + group_name + "' in run '" + run_name + "':")

    try:
        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)

        ############################
        #  Get data (NumPy array)  #
        ############################
   
        # Note, the group name is only strictly required when the run contains more than one match for the requested variable.
        # Specifying the group is still valid when there is no variable name collision, and is generally faster as it reduces file access.

        variable_data = run.get_variable_1d_from_specific_group(variable_name, group_name).get_data()

        #######################
        #  Print some values  #
        #######################

        print_data(variable_data, variable_name)

    except RuntimeError as e:
        print(e)

    print()


def get_data_for_2d_variable_from_specific_group(run_directory, run_name, variable_name, independent_variable_value, group_name):

    print("Getting data for a single 2D variable from group '" + group_name + "' in run '" + run_name + "':")

    try:
        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)

        ############################
        #  Get data (NumPy array)  #
        ############################
   
        # Note, the group name is only strictly required when the run contains more than one match for the requested variable.
        # Specifying the group is still valid when there is no variable name collision, and is generally faster as it reduces file access.

        variable_data = run.get_variable_2d_from_specific_group(variable_name, group_name).get_data_at_value(independent_variable_value)

        #######################
        #  Print some values  #
        #######################

        print_data(variable_data, variable_name, independent_variable_value)

    except RuntimeError as e:
        print(e)

    print()


def get_data_for_all_1d_variables_from_specific_group(run_directory, run_name, group_name):

    print("Getting data for all 1D variables from group '" + group_name + "' in run '" + run_name + "':")

    try:
        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)

        ###########################################
        #  Get all variables in a specific group  #
        ###########################################

        all_variables = run.get_group(group_name).get_variables_1d()

        ############################
        #  Get data (NumPy array)  #
        ############################
   
        # Note, the group name is only strictly required when the run contains more than one match for the requested variable.
        # Specifying the group is still valid when there is no variable name collision, and is generally faster as it reduces file access.
        
        variable: Variable1D
        for variable in all_variables:

            variable_data = variable.get_data()

            #######################
            #  Print some values  #
            #######################

            print_data(variable_data, variable.name)

    except RuntimeError as e:
        print(e)

    print()


def get_data_for_all_2d_variables_from_specific_group(run_directory, run_name, group_name):

    print("Getting data for all 2D variables from group '" + group_name + "' in run '" + run_name + "':")

    try:
        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)

        ###########################################
        #  Get all variables in a specific group  #
        ###########################################

        group = run.get_group(group_name)
        all_variables = group.get_variables_2d()
        independent_variable_values = group.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY).get_values_as_string()

        # Note: we can also get an independent variable using the name, for example:
        # independent_variable_values = group.get_independent_variable("location").get_values_as_string()

        ############################
        #  Get data (NumPy array)  #
        ############################
   
        # Note, the group name is only strictly required when the run contains more than one match for the requested variable.
        # Specifying the group is still valid when there is no variable name collision, and is generally faster as it reduces file access.

        variable: Variable2D
        for variable in all_variables:
            for independent_variable_value in independent_variable_values:
                variable_data = variable.get_data_at_value(independent_variable_value)

                #######################
                #  Print some values  #
                #######################

                print_data(variable_data, variable.name, independent_variable_value)
    except RuntimeError as e:
        print(e)
    
    print()


def print_data(variable_data: np.ndarray, variable_name, independent_variable_value = ""):

    if independent_variable_value != "":
        independent_variable_value = " @ " + independent_variable_value
    print(variable_name + independent_variable_value, ":\tFirst =", variable_data[0], "  Last =", variable_data[variable_data.size - 1],
          "  Min =", variable_data.min(), "  Max =", variable_data.max(), "  Mean =", variable_data.mean())


if __name__ == "__main__":
    run_script()
