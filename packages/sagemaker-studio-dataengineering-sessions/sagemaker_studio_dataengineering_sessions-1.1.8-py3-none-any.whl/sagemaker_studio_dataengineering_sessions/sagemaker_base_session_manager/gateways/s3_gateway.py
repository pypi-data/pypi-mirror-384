import boto3

class S3Gateway():
    def __init__(self):
        self.s3 = None

    def initialize_clients(self, profile=None, s3_profile=None):
        # S3 client should use different profiles other than other client
        # S3 client should almost always use the default profile
        # because the S3 client is used to download the pem for SSL verification
        # which should be done using project role
        self.s3 = self.create_s3_client(s3_profile)


    def create_s3_client(self, profile=None):
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
        return session.resource('s3')

    def download_from_s3(self, bucket_name: str, object_key: str, local_file_name: str):
        bucket = self.s3.Bucket(bucket_name)
        downloaded_file_path = bucket.download_file(object_key, local_file_name)
        return downloaded_file_path
