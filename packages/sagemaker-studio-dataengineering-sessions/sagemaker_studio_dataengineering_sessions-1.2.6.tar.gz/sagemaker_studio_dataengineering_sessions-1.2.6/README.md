# SageMakerStudioDataEngineeringSessions

SageMaker Unified Studio Data Engineering Sessions

This pacakge depends on SageMaker Unified Studio environment, if you are using SageMaker Unified Studio, see [AWS Doc](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/what-is-sagemaker-unified-studio.html) for guidance.

This package contains functionality to support SageMaker Unified Studio connecting to various AWS Compute including EMR/EMR Serverless/Glue/Redshift etc. 

It is utilizing [ipython magics](https://ipython.readthedocs.io/en/stable/interactive/magics.html) and [AWS DataZone Connections](https://docs.aws.amazon.com/datazone/latest/APIReference/API_ListConnections.html) to achieve the following features.

## Features

- Connect to remote compute
- Execute Spark code in remote compute in Python/Scala
- Execute SQL queries in remote compute
- Send local variables to remote compute


## How to setup

If you are using SageMaker Unifed Studio, you can skip this part, SageMaker Unifed Studio already set up the package.

This package contains various Jupyter Magics to achieve its functionality.

To load these magics, make sure you have iPython config file generated. If not, you could run `ipython profile create`, then a file with path `~/.ipython/profile_default/ipython_config.py` should be generated

Then you will need to add the following line in the end of that config file

```
c.InteractiveShellApp.extensions.extend(['sagemaker_studio_dataengineering_sessions.sagemaker_connection_magic'])
```

Once that is finished, you could restart the ipython kernel and run `%help` to see a list of supported magics

## Examples


To connect to remote compute, a DataZone Connection is required, you could create it via [CreateConnection API](https://docs.aws.amazon.com/datazone/latest/APIReference/API_CreateConnection.html), Let's say there's an existing connection called project.spark. 

### Supported Connection Type:

- IAM
- SPARK
- REDSHIFT
- ATHENA

### Connect to remote compute and Execute Spark Code in Python
The following example will connect to AWS Glue Interactive session and run the spark code in Glue.

```
%%pyspark project.spark

import sys
import boto3
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

args = getResolvedOptions(sys.argv, ["redshift_url", "redshift_iam_role", "redshift_tempdir","redshift_jdbc_iam_url"])
print(f"{args}")

sc = SparkContext.getOrCreate()
spark = SparkSession(sc)

df = spark.read.csv(f"s3://sagemaker-example-files-prod-{boto3.session.Session().region_name}/datasets/tabular/dirty-titanic/", header=True)
df.show(5, truncate=False)
df.printSchema()

df.createOrReplaceTempView("df_sql_tempview")
```

### Execute Spark Code in Scala
The following example will connect to AWS Glue Interactive session and run the spark code in Scala.

```
%%scalaspark project.spark
val dfScala = spark.sql("SELECT count(0) FROM df_sql_tempview")
dfScala.show()
```

### Execute SQL query in remote compute
The following example will connect to AWS Glue Interactive session and run the spark code in Scala.

```
%%sql project.redshift
select current_user()
```

### Some other helpful magics

```
%help - list available magics and related information

%send_to_remote - send local variable to remote compute

%%configure - configure spark application config in remote compute
```