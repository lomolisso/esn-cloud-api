import requests
import json
import sys

def send_model():
    num_sensors = sys.argv[1]
    
    # Load the device names from devices.json
    with open('../devices.json', 'r') as f:
        devices = json.load(f)
        device_names = devices[:int(num_sensors)]

    # Load the TFLite model
    model_file = '../gateway_model.tflite'
    tf_model = open(model_file, 'rb')

    # Prepare the request
    url = 'http://localhost:8000/api/v1/sensor/command/set/sensor-model'
    params = {'gateway_name': 'gateway_1'}
    files = {'tf_model_file': (model_file, tf_model)}
    data = {'device_names': device_names}

    # Send the request
    response = requests.post(url, params=params, files=files, data=data)

    # Check the response
    if response.status_code == 200:
        print("Model sent successfully")
    else:
        print(response.text)
        print("Failed to send model")

if __name__ == '__main__':
    send_model()