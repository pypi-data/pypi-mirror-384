import pandas as pd
import json
import requests

# eikon search function
# -----
def search_api(
                my_search_prompt,
                user_api_key,
                effort_selection,
                spatial_resolution_for_search,
                selected_london_borough = None
            ):
    
    """ 
    This is a function to search for locations in London based on a user prompt using the Eikon Search API.
    The function requires a user_api_key which can be obtained by registering for an eikon account.
    The function returns a pandas DataFrame of search results if successful, otherwise it returns an error message.
    Example usage:

    # London - all
    results_df = search_api(
                my_search_prompt="Find me a quiet park with lots of trees",
                user_api_key="your_api_key_here",
                effort_selection="low",
                spatial_resolution_for_search="London - all"
            )
    
    # for a specfic borough (i.e. Camden)
    results_df = search_api(
                my_search_prompt="Find me a quiet park with lots of trees",
                user_api_key="your_api_key_here",
                effort_selection="low",
                spatial_resolution_for_search="London - borough",
                selected_london_borough="Camden"
            )
    """


    import requests
    import pandas as pd

    # ping the endpoint to do the initial user search
    base_api_address = f'https://slugai.pagekite.me/eikon_search_agent_api'
    payload = {
            "prompt": my_search_prompt,
            "api_key":user_api_key,
            "effort_selection":effort_selection,
            "spatial_resolution_for_search": spatial_resolution_for_search,
            "selected_london_borough":selected_london_borough,
    }
        
    if spatial_resolution_for_search == "London - all" and selected_london_borough is None:
   
        r = requests.post(base_api_address, json=payload, timeout=10000)
        if r.ok:
            results_json = r.json()["successful_job_completion"]
            results_df = pd.DataFrame.from_dict(json.loads(results_json))
            return results_df
    elif spatial_resolution_for_search != "London - all" and selected_london_borough is not None:
        r = requests.post(base_api_address, json=payload, timeout=10000)
        if r.ok:
            results_json = r.json()["successful_job_completion"]
            results_df = pd.DataFrame.from_dict(json.loads(results_json))
            return results_df
    else:
        return ("You have made an incompatible query")
    

# the eikon portfolio comparison function
# -----

def eikon_portfolio_comparison(orig_uniq_id,
                              dest_uniq_id,
                              orig_lat_list,
                              orig_lon_list,
                              dest_lat_list,
                              dest_lon_list,
                              user_api_key,
                              resolution,
                              similarity_type="combined"):
    
    """
    This is a function to compare two portfolios of locations using the Eikon Portfolio Comparison API.
    The function requires two lists of unique location IDs, two lists of latitude values, and two lists of longitude values.

    The function also requires a user_api_key which can be obtained by registering for an eikon account.

    The function requires a resolution parameter which can be set as either "low", "medium", or "high".
    The function also requires a similarity_type parameter which can be set as either "visual", "descriptive", or "combined".
    The function returns a pandas DataFrame of comparison results if successful, otherwise it returns an error message.
    Example usage:
    portfolio_comparison_df = eikon_portfolio_comparison(
                                orig_uniq_id = ["loc_1","loc_2","loc_3"],
                                dest_uniq_id = ["loc_A","loc_B","loc_C"],
                                orig_lat_list = [51.5074, 51.5155, 51.5236],
                                orig_lon_list = [-0.1278, -0.1410, -0.1580],
                                dest_lat_list = [51.5090, 51.5180, 51.5250],
                                dest_lon_list = [-0.1300, -0.1450, -0.1600],
                                user_api_key="your_api_key_here",
                                resolution="medium",
                                similarity_type="combined"
                            )

    Example response: 

    A dataframe containing all combinations of location pairs 3 columns - orig, dest and similarity score column.

    orig         dest        similarity_score
    loc_1       loc_A       0.85
    loc_2       loc_B       0.78
    loc_3       loc_C       0.92
    ...


    
    """

    # check that all the datasets are of equal length
    variables_container = [orig_uniq_id,
                          dest_uniq_id,
                          orig_lat_list,
                          orig_lon_list,
                          dest_lat_list,
                          dest_lon_list]

    
    cumulative_diff = 0

    for x in variables_container:
        for y in variables_container:
            if x != y:
                comp_diff = len(x) - len(y)
                cumulative_diff += comp_diff

    # if all the columns are the same length proceed otherwise return an error:
    if cumulative_diff == 0:
        print("VALID: all inputs are the same length")

        # ping the endpoint to do the portfolio comparison
        base_api_address = f'https://slugai.pagekite.me/eikon_portfolio_comparison'
        payload = {"origin_uniq_id": orig_uniq_id,
                   "destination_uniq_id": dest_uniq_id,
                   "origin_lat_list": orig_lat_list,
                   "origin_lon_list": orig_lon_list,
                   "destination_lat_list": dest_lat_list,
                   "destination_lon_list": dest_lon_list,
                   "api_key":user_api_key,
                   "resolution":resolution,
                   "similarity_type":similarity_type,
                  }
        r = requests.post(base_api_address, json=payload, timeout=1000)
        if r.ok:
            portfolio_comparison_result_json = r.json()["portfolio_comparison_result"]
            # reconstruct dataframe
            portfolio_comparison_result_df = pd.DataFrame.from_dict(json.loads(portfolio_comparison_result_json))
            
            return portfolio_comparison_result_df
        else:
            return r.status_code
        

    else:
        return ("inputs are not of the same length. Ensure all inputs are the same length.")
