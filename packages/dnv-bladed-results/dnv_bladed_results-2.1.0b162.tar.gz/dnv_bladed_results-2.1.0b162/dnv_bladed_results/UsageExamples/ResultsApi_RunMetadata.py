from dnv_bladed_results import ResultsApi, Run, UsageExamples
import dnv_bladed_results as dnvres
import os

############   Bladed Results API: Get run metadata   ############

# Finds runs according to search criteria and displays run metadata.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Finds runs starting in a root folder using various search criteria.
    - Prints run metadata to the console.
    """

    run_directory = os.path.join(UsageExamples.__path__[0], "Runs/demo")
    display_run_metadata(run_directory)

    # Clear the cache
    ResultsApi.clear_runs()
    

def display_run_metadata(run_directory):

    ##########################################################################
    #  Get a set of runs, excluding those with unsupported calculation type  #
    ##########################################################################

    ResultsApi.SearchSettings.include_unsupported_calculations = False
    ResultsApi.SearchSettings.calculation_type_filter = dnvres.CALCULATION_TYPE_PARKED_SIMULATION

    runs = ResultsApi.get_runs(run_directory, dnvres.SEARCH_SCOPE_RECURSIVE_SEARCH)
    print("\nFound " + str(runs.size) + " runs")

    ##########################
    #  Display run metadata  #
    ##########################
    
    run: Run
    for run in runs:
        print("\nDisplaying information for run: " + run.directory + run.name)
        print("Calculation name:", run.calculation_descriptive_name)
        if run.is_turbine_simulation:
            print("\nRun is a turbine simulation")
        if run.is_post_processing_calculation:
            print("\nRun is a post-processing calculation")
        if run.is_supporting_calculation:
            print("\nRun is a supporting calculation")
        if run.was_successful:
            print("Run was successful")
        else:
            print("Run was not successful")
        print("Run date:", run.timestamp)
        try:
            print("Run execution duration (s):", str(run.execution_duration_seconds))
        except RuntimeError as e:
            print("Cannot get run execution duration")
        try:
            print("\nRun message file ($ME) content:\n", run.message_file_content)
        except RuntimeError as e:
            print("Cannot get run message file ($ME) content")

        # Print group names and variable names contained by the run
        print("\nRun contains the following groups:", run.get_group_names())
        print("\nRun contains the following variables:", run.get_variable_names(False))
        
    print()
    
    # Revert default search setting
    ResultsApi.SearchSettings.include_unsupported_calculations = True
    ResultsApi.SearchSettings.calculation_type_filter = dnvres.CALCULATION_TYPE_ALL_CALCULATION_TYPES


if __name__ == "__main__":
    run_script()
