from dnv_bladed_results import ResultsApi, Run, UsageExamples
import dnv_bladed_results as dnvres
import os

############   Bladed Results API: Basic operations   ############

# Demonstrates how to accomplish a range of basic tasks such as getting runs, variables, and data.


# A note about 1D and 2D dependent variables:
#
# A (dependent) variable is calculated as the result of changing one or more independent variables.
# Dependent variables may be one-dimensional (1D) or two-dimensional (2D).
#
# - The value of a one-dimensional variable is determined by one independent variable, known as the primary independent variable.
#
#   Example: in a time series turbine simulation, 1D variable `Rotor speed` depends on primary independent variable `Time`. 
#   The data for `Rotor speed` is a one-dimensional array indexed on time.
#
# - The value of a two-dimensional variable is determined by two independent variables, known as primary and secondary independent variables.
#
#   Example: In a time series turbine simulation with a multi-member tower, 2D variable `Tower Mx` depends on primary independent variable `Time`, 
#   and secondary independent variable `Location`.
#   The data for `Tower Mx` is a two-dimensional array indexed on member location and time.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Loads an example run.
    - Fetches groups and variables from the run.
    - Fetches independent variables from a group and from a variable.
    - Fetches data from variables, emphasising the differences between 1D and 2D variables.
    - Fetches tower and blade data from the run.
    """

    variable_1d_name = "brake speed"
    variable_1d_name_non_unique = "rotor speed"
    group_1d_name = "drive train variables"
    variable_2d_name = "support structure rotational deflection about x"
    group_2d_name = "support structure deflections"

    runs_root_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/PP")
    run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")
    run_name = "powprod5MW"
    run = ResultsApi.get_run(run_directory, run_name)

    get_runs(run_directory, run_name, runs_root_directory)
    get_variables_from_run(run, variable_1d_name, variable_2d_name)
    get_variable_from_run_specific_group(run, variable_1d_name_non_unique, group_1d_name)
    get_groups(run, group_1d_name, group_2d_name)
    get_variables_from_group(run, group_1d_name, variable_1d_name, group_2d_name, variable_2d_name)
    get_independent_variables_from_variable(run, variable_1d_name, variable_2d_name)
    get_independent_variables_from_group(run, group_1d_name, group_2d_name)
    get_data_from_variables(run, variable_1d_name, variable_2d_name)

    # The following examples demonstrate how to read data for specific tower members and blade stations:

    tower_variable_name = "tower mx"
    tower_member_name = "mbr 15 end 1"
    blade_variable_name = "blade 1 mx (principal elastic axes)"
    blade_station_location = 28.5
    get_tower_and_blade_data(run, tower_variable_name, tower_member_name, blade_variable_name, blade_station_location)

    tower_group_name = "tower member loads - local coordinates"
    tower_member_independent_variable_name = "location"
    blade_group_name = "blade 1 loads: principal elastic axes"
    blade_station_independent_variable_name = "distance along blade"
    time_independent_variable_name = "time"
    get_tower_and_blade_metadata(run, tower_group_name, tower_member_independent_variable_name, blade_group_name, blade_station_independent_variable_name, time_independent_variable_name)

    # Clear the cache
    ResultsApi.clear_runs()


##########
#  Runs  #
##########

def get_runs(run_directory, run_name, runs_root_directory):

    # Get a run from the specified directory with specified run name
    run = ResultsApi.get_run(run_directory, run_name)

    # Get all runs recursively from directory tree, starting in the specified directory
    runs = ResultsApi.get_runs(runs_root_directory)


############
#  Groups  #
############

def get_groups(run: Run, group_1d_name, group_2d_name):

    # Get a 1D group from a run
    group_1d = run.get_group(group_1d_name)

    # Get a 2D group from a run
    group_2d = run.get_group(group_2d_name)


###############
#  Variables  #
###############

def get_variables_from_run(run: Run, variable_1d_name, variable_2d_name):

    # Get a 1D variable from a run using variable name
    var_1d = run.get_variable_1d(variable_1d_name)

    # Get a 2D variable from a run using variable name
    var_2d = run.get_variable_2d(variable_2d_name)


def get_variable_from_run_specific_group(run: Run, variable_1d_name_non_unique, group_1d_name):

    # Get a 1D variable from a run using variable name and group name
    # It is only necessary to specify the group name when the same variable name appears in more than one group in the run
    # For example, variable `Rotor speed` is included in both the `Drive train variables` and `Summary information` groups
    # The Results API will raise an exception if the requested variable cannot be identified uniquely in the run.
    var_1d = run.get_variable_1d_from_specific_group(variable_1d_name_non_unique, group_1d_name)


def get_variables_from_group(run: Run, group_1d_name, variable_1d_name, group_2d_name, variable_2d_name):

    # Variables may also be requested from a group. Group and Run objects expose the same get_variable functions.

    # Get a 1D variable from a group using variable name
    var_1d = run.get_group(group_1d_name).get_variable_1d(variable_1d_name)

    # Get a 2D variable from a group using variable name
    var_2d = run.get_group(group_2d_name).get_variable_2d(variable_2d_name)

    # Get all 1D variables from a group
    vars_1d = run.get_group(group_1d_name).get_variables_1d()

    # Get all 2D variables from a group
    vars_2d = run.get_group(group_2d_name).get_variables_2d()


###########################
#  Independent Variables  #
###########################

def get_independent_variables_from_group(run: Run, group_1d_name, group_2d_name):

    # Primary independent variable
    # Get the primary independent variable from a 1D group using independent variable identifier
    primary_ind_var_1d = run.get_group(group_1d_name).get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_PRIMARY)

    # Get the primary independent variable from a 2D group using independent variable identifier
    primary_ind_var_2d = run.get_group(group_2d_name).get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_PRIMARY)

    # Secondary independent variable
    # Get the secondary independent variable from a 2D group using independent variable identifier
    secondary_ind_var_2d = run.get_group(group_2d_name).get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY)


def get_independent_variables_from_variable(run: Run, variable_1d_name, variable_2d_name):

    # Primary independent variable
    # Get the primary independent variable from a 1D group using independent variable identifier
    primary_ind_var_1d = run.get_variable_1d(variable_1d_name).get_independent_variable()

    # Get the primary independent variable from a 2D group using independent variable identifier
    primary_ind_var_2d = run.get_variable_2d(variable_2d_name).get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_PRIMARY)

    # Secondary independent variable
    # Get the secondary independent variable from a 2D group using independent variable identifier
    secondary_ind_var_2d = run.get_variable_2d(variable_2d_name).get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY)


###################
#  Variable Data  #
###################

def get_data_from_variables(run: Run, variable_1d_name, variable_2d_name):

    # Get a 1D and 2D variables
    var_1d = run.get_variable_1d(variable_1d_name)
    var_2d = run.get_variable_2d(variable_2d_name)

    # Get data from a 1D variable
    var_1d_data = var_1d.get_data()

    # See blade/tower example for how to get data for a specific value of the secondary independent variable

    # Get data from a 2D variable for a specific index of the secondary independent variable
    var_2d_data = var_2d.get_data_at_index(0)

    # Get data from a 2D variable (all independent variable values)
    var_2d_all_data = var_2d.get_data()


def get_tower_and_blade_data(run: Run, tower_variable_name, tower_member_name, blade_variable_name, blade_station_location):

    # Get blade and tower variables
    tower_variable = run.get_variable_2d(tower_variable_name)
    blade_variable = run.get_variable_2d(blade_variable_name)

    # Get tower data (string independent variable value)
    tower_member_data = tower_variable.get_data_at_value(tower_member_name)
    print("\nTower member data:", tower_member_data)

    # Get blade data (numeric independent variable value)
    blade_station_data = blade_variable.get_data_at_value(blade_station_location)
    print("\nBlade station data:", blade_station_data)

    # Get data from a 2D variable (all independent variable values)
    blade_variable_all_data = blade_variable.get_data()


#######################
#  Variable Metadata  #
#######################

def get_tower_and_blade_metadata(run: Run, tower_group_name, tower_member_independent_variable_name, blade_group_name, blade_station_independent_variable_name, time_independent_variable_name):

    # Tower
    # Get variable names
    tower_group = run.get_group(tower_group_name)
    tower_variable_names = tower_group.get_variable_names()
    print("\nTower variables:", tower_variable_names)

    # Get time values (numeric primary independent variable)
    time_values = tower_group.get_independent_variable(time_independent_variable_name).get_values_as_number()
    
    # Get member names (string secondary independent variable)
    tower_member_names = tower_group.get_independent_variable(tower_member_independent_variable_name).get_values_as_string()
    print("\nTower member names:", tower_member_names)
    
    # Blade
    # Get variable names
    blade_group = run.get_group(blade_group_name)
    blade_variable_names = blade_group.get_variable_names()
    print("\nBlade variables:", blade_variable_names)

    # Get time values (numeric primary independent variable)
    time_values = blade_group.get_independent_variable(time_independent_variable_name).get_values_as_number()

    # Get blade station values (numeric secondary independent variable)
    blade_station_values = blade_group.get_independent_variable(blade_station_independent_variable_name).get_values_as_number()
    print("\nBlade station values:", blade_station_values)


if __name__ == "__main__":
    run_script()