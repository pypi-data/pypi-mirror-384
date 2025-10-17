# Here is the place to but general helper functions

import ast
import json
from pathlib import Path
import toml
import pandas as pd
import warnings

from ._backend_calls import _backend_POST, _backend_PUT, _backend_GET


def load_file(filename: Path) -> dict | pd.DataFrame:
    """
    Load data from a file. The function currently supports JSON files.

    Parameters:
    filename (Path): The path to the file.

    Returns:
    dict: The data loaded from the file if it's a JSON.
    """
    if filename.suffix == '.csv':
        df = pd.read_csv(filename, sep=',', header=0,
                         index_col=None, na_values=['NA', '?'])
        return df

    elif filename.suffix == '.json':
        with open(filename, 'r') as file:
            return json.load(file)

    elif filename.suffix == '.toml':
        with open(filename, 'r') as file:
            return toml.load(file)

    else:
        raise ValueError(
            "You need to add the file format to the load_file function.")


def move_parameter_placeholder(component: dict) -> dict:
    """
    
    Because not every parameter from the parameter_unit.toml is on the main level of each component, but rather in a placeholder dictionary called "i_parameter_placeholder",
    we will move them to the main level for uniformity

    Refer to the relevant functions in the Backend:
    https://gitlab.com/ai4ce/ai4ce-03-backend/-/blob/main/backend/v2/routers/validators.py?ref_type=heads#L501-515
    https://gitlab.com/ai4ce/ai4ce-03-backend/-/blob/main/backend/v2/schemas/components/_base_component_schema.py?ref_type=heads#L18-67

    And the parameter unit toml in the AI4CE main repo
    https://gitlab.com/ai4ce/public-info/-/raw/main/docs/parameter_unit_list.toml
    """

    for key, value in component.get("i_parameter_placeholder", {}).items():
        if key not in component or component[key] is None:
            component[key] = value
        elif isinstance(value, list):
            component[key].extend(value)
        else:
            warnings.warn(f"Found conflicting value for key '{key}': {component[key]} vs {value}")
    return component

def get_running_backend_version() -> str:
    """Get the latest version of the backend from the openapi.json file.
    """
    status_code, response = _backend_GET("/openapi.json")
    if status_code == 200 and isinstance(response, dict) and "info" in response and "version" in response["info"]:
        return response["info"]["version"]
    return "unknown"
