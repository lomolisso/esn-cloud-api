import requests
import json
import sys

def set_state(state):
    # Load the device names from devices.json
    with open('../devices.json', 'r') as f:
        devices = json.load(f)
        device_names = devices

    # Prepare the request
    url = f'http://localhost:8000/api/v1/sensor/command/set/sensor-state/{state}'
    params = {'gateway_name': 'gateway_1'}

    # Send the request
    response = requests.post(url, params=params, json=device_names)

    # Check the response
    if response.status_code == 200:
        print("State set successfully")
    else:
        print(response.text)

if __name__ == '__main__':
    state = sys.argv[1]
    set_state(state)