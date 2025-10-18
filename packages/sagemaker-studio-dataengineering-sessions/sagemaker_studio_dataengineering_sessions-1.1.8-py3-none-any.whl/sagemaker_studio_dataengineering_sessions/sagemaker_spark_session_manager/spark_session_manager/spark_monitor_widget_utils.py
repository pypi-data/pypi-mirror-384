from IPython import get_ipython

import uuid
import json

SAGEMAKER_SESSION_INFOS_KEY = 'sagemaker_session_infos'
CURRENT_CONNECTION_KEY = 'current_connection'
EXECUTION_ID_KEY = 'execution_id'

def add_spark_monitor_widget_session_info_in_user_ns(session_infos_key, session_infos):
    if not session_infos_key:
        session_infos_key = SAGEMAKER_SESSION_INFOS_KEY + str(uuid.uuid4())
     
    if get_ipython():
        get_ipython().push({session_infos_key: json.dumps(session_infos)}, False)


def get_kernel_variable(key_str, default=None):
    for key in get_ipython().user_ns.keys():
        if key_str in key:
            data = get_ipython().user_ns.get(key)
            if data:
                return key, data

    return default, default


def get_session_infos_from_kernel():
    if get_ipython():
        key, data = get_kernel_variable(SAGEMAKER_SESSION_INFOS_KEY)
        if key and data:
            return key, json.loads(data)

    return None, None

def clear_current_connection_in_user_ns():
    session_infos_key, session_infos = get_session_infos_from_kernel()
    if not session_infos:
        return

    session_infos[CURRENT_CONNECTION_KEY] = None
    session_infos[EXECUTION_ID_KEY] = None
    get_ipython().user_ns[session_infos_key] = json.dumps(session_infos)


def set_current_connection_in_user_ns(session_infos, connection_name):
    if not session_infos:
        session_infos = {}

    session_infos[CURRENT_CONNECTION_KEY] = connection_name
    session_infos[EXECUTION_ID_KEY] = str(uuid.uuid4())
    return session_infos

def add_session_info_in_user_ns(connection_name, connection_type, session_id=None, application_id=None):
    session_infos_key, session_infos = get_session_infos_from_kernel()
    session_infos = set_current_connection_in_user_ns(session_infos, connection_name)
    session_info = {
            'connection_type': connection_type,
            'connection_name': connection_name,
            'session_id': session_id,
            'application_id': application_id
        }
    session_infos[connection_name] = session_info
    add_spark_monitor_widget_session_info_in_user_ns(session_infos_key=session_infos_key, session_infos=session_infos)

