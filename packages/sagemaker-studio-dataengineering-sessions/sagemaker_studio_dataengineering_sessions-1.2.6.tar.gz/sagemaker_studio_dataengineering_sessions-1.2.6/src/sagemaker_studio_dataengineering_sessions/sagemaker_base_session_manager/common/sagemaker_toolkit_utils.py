import datetime

from typing import Optional
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import CONNECTION_TYPE_ATHENA, CONNECTION_TYPE_IAM, \
    CONNECTION_TYPE_SPARK_GLUE, CONNECTION_TYPE_GENERAL_SPARK, CONNECTION_TYPE_SPARK_EMR_SERVERLESS, METADATA_CONTENT, \
    DATAZONE_ENDPOINT_URL, DATAZONE_DOMAIN_REGION, DOMAIN_ID, PROJECT_ID, DEFAULT_IPYTHON_NAME, \
    SAGEMAKER_DEFAULT_GLUE_CONNECTION_NAME_EXPRESS, SAGEMAKER_DEFAULT_ATHENA_CONNECTION_NAME_EXPRESS, \
    SAGEMAKER_DEFAULT_GLUE_COMPATIBILITY_CONNECTION_NAME, SAGEMAKER_DEFAULT_GLUE_CONNECTION_NAME_DEPRECATED, \
    SAGEMAKER_DEFAULT_GLUE_FINE_GRAINED_CONNECTION_NAME, SAGEMAKER_DEFAULT_REDSHIFT_CONNECTION_NAME, SAGEMAKER_DEFAULT_ATHENA_CONNECTION_NAME
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.exceptions import ConnectionNotSupportedException, \
    ConnectionNotFoundException
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.gateways.datazone_gateway import DataZoneGateway
from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.constants import CONNECTION_TYPE_REDSHIFT, \
    CONNECTION_TYPE_SPARK_EMR_EC2, SAGEMAKER_DEFAULT_CONNECTION_DISPLAYNAME, SAGEMAKER_DEFAULT_CONNECTION_NAME, SAGEMAKER_DEFAULT_CONNECTION_NAME_EXPRESS

EMR_EC2_ARN_KEY_WORD = "cluster"
EMR_SERVERLESS_ARN_KEY_WORD = "applications"


