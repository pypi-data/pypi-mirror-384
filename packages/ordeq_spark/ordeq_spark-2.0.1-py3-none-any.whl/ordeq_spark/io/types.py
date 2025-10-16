from typing import Literal

SparkFormat = Literal[
    "parquet", "iceberg", "csv", "com.microsoft.sqlserver.jdbc.spark"
]
