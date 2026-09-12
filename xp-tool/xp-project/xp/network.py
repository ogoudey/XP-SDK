from typing import List, Optional, Tuple
from pydantic import BaseModel

from concepts.compute_environment import ComputeEnvironment
from concepts.network_config import NetworkConfig
from . import auth
import requests
from concepts.computer import Computer

GATEWAY_URL = "https://www.olimn.com"
"""
class NodeConfig(BaseModel):
    user: str
    ip_address: str
    port: int
    password: str
    command: List[str]

class NetworkConfig(BaseModel):
    compute_environment_id: str
    nodes: List[Tuple[str, Optional[NodeConfig]]] = []
"""
class NetworkCouldNotFind(Exception):
    pass

class ComputeEnvironment(BaseModel):
    compute_environment_id: str
    cidr: str
    description: Optional[str] = None

def import_configs(capability_ids: List[str], compute_environment_id: str) -> NetworkConfig:
    resp = requests.get(
        f"{GATEWAY_URL}/configs",
        params={
            "capability_ids": capability_ids,
            "compute_environment_id": compute_environment_id,
        },
        headers=_auth_headers(),
    )
    resp.raise_for_status()
    return NetworkConfig.model_validate(resp.json())

def identify_compute_environment_subnet(compute_environment_id: str) -> Optional[ComputeEnvironment]:
    resp = requests.get(
        f"{GATEWAY_URL}/compute_environment/{compute_environment_id}",
        headers=_auth_headers(),
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()

def post_compute_environment() -> None:
    payload = {
        "compute_environment_id": Computer.identify(),
        "cidr": Computer.identify_network(),
        "description": None,
    }
    resp = requests.post(
        f"{GATEWAY_URL}/compute_environment",
        json=payload,
        headers=_auth_headers(),
    )
    resp.raise_for_status()

def post_configs(config: NetworkConfig, compute_environment_id: str) -> None:
    resp = requests.post(
        f"{GATEWAY_URL}/configs",
        json={
            "network_config": config.model_dump(),
            "compute_environment_id": compute_environment_id,
        },
        headers=_auth_headers(),
    )
    resp.raise_for_status()

def _auth_headers() -> dict:
    token_data = auth.load_token()
    token = token_data["access_token"] if isinstance(token_data, dict) else token_data
    return {"Authorization": f"Bearer {token}"}