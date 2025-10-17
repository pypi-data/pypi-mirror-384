from dnv_bladed_results import ResultsApi, IndependentVariable, OutputGroup1D_Float32, OutputGroup2D_Float32, UsageExamples
import dnv_bladed_results as dnvres
import numpy as np
import os
import tempfile

############   Bladed Results API: Write output group   ############

# Demonstrates how to write output groups containing:
# - 1D variables (dependent variables with one independent variable)
# - 2D variables (dependent variables with two independent variables)

# Demonstrates population of variable data using a NumPy array.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Writes 1D and 2D output groups using hard-coded data.
    - Writes 1D and 2D output groups using data from an existing output group, and applying a unit conversion before writing.
    - Writes output group using a path longer than _MAX_PATH limit on Windows.
    - Performs roundtrip validation to check the written groups contain the expected values.
    """

    output_directory = "./Output"
    source_run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")
    source_run_name = "powprod5MW"

    # Write a one-dimensional Bladed output group (a group containing only 1D variables) using hard-coded data
    write_1d_output_group_from_new_data(output_directory, "UserGroup1DTest_Basic")

    # Write a two-dimensional Bladed output group (a group containing only 2D variables) using hard-coded data
    write_2d_output_group_from_new_data(output_directory, "UserGroup2DTest_Basic")

    # Write a one-dimensional Bladed output group (a group containing only 1D variables) using data extracted and transformed from an existing output group
    write_1d_output_group_from_existing_data(source_run_directory, source_run_name, output_directory, "UserGroup1DTest_Extended")

    # Write a two-dimensional Bladed output group (a group containing only 2D variables) using data extracted and transformed from an existing output group
    write_2d_output_group_from_existing_data(source_run_directory, source_run_name, output_directory, "UserGroup2DTest_Extended")

    # Long path test, where the Bladed output group path length exceeds Windows _MAX_PATH limit
    output_run_name = "test_output_group_showing_the_new_results_api_handles_paths_that_are_longer_than_the_piffling_two_hundred_and_sixty_character_limit_on_windows"
    output_directory_temp = tempfile.gettempdir() + "/BladedResultsAPI/Output/PathWithMoreCharactersThanMaxPath/PathWithMoreCharactersThanMaxPath/PathWithMoreCharactersThanMaxPath/PathWithMoreCharactersThanMaxPath/PathWithMoreCharactersThanMaxPath/PathWithMoreCharactersThanMaxPath/PathWithMoreCharactersThanMaxPath/PathWithMoreCharactersThanMaxPath"
    write_1d_output_group_from_existing_data(source_run_directory, source_run_name, output_directory_temp, output_run_name)
    print()

    # Clear the cache
    ResultsApi.clear_runs()


def write_1d_output_group_from_new_data(output_directory, output_run_name):

    group_path = r"{0}/{1}.%999".format(output_directory, output_run_name)

    ############################
    #  Create 1D output group  #
    ############################

    # Create axis
    independent_variable = IndependentVariable("Time", "s", 0.0, 0.05)

    # Create group
    output_group_1d = OutputGroup1D_Float32(group_path, "TestGroup_Basic", "UserDefined", "Config", independent_variable)

    ######################
    #  Create some data  #
    ######################

    num_points = 100
    variable_data = np.zeros([num_points])
    for point_index in range(0, num_points - 1, 1):
        variable_data[point_index] = np.float32(point_index + 1)

    ############################
    #  Add variable with data  #
    ############################

    user_variable_name = "User variable 1D"
    si_unit = "m"
    output_group_1d.add_variable_with_data(user_variable_name, si_unit, variable_data)

    #################
    #  Write group  #
    #################
    
    success = ResultsApi.write_output(output_group_1d)
    assert success == True, "Failed to create 1D output group: " + group_path

    #####################
    #  Prove roundtrip  #
    #####################
    
    prove_1d_roundtrip(variable_data, user_variable_name, output_directory, output_run_name)

    print("\nSuccessfully created 1D group using hard-coded data, containing one variable and {0} points:\n{1}".format(
          str(independent_variable.number_of_values),
          output_group_1d.get_path()))


def write_2d_output_group_from_new_data(output_directory, output_run_name):

    group_path = r"{0}/{1}.%999".format(output_directory, output_run_name)
    
    ############################
    #  Create 2D output group  #
    ############################
    
    # Create axes
    primary_independent_variable = IndependentVariable("Time", "s", 0.0, 0.05)
    secondary_axis_intervals = ["Measurement point 1", "Measurement point 2", "Measurement point 3"]
    secondary_independent_variable = IndependentVariable("Measurement points", "N", secondary_axis_intervals)

    # Create group
    output_group_2d = OutputGroup2D_Float32(group_path, "TestGroup_Basic", "UserDefined", "Config", primary_independent_variable, secondary_independent_variable)

    ######################
    #  Create some data  #
    ######################

    num_points = 100
    num_secondary_axis_values = len(secondary_axis_intervals)
    variable_data = np.zeros([num_secondary_axis_values, num_points])
    for secondary_axis_value_index in range(0, num_secondary_axis_values - 1, 1):
        for point_index in range(0, num_points - 1, 1):
            variable_data[secondary_axis_value_index][point_index] = np.float32((secondary_axis_value_index + 1) * (point_index + 1))

    ############################
    #  Add variable with data  #
    ############################

    user_variable_name = "User variable 2D"
    si_unit = "F"
    output_group_2d.add_variable_with_data(user_variable_name, si_unit, variable_data)

    #################
    #  Write group  #
    #################
    
    success = ResultsApi.write_output(output_group_2d)
    assert success == True, "Failed to create 2D output group: " + group_path

    #####################
    #  Prove roundtrip  #
    #####################

    prove_2d_roundtrip(variable_data, user_variable_name, output_directory, output_run_name)

    print("\nSuccessfully created 2D group using hard-coded data, containing one variable, {0} secondary axis values, and {1} points:\n{2}".format(
        str(secondary_independent_variable.number_of_values),
        str(primary_independent_variable.number_of_values),
        output_group_2d.get_path()))


def write_1d_output_group_from_existing_data(source_run_directory, source_run_name, output_directory, output_run_name):

    group_path = r"{0}/{1}.%999".format(output_directory, output_run_name)

    ######################################################
    #  Create 1D output group using existing group data  #
    ######################################################

    run = ResultsApi.get_run(source_run_directory, source_run_name)

    rotating_hub_fx = run.get_variable_1d("Rotating hub Fx")
    rotating_hub_fy = run.get_variable_1d("Rotating hub Fy")
    rotating_hub_fz = run.get_variable_1d("Rotating hub Fz")
    rotating_hub_fyz = run.get_variable_1d("Rotating hub Fyz")

    # Re-use existing primary independent variable (interval axis) representing time
    independent_variable = rotating_hub_fx.get_independent_variable()

    # Create group
    output_group_1d = OutputGroup1D_Float32(group_path, "Hub forces (converted to pound-force)", "UserDefined", "Config", independent_variable)

    ######################
    #  Create some data  #
    ######################

    # Read data as NumPy array
    rotating_hub_fx_data_original = rotating_hub_fx.get_data()
    rotating_hub_fy_data_original = rotating_hub_fy.get_data()
    rotating_hub_fz_data_original = rotating_hub_fz.get_data()
    rotating_hub_fyz_data_original = rotating_hub_fyz.get_data()
    
    # Convert Newtons to pound-force
    conversion_factor = 0.2248
    rotating_hub_fx_data_modified = create_1d_variable_data(rotating_hub_fx_data_original, conversion_factor)
    rotating_hub_fy_data_modified = create_1d_variable_data(rotating_hub_fy_data_original, conversion_factor)
    rotating_hub_fz_data_modified = create_1d_variable_data(rotating_hub_fz_data_original, conversion_factor)
    rotating_hub_fyz_data_modified = create_1d_variable_data(rotating_hub_fyz_data_original, conversion_factor)

    #############################
    #  Add variables with data  #
    #############################
    
    # It doesn't actually matter that the unit is not SI - it will still work
    pound_force_units = "lbf"
    output_group_1d.add_variable_with_data(rotating_hub_fx.name, pound_force_units, rotating_hub_fx_data_modified)
    output_group_1d.add_variable_with_data(rotating_hub_fy.name, pound_force_units, rotating_hub_fy_data_modified)
    output_group_1d.add_variable_with_data(rotating_hub_fz.name, pound_force_units, rotating_hub_fz_data_modified)
    output_group_1d.add_variable_with_data(rotating_hub_fyz.name, pound_force_units, rotating_hub_fyz_data_modified)
    
    #################
    #  Write group  #
    #################
    
    success = ResultsApi.write_output(output_group_1d)
    assert success == True, "Failed to create 1D output group: " + group_path

    #####################
    #  Prove roundtrip  #
    #####################
    
    prove_1d_roundtrip(rotating_hub_fx_data_original, rotating_hub_fx.name, output_directory, output_run_name, conversion_factor)
    prove_1d_roundtrip(rotating_hub_fy_data_original, rotating_hub_fy.name, output_directory, output_run_name, conversion_factor)
    prove_1d_roundtrip(rotating_hub_fz_data_original, rotating_hub_fz.name, output_directory, output_run_name, conversion_factor)
    prove_1d_roundtrip(rotating_hub_fyz_data_original, rotating_hub_fyz.name, output_directory, output_run_name, conversion_factor)

    print("\nSuccessfully created 1D group using data transformed from an existing group, containing {0} variables and {1} points:\n{2}".format(
          str(output_group_1d.number_of_variables),
          str(independent_variable.number_of_values),
          output_group_1d.get_path()))


def write_2d_output_group_from_existing_data(source_run_directory, source_run_name, output_directory, output_run_name):

    group_path = r"{0}/{1}.%999".format(output_directory, output_run_name)
    
    ######################################################
    #  Create 2D output group using existing group data  #
    ######################################################

    run = ResultsApi.get_run(source_run_directory, source_run_name)

    tower_mx = run.get_variable_2d("Tower Mx")
    tower_my = run.get_variable_2d("Tower My")
    tower_mz = run.get_variable_2d("Tower Mz")
    tower_myz = run.get_variable_2d("Tower Myz")
    
    # Re-use existing primary independent variable (interval axis) representing time
    primary_independent_variable = tower_mx.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_PRIMARY)

    # Re-use existing secondary independent variable (axis with string labels) representing measurement locations
    secondary_independent_variable = tower_mx.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY)

    # Create group
    output_group_2d = OutputGroup2D_Float32(group_path, "Tower moments (converted to foot-pounds)", "UserDefined", "Config", primary_independent_variable, secondary_independent_variable)

    ######################
    #  Create some data  #
    ######################

    # Read data as NumPy array
    tower_mx_data_original = tower_mx.get_data()
    tower_my_data_original = tower_my.get_data()
    tower_mz_data_original = tower_mz.get_data()
    tower_myz_data_original = tower_myz.get_data()
    
    # Convert Newtons to pound-force
    conversion_factor = 0.7376
    tower_mx_data_modified = create_2d_variable_data(tower_mx_data_original, conversion_factor)
    tower_my_data_modified = create_2d_variable_data(tower_my_data_original, conversion_factor)
    tower_mz_data_modified = create_2d_variable_data(tower_mz_data_original, conversion_factor)
    tower_myz_data_modified = create_2d_variable_data(tower_myz_data_original, conversion_factor)

    #############################
    #  Add variables with data  #
    #############################

    foot_pounds_units = "lbft"
    output_group_2d.add_variable_with_data(tower_mx.name, foot_pounds_units, tower_mx_data_modified)
    output_group_2d.add_variable_with_data(tower_my.name, foot_pounds_units, tower_my_data_modified)
    output_group_2d.add_variable_with_data(tower_mz.name, foot_pounds_units, tower_mz_data_modified)
    output_group_2d.add_variable_with_data(tower_myz.name, foot_pounds_units, tower_myz_data_modified)

    #################
    #  Write group  #
    #################
    
    success = ResultsApi.write_output(output_group_2d)
    assert success == True, "Failed to create 2D output group: " + group_path

    #####################
    #  Prove roundtrip  #
    #####################

    prove_2d_roundtrip(tower_mx_data_original, tower_mx.name, output_directory, output_run_name, conversion_factor)
    prove_2d_roundtrip(tower_my_data_original, tower_my.name, output_directory, output_run_name, conversion_factor)
    prove_2d_roundtrip(tower_mz_data_original, tower_mz.name, output_directory, output_run_name, conversion_factor)
    prove_2d_roundtrip(tower_myz_data_original, tower_myz.name, output_directory, output_run_name, conversion_factor)

    print("\nSuccessfully created 2D group using data transformed from an existing group, containing {0} variables, {1} secondary axis values, and {2} points:\n{3}".format(
        str(output_group_2d.number_of_variables),
        str(secondary_independent_variable.number_of_values),
        str(primary_independent_variable.number_of_values),
        output_group_2d.get_path()))


def create_1d_variable_data(data_original, factor: float):
   
    num_points = len(data_original)

    # Copy original array, and multiply every value by 2
    data_modified = np.array(data_original, dtype=np.float32, copy=True)

    for point_index in range(0, num_points, 1):
        data_modified[point_index] = (data_modified[point_index] * factor)

    return data_modified


def prove_1d_roundtrip(data_original, user_variable_name, output_directory, output_run_name, factor: float=1.0):

    run = ResultsApi.get_run(output_directory, output_run_name)
    assert run.calculation_type == dnvres.CALCULATION_TYPE_USER_DEFINED

    data_roundtrip = run.get_variable_1d(user_variable_name).get_data()

    point_index = 0
    for val in data_original:
        assert (np.float32(val * factor)) == data_roundtrip[point_index], "Expected value equality on data roundtrip: array index = " + str(point_index)
        point_index = point_index + 1


def create_2d_variable_data(data_original, factor: float):

    num_secondary_axis_vals = len(data_original)
    num_points = len(data_original[0])

    # Copy original array, and multiply every value by 2
    data_modified = np.array(data_original, dtype=np.float32, copy=True)

    for secondary_axis_value_index in range(0, num_secondary_axis_vals, 1):
        for point_index in range(0, num_points, 1):
            data_modified[secondary_axis_value_index][point_index] = data_original[secondary_axis_value_index][point_index] * factor

    return data_modified


def prove_2d_roundtrip(data_original, user_variable_name, output_directory, output_run_name, factor: float=1.0):

    num_secondary_axis_vals = len(data_original)

    run = ResultsApi.get_run(output_directory, output_run_name)
    assert run.calculation_type == dnvres.CALCULATION_TYPE_USER_DEFINED

    data_roundtrip = run.get_variable_2d(user_variable_name).get_data()

    point_index = 0
    for secondary_axis_value_index in range(0, num_secondary_axis_vals, 1):
        for val in data_original[secondary_axis_value_index]:
            assert (np.float32(val * factor)) == (data_roundtrip[secondary_axis_value_index][point_index]), "Expected value equality on data roundtrip: secondary axis index = {0} point index = {1}".format(str(secondary_axis_value_index), str(point_index))
            point_index = point_index + 1
        point_index = 0


if __name__ == "__main__":
    run_script()
