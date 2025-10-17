import pandas as pd 
import numpy as np
import requests
import json


# we're now going to load these functions in which will interact with the eikon API

# ----------------------------------------
# POI based similarity API functions
# ----------------------------------------


# visual similarity function
# -----

def visual_similarity(location_1_lat_lon_list, location_2_lat_lon_list, resolution, user_api_key):
    """
    This is a function to get a visual similarity image between two locations given their lat, lon coordinates.
    This function requires latitude, longitude values to be in float format and provided as lists of two elements each.
    Latiude and longitude values should be in the format [latitude, longitude].
    It also requires a resolution parameter which is can be set as either "low", "medium", or "high".
    The function also requires a user_api_key which can be obtained by registering at https://slugai.pagekite.me/register
    
    Example usage:
    
    visual_similarity([51.5074, -0.1278], [48.8566, 2.3522], "low", "your_api_key_here")
    
    Example response:
    
    0.838

    The function returns a a float value between 0 and 1 if successful, otherwise it returns None.
    Values closer to 1 indicate higher visual similarity and values closer to 0 indicate lower visual similarity.
    
    """
    payload = {
            "text": "placeholder",
            "location_1": [location_1_lat_lon_list[0], location_1_lat_lon_list[1]], 
            "location_2": [location_2_lat_lon_list[0], location_2_lat_lon_list[1]],
            "api_key": user_api_key,
            "resolution": resolution
          }
    base_api_address = "https://slugai.pagekite.me/"
    endpoint_name = "get_similarity_image"
    r = requests.post(base_api_address + endpoint_name, json=payload, timeout=120)
    if r.ok:
        visual_similarity_value = r.json()["location_pair_similarity_value"]
        return float(visual_similarity_value)
    else:
        return None
    
# Descriptive similarity function
# -----
def descriptive_similarity(location_1_lat_lon_list, location_2_lat_lon_list, resolution, user_api_key):
    """
    This is a function to get a descriptive similarity value between two locations given their lat, lon coordinates.
    This function requires latitude, longitude values to be in float format and provided as lists of two elements each.
    Latiude and longitude values should be in the format [latitude, longitude].
    It also requires a resolution parameter which is can be set as either "low", "medium", or "high".
    The function also requires a user_api_key which can be obtained by registering at https://slugai.pagekite.me/register
    
    Example usage:
    
    descriptive_similarity([51.5074, -0.1278], [48.8566, 2.3522], "low", "your_api_key_here")
    
    Example response:
    
    0.65

    The function returns a a float value between 0 and 1 if successful, otherwise it returns None.
    Values closer to 1 indicate higher descriptive similarity and values closer to 0 indicate lower descriptive similarity.
    
    """
    payload = {
            "text": "placeholder",
            "location_1": [location_1_lat_lon_list[0], location_1_lat_lon_list[1]], 
            "location_2": [location_2_lat_lon_list[0], location_2_lat_lon_list[1]],
            "api_key": user_api_key,
            "resolution": resolution
          }
    base_api_address = "https://slugai.pagekite.me/"
    endpoint_name = "get_similarity_descriptive"
    r = requests.post(base_api_address + endpoint_name, json=payload, timeout=120)
    if r.ok:
        descriptive_similarity_value = r.json()["location_pair_descriptive_similarity_value"]
        return float(descriptive_similarity_value)
    else:
        return None
    

# combined similarity function
# -----
def combined_similarity(location_1_lat_lon_list, location_2_lat_lon_list, resolution, user_api_key):
    """
    This is a function to get a combined similarity value between two locations given their lat, lon coordinates.
    This combined similarity is made up of both visual and descriptive similarity.
    This function requires latitude, longitude values to be in float format and provided as lists of two elements each.
    Latiude and longitude values should be in the format [latitude, longitude].
    It also requires a resolution parameter which is can be set as either "low", "medium", or "high".
    The function also requires a user_api_key which can be obtained by registering at https://slugai.pagekite.me/register
    
    Example usage:
    
    combined_similarity([51.5074, -0.1278], [48.8566, 2.3522], "low", "your_api_key_here")
    
    Example response:
    
    0.74

    The function returns a a float value between 0 and 1 if successful, otherwise it returns None.
    Values closer to 1 indicate higher combined similarity and values closer to 0 indicate lower combined similarity.
    
    """
    payload = {
            "text": "placeholder",
            "location_1": [location_1_lat_lon_list[0], location_1_lat_lon_list[1]], 
            "location_2": [location_2_lat_lon_list[0], location_2_lat_lon_list[1]],
            "api_key": user_api_key,
            "resolution": resolution
          }
    base_api_address = "https://slugai.pagekite.me/"
    endpoint_name = "get_combined_location_similarity"
    r = requests.post(base_api_address + endpoint_name, json=payload, timeout=120)
    if r.ok:
        combined_similarity_value = r.json()["combined_similarity_value"]
        return float(combined_similarity_value)
    else:
        return None
    


# ----------------------------------------
# Area based similarity API functions
# ----------------------------------------
# tbd...