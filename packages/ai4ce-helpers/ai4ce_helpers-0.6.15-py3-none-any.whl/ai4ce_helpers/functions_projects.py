import ast
import json
from pathlib import Path
import toml
import pandas as pd

from ._backend_calls import _backend_POST, _backend_PUT, _backend_GET
from .functions import load_file

def create_new_project(project_info: dict):
    """Create a new project in the backend.
    Params:
        project_info(dict):
    Returns:
        dict:
    """
    status_code, message = _backend_POST(
        endpoint=f"/v2/projects/", data=project_info)
    if status_code == 200:
        return message
    else:
        print(f"Error creating project: {message}")
        return {"error": message}


def get_list_of_all_project_infos() -> list[tuple[int, str, str]]:
    # check for refactoring
    """A function to connect to the backend and get a list of all projects
    in the current project data base.

    Params:
        None

    Returns:
        tuple[int, str, str]: A list of tuples containing project ID, project name, and last modified date.
    """

    status_code, projects = _backend_GET(endpoint=f"/v2/projects/")
    project_ids: list[tuple[int, str, str]] = []
    if status_code == 200:
        for project in projects:
            project_ids.append((project["id"], project["project_name"], project["modified"]))
        return project_ids
    else:
        print(f"Error fetching projects: {projects}")
        return []

def get_project_info(project_id: int) -> dict:
    status_code, project_info = _backend_GET(endpoint=f"/v2/projects/{project_id}/")
    return project_info


def set_project_name(project_id: int, project_name: str) -> dict:
    """A function to set the project name of a specific project, identified by its ID.

    Params:
        project_id (int): The project Identification Number
        project_name(str): Name of the project/mission, eg OPS-Sat
    Returns:
        dict: json response from backend
    """

    data = {
        "project_id": project_id,
        "project_name": project_name,
    }

    # status, msg = _backend_put(endpoint=f"/v2/projects/{project_id}", data=data)
    # return (status, msg)
    status_code, msg = _backend_PUT(endpoint=f"/v2/projects/{project_id}/", data=data)
    if status_code != 200:
        print(f"Error setting project name: {msg}")
        return {"error": msg}
    return msg

def get_recent_project() -> tuple[int, str, str]:
    status_code, response = _backend_GET(endpoint=f"/v2/projects/recent/")
    if status_code != 200:
        print(f"Error fetching recent project: {response}")
        return (None, "No recent project found.")
    return (response["id"], response["project_name"], response["modified"])


def get_mission_orbit(project_id: int) -> dict:
    # refactored
    """A function to get the mission orbit info for a specific project based on its ID.
    Params:
        project_id (int): The project Identification Number

    Returns:
        dict: Keplerian elements to define the orbit
    """

    status_code, response = _backend_GET(endpoint=f"/v2/projects/{project_id}/mission/")
    if status_code != 200:
        print(f"Error fetching mission/orbit info: {response}")
        return {"error": response}
    return response["orbit"]


def set_mission_orbit(project_id: int, orbit_info: dict) -> dict:
    # refactored
    """A function to set the orbit in the project database. Will create an empty mission parent if it does not exist.
    Params:
        project_id (int): The project Identification Number
        orbit_info(dict): Information about the satellite's orbit
    Returns:
        dict: 
     """
    # check if project exists
    status_code, project_info = _backend_GET(endpoint=f"/v2/projects/{project_id}/")
    if status_code != 200:
        print(f"Error fetching project info: {project_info}")
        return {status_code: project_info}
    status_code, mission_info = _backend_GET(
        endpoint=f"/v2/projects/{project_id}/mission/")
    if status_code == 404:
        print(f"No mission info found for project {project_id}. Creating new mission info.")
        mission_info = {
            "mission_name": f"Mission {project_info['project_name']}",
            "orbit": orbit_info,
        }
        status_code, response = _backend_POST(endpoint=f"/v2/projects/{project_id}/mission/", data=mission_info)
        if status_code != 201:
            print(f"Error creating mission info: {response}")
            return {status_code: response}
        return response
    elif status_code == 200:
        # update possible mission_info["orbit"] with new orbit_info
        print(f"Mission info found for project {project_id}. Updating orbit info.")
        mission_info["orbit"].update(orbit_info)
        status_code, response = _backend_PUT(endpoint=f"/v2/projects/{project_id}/mission/", data=mission_info)
        if status_code != 200:
            print(f"Error updating mission info: {response}")
            return {status_code: response}
        return response
    else:
        print(f"Error fetching mission info: {mission_info}")
        return {status_code: mission_info}


def get_enabled_components(nested_dict, enabled_components=None) -> list:
    # check for refactoring
    """
    Recursively traverses a nested dictionary to find and return a list of components that are enabled.

    Parameters:
    nested_dict (dict): The nested dictionary to traverse.
    enabled_components (list, optional): A list to store the names of the enabled components.
                                         Defaults to None, in which case a new list is created.

    Returns:
    list: A list of the names of the enabled components.
    """

    if enabled_components is None:
        enabled_components = []

    for key, value in nested_dict.items():
        if isinstance(value, dict):
            if value.get('Enabled') == True:
                enabled_components.append(key)
                pass
            get_enabled_components(value, enabled_components)

    return enabled_components




def traverse_and_modify(d: dict, sys_config_enabled: dict):
    # check for refactoring
    for key, value in d.items():
        if isinstance(value, dict):
            component = key
            traverse_and_modify(d=value, sys_config_enabled=sys_config_enabled)
        else:
            # This block executes only if `value` is not a dict, i.e., at the deepest level
            # if d["Enabled"] is True or d["Enable"] is True or :
            try:
                if d["Enabled"] is True:
                    sys_config_enabled.update(enable_component(
                        component_name=key, data=load_file(Path("data/backend_sys_default.json"))))
            except KeyError as e:
                print("Error: ", e)


