class BaseConnection(object):
    def __init__(self, connection_name: str,
                 connection_id: str,
                 region: str):
        self.connection_name = connection_name
        self.connection_id = connection_id
        self.region = region
