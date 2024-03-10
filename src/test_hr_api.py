# Set path to export zip file 
import zipfile
import numpy as np
import json
from datetime import datetime
import requests
import configparser
import math
import os

RUNALYZE_API_ENDPOINT = 'https://runalyze.com/api/v1/'

config = configparser.ConfigParser()
config.read("configs/config.txt")
apitoken = config.get("configuration","apitoken")

zip_path = config.get("configuration","zip_path")
default_measurement_state = config.get("configuration","default_measurement_state")
raw_data_path = config.get("configuration","raw_data_path")

processed_data_log_path = 'data/processed.json'


hr_dict = {
            "date_time": "2024-03-08T05:52:35Z",
            "heart_rate": 73.36642015026383
        }


def send_to_api(metric : str, data_dict : dict) -> int:
    """
    A Function that sends the data to the Runalyze API.
    POST ​/api​/v1​/metrics​/hrv
    """
    
    # Send the data to the Runalyze API
    print("Sending data to the Runalyze API...")

    # remove pair from dictionary
    #data_dict.pop('sent_to_api')

    # Set the URL for the Runalyze API
    if metric == 'hrv':
        url = "https://runalyze.com/api/v1/metrics/hrv"
    if metric == 'resting_hr':
        url = "https://runalyze.com/api/v1/metrics/heartRateRest"

    #url = 'https://runalyze.com/api/v1/ping'
    headers = {'token': f'{apitoken}', 'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, json=data_dict)

    print(response)

    # Check if the request was successful
    if response.status_code == 201:
        
        print("Data sent successfully!")
        #print(response._content.decode('utf-8'))
        return 201
    else:
        #print(f"Failed to send data! Status code: {response.status_code}")
        print(f"Failed to send data! at {url}")
        return response.status_code
    
print(send_to_api('resting_hr', hr_dict))