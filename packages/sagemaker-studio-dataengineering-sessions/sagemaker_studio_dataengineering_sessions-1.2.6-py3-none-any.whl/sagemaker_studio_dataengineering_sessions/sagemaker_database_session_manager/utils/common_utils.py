def get_redshift_gamma_endpoint(region="us-east-1"):
    # TODO support other partition
    return "https://aws-cookie-monster-qa.amazon.com"


def get_redshift_serverless_gamma_endpoint(region="us-east-1"):
    # TODO support other partition
    return f"https://qa.{region}.serverless.redshift.aws.a2z.com"


def get_athena_gamma_endpoint(region="us-east-1"):
    # TODO support other partition
    return f"https://athena-webservice-preprod.{region}.amazonaws.com/"


def get_sqlworkbench_endpoint(region="us-east-1", is_gamma=False):
    if is_gamma:
        return f"https://api-v2.gamma.{region}.workbench.cranberry.aws.dev"
    return f"https://api-v2.sqlworkbench.{region}.amazonaws.com"