class SageMakerToolkitUtils(object):
    _connection_type_mapping = {
        CONNECTION_TYPE_GENERAL_SPARK : [],
        CONNECTION_TYPE_REDSHIFT: [],
        CONNECTION_TYPE_ATHENA: []
    }
    _datazone_gateway = DataZoneGateway()
    _connection_name_to_connection_id_mapping = {}
    _connection_id_to_connection_details_mapping = {}
    _connection_id_last_cached_time = {}
    _connection_list_last_cached_time = None
    _glue_connection_names = []
    _cache_time_minutes = 5
    _is_express_mode = None
    _default_connection = None
    _default_spark_connection = None
    _default_sql_connection = None

    @classmethod
    def get_connection_type_mapping(cls):
        if (not cls._connection_list_last_cached_time or (cls._connection_list_last_cached_time
                and datetime.datetime.now() - cls._connection_list_last_cached_time > datetime.timedelta(minutes=cls._cache_time_minutes))):
            try:
                cls._cache_connection_list_from_datazone()
            except:
                pass
        return cls._connection_type_mapping

    @classmethod
    def get_connection_detail(cls, sagemaker_connection_name: str, with_secret: Optional[bool] = False) -> dict:
        if (cls._is_default_ipython(sagemaker_connection_name)): 
            # This function should never be called with default IPython name
            raise ValueError(f"Invalid sagemaker_connection_name: {sagemaker_connection_name}")
        connection_detail = cls._get_connection_detail_with_connection_name(
            sagemaker_connection_name=sagemaker_connection_name, with_secret=with_secret)
        return connection_detail

    @classmethod
    def is_connection_valid(cls, sagemaker_connection_name) -> bool:
        if (cls._is_default_ipython(sagemaker_connection_name)): 
            return True
        try:
            cls.get_connection_detail(sagemaker_connection_name=sagemaker_connection_name)
            return True
        except:
            return False

    @classmethod
    def get_connection_detail_from_id(cls, connection_id: str, with_secret: Optional[bool] = False) -> dict:
        return cls._get_connection_detail_with_connection_id(connection_id, with_secret=with_secret)

    @classmethod
    def get_connection_type(cls, sagemaker_connection_name: str) -> str:
        if (cls._is_default_ipython(sagemaker_connection_name)): 
            return CONNECTION_TYPE_IAM
        if sagemaker_connection_name == SAGEMAKER_DEFAULT_CONNECTION_DISPLAYNAME:
            sagemaker_connection_name = cls._get_default_connection_name()
        connection_detail = cls.get_connection_detail(sagemaker_connection_name=sagemaker_connection_name)
        connection_type = connection_detail["type"]
        if ((connection_type == CONNECTION_TYPE_ATHENA
             or connection_type == CONNECTION_TYPE_REDSHIFT)
                or connection_type == CONNECTION_TYPE_IAM):
            return connection_type
        elif connection_type == CONNECTION_TYPE_GENERAL_SPARK:
            if connection_detail["props"] and "sparkGlueProperties" in connection_detail["props"]:
                return CONNECTION_TYPE_SPARK_GLUE
            if connection_detail["props"] and "sparkEmrProperties" in connection_detail["props"]:
                if connection_detail["props"]["sparkEmrProperties"]["computeArn"] and EMR_EC2_ARN_KEY_WORD in \
                        connection_detail["props"]["sparkEmrProperties"]["computeArn"]:
                    return CONNECTION_TYPE_SPARK_EMR_EC2
                elif connection_detail["props"]["sparkEmrProperties"]["computeArn"] and EMR_SERVERLESS_ARN_KEY_WORD in \
                        connection_detail["props"]["sparkEmrProperties"]["computeArn"]:
                    return CONNECTION_TYPE_SPARK_EMR_SERVERLESS
                else:
                    raise RuntimeError(f"Unable to determine the EMR type of connection {sagemaker_connection_name}")
        raise ConnectionNotSupportedException(f"{sagemaker_connection_name} type {connection_type} is not supported")

    @classmethod
    def get_connection_id_from_connection_name(cls, sagemaker_connection_name: str) -> str | None:
        if (cls._is_default_ipython(sagemaker_connection_name)): 
            # This function should never be called with default IPython name
            raise ValueError(f"Invalid sagemaker_connection_name: {sagemaker_connection_name}")
        if sagemaker_connection_name == SAGEMAKER_DEFAULT_CONNECTION_DISPLAYNAME:
            sagemaker_connection_name = cls._get_default_connection_name()
        connection_detail = cls._get_connection_detail_with_connection_name(sagemaker_connection_name, False)
        return connection_detail["connectionId"]

    @classmethod
    def has_key_chain_in_connection_detail(cls, connection, key_chain):
        """
        checks if a nested dictionary contains a chain of keys.
        This function can be used to check if a connection detail contains a chain of keys in its response
        example: SageMakerToolkitUtils.has_key_chain_in_connection_detail(athena_connection_details, ["props", "athenaProperties", "workgroupName"]) -> true
        example: SageMakerToolkitUtils.has_key_chain_in_connection_detail(athena_connection_details, ["props", "redshiftProperties", "workgroupName"]) -> false
        """
        current_dict = connection
        for key in key_chain:
            if not isinstance(current_dict, dict):
                return False
            if key not in current_dict:
                return False
            current_dict = current_dict[key]
        return True

    @classmethod
    def get_glue_connection_names(cls) -> list:
        return cls._glue_connection_names

    @classmethod
    def _cache_connection_list_from_datazone(cls):
        cls._initialize_datazone_gateway_if_not_exist()
        connection_list = cls._datazone_gateway.list_connections()
        cls._glue_connection_names = []
        for connection in connection_list:
            connection_type = connection["type"]
            typeList = cls._connection_type_mapping.get(connection_type, [])
            typeList.append(connection["name"])
            cls._connection_type_mapping[connection_type] = typeList

            cls._connection_name_to_connection_id_mapping[connection["name"]] = connection["connectionId"]
            if (cls._is_connection_ready(connection)
                    and "physicalEndpoints" in connection.keys() and connection["physicalEndpoints"]):
                for physicalEndpoint in connection["physicalEndpoints"]:
                    if ("glueConnectionName" in physicalEndpoint.keys()
                            and physicalEndpoint["glueConnectionName"] not in cls._glue_connection_names):
                        cls._glue_connection_names.append(physicalEndpoint["glueConnectionName"])
        cls._connection_list_last_cached_time = datetime.datetime.now()
        return

    @classmethod
    def _get_connection_detail_with_connection_id(cls, connection_id: str, with_secret: Optional[bool] = False):
        cls._initialize_datazone_gateway_if_not_exist()
        if (not with_secret and connection_id in cls._connection_id_to_connection_details_mapping and
                connection_id in cls._connection_id_last_cached_time and
                datetime.datetime.now() - cls._connection_id_last_cached_time[connection_id] <= datetime.timedelta(minutes=cls._cache_time_minutes)):
            return cls._connection_id_to_connection_details_mapping[connection_id]
        else:
            connection_detail = cls._datazone_gateway.get_connection(connection_id, with_secret=bool(with_secret))
            cls._connection_id_to_connection_details_mapping[connection_id] = connection_detail
            cls._connection_id_last_cached_time[connection_id] = datetime.datetime.now()
            return connection_detail

    @classmethod
    def _get_connection_detail_with_connection_name(cls, sagemaker_connection_name: str,
                                                    with_secret: Optional[bool] = False) -> dict:
        if (sagemaker_connection_name in cls._connection_name_to_connection_id_mapping
                and cls._connection_list_last_cached_time is not None
                and datetime.datetime.now() - cls._connection_list_last_cached_time
                <= datetime.timedelta(minutes=cls._cache_time_minutes)):

            connection_id = cls._connection_name_to_connection_id_mapping[sagemaker_connection_name]
            try:
                connection_detail = cls._get_connection_detail_with_connection_id(connection_id,
                                                                                  with_secret=with_secret)
            except Exception:
                raise ConnectionNotFoundException(f"Could not get connection: {sagemaker_connection_name} from DataZone")
        else:
            cls._cache_connection_list_from_datazone()
            if sagemaker_connection_name not in cls._connection_name_to_connection_id_mapping:
                raise ConnectionNotFoundException(
                    f"Connection {sagemaker_connection_name} does not exist")
            connection_id = cls._connection_name_to_connection_id_mapping[sagemaker_connection_name]
            connection_detail = cls._get_connection_detail_with_connection_id(connection_id, with_secret=with_secret)
        return connection_detail

    @classmethod
    def _initialize_datazone_gateway_if_not_exist(cls):
        if cls._datazone_gateway.datazone_client is None:
            cls._datazone_gateway.initialize_default_clients()

    @classmethod
    def is_express_mode(cls) -> bool:
        """Get express mode flag from domain detail."""
        if cls._is_express_mode is None:
            cls._initialize_datazone_gateway_if_not_exist()
            domain = cls._datazone_gateway.get_domain()
            cls._is_express_mode = cls._datazone_gateway.is_express_mode(domain)
        return cls._is_express_mode

    @classmethod
    def _is_connection_ready(cls, connection):
        if ("props" in connection.keys() and connection["props"]
                and "glueProperties" in connection["props"].keys() and connection["props"]["glueProperties"]
                and "status" in connection["props"]["glueProperties"].keys()
                and connection["props"]["glueProperties"]["status"] == "READY"):
            return True
        else:
            return False

    @classmethod
    def _get_default_connection_name(cls):
        if cls._default_connection is None:
            if cls.is_express_mode():
                if cls.is_connection_valid(SAGEMAKER_DEFAULT_CONNECTION_NAME_EXPRESS):
                    cls._default_connection = SAGEMAKER_DEFAULT_CONNECTION_NAME_EXPRESS
                else:
                    cls._default_connection = DEFAULT_IPYTHON_NAME
            else:
                if cls.is_connection_valid(SAGEMAKER_DEFAULT_CONNECTION_NAME):
                    cls._default_connection = SAGEMAKER_DEFAULT_CONNECTION_NAME
                else:
                    cls._default_connection = DEFAULT_IPYTHON_NAME
        return cls._default_connection

    @classmethod
    def _get_default_spark_connection_name(cls):
        if cls._default_spark_connection is None:
            if cls.is_express_mode():
                if cls.is_connection_valid(SAGEMAKER_DEFAULT_GLUE_CONNECTION_NAME_EXPRESS):
                    cls._default_spark_connection = SAGEMAKER_DEFAULT_GLUE_CONNECTION_NAME_EXPRESS
                else:
                    cls._default_spark_connection = ""
            else:
                if cls.is_connection_valid(SAGEMAKER_DEFAULT_GLUE_COMPATIBILITY_CONNECTION_NAME):
                    cls._default_spark_connection = SAGEMAKER_DEFAULT_GLUE_COMPATIBILITY_CONNECTION_NAME
                elif cls.is_connection_valid(SAGEMAKER_DEFAULT_GLUE_CONNECTION_NAME_DEPRECATED):
                    cls._default_spark_connection = SAGEMAKER_DEFAULT_GLUE_CONNECTION_NAME_DEPRECATED
                elif cls.is_connection_valid(SAGEMAKER_DEFAULT_GLUE_FINE_GRAINED_CONNECTION_NAME):
                    cls._default_spark_connection = SAGEMAKER_DEFAULT_GLUE_FINE_GRAINED_CONNECTION_NAME
                else:
                    cls._default_spark_connection = ""
        return cls._default_spark_connection

    @classmethod
    def _get_default_sql_connection_name(cls):
        if cls._default_sql_connection is None:
            if cls.is_express_mode():
                if cls.is_connection_valid(SAGEMAKER_DEFAULT_ATHENA_CONNECTION_NAME_EXPRESS):
                    cls._default_sql_connection = SAGEMAKER_DEFAULT_ATHENA_CONNECTION_NAME_EXPRESS
                else:
                    cls._default_sql_connection = ""
            else:
                if cls.is_connection_valid(SAGEMAKER_DEFAULT_REDSHIFT_CONNECTION_NAME):
                    cls._default_sql_connection = SAGEMAKER_DEFAULT_REDSHIFT_CONNECTION_NAME
                elif cls.is_connection_valid(SAGEMAKER_DEFAULT_ATHENA_CONNECTION_NAME):
                    cls._default_sql_connection = SAGEMAKER_DEFAULT_ATHENA_CONNECTION_NAME
                else:
                    cls._default_sql_connection = ""
        return cls._default_sql_connection

    @classmethod
    def _is_default_ipython(cls, sagemaker_connection_name: str) -> bool:
        return sagemaker_connection_name == DEFAULT_IPYTHON_NAME
