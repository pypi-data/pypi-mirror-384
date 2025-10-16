import ast
import json
from pathlib import Path
import toml
import pandas as pd

from ._backend_calls import _backend_POST, _backend_PUT, _backend_GET



def get_tags_from_string(str_of_tags: str) -> list[str]:
    """
    example_tags_str = "['satellite', 'power', 'solar-panels']"
    check https://gitlab.com/ai4ce/ai4ce-03-backend/-/blob/main/backend/v2/schemas/components/_uid_maps.py for valid tags
    """
    # The string representation of a list of tags

    # Convert the string to an actual list using ast.literal_eval
    tags: list = ast.literal_eval(str_of_tags)
    return tags


def comp_create(comp_info: dict) -> dict:
    """Create a new component in the backend.
    Params:
        comp_info(dict): Information about the component
    Returns:
        dict:
    """
    status_code, msg = _backend_POST(
        endpoint=f"/v2/components/", data=comp_info)
    return status_code, msg

def export_components() -> dict:
    """Fetches all decisions from the DecisionDB and returns them as a dictionary.

    Returns:
        dict: A dictionary containing all decisions fetched from the DecisionDB.
    """
    status_code, response = _backend_GET(endpoint="/v2/components/export/")
    return response

def get_comp_statistics() -> dict:

    status_code, response = _backend_GET(endpoint="/v2/streamlit/db/stats/components")
    return response


def split_uid(uid: str) -> tuple[str, str, str, int | str]:
    """Splits a component UID into its constituent parts: type, subtype, and name.

    Args:
        uid (str): The UID of the component in the format 'type-subtype-name'.

    Returns:
        tuple: A tuple containing the type, subtype, and name of the component.
    """
    try:
        system_uid, subsystem_uid, component_class, component_id = uid.split("_", 3)
        try:
            component_id = int(component_id)
        except ValueError:
            pass
        return system_uid, subsystem_uid, component_class, component_id
    except ValueError:
        raise ValueError("Invalid UID format. Expected UID format: <system>_<subsystem>_<component_class>_<component_id>")