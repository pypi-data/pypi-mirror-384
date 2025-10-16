from dnv_bladed_results import ResultsApi, IndependentVariable, UsageExamples
import dnv_bladed_results as dnvres
import os

############   Bladed Results API: Get variable metadata   ############

# Demonstrates how to get metadata data for:
# - 1D variables (dependent variables with one independent variable)
# - 2D variables (dependent variables with two independent variables)


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Gets 1D and 2D dependent variables and prints metadata to the console.
    - Gets independent variables and prints metadata to the console.
    """

    run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")
    run_name = "powprod5mw"

    # 1D variable
    display_variable_info(run_directory, run_name, "Rotating hub Mx")

    # 2D variable
    display_variable_info(run_directory, run_name, "Tower Mx")

    # Clear the cache
    ResultsApi.clear_runs()


def display_variable_info(run_directory, run_name, variable_name):

    try:

        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)

        ###############################
        #  Display variable metadata  #
        ###############################
    
        # Get 1D or 2D variable depending on which type is found
        if run.contains_variable_1d(variable_name):
            variable = run.get_variable_1d(variable_name)
        elif run.contains_variable_2d(variable_name):
            variable = run.get_variable_2d(variable_name)
        else:
            print("\nRun does not contain variable with name '" + variable_name + "'!")
            return

        #######################
        #  Basic information  #
        #######################

        print("\nVariable name is '" + variable.name + "'")
        print("Variable quantity code is '" + variable.quantity_code + "'")
        print("Variable SI unit is '" + variable.si_unit + "'")
        if (run.is_turbine_simulation):
            print("Simulation length = " + str(variable.time_domain_simulation_length) + " seconds")
            print("Start time = " + str(variable.time_domain_simulation_output_start_time) + " seconds")
            print("Timestep = " + str(variable.time_domain_simulation_output_timestep) + " seconds")

        ######################
        #  Data information  #
        ######################

        print("Data contains " + str(variable.data_point_count) + " points")

        if variable.data_type == dnvres.VARIABLE_DATA_TYPE_FLOAT32:
            # Note: NumPy single precision appears to be slightly lower resolution than native single precision, whereas double precision matches exactly
            print("Data is single precision")
        else:
            print("Data is double precision")

        if variable.data_format == dnvres.VARIABLE_DATA_FORMAT_BINARY:
            print("Data format is binary")
        else:
            print("Data format is ASCII")

        ######################################
        #  Independent variable information  #
        ######################################
        
        print("Variable has " + str(variable.number_of_independent_variables) + " independent variable(s)")
        ind_vars = variable.get_independent_variables()
        ind_var: IndependentVariable
        i = 1
        for ind_var in ind_vars:
            print("    Independent variable " + str(i) + " name is '" + ind_var.name + "'")
            print("    Independent variable " + str(i) + " unit is '" + ind_var.si_unit + "'")
            if ind_var.axis_type == dnvres.AXIS_TYPE_INTERVAL:
                print("    Independent variable " + str(i) + " axis type is interval")
            elif ind_var.axis_type == dnvres.AXIS_TYPE_LABELLED_STRING:
                print("    Independent variable " + str(i) + " axis type is labelled string")
                print("    Independent variable " + str(i) + " values:" + str(ind_var.get_values_as_string()))
            else:
                print("    Independent variable " + str(i) + " axis type is labelled number")
                print("    Independent variable " + str(i) + " values:" + str(ind_var.get_values_as_string()))
            i = i + 1

        ##############################
        #  Parent group information  #
        ##############################

        print("Variable parent group name is '" + variable.parent_group_name + "'")
        print("Variable parent group path is '" + variable.parent_group_header_file_full_path + "'")
        print("Variable parent group number is", variable.parent_group_number)
        print()

    except RuntimeError as e:
        print(e)


if __name__ == "__main__":
    run_script()