def enable_component(component_name: str, data: dict) -> dict:
    # check for refactoring
    """Recursively search for a component in the nested dictionary from the backend
    and set 'enabled' to True if the feature name matches any key or value (case-insensitive).

    Parameters:
        data (dict): The nested dictionary to search within.
        feature_name (str): The feature name to search for, case-insensitively.

    Returns:
        dict: edited dict
    """

    for key, value in data.items():
        #  print(key, value)
        if isinstance(value, dict):
            enable_component(component_name, value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    enable_component(component_name, item)
        if key.lower() == component_name.lower() or str(value).lower() == component_name.lower():
            data['enabled'] = True
    return data


def set_sys_arch(project_id: int, sys_arch: dict) -> dict:
    # refactored
    """A function to set the system architecture in the project database. Updates the existing architecture if it exists.
    Params:
        project_id (int): The project Identification Number
        sys_arch(dict): Information about the satelllite's modules, which form the system architecture
    Returns:
        dict: Backend version of the system architecture or the status_code and error message.
     """

    sys_arch_example = {
        "system_type": "string",
        "satellite_class": "string",
        "OAP_W": 0,
        "requirements": {},
        "aodcs": {
          "enabled": False,
          "amount_of_entities": 0,
          "description": "string",
          "eFunctions": [],
          "type": "string",
          "components": [],
          "depending_parameters": [],
          "cmg": {
            "enabled": False,
            "amount_of_entities": 0,
            "description": "string",
            "eFunctions": [],
            "requirements": {}
          },
          "magnetorquers": {
            "enabled": False,
            "amount_of_entities": 0,
            "description": "string",
            "eFunctions": [],
            "requirements": {}
          },
        },
        "tcs": {
          "enabled": False,
          "amount_of_entities": 0,
          "description": "string",
          "eFunctions": [],
          "requirements": {},
          "coatings": {
            "enabled": False,
            "amount_of_entities": 0,
            "description": "string",
            "eFunctions": [],
            "requirements": {}
          },
          "heaters": {
            "enabled": False,
            "amount_of_entities": 0,
            "description": "string",
            "eFunctions": [],
            "requirements": {}
          }
        }
    }

    status_code, response = _backend_POST(
        endpoint=f"/v2/projects/{project_id}/system/", data=sys_arch)
    if status_code == 201:
        return response
    if status_code == 400:
        status_code, response = _backend_PUT(
            endpoint=f"/v2/projects/{project_id}/system/", data=sys_arch)
        if status_code == 200:
            return response

    return {status_code: response}


def get_sys_arch(project_id: int) -> dict:
    """A function to get the system configuration info for a specific project based on its ID.
    Params:
        project_id (int): The project Identification Number

    Returns:
        dict: System information
    """

    status_code, response = _backend_GET(
        endpoint=f"/v2/projects/{project_id}/system/")
    return response

#  set_comp_list(project: int, not_yet_defined: dict)
# For each selected system generator, we need a place to store the corresponding found comp lists
# Every generator can produce n sets of components


def set_sys_generator(project_id: int, sys_gen_info: dict) -> dict:
    response = _backend_POST(
        endpoint=f"/v2/projects/{project_id}/sysgen/", data=sys_gen_info)
    return response


def update_sys_generator(project_id: int, sys_gen_info: dict) -> dict:
    response = _backend_PUT(
        endpoint=f"/v2/projects/{project_id}/sysgen/", data=sys_gen_info)
    return response


def set_trained_model(project_id: int, model_info: dict) -> dict:
    """A function to upload a trained AI model.
    Params:
        project_id (int): The project Identification Number
        model (ASKYOUNES): info about model

    Returns:
        dict: Upload server response
    """

    sta, msg = _backend_POST(endpoint=f"/v2/projects/{project_id}/sysgen/",
                             data=model_info)

    return msg


def get_prepared_system_generator_info(project_id: int) -> list:
    """A function to get all prepared system generators.
    Params:
        project_id (int): The project Identification Number

    Returns:
        list: list of dictionaries with infos for the prepared system generators
    """

    status_code, response = _backend_GET(
        endpoint=f"/v2/projects/{project_id}/sysgen/")
    return response


def set_sys_arch_defaults(system: dict, project_id: int) -> dict:
    """Translate a system configuration from a TOML file dictionary previously handled by load_file() to a format that can be uploaded to the backend.

    Parameters:
    system (dict): The system configuration in TOML format.

    Returns:
    dict: The system configuration in a format that can be uploaded to the backend.
    """

    sys_config_enabled = {}
    # Loading System Configuration
    for key, value in system.items():
        if isinstance(value, dict):
            traverse_and_modify(d=value, sys_config_enabled=sys_config_enabled)

    response = set_sys_arch(project_id=project_id, sys_arch=sys_config_enabled)
    pass
    return response


def set_new_project(project_info: dict) -> dict:
    """Create a new project in the backend.
    Params:
        project_info(dict):
    Returns:
        dict:
    """
    status_code, response = _backend_POST(
        endpoint="/v2/projects/", data=project_info)
    if status_code == 201:
        return response
    return {status_code: response}


# def get_trained_model(project_id: int) -> mode: ASKYOUNES
#     pass


# def set_train_log(project_id: int, logs: ASKYOUNES) -> DB_response: ASKALEX
#     pass


# def get_train_logs(project_id: int) -> logs: ASKYOUNE   pass

