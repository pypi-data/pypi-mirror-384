from itertools import starmap

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import DataType, StructField, StructType


def create_schema(
    schema: tuple[tuple[str, DataType, bool], ...],
) -> StructType:
    """Utility method that creates a Spark StructType (or, schema) from tuple
    inputs, without need to import and write StructType & StructField

    Args:
        schema: tuple of schema inputs

    Returns:
        StructType
    """

    return StructType(list(starmap(StructField, schema)))


def apply_schema(df: DataFrame, schema: StructType) -> DataFrame:
    """Applies a schema to the DataFrame, meaning:
    - select only those columns in the schema from the DataFrame
    - cast these to the types specified in the schema

    Note that this method does **not** check for nullability in the schema.

    Args:
        df: DataFrame
        schema: StructType (schema)

    Returns:
        the DataFrame with schema applied
    """

    return df.select(*[
        F.col(column.name)
        .cast(schema[column.name].dataType)
        .alias(column.name)
        for column in schema
    ])


def get_spark_session() -> SparkSession:
    """Helper to get the SparkSession

    Returns:
        the spark session object

    Raises:
        RuntimeError: when the spark session is not active
    """
    session = SparkSession.getActiveSession()
    if session is None:
        raise RuntimeError("Spark session must be active.")
    return session
