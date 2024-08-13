""" Edge Sensor Commands """

import enum
from pydantic import BaseModel
from typing import Optional

class Method(str, enum.Enum):
    GET = "get"
    SET = "set"

class GatewayAPIWithSensors(BaseModel):
    """
    Schema for the Gateway API
    """

    gateway_name: str
    url: str
    target_sensors: list[str]

class BaseCommand(BaseModel):
    method: Method
    target: GatewayAPIWithSensors
    property_name: Optional[str] = None
    property_value: object = None

# --- Property: Sensor State ---

class SensorState(str, enum.Enum):
    INITIAL = "initial"
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    WORKING = "working"
    IDLE = "idle"
    ERROR = "error"


class SensorStateCommand(BaseCommand):
    property_name: str = "sensor-state"

class SetSensorState(SensorStateCommand):
    method: Method = Method.SET
    property_value: SensorState

class GetSensorState(SensorStateCommand):
    method: Method = Method.GET


# --- Property: Inference Layer ---

class InferenceLayer(int, enum.Enum):
    CLOUD = 2
    GATEWAY = 1
    SENSOR = 0


class InferenceLayerCommand(BaseCommand):
    property_name: str = "inference-layer"

class SetInferenceLayer(InferenceLayerCommand):
    method: Method = Method.SET
    property_value: InferenceLayer

class GetInferenceLayer(InferenceLayerCommand):
    method: Method = Method.GET

# --- Property: Sensor Config ---

class SensorConfig(BaseModel):
    sleep_interval_ms: int

class SensorConfigCommand(BaseCommand):
    property_name: str = "sensor-config"

class SetSensorConfig(SensorConfigCommand):
    method: Method = Method.SET
    property_value: SensorConfig

class GetSensorConfig(SensorConfigCommand):
    method: Method = Method.GET

# --- Property: Sensor Model ---

class SensorModel(BaseModel):
    """
    Schema for the Sensor Model
    """

    tf_model_b64: str
    tf_model_bytesize: int


class SensorModelCommand(BaseCommand):
    property_name: str = "sensor-model"

class SetSensorModel(SensorModelCommand):
    method: Method = Method.SET
    property_value: SensorModel

# --- Property: Inference Latency Benchmark ---

class InferenceLatencyBenchmark(BaseModel):
    sensor_name: str
    inference_layer: InferenceLayer
    send_timestamp: int


class InferenceLatencyBenchmarkCommand(BaseCommand):
    property_name: str = "inf-latency-bench"
    method: Method = Method.SET
    property_value: InferenceLatencyBenchmark