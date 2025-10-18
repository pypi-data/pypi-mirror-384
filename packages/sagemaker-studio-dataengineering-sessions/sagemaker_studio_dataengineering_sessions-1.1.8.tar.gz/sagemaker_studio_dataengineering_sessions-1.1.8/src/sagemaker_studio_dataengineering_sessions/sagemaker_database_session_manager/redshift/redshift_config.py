class Config:
    def __init__(self):
        # Redshift connector
        # https://github.com/aws/amazon-redshift-python-driver/blob/b2dde82ec9156e2adcc801ac54c051f3cfe61e33/redshift_connector/__init__.py#L112
        self.use_sql_workbench = True
        self.catalog_name = None
        self.schema_name = None
