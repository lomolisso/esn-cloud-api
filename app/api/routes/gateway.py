"""
Routes for the Gateway layer of the PdM-ESN system.
"""
import json
from fastapi import APIRouter, status, HTTPException
from app.core.config import CLOUD_INFERENCE_LAYER, LATENCY_BENCHMARK, ADAPTIVE_INFERENCE
from app.api.schemas.cloud_api import gateway as gw_schemas
from app.api.schemas.data_ms import data as data_schemas
from app.api.schemas.command_ms import sensor_resp as s_resp_schemas
from app.api.schemas.command_ms import sensor_cmd as s_cmd_schemas
from app.api import utils

gateway_router = APIRouter(tags=["Gateway Routes"])

# --- Command Responses ---

@gateway_router.post("/store/sensor/response/get/sensor-state", status_code=status.HTTP_202_ACCEPTED)
async def store_sensor_state_response(response: s_resp_schemas.SensorStateResponse):
    response = await utils.store_sensor_state_response(response)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=response.status_code, detail=response.json())

@gateway_router.post("/store/sensor/response/get/inference-layer", status_code=status.HTTP_202_ACCEPTED)
async def store_sensor_inference_layer_response(response: s_resp_schemas.InferenceLayerResponse):
    response = await utils.store_sensor_inference_layer_response(response)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=response.status_code, detail=response.json())

@gateway_router.post("/store/sensor/response/get/sensor-config", status_code=status.HTTP_202_ACCEPTED)
async def store_sensor_config_response(response: s_resp_schemas.SensorConfigResponse):
    response = await utils.store_sensor_config_response(response)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=response.status_code, detail=response.json())

# --- Export Routes ---

@gateway_router.post("/export/sensor-reading", status_code=status.HTTP_201_CREATED)
async def export_sensor_data(sensor_reading: gw_schemas.SensorReadingExport):
    # Step 1: Make sure that at least both sensor and gateway exist
    gateway_name, sensor_name = sensor_reading.metadata.gateway_name, sensor_reading.metadata.sensor_name
    response = await utils.read_edge_sensor(
        gateway_name, sensor_name
    )  # Checks both sensor and gateway, see data microservice.
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    # Step 2: Create sensor reading
    reading_uuid = sensor_reading.export_value.uuid
    reading = data_schemas.CreateSensorReading(
        uuid=reading_uuid, values=json.dumps(sensor_reading.export_value.values)
    )
    response = await utils.create_sensor_reading(gateway_name, sensor_name, reading)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
@gateway_router.post("/export/prediction-request", status_code=status.HTTP_202_ACCEPTED)
async def export_prediction_request(prediction_request: gw_schemas.PredictionRequestExport):
    # Step 1: Make sure that at least both sensor and gateway exist
    gateway_name, sensor_name = prediction_request.metadata.gateway_name, prediction_request.metadata.sensor_name
    response = await utils.read_edge_sensor(
        gateway_name, sensor_name
    )  # Checks both sensor and gateway, see data microservice.
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    # Step 2: verify the request inference layer is correct
    request_inference_layer = prediction_request.export_value.inference_descriptor.inference_layer
    if request_inference_layer != CLOUD_INFERENCE_LAYER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inference layer must be cloud.")
    
    # Step 3: Send the prediction request to the inference microservice
    response = await utils.send_prediction_request(prediction_request)
    if response.status_code != status.HTTP_202_ACCEPTED:
        raise HTTPException(status_code=response.status_code, detail=response.json())

@gateway_router.post("/export/prediction-result", status_code=status.HTTP_201_CREATED)
async def export_prediction_result(prediction_result: gw_schemas.PredictionResultExport):
    # Step 1: Make sure that at least both sensor and gateway exist
    gateway_name, sensor_name = prediction_result.metadata.gateway_name, prediction_result.metadata.sensor_name
    response = await utils.read_edge_sensor(
        gateway_name, sensor_name
    )
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    # Step 2: Save the prediction result in the data microservice
    reading_uuid = prediction_result.export_value.reading_uuid
    prediction = prediction_result.export_value.prediction
    inference_layer = prediction_result.export_value.inference_layer
    
    data_prediction_result = data_schemas.PredictionResult(
        prediction=prediction,
        inference_layer=inference_layer
    )
    
    response = await utils.create_prediction_result(gateway_name, sensor_name, reading_uuid, data_prediction_result)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    if inference_layer == CLOUD_INFERENCE_LAYER:
        # Step 3: Handle heuristic result if adaptive inference is enabled.
        # Note only cloud predictions are handled as gateway predictions are handled by the gateway.
        if ADAPTIVE_INFERENCE:
            heuristic_result = prediction_result.export_value.heuristic_result
            await utils.handle_heuristic_result(gateway_name, sensor_name, heuristic_result)
        if LATENCY_BENCHMARK:
            gateway_api_with_sensors = await utils.get_gateway_api_with_sensors(gateway_name, [sensor_name])
            command = s_cmd_schemas.InferenceLatencyBenchmarkCommand(
                target=gateway_api_with_sensors,
                resource_value=s_cmd_schemas.InferenceLatencyBenchmark(
                    reading_uuid=reading_uuid,
                    send_timestamp=prediction_result.export_value.send_timestamp,
                )
            )
            response = await utils.send_inference_latency_benchmark_command(command)
            if response.status_code != status.HTTP_202_ACCEPTED:
                raise HTTPException(status_code=response.status_code, detail=response.json())

    
        
@gateway_router.post("/export/inference-latency-benchmark", status_code=status.HTTP_201_CREATED)
async def export_inference_latency_benchmark(inf_latency_bench: gw_schemas.InferenceLatencyBenchmarkExport):
    # Step 1: Make sure that gateway, sensor and reading exist
    gateway_name = inf_latency_bench.metadata.gateway_name
    sensor_name = inf_latency_bench.metadata.sensor_name
    reading_uuid = inf_latency_bench.export_value.reading_uuid
    response = await utils.read_sensor_reading(gateway_name, sensor_name, reading_uuid)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    # Step 2: Create inference latency benchmark
    if LATENCY_BENCHMARK:
        reading_uuid = inf_latency_bench.export_value.reading_uuid
        data = data_schemas.InferenceLatencyBenchmark(
            send_timestamp=inf_latency_bench.export_value.send_timestamp,
            recv_timestamp=inf_latency_bench.export_value.recv_timestamp,
            inference_latency=inf_latency_bench.export_value.inference_latency
        )
        response = await utils.create_inference_latency_benchmark(
            gateway_name, sensor_name, reading_uuid, data
        )
        if response.status_code != status.HTTP_201_CREATED:
            raise HTTPException(status_code=response.status_code, detail=response.json())
