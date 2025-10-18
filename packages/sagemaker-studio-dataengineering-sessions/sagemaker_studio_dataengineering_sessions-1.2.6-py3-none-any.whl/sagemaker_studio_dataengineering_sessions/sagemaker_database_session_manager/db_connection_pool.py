from amazon_sagemaker_sql_execution.connection_pool import ConnectionPool


class DatabaseConnectionPool:
    """This is a wrapper over ConnectionPool from amazon_sagemaker_sql_execution to ensure single
     instance of DatabaseConnectionPool over multiple DatabaseSessionManagers"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = ConnectionPool()
        return cls._instance
