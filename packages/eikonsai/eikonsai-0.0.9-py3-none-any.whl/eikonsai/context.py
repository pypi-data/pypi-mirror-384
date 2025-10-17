import numpy as np
import pandas as pd
import requests
import json
from PIL import Image
import base64, io, requests

# we're now going to load these functions in which will interact with the eikon API

# ---------------
# location description function
# ---------------

def get_location_description(lat, lon, resolution, user_api_key):
    """
    This is a function to get a location ddescription from lat, lon coordinates.
    This function requires latitude, longitude values to be in float format.
    It also requires a resolution parameter which is can be set as either "low", "medium", or "high".
    The function also requires a user_api_key which can be obtained by registering at https://slugai.pagekite.me/register
    The function returns a string location description if successful, otherwise it returns None.
    Example usage:
    location_str = get_location_description(51.5074, -0.1278, "low", "your_api_key_here")
    
    """
    # this is for wimbledon low resolution 
    base_api_address = "https://slugai.pagekite.me/get_location_description"
    payload = {"text": "placeholder",
            "location": [lat, lon],
            "resolution":resolution,
            "api_key":user_api_key}
    r = requests.post(base_api_address, json=payload, timeout=120)
    # print(r)
    if r.ok:
        location_str = r.json()["location_description"]
        return location_str
    else:
        return None
    

def get_location_image(lat, lon, resolution, user_api_key):


    """
    This is a function to get a location image from lat, lon coordinates.
    This function requires latitude, longitude values to be in float format.
    It also requires a resolution parameter which is can be set as either "low", "medium", or "high".
    The function also requires a user_api_key which can be obtained by registering at https://slugai.pagekite.me/register
    The function returns a Pillow image object if successful, otherwise it returns None.
    Example usage:
    img = get_location_image(51.5074, -0.1278, "low", "your_api_key_here")

    """
    base_api_address = "https://slugai.pagekite.me/get_location_image"
    payload = {"text": "placeholder",
            "location": [lat, lon],
            "resolution":resolution,
            "api_key": user_api_key}
    r = requests.post(base_api_address, json=payload, timeout=120)
    if r.ok:
        b64_str = r.json()["location_image"]
        # 2) —— DECODE bytes -------------------------------------------------
        img_bytes = base64.b64decode(b64_str)

        # 3) —— LOAD into an image object -----------------------------------
        # Pillow can open from a bytes-buffer
        img = Image.open(io.BytesIO(img_bytes))
        return img
    else:
        return None