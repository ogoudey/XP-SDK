from concepts.ego import Ego
from pathlib import Path
from concepts.network_config import NetworkConfig, NodeConfig
from concepts.compute_environment import ComputeEnvironment
from typing import Optional, List, Tuple
from . import network
from .errors import MainError
from concepts.computer import Computer

ego: Optional[Ego] = None
network_config: Optional[NetworkConfig] = None

# ------------ Configging ------------ #

def _get_capability_ids_from_claims(claims: List[str]) -> List[str]:
    return [capability for capability in claims] # optimistically granted

def self_realize(codebase_root: Path | str, capability_claims: List[str], features: Optional[dict] = None) -> List[str]:
    """
    Realizes the codebase
    """
    
    if type(codebase_root) is str:
        codebase_root = Path(codebase_root)
    codebase=codebase_root.name
    capability_ids = _get_capability_ids_from_claims(capability_claims)
    experience_dna = features
    global ego
    ego = Ego(
        codebase=codebase,
        capability_ids=capability_ids,
        experience_dna=experience_dna
    )
    return capability_ids

def list_capabilities(detail: bool = False) -> list:
    return network.list_capabilities(detail)

def describe_capability(capability_id: str) -> str:
    return network.describe_capability(capability_id)

def publish_capability(path: str, capability_id: str) -> dict:
    return network.publish_capability(path, capability_id)

def delete_capability(capability_id: str) -> None:
    network.delete_capability(capability_id)

def update_capability(capability_id: str, message: str):
    return network.update_capability_status(capability_id, message)

def see_capability(capability_id: str):
    return network.see_capability_status(capability_id)

def export_compute_environment():
    network.post_compute_environment()

def self_materialize() -> str:
    global subnet
    subnet = network.identify_compute_environment_subnet(Computer.identify())
    if subnet is None:
        raise network.NetworkCouldNotFind("CE not identified by the network!")
    else:
        print(f"(CE {Computer.identify()} belongs to subnet {subnet}, identified by the network...)")
    return subnet
    
def import_configs() -> NetworkConfig:
    global network_config
    network_config = network.import_configs(ego.capability_ids, Computer.identify())
    return network_config

def add_config(
    node_key: str,
    user: str,
    ip_address: str,
    port: int,
    password: str,
    command: List[str]
):
    global network_config
    if network_config is None:
        network_config = NetworkConfig()
    network_config.nodes.append(
        (node_key,
        NodeConfig(
            user=user,
            ip_address=ip_address,
            port=port,
            password=password,
            command=command)
        )
    )

def export_configs():
    if network_config is None:
        raise network.NetworkCouldNotFind("Network configuration is not set. Use `xp.add_config`")
    network.post_configs(network_config, Computer.identify())

# --------------- end Configging ------------- #

# ----------------- Capabilities --------------- #


# --------------- end Capabilities ---------------- #

def pin_experience():
    pass

def locate_experience():
    pass