import requests
import json
import sys

def set_layer(layer):
    num_sensors = sys.argv[2]
    
    # Load the device names from devices.json
    with open('../devices.json', 'r') as f:
        devices = json.load(f)
        device_names = devices[:int(num_sensors)]

    # Prepare the request
    url = f'http://localhost:8000/api/v1/sensor/command/set/inference-layer/{layer}'
    params = {'gateway_name': 'gateway_1'}

    # Send the request
    response = requests.post(url, params=params, json=device_names)

    # Check the response
    if response.status_code == 200:
        print("Inference layer set successfully")
    else:
        print(response.text)

if __name__ == '__main__':
    layer = sys.argv[1]
    set_layer(layer)