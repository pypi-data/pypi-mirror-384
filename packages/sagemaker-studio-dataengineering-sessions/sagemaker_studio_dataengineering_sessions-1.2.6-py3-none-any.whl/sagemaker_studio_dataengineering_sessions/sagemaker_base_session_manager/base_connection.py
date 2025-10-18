class BaseConnection(object):
    def __init__(self, connection_name: str,
                 connection_id: str,
                 region: str,
                 enable_tip: bool = False):
        self.connection_name = connection_name
        self.connection_id = connection_id
        self.region = region
        self.enable_tip = enable_tip
