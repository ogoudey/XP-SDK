# ------------- Trust Practice Example ------------ #
import xp

global_entity = "object1"
global_capability_id = "cap_162"

# --------------- Initialize Universal Capability Model ----------- #
# Initialize the initial capability in the db
from typing import Union
from pathlib import Path
def run_initialize(path_str: str):
    xp.publish_capability(path_str, global_capability_id)
    print(xp.describe_capability(global_capability_id))

# ---- Capability Former ---- #
# simple serialization.
import json
import rich
from rich.prompt import Prompt

def _parse_input_value(val_str: str):
    """Attempts to parse input string into JSON types (dict, list, int, bool).
    Falls back to raw string if parsing fails."""
    val_str = val_str.strip()
    if not val_str:
        return None
    try:
        return json.loads(val_str)
    except json.JSONDecodeError:
        return val_str

def _update_nested_dict(d: dict) -> dict:
    """Recursively prompt to view, add, or modify keys including nested dicts/JSON."""
    keys = list(d.keys())
    rich.print(f"Current keys: [bold cyan]{keys}[/bold cyan]")
    
    # Allow picking an existing key OR entering a new key
    selected_key = Prompt.ask("Which key to modify (or enter a new key name)?")
    
    current_val = d.get(selected_key)
    
    if current_val is not None:
        rich.print(f"Current value for [bold]{selected_key}[/bold]: {current_val}")

    new_val_raw = Prompt.ask(
        f"Enter new value for [bold]{selected_key}[/bold] (JSON dict/list, string, or leave blank to navigate)"
    )
    
    parsed_val = _parse_input_value(new_val_raw)
    
    if parsed_val is not None:
        # If the user typed a JSON object like {"newkey": "newvalue"}, 
        # it is parsed into a Python dict here.
        if isinstance(parsed_val, dict) and isinstance(current_val, dict):
            # Merge into existing dict or overwrite
            current_val.update(parsed_val)
            d[selected_key] = current_val
        else:
            d[selected_key] = parsed_val
    
    # If the resulting target field is a dictionary (either previously or newly parsed),
    # give the option to recurse further into it.
    if isinstance(d.get(selected_key), dict):
        if Prompt.ask(f"Recurse into [bold]{selected_key}[/bold]?", choices=["y", "n"], default="y") == "y":
            d[selected_key] = _update_nested_dict(d[selected_key])
            
    return d

def _update_string(s: str) -> Union[dict, str]:
    new_val_raw = Prompt.ask(
        f"Enter new value for [bold]{s}[/bold] (JSON dict/list, string, or leave blank to navigate)"
    )
    
    parsed_val = _parse_input_value(new_val_raw)

    if isinstance(parsed_val, dict):
        if Prompt.ask(f"Recurse into [bold]{parsed_val}[/bold]?", choices=["y", "n"], default="y") == "y":
            parsed_val = _update_nested_dict(parsed_val)

    return parsed_val

def run_practice():

    # Moment 1 of trust
    entity_to_cap_id = {
        global_entity: global_capability_id
    }
    initial_capability = xp.see_capability(entity_to_cap_id[global_entity])
    rich.print(
        f"[bold yellow]Initial capability:[/bold yellow]"
    )
    rich.print(initial_capability)
    capability_model = initial_capability["status"]

    while True:
        rich.print("\n[bold green]Current Capability Model:[/bold green]")
        rich.print(capability_model)

        # Main prompt loop
        action = Prompt.ask(
            "\nActions: [u]u[/u]pdate model, [s]e[/s]nd update to API, [q]uit",
            choices=["u", "s", "q"],
            default="u",
        )

        if action == "q":
            break

        if action == "u":
            # Select target entity
            entities = list(entity_to_cap_id.keys())
            entity = Prompt.ask("Which entity?", choices=entities)

            # Traverse and modify the capability model recursively
            if isinstance(capability_model, dict):
                capability_model = _update_nested_dict(capability_model)
            elif isinstance(capability_model, str):
                capability_model = _update_string(capability_model)

        elif action == "s":
            # Send payload to API
            entity = Prompt.ask(
                "Select entity ID to update", choices=list(entity_to_cap_id.keys())
            )
            target_cap_id = entity_to_cap_id[entity]

            payload = json.dumps(capability_model)
            xp.update_capability(target_cap_id, payload)
            rich.print(
                f"[bold green]Successfully sent updated capability for {entity} ({target_cap_id})![/bold green]"
            )
            seen = xp.see_capability(target_cap_id)
            rich.print(
                f"[bold yellow]Found:[/bold yellow]"
            )
            rich.print(seen)





import sys
if __name__ == "__main__":
    match sys.argv[1]:
        case "init":
            run_initialize(sys.argv[2])
        case "practice":
            run_practice()
        case _:
            print("Provide \"init\" or \"practice\"...")
            sys.exit(1)