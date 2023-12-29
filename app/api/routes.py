"""
Routes for the api.

13/11/2022
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.dependencies import get_session
from app.api.model import schemas, crud
from app.api import utils as api_utils
import logging

api_router = APIRouter(prefix="/api")


@api_router.get("/gateway")
async def get_edge_gateways(
    session=Depends(get_session),
) -> list[schemas.EdgeGatewayOut]:
    """
    Returns a list of JSON's with the last PAGE_SIZE edge gateways.
    """

    return crud.read_edge_gateways(session=session)


@api_router.get("/gateway/{gateway_uuid}")
async def get_edge_gateway(
    gateway_uuid: str, session=Depends(get_session)
) -> schemas.EdgeGatewayOut:
    """
    Returns an edge gateway.
    """

    return crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)


@api_router.post("/gateway/register")
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
    gateway_info = api_utils.get_from_gateway_api(session, db_edge_gateway, "/gateway")
    crud.update_edge_gateway(
        uuid=db_edge_gateway.uuid,
        session=session,
        fields=gateway_info,
    )

    return {"message": "Gateway registered successfully!"}


@api_router.get("/gateway/{gateway_uuid}/devices/discover")
async def discover_devices(gateway_uuid: str, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")
    return api_utils.get_from_gateway_api(session, edge_gateway, "/devices/discover")


@api_router.post("/gateway/{gateway_uuid}/devices/bind")
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
        endpoint="/devices/provision",
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


@api_router.post("/gateway/{gateway_uuid}/devices/predictive-model")
async def devices_predictive_model(
    gateway_uuid, predictive_model: UploadFile = File(...), session=Depends(get_session)
):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [dev.device_name for dev in edge_gateway.edge_sensors]

    api_utils.post_file_to_gateway_api(
        session=session,
        endpoint="/devices/predictive-model",
        edge_gateway=edge_gateway,
        file={"predictive_model": predictive_model.file},
        form_data={"devices": devices},
    )
    return {"message": "Predictive model uploaded successfully!"}


@api_router.post("/gateway/{gateway_uuid}/devices/config")
async def config_devices(
    gateway_uuid,
    config: schemas.EdgeSensorConfig,
    session=Depends(get_session),
):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [dev.device_name for dev in edge_gateway.edge_sensors]

    api_utils.post_json_to_gateway_api(
        session=session,
        endpoint="/devices/config",
        edge_gateway=edge_gateway,
        json_data={
            "devices": devices,
            "params": config.model_dump()
        },
    )
    return {"message": "Devices configured successfully!"}


@api_router.post("/gateway/{gateway_uuid}/devices/ready")
async def ready_devices(gateway_uuid, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [device.device_name for device in edge_gateway.edge_sensors]

    api_utils.post_form_data_to_gateway_api(
        session=session,
        endpoint="/devices/ready",
        edge_gateway=edge_gateway,
        form_data={"devices": devices},
    )

    return {"message": "Devices ready successfully!"}

@api_router.post("/gateway/{gateway_uuid}/devices/start")
async def start_devices(gateway_uuid, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [device.device_name for device in edge_gateway.edge_sensors]

    api_utils.post_form_data_to_gateway_api(
        session=session,
        endpoint="/devices/start",
        edge_gateway=edge_gateway,
        form_data={"devices": devices},
    )

    # update working state to True for all devices.
    for device in devices:
        crud.update_edge_sensor_by_device_name(
            session=session,
            device_name=device["device_name"],
            fields={"working_state": True},
        )

    return {"message": "Devices started successfully!"}


@api_router.post("/gateway/{gateway_uuid}/devices/stop")
async def stop_devices(gateway_uuid, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [device.device_name for device in edge_gateway.edge_sensors]

    api_utils.post_form_data_to_gateway_api(
        session=session,
        endpoint="/devices/stop",
        edge_gateway=edge_gateway,
        form_data={"devices": devices},
    )

    # update working state to False for all devices.
    for device in devices:
        crud.update_edge_sensor_by_device_name(
            session=session,
            device_name=device["device_name"],
            fields={"working_state": False},
        )

    return {"message": "Devices stopped successfully!"}


@api_router.post("/gateway/{gateway_uuid}/devices/reset")
async def reset_devices(gateway_uuid, session=Depends(get_session)):
    edge_gateway = crud.read_edge_gateway_by_uuid(session=session, uuid=gateway_uuid)
    if edge_gateway is None:
        raise HTTPException(status_code=404, detail="Edge gateway not found")

    devices = [dev.device_name for dev in edge_gateway.edge_sensors]

    api_utils.post_form_data_to_gateway_api(
        session=session,
        endpoint="/devices/reset",
        edge_gateway=edge_gateway,
        form_data={"devices": devices},
    )
    return {"message": "Devices reset successfully!"}


@api_router.post("/export/measurement")
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
