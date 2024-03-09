# Set path to export zip file 
import zipfile
import numpy as np
import json
from datetime import datetime
import requests
import configparser

RUNALYZE_API_ENDPOINT = 'https://runalyze.com/api/v1/'

config = configparser.ConfigParser()
config.read("configs/config.txt")
apitoken = config.get("configuration","apitoken")

zip_path = config.get("configuration","zip_path")
default_measurement_state = config.get("configuration","default_measurement_state")
raw_data_patch = config.get("configuration","raw_data_path")
"""zip_path = 'export.zip'
default_measurement_state = 'awake'
raw_data_patch = 'data'"""

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
        

        data_dict = {}
        rr_values = file.read()
        rr_values = rr_values.split('\n')
        rr_values = [int(i) for i in rr_values if i]

        
        
        rmssd = calculate_rmssd(rr_values)
        sdsd = calculate_sdsd(rr_values)
        lnrmssd = calculate_lnrmssd(rr_values)
        hrv = calculate_hrv(rmssd, sdsd, lnrmssd)

        
        data_dict['date_time'] = parse_unixtime_to_runalyze_format(unix_time)
        data_dict['measurement_type'] = default_measurement_state
        data_dict['rmssd'] = rmssd
        #data_dict['hrv'] = int(hrv)
        #data_dict['sdnn'] = sdsd
        #data_dict['lnrmssd'] = lnrmssd
        data_dict['Sent to API'] = False

        print(data_dict)

        processed_data_log[file_id] = data_dict

        with open(processed_data_log_path, 'w') as file:
            json.dump(processed_data_log, file, indent=4)

        
        return file_id



def calculate_rmssd(rr_values : list) -> float:
    """
    A Function that calculates the RMSSD from the RR-values.
    """
    rr_diff = np.diff(rr_values)
    rr_diff = rr_diff ** 2
    rmssd = np.sqrt(np.mean(rr_diff))
    return rmssd


def calculate_sdsd(rr_values : list) -> float:
    """
    A Function that calculates the SDSD from the RR-values.
    """
    rr_diff = np.diff(rr_values)
    sdsd = np.std(rr_diff)
    return sdsd

def calculate_lnrmssd(rr_values : list) -> float:
    """
    A Function that calculates the lnRMSSD from the RR-values.
    """
    rmssd = calculate_rmssd(rr_values)
    lnrmssd = np.log(rmssd)
    return lnrmssd

def calculate_hrv(rmssd : float, sdsd : float, lnrmssd : float) -> str:
    """
    A Function that calculates a numeric HRV score from the RMSSD, SDSD and lnRMSSD.
    """
    hrv = rmssd + sdsd + lnrmssd
    return hrv
  


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

def send_to_api(data_dict : dict) -> None:
    """
    A Function that sends the data to the Runalyze API.
    POST ​/api​/v1​/metrics​/hrv
    """
    
    # Send the data to the Runalyze API
    print("Sending data to the Runalyze API...")

    # Set the URL for the Runalyze API
    url = "https://runalyze.com/api/v1/metrics/hrv"

    #url = 'https://runalyze.com/api/v1/ping'
    headers = {'token': f'{apitoken}', 'Content-Type': 'application/json'}

    response = requests.post(url, headers=headers, json=data_dict)

    print(response.text)

    # Check if the request was successful
    if response.status_code == 201:
        
        print("Data sent successfully!")
        print(response._content.decode('utf-8'))
        return 200
    else:
        print(f"Failed to send data! Status code: {response.status_code}")
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
    unzip_data(zip_path, raw_data_patch)

    file_path = r"data\Julian\2024-03-07 21-43-06.txt"
    
    file_id = process_file(file_path)

    data_log = load_processed_data_log()
    send_to_api(data_log[file_id])
