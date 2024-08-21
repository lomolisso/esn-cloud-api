from app.core.config import (
    DATA_MICROSERVICE_URL,
    COMMAND_MICROSERVICE_URL,
    INFERENCE_MICROSERVICE_URL,
    GATEWAY_INFERENCE_LAYER,
    HEURISTIC_ERROR_CODE,
)
from app.api.schemas.data_ms import data as data_schemas
from app.api.schemas.cloud_api import gateway as gw_schemas
from app.api.schemas.command_ms import gateway_cmd as gw_cmd_schemas
from app.api.schemas.command_ms import sensor_cmd as s_cmd_schemas
from app.api.schemas.command_ms import sensor_resp as s_resp_schemas
from app.api.schemas.inference_ms import inference as inf_schemas
from fastapi import UploadFile, status, HTTPException
import httpx
import base64
import zlib
import asyncio

# --- Async Polling ---
async def async_sleep(ms: int):
    await asyncio.sleep(ms / 1000)

# --- Primitive functions for microservice communication ---


async def _post_json_to_microservice(url: str, json_data: dict):
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        return await client.post(url, json=json_data)


async def _put_json_to_microservice(url: str, json_data: dict):
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        return await client.put(url, json=json_data)


async def _get_from_microservice(url: str):
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        return await client.get(url)


async def _delete_from_microservice(url: str):
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        return await client.delete(url)


# --- Data microservice functions ---


# CRUD operations for edge gateways
async def create_edge_gateway(data: data_schemas.CreateEdgeGateway):
    return await _post_json_to_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway", data.model_dump()
    )


async def update_edge_gateway(data: data_schemas.UpdateEdgeGateway):
    return await _put_json_to_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway", data.model_dump()
    )


async def read_edge_gateway(device_name: str):
    return await _get_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{device_name}"
    )


async def read_edge_gateways():
    return await _get_from_microservice(f"{DATA_MICROSERVICE_URL}/gateway")


async def delete_edge_gateway(device_name: str):
    return await _delete_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{device_name}"
    )


# CRUD operations for edge sensors
async def create_edge_sensor(gateway_name: str, data: data_schemas.CreateEdgeSensor):
    return await _post_json_to_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor", data.model_dump()
    )


async def update_edge_sensor(gateway_name: str, device_name: str, data: data_schemas.UpdateEdgeSensor):
    return await _put_json_to_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{device_name}", data.model_dump()
    )


async def read_edge_sensor(gateway_name: str, device_name: str):
    return await _get_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{device_name}"
    )


async def read_edge_sensors(gateway_name: str):
    return await _get_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor"
    )


async def delete_edge_sensor(gateway_name: str, device_name: str):
    return await _delete_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{device_name}"
    )


# CRUD operations for sensor config
async def create_or_update_sensor_config(
    gateway_name: str, sensor_name: str, data: data_schemas.SensorConfig
):
    return await _post_json_to_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/config",
        data.model_dump(),
    )


async def read_sensor_config(gateway_name: str, sensor_name: str):
    return await _get_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/config"
    )


async def delete_sensor_config(gateway_name: str, sensor_name: str):
    return await _delete_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/config"
    )


# CRUD operations for sensor readings
async def read_sensor_readings(gateway_name: str, sensor_name: str):
    return await _get_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/readings"
    )


async def read_sensor_reading(gateway_name: str, sensor_name: str, reading_uuid: str):
    return await _get_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/reading/{reading_uuid}"
    )


async def delete_sensor_readings(gateway_name: str, sensor_name: str):
    return await _delete_from_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/readings"
    )


async def create_sensor_reading(
    gateway_name: str, sensor_name: str, data: data_schemas.CreateSensorReading
):
    return await _post_json_to_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/reading",
        data.model_dump(),
    )


# CRUD operations for prediction results
async def create_prediction_result(
    gateway_name: str,
    sensor_name: str,
    reading_uuid: str,
    data: data_schemas.PredictionResult,
):
    return await _post_json_to_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/reading/{reading_uuid}/prediction",
        data.model_dump(),
    )


# CRUD operations for inference latency benchmark
async def create_inference_latency_benchmark(
    gateway_name: str,
    sensor_name: str,
    data: data_schemas.InferenceLatencyBenchmark,
):
    return await _post_json_to_microservice(
        f"{DATA_MICROSERVICE_URL}/gateway/{gateway_name}/sensor/{sensor_name}/inference/latency",
        data.model_dump(),
    )


# --- Command microservice functions ---

# Edge Gateway Commands

async def get_available_sensors(
    command: gw_cmd_schemas.GetAvailableSensors,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/gateway/command/get/available-sensors",
        command.model_dump(),
    )

async def get_provisioned_sensors(
    command: gw_cmd_schemas.GetProvisionedSensors,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/gateway/command/get/provisioned-sensors",
        command.model_dump(),
    )

async def add_provisioned_sensors(
    command: gw_cmd_schemas.AddProvisionedSensors,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/gateway/command/add/provisioned-sensors",
        command.model_dump(),
    )

async def set_gateway_model(
    command: gw_cmd_schemas.GatewayModelCommand,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/gateway/command/set/gateway-model",
        command.model_dump(),
    )

async def add_registered_sensors(
    command: gw_cmd_schemas.AddRegisteredSensors,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/gateway/command/add/registered-sensors",
        command.model_dump(),
    )


# Edge Sensor Commands

async def set_sensor_state(
    command: s_cmd_schemas.SetSensorState,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/sensor/command/set/sensor-state",
        command.model_dump(),
    )

async def get_sensor_state(
    command: s_cmd_schemas.GetSensorState,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/sensor/command/get/sensor-state",
        command.model_dump(),
    )

