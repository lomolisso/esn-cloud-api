"""
Routes for the Gateway layer of the PdM-ESN system.
"""
import json
from fastapi import APIRouter, status, HTTPException
from app.core.config import CLOUD_INFERENCE_LAYER, LATENCY_BENCHMARK, ADAPTIVE_INFERENCE, POLLING_INTERVAL_MS, SENSOR_INFERENCE_LAYER
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

@gateway_router.post("/export/sensor-data", status_code=status.HTTP_201_CREATED)
async def export_sensor_data(sensor_data: gw_schemas.SensorDataExport):
    # Step 1: Make sure that at least both sensor and gateway exist
    gateway_name, sensor_name = sensor_data.metadata.gateway_name, sensor_data.metadata.sensor_name
    response = await utils.read_edge_sensor(
        gateway_name, sensor_name
    )  # Checks both sensor and gateway, see data microservice.
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    # Step 2: Handle the prediction if needed
    _inference_descriptor: gw_schemas.InferenceDescriptor = sensor_data.export_value.inference_descriptor
    _inference_layer = _inference_descriptor.inference_layer
    if _inference_layer == gw_schemas.InferenceLayer.CLOUD:
        # Step 2.1: send prediction request to cloud-inference-ms
        response = await utils.send_prediction_request(sensor_data)
        if response.status_code != status.HTTP_202_ACCEPTED:
            raise HTTPException(status_code=response.status_code, detail=response.json())
        
        # Step 2.2: poll for prediction result
        task_id = response.json()["task_id"]
        prediction_result, heuristic_result = None, None
        while True:
            response = await utils.get_prediction_result(task_id)
            if response.status_code == status.HTTP_200_OK:
                json_response = response.json()
                if json_response["status"] == "SUCCESS":
                    prediction_result = json_response["result"]["prediction_result"]
                    heuristic_result = json_response["result"]["heuristic_result"]
                    break
                elif json_response["status"] == "FAILURE":
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Prediction task failed.")
                else:   # status == "PENDING"
                    await utils.async_sleep(POLLING_INTERVAL_MS)
            else:
                raise HTTPException(status_code=response.status_code, detail=response.json())
        
        # Step 2.3: Update sensor data with prediction result
        sensor_data.export_value.inference_descriptor.prediction = prediction_result

        # Step 2.4: Export inference latency benchmark if enabled
        if LATENCY_BENCHMARK:
            await utils.send_inference_latency_benchmark_command(sensor_data)
            
        # Step 2.5: Handle heuristic result if adaptive inference is enabled.
        if ADAPTIVE_INFERENCE:
            await utils.handle_heuristic_result(gateway_name, sensor_name, heuristic_result)
    
    # Step 3: Create sensor reading
    sensor_reading = sensor_data.export_value.reading
    reading = data_schemas.CreateSensorReading(
        uuid=sensor_reading.uuid, values=json.dumps(sensor_reading.values)
    )
    response = await utils.create_sensor_reading(gateway_name, sensor_name, reading)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    # Step 4: Create prediction result
    prediction_result = sensor_data.export_value.inference_descriptor.prediction
    data_prediction_result = data_schemas.PredictionResult(
        prediction=prediction_result,
        inference_layer=_inference_layer
    )
    response = await utils.create_prediction_result(gateway_name, sensor_name, sensor_reading.uuid, data_prediction_result)
    if response.status_code != status.HTTP_201_CREATED:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    # Step 5: Create Inference Latency Benchmark entry in data ms if SENSOR_INFERENCE_LAYER
    if LATENCY_BENCHMARK and _inference_layer == gw_schemas.InferenceLayer.SENSOR:
        inf_latency_bench = data_schemas.InferenceLatencyBenchmark(
            sensor_name=sensor_name,
            inference_layer=_inference_descriptor.inference_layer,
            send_timestamp=_inference_descriptor.send_timestamp,
            recv_timestamp=_inference_descriptor.recv_timestamp,
            inference_latency=_inference_descriptor.inference_latency
        )
        response = await utils.create_inference_latency_benchmark(
            gateway_name, sensor_name, inf_latency_bench
        )
        if response.status_code != status.HTTP_201_CREATED:
            raise HTTPException(status_code=response.status_code, detail=response.json())

       
@gateway_router.post("/export/inference-latency-benchmark", status_code=status.HTTP_201_CREATED)
async def export_inference_latency_benchmark(inf_latency_bench: gw_schemas.InferenceLatencyBenchmarkExport):
    # Step 1: Make sure that gateway, sensor and reading exist
    gateway_name = inf_latency_bench.metadata.gateway_name
    sensor_name = inf_latency_bench.metadata.sensor_name

    # Step 2: Create inference latency benchmark
    if LATENCY_BENCHMARK:
        response = await utils.create_inference_latency_benchmark(
            gateway_name, sensor_name, inf_latency_bench.export_value
        )
        if response.status_code != status.HTTP_201_CREATED:
            raise HTTPException(status_code=response.status_code, detail=response.json())
