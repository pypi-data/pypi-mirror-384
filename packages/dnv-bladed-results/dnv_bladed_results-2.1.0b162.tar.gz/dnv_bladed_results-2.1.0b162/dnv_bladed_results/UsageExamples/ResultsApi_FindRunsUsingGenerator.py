from dnv_bladed_results import ResultsApi, Run, RunsIterator, RunsIteratorRegex, UsageExamples
import dnv_bladed_results as dnvres
import os

############   Bladed Results API: Find runs using RunsIterator with generator   ############

# The RunsIterator object allows a Python client to use a generator to process runs asynchronously.
# The generator yields a run each time one is found based on the search criteria.
# Runs returned by RunsIterator are intentionally not added to the run cache, helping to reduce memory consumption.


def run_script():
    r"""
    Example script that runs when this Python module is called as the main function.
    
    - Finds runs iteratively starting in a root folder using various search criteria:
    
      - runs filtered on completion state and calculation type
      - runs matching name
      - runs matching name regex.
    """

    runs_root_folder = os.path.join(UsageExamples.__path__[0], "Runs")
    from datetime import datetime
    start_time = datetime.now()
    find_runs_using_generator(runs_root_folder)
    end_time = datetime.now()
    total_time = end_time - start_time
    print("\nTime taken (s) =", total_time.total_seconds(), "\n")

    # Clear the cache
    ResultsApi.clear_runs()


def runs_generator(iterator: RunsIterator):
    run = iterator.get_next_run()
    while run is not None:
        yield run
        run = iterator.get_next_run()


def display_runs(description, runs):
    print("\nShowing " + description + ":")
    run: Run
    for run in runs:
        print(run.directory + run.name)


def find_runs_using_generator(root_folder):
    
    ###################################################
    #  Iterate all unsuccessful runs using generator  #
    ###################################################

    ResultsApi.SearchSettings.completion_state_filter = dnvres.COMPLETION_STATE_UNSUCCESSFUL_RUNS_ONLY
    iterator = RunsIterator(root_folder)
    unsuccessful_runs = runs_generator(iterator)
    display_runs("runs that did not succeed", unsuccessful_runs)
    ResultsApi.SearchSettings.completion_state_filter = dnvres.COMPLETION_STATE_ALL_COMPLETION_STATES

    #########################################################
    #  Iterate all turbine simulation runs using generator  #
    #########################################################

    ResultsApi.SearchSettings.calculation_type_filter = dnvres.CALCULATION_TYPE_ALL_TURBINE_SIMULATIONS
    iterator = RunsIterator(root_folder)
    turbine_simulation_runs = runs_generator(iterator)
    display_runs("turbine simulation runs", turbine_simulation_runs)
    ResultsApi.SearchSettings.calculation_type_filter = dnvres.CALCULATION_TYPE_ALL_CALCULATION_TYPES

    ###################################################
    #  Find all post-processing runs using generator  #
    ###################################################

    ResultsApi.SearchSettings.calculation_type_filter = dnvres.CALCULATION_TYPE_ALL_POST_PROCESSING_CALCULATIONS
    iterator = RunsIterator(root_folder)
    post_processing_runs = runs_generator(iterator)
    display_runs("post-processing runs", post_processing_runs)
    ResultsApi.SearchSettings.calculation_type_filter = dnvres.CALCULATION_TYPE_ALL_CALCULATION_TYPES

    #############################################################
    #  Find runs matching a name - case insensitive by default  #
    #############################################################

    iterator = RunsIterator(root_folder, "powprod")
    runs_named_powprod = runs_generator(iterator)
    display_runs("runs named 'powprod'", runs_named_powprod)
    
    #####################################################
    #  Find runs with name matching regular expression  #
    #####################################################

    iterator = RunsIteratorRegex(root_folder, r".*\d+.*")
    runs_with_number_in_name = runs_generator(iterator)
    display_runs("runs with name containing a number", runs_with_number_in_name)
    
    iterator = RunsIteratorRegex(root_folder, "p.*")
    runs_with_name_starting_with_p = runs_generator(iterator)
    display_runs("runs with name beginning wih letter 'p'", runs_with_name_starting_with_p)


if __name__ == "__main__":
    run_script()
