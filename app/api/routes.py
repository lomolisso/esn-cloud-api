"""
Routes for the api.

13/11/2022
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.dependencies import get_session
from app.api.model import schemas, crud, enums
from app.api import utils as api_utils
from sqlalchemy.orm import Session
import logging

PAGE_SIZE = 8

api_router = APIRouter(prefix="/api")


@api_router.get("/get-edge-gateways")
async def get_edge_gateways(
    session=Depends(get_session),
) -> list[schemas.EdgeGatewayOut]:
    """
    Returns a list of JSON's with the last PAGE_SIZE edge gateways.
    """

    return crud.read_edge_gateways(session=session, page_size=PAGE_SIZE)


@api_router.get("/get-edge-gateway/{gateway_uuid}")
async def get_edge_gateway(
    gateway_uuid: str, session=Depends(get_session)
) -> schemas.EdgeGatewayOut:
    """
    Returns an edge gateway.
    """

    return crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)


@api_router.post("/register_gateway")
async def register_gateway(
    edge_gateway: schemas.EdgeGatewayIn, session=Depends(get_session)
):
    # create a row for the gateway and store the url and pop.
    gateway_fields = edge_gateway.model_dump()
    gateway_fields["jwt_token"] = api_utils.post_pop_to_gateway_api(
        url=edge_gateway.url, pop=edge_gateway.proof_of_possession
    )

    db_edge_gateway = crud.create_edge_gateway(
        session=session,
        fields=gateway_fields,
    )

    # ask the gateway for the rest of the data.
    gateway_info = api_utils.get_from_gateway_api(
        session, db_edge_gateway, "/get-gateway-info"
    )
    crud.update_edge_gateway(
        uuid=db_edge_gateway.uuid,
        session=session,
        fields=gateway_info,
    )

    return {"message": "Gateway registered successfully!"}


@api_router.get("/gateway/{gateway_uuid}/discover-devices")
async def discover_devices(gateway_uuid: str, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")
    return api_utils.get_from_gateway_api(session, edge_gateway, "/discover-devices")


@api_router.post("/gateway/{gateway_uuid}/bind-devices")
async def bind_edge_sensors(
    gateway_uuid: str,
    edge_sensors: list[schemas.BLEDeviceWithPoP],
    session=Depends(get_session),
):
    # check if the gateway exists.
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    # check if the edge sensors belong to a gateway.
    for device in edge_sensors:
        _edge_sensor = crud.read_edge_sensor_by_device_name(
            session=session, device_name=device.device_name
        )
        if _edge_sensor is not None:
            if _edge_sensor.gateway_uuid != edge_gateway.uuid:
                raise HTTPException(
                    status_code=409,
                    detail=f"Edge sensor {device.device_name} belongs to another gateway",
                )
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Edge sensor {device.device_name} already exists",
                )

    # step 1: command the gateway to register the devices in edgex foundry.
    json_data = [device.model_dump() for device in edge_sensors]
    edgex_response = api_utils.post_json_to_gateway_api(
        session=session,
        edge_gateway=edge_gateway,
        endpoint="/upload-edgex-devices",
        json_data=json_data,
    )
    logging.info(
        f"Edge sensors ({len(edge_sensors)}) registered in edgex foundry successfully!"
    )

    # step 2: ask the gateway to provision WiFi credentials to the devices.
    ble_prov_response = api_utils.post_json_to_gateway_api(
        session=session,
        edge_gateway=edge_gateway,
        endpoint="/provision-devices",
        json_data=json_data,
    )
    provisioned = ble_prov_response["provisioned"]
    logging.info(f"Edge sensors ({len(provisioned)}) provisioned successfully!")
    # TODO: Delete not provisioned devices from EdgeX Foundry core metadata.

    # step 3: create the edge sensors in the database.
    for edgex_device in edgex_response:
        if edgex_device["device_name"] in provisioned:
            crud.create_edge_sensor(
                session=session, gateway_uuid=edge_gateway.uuid, fields=edgex_device
            )

    return {
        "message": "Edge sensor added to the gateway successfully!",
        "provisioned": provisioned,
    }


@api_router.post("/mqtt-connection-status")
async def mqtt_device_connected(
    payload: schemas.MQTTConnectionStatus,
    session=Depends(get_session),
):
    edge_sensor = crud.read_edge_sensor_by_device_name(
        session=session, device_name=payload.device_name
    )
    if edge_sensor is None:
        raise HTTPException(status_code=404, detail="Edge sensor not found")

    operating_state = (
        enums.EdgeSensorOperatingState.UP
        if payload.mqtt_connection_status
        else enums.EdgeSensorOperatingState.DOWN
    )
    crud.update_edge_sensor_by_uuid(
        session=session,
        uuid=edge_sensor.uuid,
        fields={"operating_state": operating_state},
    )
    return {"message": "MQTT connection status updated successfully!"}


@api_router.post("/edge-sensor-measurement")
async def edge_sensor_measurement(
    device_data: schemas.EdgeSensorMeasurements, session=Depends(get_session)
):
    """
    Receives a measurement from an edge sensor.
    """
    edge_sensor = crud.read_edge_sensor_by_device_name(
        session=session, device_name=device_data.device_name
    )
    if edge_sensor is None:
        raise HTTPException(status_code=404, detail="Edge sensor not found")


@api_router.post("/{gateway_uuid}/lock-devices")
async def lock_devices(gateway_uuid: str, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [
        {
            "device_name": device.device_name,
            "edgex_device_uuid": str(device.edgex_device_uuid),
        }
        for device in edge_gateway.edge_sensors
    ]

    api_utils.post_json_to_gateway_api(
        session=session,
        json_data=devices,
        endpoint="/lock-devices",
        edge_gateway=edge_gateway,
    )
    return {"message": "Devices locked successfully!"}


@api_router.post("/{gateway_uuid}/unlock-devices")
async def unlock_devices(gateway_uuid: str, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [
        {
            "device_name": device.device_name,
            "edgex_device_uuid": str(device.edgex_device_uuid),
        }
        for device in edge_gateway.edge_sensors
    ]

    api_utils.post_json_to_gateway_api(
        session=session,
        json_data=devices,
        endpoint="/unlock-devices",
        edge_gateway=edge_gateway,
    )
    return {"message": "Devices unlocked successfully!"}


@api_router.post("/{gateway_uuid}/start-devices")
async def start_devices(gateway_uuid, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [
        {
            "device_name": device.device_name,
            "device_address": device.device_address,
            "edgex_device_uuid": str(device.edgex_device_uuid),
        }
        for device in edge_gateway.edge_sensors
    ]

    api_utils.post_json_to_gateway_api(
        session=session,
        json_data=devices,
        endpoint="/start-devices",
        edge_gateway=edge_gateway,
    )
    return {"message": "Devices started successfully!"}


@api_router.post("/{gateway_uuid}/stop-devices")
async def stop_devices(gateway_uuid, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [
        {
            "device_name": device.device_name,
            "edgex_device_uuid": str(device.edgex_device_uuid),
        }
        for device in edge_gateway.edge_sensors
    ]

    api_utils.post_json_to_gateway_api(
        session=session,
        json_data=devices,
        endpoint="/stop-devices",
        edge_gateway=edge_gateway,
    )
    return {"message": "Devices stopped successfully!"}


@api_router.post("/{gateway_uuid}/config-devices")
async def config_devices(
    gateway_uuid, config: schemas.EdgeSensorConfig, session=Depends(get_session)
):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [
        {
            "device_name": device.device_name,
            "edgex_device_uuid": str(device.edgex_device_uuid),
        }
        for device in edge_gateway.edge_sensors
    ]

    api_utils.post_json_to_gateway_api(
        session=session,
        json_data={"devices": devices, "config": config.model_dump()},
        endpoint="/config-devices",
        edge_gateway=edge_gateway,
    )
    return {"message": "Devices configured successfully!"}
