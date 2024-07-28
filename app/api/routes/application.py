"""
Routes for the Application layer of the PdM-ESN System.
"""

from fastapi import APIRouter, UploadFile, File, status, HTTPException
from app.api.schemas.data_ms import data as data_schemas
from app.api.schemas.inference_ms import inference as inf_schemas
from app.api.schemas.command_ms import gateway_cmd as gw_cmd_schemas
from app.api.schemas.command_ms import sensor_cmd as s_cmd_schemas
from app.api import utils

application_router = APIRouter(tags=["Application Routes"])

# ----------------- Inference Microservice Routes ----------------- #

@application_router.post("/model", status_code=status.HTTP_202_ACCEPTED)
async def upload_model(tf_model_file: UploadFile = File(...)):
    tf_model = await utils.serialize_model_file(tf_model_file)
    response = await utils.set_cloud_model(
        inf_schemas.CloudModel(**tf_model)
    )
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {"message": "Model uploaded to Inference Microservice"}

# ----------------- Data Microservice Routes ----------------- #

@application_router.post("/gateway/register")
async def register_gateway(gateway: data_schemas.CreateEdgeGateway):
    response = await utils.create_edge_gateway(gateway)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {"message": "Gateway registered successfully"}

@application_router.get("/gateway/{gateway_name}")
async def get_gateway(gateway_name: str):
    response = await utils.read_edge_gateway(gateway_name)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json() 

@application_router.get("/gateway/{gateway_name}/sensor")
async def get_sensors(gateway_name: str):
    response = await utils.read_edge_gateway(gateway_name)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    response = await utils.read_edge_sensors(gateway_name)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()

@application_router.get("/gateway/{gateway_name}/sensor/{sensor_name}")
async def get_sensor(gateway_name: str, sensor_name: str):
    response = await utils.read_edge_sensor(gateway_name, sensor_name)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()

# ----------------- Command Microservice Routes ----------------- #

