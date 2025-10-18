try:
    import boto3
    import pandas
    import pickle
    import re
    import warnings

    from botocore.exceptions import ClientError

    # Prevents evaluated output from being muddied by pyspark warnings about loading to driver
    warnings.filterwarnings('ignore')
except ModuleNotFoundError as e:
    pass



def env_validation():
    try:
        import boto3
        import pandas
        import pickle
        import re
        import warnings

        from botocore.exceptions import ClientError
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(f"Missing required libraries on compute. Error: {error}")


class S3VariableManager:
    def __init__(self, project_s3_path):
        self.project_s3_path = project_s3_path
        env_validation()
        self.s3 = boto3.client('s3')

        match = re.match(r'^s3://([^/]+)/?(.*)$', project_s3_path)
        if not match:
            raise ValueError("Invalid S3 location. Please use the format: s3://bucket-name/path")

        self.s3_bucket = match.group(1)
        self.s3_prefix = match.group(2)

    def push(self, var, var_name, namespace, force=False):
        if not force:
            self._validate_var_not_exists(var_name, namespace)

        var_clazz = self._get_canonical_class_name(var)
        if var_clazz == "pyspark.sql.DataFrame" or var_clazz == "pyspark.sql.dataframe.DataFrame":
            # if spark dataframe
            converted_var = var.toPandas()
            converted_var.to_parquet(self._construct_var_s3_path(var_name, namespace), engine='pyarrow')
        elif var_clazz == "pyspark.pandas.DataFrame" or var_clazz == "pyspark.pandas.frame.DataFrame":
            # if pandas-on-spark dataframe
            converted_var = var.to_pandas()
            converted_var.to_parquet(self._construct_var_s3_path(var_name, namespace), engine='pyarrow')
        elif var_clazz == "pandas.core.frame.DataFrame":
            var.to_parquet(self._construct_var_s3_path(var_name, namespace), engine='pyarrow')
        else:
            self.s3.put_object(Bucket=self.s3_bucket,
                               Key=self._construct_var_s3_prefix(var_name, namespace),
                               Body=pickle.dumps(var))

    def pop(self, var_name, namespace):
        try:
            return pandas.read_parquet(self._construct_var_s3_path(var_name, namespace))
        except:
            var_prefix = self._construct_var_s3_prefix(var_name, namespace)
            try:
                response = self.s3.get_object(Bucket=self.s3_bucket, Key=var_prefix)
            except self.s3.exceptions.NoSuchKey:
                raise ValueError(f"""Variable {var_name} not found: Check if variable exists or if namespace '{namespace}' is correct""")
            serialized_obj = response['Body'].read()
            return pickle.loads(serialized_obj)

    def upload_parquet(self, df, s3_suffix):
        if df is not None and not self._validate_object_exists(f"{self.s3_prefix}/{s3_suffix}"):
            df.to_parquet(f"{self.project_s3_path}/{s3_suffix}", engine='pyarrow')

    def upload_json(self, json_str, s3_suffix):
        key = f"{self.s3_prefix}/{s3_suffix}"
        if json_str is not None and not self._validate_object_exists(key):
            self.s3.put_object(Bucket=self.s3_bucket, Key=key, Body=json_str)

    def check_folder_exists(self, s3_suffix: str):
        if not s3_suffix.endswith("/"):
            s3_suffix += "/"
        prefix = f"{self.s3_prefix}/{s3_suffix}"
        response = self.s3.list_objects_v2(Bucket=self.s3_bucket, Prefix=prefix, MaxKeys=1)
        return "Contents" in response and len(response["Contents"]) > 0

    def _construct_var_s3_path(self, var_name, namespace):
        return f"{self.project_s3_path}/sys/kernel-var/{namespace}/{var_name}"

    def _construct_var_s3_prefix(self, var_name, namespace):
        return f"{self.s3_prefix}/sys/kernel-var/{namespace}/{var_name}"

    def _get_canonical_class_name(self, obj):
        return f"{obj.__class__.__module__}.{obj.__class__.__name__}"

    def _validate_object_exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.s3_bucket, Key=key)
            return True
        except ClientError as error:
            if error.response['Error']['Code'] == "404":
                return False
            else:
                raise error

    def _validate_var_not_exists(self, var_name: str, namespace: str) -> None:
        if self._validate_object_exists(self._construct_var_s3_prefix(var_name, namespace)):
            raise ValueError(f"The variable '{var_name}' already exists in storage. To replace it, use the --force option.")
