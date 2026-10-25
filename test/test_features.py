import xp
from xp import network
from pathlib import Path
from xp.errors import MainError
import rich

def test_self_realize():
    print(f"File name: {__name__}")
    print(f"Parent: {Path(__name__).resolve()}")
    print(f"XP Project: {Path(__name__).parent / 'xp-project'}")
    print(f"Self-realization: {xp.self_realize(Path(__name__).resolve(), ["idk"])}")

def test_import_configs_null():
    """Verify server connection really..."""
    print(f"Self-realization: {xp.self_realize(Path(__name__).resolve(), ["idk"])}")

def test_self_materialize_non_network():
    try:
        ce_id = xp.self_materialize()
    except network.NetworkCouldNotFind as e:
        print(f"Handled: {e}")

def test_export_configs_null():
    try:
        xp.export_configs()
    except MainError as e:
        print(f"Handled: {e}")
    except network.NetworkCouldNotFind as e:
        print(f"Handled {e}")

def test_export_configs_null_ce():
    xp.export_compute_environment()
    xp.add_config(
        node_key="localhostolin",
        user="olin",
        ip_address="localhost",
        port=5000,
        password="",
        command=["echo", "hello world"]
    )
    try:
        xp.export_configs()
    except network.NetworkCouldNotFind as e:
        print(f"Handled {e}")

def test_export_configs():
    xp.export_compute_environment()
    xp.add_config(
        node_key="localhostolin",
        user="olin",
        ip_address="localhost",
        port=5000,
        password="",
        command=["echo", "hello world"]
    )
    try:
        xp.export_configs()
    except MainError as e:
        print(f"Handled: {e}")

def test_import_configs():
    xp.add_config(
        node_key="localhostolin",
        user="olin",
        ip_address="localhost",
        port=5000,
        password="",
        command=["echo", "hello world"]
    )
    xp.export_configs()
    xp.self_materialize()
    network_config = xp.import_configs()
    rich.print(network_config)
