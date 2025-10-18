import json


# This is temporary to support private beta use case:
# Access redshift via glue
# same as:
# https://code.amazon.com/packages/AWSGlueInteractiveSessionsKernel/commits/0e42fe7fbde5fdd559bb7c2635c10daf4b09af50
# This need to change once the approach of using Redshift connection from a Glue connection is finalized
def retrieve_sagemaker_metadata_from_file(logger=None):
    try:
        # Opening JSON file
        with open('/opt/ml/metadata/resource-metadata.json') as f:
            metadata = json.load(f)
            return metadata
    except Exception as e:
        if logger is not None:
            logger.error(f"Unable to retrieve sagemaker metadata from file: {e}")
        return None