async def retrieve_sensor_state(
    command_uuids: list[str],
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/retrieve/sensor/response/get/sensor-state",
        command_uuids,
    )

async def set_inference_layer(
    command: s_cmd_schemas.SetInferenceLayer,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/sensor/command/set/inference-layer",
        command.model_dump(),
    )

async def get_inference_layer(
    command: s_cmd_schemas.GetInferenceLayer,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/sensor/command/get/inference-layer",
        command.model_dump(),
    )

async def retrieve_inference_layer(
    command_uuids: list[str],
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/retrieve/sensor/response/get/inference-layer",
        command_uuids,
    )

async def set_sensor_config(
    command: s_cmd_schemas.SetSensorConfig,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/sensor/command/set/sensor-config",
        command.model_dump(),
    )

async def get_sensor_config(
    command: s_cmd_schemas.GetSensorConfig,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/sensor/command/get/sensor-config",
        command.model_dump(),
    )

async def retrieve_sensor_config(
    command_uuids: list[str],
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/retrieve/sensor/response/get/sensor-config",
        command_uuids,
    )

async def set_sensor_model(
    command: s_cmd_schemas.SetSensorModel,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/sensor/command/set/sensor-model",
        command.model_dump(),
    )

async def send_inference_latency_benchmark_command(
    sensor_data: gw_schemas.SensorDataExport,
):
    gateway_name = sensor_data.metadata.gateway_name
    sensor_name = sensor_data.metadata.sensor_name
    send_timestamp = sensor_data.export_value.inference_descriptor.send_timestamp

    command = s_cmd_schemas.InferenceLatencyBenchmarkCommand(
        target = await get_gateway_api_with_sensors(gateway_name, [sensor_name]),
        property_value=s_cmd_schemas.InferenceLatencyBenchmark(
            sensor_name=sensor_name,
            inference_layer=s_cmd_schemas.InferenceLayer.CLOUD,
            send_timestamp=send_timestamp,
        )
    )
    response = await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/sensor/command/set/inf-latency-bench",
        command.model_dump(),
    )
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())

# Command Response Callbacks

async def store_sensor_state_response(
    response: s_resp_schemas.SensorStateResponse,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/store/sensor/response/get/sensor-state",
        response.model_dump(),
    )

async def store_sensor_inference_layer_response(
    response: s_resp_schemas.InferenceLayerResponse,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/store/sensor/response/get/inference-layer",
        response.model_dump(),
    )

async def store_sensor_config_response(
    response: s_resp_schemas.SensorConfigResponse,
):
    return await _post_json_to_microservice(
        f"{COMMAND_MICROSERVICE_URL}/store/sensor/response/get/sensor-config",
        response.model_dump(),
    )

# --- Inference microservice functions ---

async def set_cloud_model(predictive_model: inf_schemas.CloudModel):
    return await _post_json_to_microservice(
        f"{INFERENCE_MICROSERVICE_URL}/model/upload", predictive_model.model_dump()
    )


async def send_prediction_request(prediction_request: inf_schemas.PredictionRequestExport):
    return await _put_json_to_microservice(
        f"{INFERENCE_MICROSERVICE_URL}/model/prediction/request",
        prediction_request.model_dump(),
    )

async def get_prediction_result(task_id: str):
    return await _get_from_microservice(f"{INFERENCE_MICROSERVICE_URL}/model/prediction/result/{task_id}")


async def handle_heuristic_result(gateway_name: str, sensor_name: str, heuristic_result: int):
    gateway_api_with_sensors = await get_gateway_api_with_sensors(gateway_name, [sensor_name])
    if heuristic_result == HEURISTIC_ERROR_CODE:    # set sensor state to error
        command = s_cmd_schemas.SetSensorState(
            target=gateway_api_with_sensors,
            property_value=s_cmd_schemas.SensorState.ERROR
        )
        response = await set_sensor_state(command)
        if response.status_code != status.HTTP_202_ACCEPTED:
            raise HTTPException(status_code=response.status_code, detail=response.json())
    elif heuristic_result == GATEWAY_INFERENCE_LAYER:    # set sensor inference layer to gateway
        command = s_cmd_schemas.SetInferenceLayer(
            target=gateway_api_with_sensors,
            property_value=s_cmd_schemas.InferenceLayer.GATEWAY
        )
        response = await set_inference_layer(command)
        if response.status_code != status.HTTP_202_ACCEPTED:
            raise HTTPException(status_code=response.status_code, detail=response.json())
    

# --- Gateway Comm Utility Functions ---

async def get_gateway_api(gateway_name: str):
    response = await read_edge_gateway(gateway_name)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    gateway_url = response.json()["url"]
    return gw_cmd_schemas.GatewayAPI(gateway_name=gateway_name, url=gateway_url)

async def get_gateway_api_with_sensors(gateway_name: str, sensor_names: list[str]):
    response = await read_edge_gateway(gateway_name)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    gateway_url = response.json()["url"]

    for sensor in sensor_names:
        response = await read_edge_sensor(gateway_name, sensor)
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=response.status_code, detail=response.json())

    return s_cmd_schemas.GatewayAPIWithSensors(gateway_name=gateway_name, url=gateway_url, target_sensors=sensor_names)


# --- Model Utility Functions ---
async def serialize_model_file(tf_model_file: UploadFile):
    # Read the file content
    file_content = await tf_model_file.read()

    # Get the file byte size
    tf_model_bytesize = len(file_content)

    # Compress the file content
    file_content = zlib.compress(file_content)

    # Serialize the file content to base64
    tf_model_b64 = base64.b64encode(file_content).decode("utf-8")
    return {"tf_model_b64": tf_model_b64, "tf_model_bytesize": tf_model_bytesize}
