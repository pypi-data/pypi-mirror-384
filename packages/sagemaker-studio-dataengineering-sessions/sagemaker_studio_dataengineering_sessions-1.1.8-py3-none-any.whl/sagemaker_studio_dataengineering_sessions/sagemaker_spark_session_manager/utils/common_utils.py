def get_glue_endpoint(region="us-east-1", stage="prod"):
    domain = "glue-gamma" if stage == "gamma" else "glue"
    # TODO support other partition
    api_domain = "amazonaws.com"
    return f"https://{domain}.{region}.{api_domain}"


def get_redshift_endpoint(region="us-east-1", stage="prod"):
    # TODO support other partition
    # Endpoints: https://regions.aws.dev/services/statuses/region/iad/redshift-data
    if stage == "gamma":
        return f"https://qa.{region}.query.redshift.aws.a2z.com/"
    else:
        return f"redshift-data.{region}.amazonaws.com"


def get_account_id_from_arn(arn):
    return arn.split(":")[4]
