from anyio import sleep
from .functions_projects import get_list_of_all_project_infos, get_recent_project
from ._backend_calls import _backend_GET
from .functions import move_parameter_placeholder
import streamlit as st

def st_project_selector(title: str = None):

    projects_simple_list = get_list_of_all_project_infos()

    if title:
        st.subheader(title)


    if st.button("Get recent project"):
        (st.session_state["project_id"],
         st.session_state["project_name"],
         st.session_state["modified"]) = get_recent_project()

    # Let the user select a project from the list of projects in the project DB
    selected_project = st.selectbox("Project",
                                    projects_simple_list,
                                    index=None,
                                    placeholder="Select a project",
                                    format_func=lambda x: f"{x[1]}")
    if selected_project is not None:
        st.session_state["project_id"] = selected_project[0]
        st.session_state["project_name"] = selected_project[1]

    if 'project_id' not in st.session_state or st.session_state['project_id'] is None:
        st.metric(label="   ",
              value="<-- Please select")
    else:
        st.metric(label=f"Active project ID: {st.session_state['project_id']}",
                  value=f"{st.session_state['project_name']}")
        
    return st.session_state.get("project_id", None)


def st_system_generator_selector():
    """A function which adds a system generator selector to the top of the page.
    A system generator is the stored as part of the project in the backend.

    Suitable to be used in conjunction with st_project_selector().
    """
    # check if the project is set and exit without doing anything if not
    if 'project_id' not in st.session_state:
        return None

    # get the list of system generators for the current project
    status_code, system_generators = _backend_GET(f"/projects/{st.session_state['project_id']}/sysgen/")

    # if successful display a selector for the system generators based on their IDs and names
    if status_code == 200:
        selected_sysgen = st.selectbox("System Generator",
                                            [(sysgen["id"], sysgen["description"])
                                             for sysgen in system_generators],
                                            index=None,
                                            placeholder="Select a system generator",
                                            format_func=lambda x: f"{x[1]}")

        if selected_sysgen is not None:
            st.session_state["sysgen_id"] = int(selected_sysgen[0])
            st.session_state["sysgen_description"] = selected_sysgen[1]
    else:
        st.error(f"Error while loading system generators: {system_generators}")

    # After selecting a system generator, extract and present the generated designs from system_generators with the ID system_generators_id
    if 'sysgen_id' not in st.session_state:
        st.stop()
    
    status_code, system_generator = _backend_GET(f"/projects/{st.session_state['project_id']}/sysgen/{st.session_state['sysgen_id']}/")
    if status_code == 200:
        st.session_state["system_generator"] = system_generator
        st.session_state["generated_designs"] = system_generator.get("generated_designs")
    else:
        st.error(f"Error while loading generated designs: {system_generator}")

    return st.session_state.get("sysgen_id", None)

