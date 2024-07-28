"""
Sensor Command Response Schemas

GET Commands involving interaction with sensors whether it be direct (MQTT) or indirect (BLE)
require decoupling the response from the request (contrary to a SET command where HTTP status codes
are sufficient).

This module contains the response schemas for the Sensor Commands which fall under the requirements
mentioned above.
"""

from pydantic import BaseModel
from app.api.schemas.command_ms.sensor_cmd import SensorConfig, InferenceLayer, SensorState, Method
from typing import Optional

class Metadata(BaseModel):
    """
    Metadata for the response
    """

    sender: str
    command_uuid: str
    gateway_name: str

class BaseResponse(BaseModel):
    metadata: Metadata
    resource_name: Optional[str] = None
    resource_value: object = None
    method: Method = Method.GET

class SensorConfigResponse(BaseResponse):
    resource_name: str = "sensor-config"
    resource_value: SensorConfig

class InferenceLayerResponse(BaseResponse):
    resource_name: str = "inference-layer"
    resource_value: InferenceLayer

class SensorStateResponse(BaseResponse):
    resource_name: str = "sensor-state"
    resource_value: SensorState