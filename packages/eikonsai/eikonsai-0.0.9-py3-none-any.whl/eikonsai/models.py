import numpy as np 
import pandas as pd 
import requests
import re
import base64
from io import BytesIO
from PIL import Image
# These are the core ai models offered via the eikon APIs
# ----------------------------------------

# Vision model
# -----
def vision_model_analysis(pil_image_object, user_api_key):
    """
    This is a function to get an analysis of an image using a vision AI model.
    This function requires an image in base64 string format.
    The function also requires a user_api_key which can be obtained by registering at https://slugai.pagekite.me/register
    The function returns a string analysis if successful, otherwise it returns None.
    
    Example usage:

    load an image and convert to base64 string in memory
    from PIL import Image
    import base64, io

    image = Image.open("my_image.jpg")
    buffered = io.BytesIO()
    # convert this to to base64 string in memory without saving it



    analysis_str = get_vision_model_analysis(my_image_base64_str, "your_api_key_here")

    Example response:
    
    "A scenic view of a mountain during sunset with vibrant colors in the sky."

    """

    def image_to_base64(image):
        buffered = BytesIO()
        # Get the format from the image
        format = image.format if image.format else 'JPEG'
        # Save the image with its original format
        image.save(buffered, format=format)
        return base64.b64encode(buffered.getvalue()).decode()
    
    image_base64_str = image_to_base64(pil_image_object)
    
    base_api_address = "https://slugai.pagekite.me/"
    endpoint = "get_vlm_output"
    payload = {"prompt": "placeholder",
            "image_base64": image_base64_str,
            "api_key":user_api_key}
    r = requests.post(base_api_address + endpoint, json=payload, timeout=600)
    if r.ok:
        analysis_str = r.json()["image_analysis"]
        return analysis_str
    else:
        return None
    

# Object detection model
# -----

def object_detection(lat,lon,resolution, user_api_key):
    """
    This is a function to get an object detection analysis of a location image using an object detection AI model.
    The function requires latitude, longitude values to be in float format.
    It also requires a resolution parameter which is can be set as either "low", "medium", or "high".
    The function also requires a user_api_key which can be obtained by registering at https://slugai.pagekite.me/register
    The function returns a dictionary of detected objects and their counts if successful, otherwise it returns None.
    
    Example usage:

    location_id = get_location_id(51.5074, -0.1278, "low", "your_api_key_here")
    object_counts = object_detection(location_id, "your_api_key_here")

    Example response:
    
    {
        "person": 5,
        "car": 2,
        "tree": 10
    }

    """

    base_api_address = "https://slugai.pagekite.me/"
    endpoint = "get_objects_detected_in_location"
    payload = {"text": "placeholder",
            "lat": lat,
            "lon":lon,
            "resolution":resolution,
            "api_key":user_api_key}
    r = requests.post(base_api_address + endpoint, json=payload, timeout=600)
    if r.ok:
        object_detected_str = r.json()["objects"]
        return object_detected_str
    else:
        return None