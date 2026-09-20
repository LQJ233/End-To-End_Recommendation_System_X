from pyspark.sql import SparkSession

from local_env import get_env


ICEBERG_VERSION = "1.10.0"
HADOOP_AWS_VERSION = "3.3.4"
AWS_SDK_VERSION = "1.12.367"


def create_spark(app_name: str, extra_packages: list[str] | None = None) -> SparkSession:
    packages = [
        f"org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:{ICEBERG_VERSION}",
        f"org.apache.hadoop:hadoop-aws:{HADOOP_AWS_VERSION}",
        f"com.amazonaws:aws-java-sdk-bundle:{AWS_SDK_VERSION}",
    ]
    if extra_packages:
        packages.extend(extra_packages)

    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.jars.packages", ",".join(packages))
        .config("spark.jars.repositories", "https://maven.aliyun.com/repository/central")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.iceberg.type", "hadoop")
        .config("spark.sql.catalog.iceberg.warehouse", "s3a://warehouse/iceberg")
        .config("spark.hadoop.fs.s3a.endpoint", get_env("MINIO_ENDPOINT", "http://127.0.0.1:9000"))
        .config("spark.hadoop.fs.s3a.access.key", get_env("MINIO_ACCESS_KEY"))
        .config("spark.hadoop.fs.s3a.secret.key", get_env("MINIO_SECRET_KEY"))
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.driver.memory", "4g")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )
