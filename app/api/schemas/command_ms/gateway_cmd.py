""" Edge Gateway Commands """

import enum
from pydantic import BaseModel
from typing import Optional


class Method(str, enum.Enum):
    GET = "get"
    SET = "set"
    ADD = "add"

class GatewayAPI(BaseModel):
    """
    Schema for the Gateway API
    """

    gateway_name: str
    url: str

class BaseCommand(BaseModel):
    method: Method
    target: GatewayAPI
    resource_name: Optional[str] = None
    resource_value: object = None

# --- Resource: Gateway Model ---
class GatewayModel(BaseModel):
    """
    Schema for the Gateway Model
    """

    tf_model_bytesize: int
    tf_model_b64: str

class GatewayModelCommand(BaseCommand):
    resource_name: str = "gateway-model"

class SetGatewayModel(GatewayModelCommand):
    method: Method = Method.SET
    resource_value: GatewayModel

# --- Resource: Available Sensors ---
class BLEDevice(BaseModel):
    """
    Schema for the BLE Device
    """

    device_name: str
    device_address: str

class AvailableSensorsCommand(BaseCommand):
    """
    Schema for the Get Available Sensors Command
    """

    resource_name: str = "available-sensors"

class GetAvailableSensors(AvailableSensorsCommand):
    method: Method = Method.GET

# --- Resource: Provisioned Sensors ---
class BLEDeviceWithPoP(BLEDevice):
    """
    Schema for the BLE Device with PoP
    """

    device_pop: str

class ProvisionedSensorsCommand(BaseCommand):
    """
    Schema for the Get Provisioned Sensors Command
    """

    resource_name: str = "provisioned-sensors"

class GetProvisionedSensors(ProvisionedSensorsCommand):
    method: Method = Method.GET

class AddProvisionedSensors(ProvisionedSensorsCommand):
    method: Method = Method.ADD
    resource_value: list[BLEDeviceWithPoP]


# --- Resource: Registered Sensors ---
class SensorDescriptor(BaseModel):
    """
    Schema for the Sensor Descriptor
    """

    device_name: str
    device_address: str

class RegisteredSensorsCommand(BaseCommand):
    """
    Schema for the Get Registered Sensors Command
    """

    resource_name: str = "registered-sensors"

class GetRegisteredSensors(RegisteredSensorsCommand):
    method: Method = Method.GET

class AddRegisteredSensors(RegisteredSensorsCommand):
    method: Method = Method.ADD
    # each target gets a list of SensorDescriptor to register
    resource_value: list[SensorDescriptor]