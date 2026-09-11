from concepts.ego import Ego
from pathlib import Path
from concepts.network_config import NetworkConfig, NodeConfig
from concepts.compute_environment import ComputeEnvironment
from typing import Optional, List

ego: Optional[Ego] = None
compute_environment: Optional[ComputeEnvironment] = None
network_config: Optional[NetworkConfig] = None


def _get_capability_ids_from_claims(claims: List[str]) -> List[str]:
    return [capability for capability in claims] # optimistically granted

def self_realize(codebase_root: Path, capability_claims: List[str], features: Optional[dict] = None) -> List[str]:
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

from concepts.computer import Computer
def self_materialize() -> str:
    _id = Computer.identify()
    global compute_environment
    compute_environment = network.identify_compute_environment(_id)
    return _id
    
def import_configs() -> NetworkConfig:
    global network_config
    network_config = network.import_configs(ego.capability_ids, compute_environment.get_id())
    return network_config

def add_config(
    user: str,
    ip_address: str,
    port: int,
    password: str,
    command: List[str]
):
    global network_config
    if network_config is None:
        network_config = NetworkConfig()
    network_config.nodes.append(NodeConfig(
        user=user,
        ip_address=ip_address,
        port=port,
        password=password,
        command=command
    ))

def export_configs():
    if network_config is None:
        raise ValueError("Network configuration is not set. Use `xp.add_config`")
    network.post_configs(network_config, compute_environment.get_id())

def pin_experience():
    pass

def locate_experience():
    pass