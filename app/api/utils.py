import requests
import json
from app.api.model import crud
from functools import wraps


def post_pop_to_gateway_api(url, pop):
    auth_response = requests.post(
        url=f"{url}/auth",
        json={"pop": pop},
        headers={"Content-Type": "application/json"},
    )
    if auth_response.status_code != 200:
        raise Exception("Gateway authentication failed.")

    return auth_response.json()["jwt_token"]


def authenticate_to_gateway_api(session, edge_gateway):
    auth_response = requests.post(
        url=f"{edge_gateway.url}/auth",
        json={"pop": edge_gateway.proof_of_possession},
        headers={"Content-Type": "application/json"},
    )
    if auth_response.status_code != 200:
        raise Exception("Gateway authentication failed.")

    return crud.update_edge_gateway(
        uuid=edge_gateway.uuid,
        session=session,
        fields=auth_response.json(),
    )


def jwt_token_refresh_decorator(api_call_function):
    @wraps(api_call_function)
    def wrapper(session, edge_gateway, *args, **kwargs):
        response = api_call_function(session, edge_gateway, *args, **kwargs)
        if response.status_code == 401:  # Unauthorized => JWT token expired.
            # Re-authenticate
            edge_gateway = authenticate_to_gateway_api(session, edge_gateway)
            # Try the API call again with the new token
            return api_call_function(session, edge_gateway, *args, **kwargs)
        elif response.status_code != 200:  # Other error
            raise Exception(
                f"Gateway API call failed. Status code: {response.status_code}"
            )
        return response.json()

    return wrapper


@jwt_token_refresh_decorator
def get_from_gateway_api(session, edge_gateway, endpoint):
    return requests.get(
        url=f"{edge_gateway.url}{endpoint}",
        headers={"Authorization": f"Bearer {edge_gateway.jwt_token}"},
    )


@jwt_token_refresh_decorator
def post_form_data_to_gateway_api(session, edge_gateway, endpoint, form_data):
    return requests.post(
        url=f"{edge_gateway.url}{endpoint}",
        headers={"Authorization": f"Bearer {edge_gateway.jwt_token}"},
        data=form_data,
    )


@jwt_token_refresh_decorator
def post_json_to_gateway_api(session, edge_gateway, endpoint, json_data=None):
    return requests.post(
        url=f"{edge_gateway.url}{endpoint}",
        headers={"Authorization": f"Bearer {edge_gateway.jwt_token}"},
        json=json_data,
    )

@jwt_token_refresh_decorator
def post_file_to_gateway_api(session, edge_gateway, endpoint, file, form_data=None):
    return requests.post(
        url=f"{edge_gateway.url}{endpoint}",
        headers={"Authorization": f"Bearer {edge_gateway.jwt_token}"},
        data=form_data,
        files=file,
    )


@jwt_token_refresh_decorator
def post_command_to_gateway_api(session, edge_gateway, endpoint, command):
    return post_json_to_gateway_api(
        session=session,
        edge_gateway=edge_gateway,
        endpoint=endpoint,
        json_data={"command": command},
    )
