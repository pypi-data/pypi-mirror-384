from dnv_bladed_results import ResultsApi, Group, IndependentVariable, UsageExamples
import dnv_bladed_results as dnvres
import os
import h5py
from pathlib import Path

############   Bladed Results API: Export data to HDF5 (.h5) file format   ############

# Demonstrates how to export variables to an HDF5 data file.

# This example requires the h5py library, available via pip.  It has been tested with h5py >= 3.14.0.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Exports data for all variables in every group in a run to an HDF5 data file.
    - Exports data for all variables in a group to an HDF5 data file.
    - Exports data for selected 1D and 2D variables to the same HDF5 data file.
    """

    # Create output directory
    output_directory = "./Output"
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    source_run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")
    source_run_name = "powprod5MW"

    # 1D + 2D groups
    export_all_groups_in_run(source_run_directory, source_run_name, os.path.join(output_directory, "powprod5MW.h5").replace("\\","/"))

    # 1D group
    export_all_variables_in_group(source_run_directory, source_run_name, "Hub loads: rotating GL coordinates", os.path.join(output_directory, "Hub_Loads.h5").replace("\\","/"))

    # 2D group - numeric secondary axis
    export_all_variables_in_group(source_run_directory, source_run_name, "Blade 1 Loads: Principal elastic axes", os.path.join(output_directory, "Blade_1_Loads.h5").replace("\\","/"))

    # 2D group - labelled string secondary axis
    export_all_variables_in_group(source_run_directory, source_run_name, "Tower member loads - local coordinates", os.path.join(output_directory, "Tower_Member_Loads.h5").replace("\\","/"))

    # 1D + 2D variable data
    export_selected_variables(source_run_directory, source_run_name, "Rotating hub Mx", "Tower Mx", os.path.join(output_directory, "RotatingHubMx_TowerMx.h5").replace("\\","/"))

    # Clear the cache
    ResultsApi.clear_runs()


def export_all_groups_in_run(source_run_directory, source_run_name, h5_file_path):

    ################################
    #  Get a specific run by name  #
    ################################

    run = ResultsApi.get_run(source_run_directory, source_run_name)
    all_groups = run.get_groups()

    try:
        
        #########################################################
        #  Get variable data as NumPy array and export as HDF5  #
        #########################################################

        with h5py.File(h5_file_path, 'w') as h5File:

            group: Group
            for group in all_groups:
                variable_names_in_group = group.get_variable_names()
                h5_variables_group = h5File.create_group(group.name)
            
                for variable_name in variable_names_in_group:
                    if group.is_one_dimensional:
                        variable_data = group.get_variable_1d(variable_name).get_data()
                    else:
                        variable_data = group.get_variable_2d(variable_name).get_data()

                    # Add variable data
                    h5_variables_group.create_dataset(variable_name, data=variable_data)
                
                # Create axes
                create_axes(h5File, h5_variables_group, group, variable_names_in_group)

        print("\nSuccessfully exported all groups in run '" + source_run_name + "' to " + h5_file_path)

    except RuntimeError as e:
        print(e)

def export_all_variables_in_group(source_run_directory, source_run_name, group_name, h5_file_path):

    ################################
    #  Get a specific run by name  #
    ################################

    run = ResultsApi.get_run(source_run_directory, source_run_name)
    
    ##################################################
    #  Get the group containing variables to export  #
    ##################################################

    group = run.get_group(group_name)

    ##################################
    #  Get variables from the group  #
    ##################################

    variables_names_in_group = group.get_variable_names()

    try:
        
        #########################################################
        #  Get variable data as NumPy array and export as HDF5  #
        #########################################################

        with h5py.File(h5_file_path, 'w') as h5File:
            h5_variables_group = h5File.create_group(group.name)
            
            for variable_name in variables_names_in_group:
                if group.is_one_dimensional:
                    variable_data = group.get_variable_1d(variable_name).get_data()
                else:
                    variable_data = group.get_variable_2d(variable_name).get_data()

                # Add variable data
                h5_variables_group.create_dataset(variable_name, data=variable_data)

            # Create axes
            create_axes(h5File, h5_variables_group, group, variables_names_in_group)

        print("\nSuccessfully exported all variables in group '" + group_name + "' to " + h5_file_path)

        #####################
        #  Prove roundtrip  #
        #####################

        with h5py.File(h5_file_path, 'r') as h5_file:
            for variable_name in variables_names_in_group:
                if group.is_one_dimensional:
                    numpy_1d_arrays_equal(group.get_variable_1d(variable_name).get_data(), h5_file[group.name + "/" + variable_name][:])
                else:
                    numpy_2d_arrays_equal(group.get_variable_2d(variable_name).get_data(), h5_file[group.name + "/" + variable_name][:])
        
        print("Successfully imported all variables from '" + h5_file_path + "' and checked equality with source data")

    except RuntimeError as e:
        print(e)


def export_selected_variables(source_run_directory, source_run_name, variable_name_1d, variable_name_2d, h5_file_path):

    ################################
    #  Get a specific run by name  #
    ################################

    run = ResultsApi.get_run(source_run_directory, source_run_name)
    
    try:        
        #############################
        #  Get data as NumPy array  #
        #############################
        
        variable_data_1d = run.get_variable_1d(variable_name_1d).get_data()
        variable_data_2d = run.get_variable_2d(variable_name_2d).get_data()

        #########################
        #  Export data as HDF5  #
        #########################

        with h5py.File(h5_file_path, 'w') as hf:
            hf.create_dataset(variable_name_1d, data=variable_data_1d)
            hf.create_dataset(variable_name_2d, data=variable_data_2d)
            
        print("\nSuccessfully exported 1D variable '" + variable_name_1d + "' and 2D variable '" + variable_name_2d + "' to " + h5_file_path)

        #####################
        #  Prove roundtrip  #
        #####################

        with h5py.File(h5_file_path, 'r') as hf:
            numpy_1d_arrays_equal(variable_data_1d, hf[variable_name_1d][:])
            numpy_2d_arrays_equal(variable_data_2d, hf[variable_name_2d][:])

        print("Successfully imported all variables from '" + h5_file_path + "' and checked equality with source data\n")

    except RuntimeError as e:
        print(e)


# Support functions

def create_axes(h5_file: h5py.File, h5_variables_group: h5py.Group, group: Group, variable_names_in_group):
    h5_axes_group = h5_variables_group.create_group("Axes")

    axis_index = 0
    independent_variables_in_group = group.get_independent_variables()
    independent_variable: IndependentVariable
    for independent_variable in independent_variables_in_group:
        independent_variable_name = independent_variable.name
        if independent_variable.axis_type == dnvres.AXIS_TYPE_LABELLED_STRING:
            values = independent_variable.get_values_as_string()
            values_ascii = [n.encode("ascii", "ignore") for n in values]
            h5_axes_group.create_dataset(independent_variable_name, data=values_ascii)
        else:
            h5_axes_group.create_dataset(independent_variable_name, data=independent_variable.get_values_as_number())
        h5_file[h5_axes_group.name + "/" + independent_variable_name].make_scale(independent_variable_name + " [" + independent_variable.si_unit + "]")
        
        for variable_name in variable_names_in_group:
            h5_file[h5_variables_group.name + "/" + variable_name].dims[axis_index].attach_scale(h5_file[h5_axes_group.name + "/" + independent_variable_name])
        axis_index = axis_index + 1


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
