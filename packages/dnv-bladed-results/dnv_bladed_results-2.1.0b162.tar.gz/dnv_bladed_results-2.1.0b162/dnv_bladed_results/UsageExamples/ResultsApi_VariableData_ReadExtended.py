from dnv_bladed_results import ResultsApi, UsageExamples
import dnv_bladed_results as dnvres
import os

############   Bladed Results API: Get variable data (extended)   ############

# Demonstrates how to specify a data type to use when reading 1D and 2D variables.
# Demonstrates how to get data for 2D variables (dependent variables with two independent variables) for specific secondary axis values.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Gets data for 1D and 2D variables, specifying the target data type.
    - Get data for 2D variables for specific independent variable values.
    - Prints to the console the first and last value for the data sets returned above.
    """

    run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo/powprod5MW")

    # Note that we do not need to provide run or variable names with the correct case
    run_name = "powprod5mw"

    # Read the same data twice, but using a different precision setting each time
    data_type_specifiers = [[dnvres.DATA_TYPE_SPECIFIER_READ_AS_SERIALISED_TYPE, "serialised"], [dnvres.DATA_TYPE_SPECIFIER_READ_AS_FLOAT64, "double"]]
    for type_specifier in data_type_specifiers:
        
        # Specify data type precision
        ResultsApi.CacheSettings.data_type_for_reading = type_specifier[0]

        print("\n*** Reading data as " + type_specifier[1] + " precision ***")

        # Note that we do not need to provide run or variable names with the correct case
        
        # 1D dependent variable
        get_data_for_1d_variable(run_directory, run_name, "rotating hub mx")
        
        # 2D dependent variable, secondary independent variable with string values
        get_data_for_2d_variable(run_directory, run_name, "tower mx")

        # 2D dependent variable, secondary independent variable with numeric values
        get_data_for_2d_variable(run_directory, run_name, "blade 1 mx (principal elastic axes)")

        # Unload data before re-reading as a new type
        ResultsApi.clear_runs()

    # 2D variable: Get data for a specified secondary axis value - string axis (2D variable)
    get_data_for_2d_variable_at_specific_independent_variable_value(run_directory, run_name, "tower mx", "Mbr 6 End 1", 2)

    # 2D variable: Get data for a specified secondary axis value - numeric axis (2D variable)
    get_data_for_2d_variable_at_specific_independent_variable_value(run_directory, run_name, "blade 1 mx (principal elastic axes)", 4.8400002, 1)

    # Clear the cache
    ResultsApi.clear_runs()

    # Restore default setting
    ResultsApi.CacheSettings.data_type_for_reading = dnvres.DATA_TYPE_SPECIFIER_READ_AS_SERIALISED_TYPE


def get_data_for_1d_variable(run_directory, run_name, variable_name):

    try:

        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)
    
        #####################
        #  Get 1D variable  #
        #####################

        var_1d = run.get_variable_1d(variable_name)
        
        print("\nData for 1D variable '" + var_1d.name + "' contains " + str(var_1d.data_point_count) + " points")

        ############################
        #  Get data (NumPy array)  #
        ############################

        # We don't need to specify the data type (float/double), despite the fact the C++ Calculation Results library is statically typed
        # The API proxy resolves the correct type for us (as determined by ResultsApiSettings) and Python's dynamic type system does the rest
        variable_data = var_1d.get_data()

        ######################
        #  Print some values #
        ######################
        print("Value at first index =", variable_data[0])
        print("Value at last  index =", variable_data[variable_data.size - 1])

    except RuntimeError as e:
        print(e)


def get_data_for_2d_variable(run_directory, run_name, variable_name):

    try:
        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)
    
        #####################
        #  Get 2D variable  #
        #####################

        var_2d = run.get_variable_2d(variable_name)

        print("\nData for 2D variable '" + var_2d.name + "' contains " + str(var_2d.data_point_count) + " points")

        ########################################
        #  Get secondary independent variable  #
        ########################################

        # Get the independent variable using the IndependentVariableId key
        secondary_independent_variable = var_2d.get_independent_variable(dnvres.INDEPENDENT_VARIABLE_ID_SECONDARY)

        # Note: we can also get an independent variable using the name, for example:
        # secondaryIndependentVariable = var2D.GetIndependentVariable("location")
        
        # Get the independent variable values
        if (secondary_independent_variable.axis_type == dnvres.AXIS_TYPE_LABELLED_STRING):
            secondary_independent_variable_values = secondary_independent_variable.get_values_as_string()
        else:
            secondary_independent_variable_values = secondary_independent_variable.get_values_as_number()

        # Print some values for each independent variable data series
        for secondary_independent_variable_value in secondary_independent_variable_values:

            ############################
            #  Get data (NumPy array)  #
            ############################

            # We don't need to specify the data type (float/double), despite the fact the C++ Calculation Results library is statically typed
            # The API proxy resolves the correct type for us (as determined by ResultsApiSettings) and Python's dynamic type system does the rest
            variable_data = var_2d.get_data_at_value(secondary_independent_variable_value)

            # Print some values
            print("Value at first index @ " + str(secondary_independent_variable_value) + "\t=", variable_data[0])
            print("Value at last  index @ " + str(secondary_independent_variable_value) + "\t=", variable_data[variable_data.size - 1])

    except RuntimeError as e:
        print(e)


def get_data_for_2d_variable_at_specific_independent_variable_value(run_directory, run_name, variable_name, secondary_independent_variable_value, value_index):

    try:

        ################################
        #  Get a specific run by name  #
        ################################

        run = ResultsApi.get_run(run_directory, run_name)

        ##############
        #  Get data  #
        ##############

        variable = run.get_variable_2d(variable_name)

        print("Data for 2D variable '" + variable.name + "' contains " + str(variable.data_point_count) + " points")
    
        ############################
        #  Get data (NumPy array)  #
        ############################

        variable_data_at_secondary_axis_value = variable.get_data_at_value(secondary_independent_variable_value)

        # Hint: the data series at a secondary axis value can also be obtained using the zero-based index - useful when numeric axis values
        # contain floating point artefacts, e.g. 1.0000001 instead of 1.0
        variable_data_at_secondary_axis_index = variable.get_data_at_index(value_index)

        # Ensure data returned from value and index is the same
        for a, b in zip(variable_data_at_secondary_axis_value, variable_data_at_secondary_axis_index):
            assert a == b 
        
        # Print some values
        print("Value at first index @ " + str(secondary_independent_variable_value) + "\t=", variable_data_at_secondary_axis_value[0])
        print("Value at last  index @ " + str(secondary_independent_variable_value) + "\t=", variable_data_at_secondary_axis_value[variable_data_at_secondary_axis_value.size - 1])

        print()

    except RuntimeError as e:
        print(e)


if __name__ == "__main__":
    run_script()
