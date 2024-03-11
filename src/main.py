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

# If the post-processed data log file exists, load , else create an empty dictionary

try:
    with open(processed_data_log_path, 'r') as file:
        processed_data_log = json.load(file)
except FileNotFoundError:
    processed_data_log = {}




def unzip_data(zip_path : str, raw_data_patch : str) -> None:
    """
    A Function that unzips the zip file and does not overwrite existing files.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(raw_data_patch)
        print('Unzip completed')

def process_file(file_path : str) -> None:
    """
    A Function that reads the file with raw RR-distances perline and calculates the HRV-parameters.
    """
    with open(file_path, 'r') as file:
        
        unix_time = parse_file_name_date(file.name)

        file_id = file.name.split('\\')[-1].split('.')[0]
        if file_id in processed_data_log:
            print(f"File {file.name} already processed. Skipping...")
        

        hrv_data_dict = {}
        resting_hr_data_dict = {}

        rr_values = file.read()
        rr_values = rr_values.split('\n')
        rr_values = [int(i) for i in rr_values if i]

        
        
        rmssd = calculate_rmssd(rr_values)
        hr = calculate_hr(rr_values)


        
        hrv_data_dict['date_time'] = parse_unixtime_to_runalyze_format(unix_time)
        hrv_data_dict['measurement_type'] = default_measurement_state
        hrv_data_dict['rmssd'] = rmssd
        hrv_data_dict['sent_to_api'] = False

        resting_hr_data_dict['sent_to_api'] = False
        resting_hr_data_dict['date_time'] = parse_unixtime_to_runalyze_format(unix_time)
        resting_hr_data_dict['heart_rate'] = hr
        
        print(hrv_data_dict)
        print(resting_hr_data_dict)

        processed_data_log[file_id] = {}
        processed_data_log[file_id]["hrv"] = hrv_data_dict
        processed_data_log[file_id]["resting_hr"] = resting_hr_data_dict


        with open(processed_data_log_path, 'w') as file:
            json.dump(processed_data_log, file, indent=4)

        
        return file_id

def calculate_hr(rr_diff : list) -> float:
    """
    A Function that calculates the HR from the RR-values.
    """
    # Calculate the HR from the RR-values
    hr = 60000 / np.mean(rr_diff)
    return int(hr)



def calculate_rmssd(rr_intervals : list) -> float:
    """
    A Function that calculates the RMSSD from the RR-values.
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5624990/ 
    """
    # Step 1: Calculate successive differences
    successive_diff = [rr_intervals[i + 1] - rr_intervals[i] for i in range(len(rr_intervals) - 1)]

    # Step 2: Square each successive difference
    squared_diff = [diff ** 2 for diff in successive_diff]

    # Step 3: Calculate the mean of squared differences
    mean_squared_diff = sum(squared_diff) / (len(squared_diff)-1)

    # Step 4: Calculate the square root of the mean squared differences to get RMSSD
    rmssd = math.sqrt(mean_squared_diff)

    return rmssd

  


def parse_file_name_date(file_name : str) -> datetime:
    """
    A Function that parses the date from the file name.
    """
    date_string = file_name.split('\\')[-1].split('.')[0]
    print(date_string)
    date_format = "%Y-%m-%d %H-%M-%S"

    # Parse the date string
    parsed_date = datetime.strptime(date_string, date_format)

    # Convert the parsed date to Unix time
    unix_time = int(parsed_date.timestamp())

    print("Unix Time:", unix_time)
    return unix_time

def parse_unixtime_to_runalyze_format(unix_time : int) -> str:
    """
    A Function that converts the Unix time to the format that Runalyze uses.
    """
    # Create a datetime object from Unix time
    utc_datetime = datetime.utcfromtimestamp(unix_time)

    # Format the datetime object as a string in the desired format
    formatted_date = utc_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    print("Formatted Date:", formatted_date)
    return formatted_date

def send_to_api(metric : str, data_dict : dict) -> int:
    """
    A Function that sends the data to the Runalyze API.
    POST ​/api​/v1​/metrics​/hrv
    """
    
    # Send the data to the Runalyze API
    print("Sending data to the Runalyze API...")

    # remove pair from dictionary
    data_dict.pop('sent_to_api')

    # Set the URL for the Runalyze API
    if metric == 'hrv':
        url = "https://runalyze.com/api/v1/metrics/hrv"
    if metric == 'resting_hr':
        url = "https://runalyze.com/api/v1/metrics/heartRateRest"

    #url = 'https://runalyze.com/api/v1/ping'
    headers = {'token': f'{apitoken}', 'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, json=data_dict)

    print(response.text)

    # Check if the request was successful
    if response.status_code == 201:
        
        print("Data sent successfully!")
        #print(response._content.decode('utf-8'))
        return 201
    else:
        #print(f"Failed to send data! Status code: {response.status_code}")
        print(f"Failed to send data! at {url}")
        return response.status_code


# Load processed data log
def load_processed_data_log() -> dict:
    """
    A Function that loads the processed data log from the file.
    """
    try:
        with open(processed_data_log_path, 'r') as file:
            processed_data_log = json.load(file)
    except FileNotFoundError:
        processed_data_log = {}
    return processed_data_log


if __name__ == '__main__':
    unzip_data(zip_path, raw_data_path)

    #file_path = r"data\Julian_Huber\2024-03-08 06-52-35.txt"
    
    # loop all text files in the data folder
    # including subfolders

    for root, dirs, files in os.walk(raw_data_path):
        for file in files:

            if file.endswith(".txt"):
                if file.startswith("!"):
                    continue
                file_path = os.path.join(root, file)

                file_id = process_file(file_path)

    data_log = load_processed_data_log()

    # loop thorugh the data log and send the data to the API if it has not been sent yet

    for file_id in data_log:

        for metric in ['hrv', 'resting_hr']: # , 'resting_hr
            if not data_log[file_id][metric]['sent_to_api']:
                data_dict = data_log[file_id][metric]
                data_dict_send = data_dict.copy()
                print(data_dict)
                response = send_to_api(metric, data_dict_send)
                if response == 201 or response == 200:
                    data_log[file_id][metric]['sent_to_api'] = True
    
    with open(processed_data_log_path, 'w') as file:
        json.dump(data_log, file, indent=4) 

    #send_to_api(data_log[file_id])