# Gateway Commands
@application_router.post("/gateway/command/get/available-sensors")
async def get_available_sensors(gateway_name: str):
    gateway_api = await utils.get_gateway_api(gateway_name)
    command = gw_cmd_schemas.GetAvailableSensors(target=gateway_api)

    response = await utils.get_available_sensors(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return [
        gw_cmd_schemas.BLEDevice(**device)
        for device in response.json()
    ]

@application_router.post("/gateway/command/get/provisioned-sensors")
async def get_provisioned_sensors(gateway_name: str) -> list[gw_cmd_schemas.BLEDevice]:
    gateway_api = await utils.get_gateway_api(gateway_name)
    command = gw_cmd_schemas.GetProvisionedSensors(target=gateway_api)

    response = await utils.get_provisioned_sensors(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return [
        gw_cmd_schemas.BLEDevice(**device)
        for device in response.json()
    ]

@application_router.post("/gateway/command/add/provisioned-sensors")
async def add_provisioned_sensors(gateway_name: str, devices: list[gw_cmd_schemas.BLEDeviceWithPoP]):
    gateway_api = await utils.get_gateway_api(gateway_name)
    command = gw_cmd_schemas.AddProvisionedSensors(
        target=gateway_api,
        resource_value=devices,
    )

    response = await utils.add_provisioned_sensors(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "ADD Provisioned Sensors Command sent to Command Microservice for processing",
    }

@application_router.post("/gateway/command/set/gateway-model")
async def set_gateway_model(gateway_name: str, tf_model_file: UploadFile = File(...)):
    tf_model = await utils.serialize_model_file(tf_model_file)
    gateway_api = await utils.get_gateway_api(gateway_name)
    command = gw_cmd_schemas.SetGatewayModel(
        target=gateway_api,
        resource_value=gw_cmd_schemas.GatewayModel(**tf_model),
    )

    response = await utils.set_gateway_model(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "SET Gateway Model Command sent to Command Microservice for processing",
    }

@application_router.post("/gateway/command/add/registered-sensors")
async def add_registered_sensors(gateway_name: str, sensors: list[gw_cmd_schemas.SensorDescriptor]):
    for sensor in sensors:
        response = await utils.create_edge_sensor(gateway_name, sensor)
        if response.status_code != status.HTTP_201_CREATED:
            raise HTTPException(status_code=response.status_code, detail=response.json())
    
    gateway_api = await utils.get_gateway_api(gateway_name)
    command = gw_cmd_schemas.AddRegisteredSensors(
        target=gateway_api,
        resource_value=sensors,
    )

    response = await utils.add_registered_sensors(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return {
        "message": "ADD Registered Sensors Command sent to Command Microservice for processing",
    }

# Sensor Commands
@application_router.post("/sensor/command/set/sensor-state/{state}")
async def set_sensor_state(gateway_name: str, sensors: list[str], state: s_cmd_schemas.SensorState):
    gateway_api_with_sensors = await utils.get_gateway_api_with_sensors(gateway_name, sensors)
    command = s_cmd_schemas.SetSensorState(
        target=gateway_api_with_sensors,
        resource_value=state,
    )

    for sensor_name in sensors:
        response = await utils.update_edge_sensor(
            gateway_name=gateway_name,
            device_name=sensor_name,
            data=data_schemas.UpdateEdgeSensor(
                device_name=sensor_name,
                state=state
            ),
        )
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=response.status_code, detail=response.json())


    response = await utils.set_sensor_state(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "SET Sensor State Command sent to Command Microservice for processing",
    }

@application_router.post("/sensor/command/get/sensor-state")
async def command_get_sensor_state(gateway_name: str, sensors: list[str]):
    gateway_api_with_sensors = await utils.get_gateway_api_with_sensors(gateway_name, sensors)
    command = s_cmd_schemas.GetSensorState(target=gateway_api_with_sensors)

    response = await utils.get_sensor_state(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "GET Sensor State Command sent to Command Microservice for processing",
        "command_uuids": response.json()["command_uuids"],
    }

@application_router.post("/sensor/response/get/sensor-state")
async def response_get_sensor_state(command_uuids: list[str]):
    response = await utils.retrieve_sensor_state(command_uuids)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()

@application_router.post("/sensor/command/set/inference-layer/{layer}")
async def set_sensor_inference_layer(gateway_name: str, sensors: list[str], layer: s_cmd_schemas.InferenceLayer):
    inference_layers = [
        s_cmd_schemas.InferenceLayer.CLOUD,
        s_cmd_schemas.InferenceLayer.GATEWAY,
        s_cmd_schemas.InferenceLayer.SENSOR
    ]
    if layer not in inference_layers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid layer, must be one of: cloud, gateway, sensor")
    
    gateway_api_with_sensors = await utils.get_gateway_api_with_sensors(gateway_name, sensors)
    command = s_cmd_schemas.SetInferenceLayer(
        target=gateway_api_with_sensors,
        resource_value=layer,
    )
    response = await utils.set_inference_layer(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "SET Sensor Inference Layer Command sent to Command Microservice for processing",
    }

@application_router.post("/sensor/command/get/inference-layer")
async def command_get_sensor_inference_layer(gateway_name: str, sensors: list[str]):
    gateway_api_with_sensors = await utils.get_gateway_api_with_sensors(gateway_name, sensors)
    command = s_cmd_schemas.GetInferenceLayer(target=gateway_api_with_sensors)

    response = await utils.get_inference_layer(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "GET Sensor Inference Layer Command sent to Command Microservice for processing",
        "command_uuids": response.json()["command_uuids"],
    }

@application_router.post("/sensor/response/get/inference-layer")
async def response_get_sensor_inference_layer(command_uuids: list[str]):
    response = await utils.retrieve_inference_layer(command_uuids)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()

@application_router.post("/sensor/command/set/sensor-config")
async def set_sensor_config(gateway_name: str, sensors: list[str], config: s_cmd_schemas.SensorConfig):
    gateway_api_with_sensors = await utils.get_gateway_api_with_sensors(gateway_name, sensors)
    command = s_cmd_schemas.SetSensorConfig(
        target=gateway_api_with_sensors,
        resource_value=config,
    )

    for sensor_name in sensors:
        response = await utils.create_or_update_sensor_config(
            gateway_name, sensor_name, config
        )
        if response.status_code != status.HTTP_201_CREATED:
            raise HTTPException(status_code=response.status_code, detail=response.json())
    
    response = await utils.set_sensor_config(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "SET Sensor Config Command sent to Command Microservice for processing",
    }

@application_router.post("/sensor/command/get/sensor-config")
async def command_get_sensor_config(gateway_name: str, sensors: list[str]):
    gateway_api_with_sensors = await utils.get_gateway_api_with_sensors(gateway_name, sensors)
    command = s_cmd_schemas.GetSensorConfig(target=gateway_api_with_sensors)

    response = await utils.get_sensor_config(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "GET Sensor Config Command sent to Command Microservice for processing",
        "command_uuids": response.json()["command_uuids"],
    }

@application_router.post("/sensor/response/get/sensor-config")
async def response_get_sensor_config(command_uuids: list[str]):
    response = await utils.retrieve_sensor_config(command_uuids)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return response.json()

@application_router.post("/sensor/command/set/sensor-model")
async def set_sensor_model(gateway_name: str, device_names: list[str], tf_model_file: UploadFile = File(...)):
    tf_model = await utils.serialize_model_file(tf_model_file)
    gateway_api_with_sensors = await utils.get_gateway_api_with_sensors(gateway_name, device_names)
    command = s_cmd_schemas.SetSensorModel(
        target=gateway_api_with_sensors,
        resource_value=s_cmd_schemas.SensorModel(
            **tf_model
        ),
    )

    response = await utils.set_sensor_model(command)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    return {
        "message": "SET Sensor Model Command sent to Command Microservice for processing",
    }
