from dnv_bladed_results import ResultsApi, UsageExamples
import os
import scipy.io
from pathlib import Path

############   Bladed Results API: Export data to Matlab (.mat) file format   ############

# Demonstrates how to export variables to a Matlab data file.

# This example requires the scipy library, available via pip.  It has been tested with scipy >= 1.13.1.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Exports data for all variables in a group to a Matlab data file.
    - Exports data for selected 1D and 2D variables to the same Matlab data file.
    """

    # Create output directory
    output_directory = "./Output"
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    source_run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")
    source_run_name = "powprod5MW"

    # 1D group
    export_all_variables_in_group(source_run_directory, source_run_name, "Hub loads: rotating GL coordinates", os.path.join(output_directory, "Hub_Loads.mat").replace("\\","/"))

    # 2D group - numeric secondary axis
    export_all_variables_in_group(source_run_directory, source_run_name, "Blade 1 Loads: Principal elastic axes", os.path.join(output_directory, "Blade_1_Loads.mat").replace("\\","/"))

    # 2D group - labelled string secondary axis
    export_all_variables_in_group(source_run_directory, source_run_name, "Tower member loads - local coordinates", os.path.join(output_directory, "Tower_Member_Loads.mat").replace("\\","/"))

    # 1D + 2D variables
    export_selected_variables(source_run_directory, source_run_name, "Rotating hub Mx", "Tower Mx", os.path.join(output_directory, "RotatingHubMx_TowerMx.mat").replace("\\","/"))

    # Clear the cache
    ResultsApi.clear_runs()


def export_all_variables_in_group(source_run_directory, source_run_name, source_group_name, mat_file_path):

    ################################
    #  Get a specific run by name  #
    ################################

    run = ResultsApi.get_run(source_run_directory, source_run_name)

    ##################################################
    #  Get the group containing variables to export  #
    ##################################################

    group = run.get_group(source_group_name)

    ##################################
    #  Get variables from the group  #
    ##################################

    variable_names_in_group = group.get_variable_names()

    try:
        
        ######################################
        #  Get variable data as NumPy array  #
        ######################################

        variable_name_to_data = dict()
        for variable_name in variable_names_in_group:
            if group.is_one_dimensional:
                variable_data = group.get_variable_1d(variable_name).get_data()
            else:
                variable_data = group.get_variable_2d(variable_name).get_data()
            variable_name_to_data[variable_name]=variable_data
            
        ################################
        #  Export data as Matlab format  #
        ################################

        scipy.io.savemat(mat_file_path, variable_name_to_data)

        print("\nSuccessfully exported all variables in group '" + source_group_name + "' to " + mat_file_path)
            
        #####################
        #  Prove roundtrip  #
        #####################

        result_file = scipy.io.loadmat(mat_file_path)

        for variable_name in variable_names_in_group:
            variable_data = variable_name_to_data[variable_name]

            if group.is_one_dimensional:
                numpy_1d_arrays_equal(variable_data, result_file.get(variable_name)[0])
            else:
                numpy_2d_arrays_equal(variable_data, result_file.get(variable_name))
        
        print("Successfully imported all variables from '" + mat_file_path + "' and checked equality with source data")

    except RuntimeError as e:
        print(e)


def export_selected_variables(source_run_directory, source_run_name, variable_name_1d, variable_name_2d, mat_file_path):

    ################################
    #  Get a specific run by name  #
    ################################

    run = ResultsApi.get_run(source_run_directory, source_run_name)
    
    try:        
        ######################################
        #  Get variable data as NumPy array  #
        ######################################

        variable_data_1d = run.get_variable_1d(variable_name_1d).get_data()
        variable_data_2d = run.get_variable_2d(variable_name_2d).get_data()

        ################################
        #  Save data as Matlab format  #
        ################################

        scipy.io.savemat(mat_file_path, {variable_name_1d: variable_data_1d, variable_name_2d: variable_data_2d})

        print("\nSuccessfully exported 1D variable '" + variable_name_1d + "' and 2D variable '" + variable_name_2d + "' to " + mat_file_path)

        #####################
        #  Prove roundtrip  #
        #####################

        result_file = scipy.io.loadmat(mat_file_path)

        numpy_1d_arrays_equal(variable_data_1d, result_file.get(variable_name_1d)[0])
        numpy_2d_arrays_equal(variable_data_2d, result_file.get(variable_name_2d))

        print("Successfully imported all variables from '" + mat_file_path + "' and checked equality with source data\n")

    except RuntimeError as e:
        print(e)


# Support functions

def numpy_1d_arrays_equal(expected, actual):
    # Assert 1D variable point count equality
    expected_num_points = len(expected)
    assert expected_num_points == len(actual)

    # Assert 1D variable value equality
    for point_index in range(0, expected_num_points, 1):
        assert expected[point_index] == actual[point_index]


def numpy_2d_arrays_equal(expected, actual):
    # Assert 2D variable point count equality
    expected_num_secondary_axis_values = len(expected)
    assert expected_num_secondary_axis_values == len(actual)

    # Assert 2D variable value equality
    for secondary_axis_value_index in range(0, expected_num_secondary_axis_values, 1):
        numpy_1d_arrays_equal(expected[secondary_axis_value_index], actual[secondary_axis_value_index])


if __name__ == "__main__":
    run_script()
