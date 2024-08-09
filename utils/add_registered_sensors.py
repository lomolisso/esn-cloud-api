import requests
import json

def add_registered_sensors():
    # Load the device names from devices.json
    with open('../devices.json', 'r') as f:
        devices = json.load(f)
        device_names = devices

    # Prepare the request
    url = 'http://localhost:8000/api/v1/gateway/command/add/registered-sensors'
    params = {'gateway_name': 'gateway_1'}
    data = []
    for i in range(len(device_names)):
        data.append({"device_name": device_names[i], "device_address": str(i)})

    # Send the request
    response = requests.post(url, params=params, json=data)

    # Check the response
    if response.status_code == 200:
        print("Sensors added successfully")
    else:
        print(response.text)
        print("Failed to add sensors")

if __name__ == '__main__':
    add_registered_sensors()