def st_generated_design_selector():
    """A function which adds a generated design selector to the top of the page.
    A generated design is the stored as part of the project in the backend.

    Suitable to be used in conjunction with st_project_selector().
    """
    # check if the project is set and exit without doing anything if not
    if 'project_id' not in st.session_state:
        return None

    # get the list of system generators for the current project
    status_code, system_generators = _backend_GET(f"/projects/{st.session_state['project_id']}/sysgen/")

    # if successful display a selector for the system generators based on their IDs and names
    if status_code == 200:
        selected_sysgen = st.selectbox("System Generator",
                                            [(sysgen["id"], sysgen["description"])
                                             for sysgen in system_generators],
                                            index=None,
                                            placeholder="Select a system generator",
                                            format_func=lambda x: f"{x[1]}")

        if selected_sysgen is not None:
            st.session_state["sysgen_id"] = int(selected_sysgen[0])
            st.session_state["sysgen_description"] = selected_sysgen[1]
    else:
        st.error(f"Error while loading system generators: {system_generators}")

    # After selecting a system generator, extract and present the generated designs from system_generators with the ID system_generators_id
    if 'sysgen_id' in st.session_state:
        status_code, system_generator = _backend_GET(f"/projects/{st.session_state['project_id']}/sysgen/{st.session_state['sysgen_id']}/")
        if status_code == 200:
            st.session_state["system_generator"] = system_generator
            st.session_state["generated_designs"] = system_generator.get("generated_designs")
        else:
            st.error(f"Error while loading generated designs: {system_generator}")

    # display the generated designs (comp_list_uids) in a selectbox
    # Only show design selector and warnings if a system generator has been selected
    if 'sysgen_id' in st.session_state:
        if 'generated_designs' in st.session_state and st.session_state["generated_designs"]:
            selected_generated_design = st.selectbox("Generated Design",
                                             [(design["id"], design["comp_list_uids"])
                                              for design in st.session_state["generated_designs"]],
                                             index=None,
                                             placeholder="Select a generated design",
                                             format_func=lambda x: f"Design #{x[0]}, Components: {x[1]}")
            if selected_generated_design is not None:
                st.session_state["generated_design_id"] = selected_generated_design[0]
                st.session_state["generated_design_comp_list_uids"] = selected_generated_design[1]
        else:
            st.warning("No generated designs available for the selected system generator.")

    # display the selected system generator and generated design
    if 'sysgen_description' in st.session_state and 'generated_design_comp_list_uids' in st.session_state:
        st.metric(label=f"Selected System Generator (ID: {st.session_state['sysgen_id']})",
                  value=st.session_state["sysgen_description"])
        st.metric(label=f"Selected Generated Design (ID: {st.session_state['generated_design_id']})",
                  value=str(st.session_state["generated_design_comp_list_uids"]))
    elif 'sysgen_description' in st.session_state:
        st.metric(label="Selected System Generator",
                  value=st.session_state["sysgen_description"])
    
    return st.session_state.get("generated_design_id", None)


def st_load_components(uid_list: list[str] = None) -> dict[str, dict]:
    """Loads the defined UIDs from the backend into the session state under session_state['db']['components'][{uid}]
    If no list of UIDs is given, check the current projects system generators and iterate over all generated designs with their comp_list_uids.

    Displays a cute spinner while loading.
    """

    # exit if no data is given to act upon (selection has not been made previously)
    if 'project_id' not in st.session_state and uid_list is None:
        return {}

    # create sessions state db if not exists
    if 'db' not in st.session_state:
        st.session_state['db'] = {}
    if 'components' not in st.session_state['db']:
        st.session_state['db']['components'] = {}

    # show infobox with loading message
    with st.spinner("Loading components..."):
        if uid_list is None and 'project_id' in st.session_state:
            status_code, system_generators = _backend_GET(f"/projects/{st.session_state['project_id']}/sysgen/")
            for sysgen in system_generators:
                status_code, system_generator = _backend_GET(f"/projects/{st.session_state['project_id']}/sysgen/{sysgen['id']}/")
                if status_code == 200:
                    for design in system_generator.get("generated_designs", []):
                        for component_uid in design.get("comp_list_uids", []):
                            if component_uid not in st.session_state['db']['components']:
                                status_code, component = _backend_GET(f"/v2/components/{component_uid}")
                                if status_code == 200:
                                    st.session_state['db']['components'][component_uid] = component
                                else:
                                    st.error(f"Error loading component {component_uid}: {component}")
                else:
                    st.error(f"Error loading system generator {sysgen['id']}: {system_generator}")

        else:
            # Load each component by UID
            for component_uid in uid_list:
                status_code, component = _backend_GET(f"/v2/components/{component_uid}")
                if status_code == 200:
                    st.session_state['db']['components'][component_uid] = component
                else:
                    st.error(f"Error loading component {component_uid}: {component}")


    for component_uid, component in st.session_state['db']['components'].items():
        st.session_state['db']['components'][component_uid] = move_parameter_placeholder(component)
    
    return st.session_state['db']['components']