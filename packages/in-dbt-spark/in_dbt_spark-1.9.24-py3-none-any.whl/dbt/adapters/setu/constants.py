from enum import Enum

from dbt.adapters.setu.models import StatementKind

DEFAULT_SPARK_VERSION = "3.1"
DEFAULT_DRIVER_MEMORY = "4G"
DEFAULT_DRIVER_CORES = 2
DEFAULT_EXECUTOR_MEMORY = "1G"
DEFAULT_EXECUTOR_CORES = 1
DEFAULT_NUM_EXECUTORS = 100
DEFAULT_SPARK_APPLICATION_NAME = "DBT_Default_Session_Name"
DEFAULT_YARN_QUEUE = "misc_default"
DEFAULT_HEARTBEAT_TIMEOUT = 900
DEFAULT_EXECUTION_TAGS = {"gpu": False, "pool": "dev"}
DEFAULT_JAVA_RUNTIME_VERSION = "11.0.13-msft"
DEFAULT_SPARK_DRIVER_ENV_JAVA_HOME = "/export/apps/jdk/JDK-11_0_13-msft"
DEFAULT_SPARK_YARN_APP_MASTER_ENV_JAVA_HOME = "/export/apps/jdk/JDK-11_0_13-msft"
DEFAULT_SPARK_EXECUTOR_ENV_JAVA_HOME = "/export/apps/jdk/JDK-11_0_13-msft"

DEFAULT_SPARK_CONF = {
    "spark.jars.ivy": "ivy2-repo",
    "spark.yarn.security.credentials.hive.enabled": "true",
    "spark.sql.sources.partitionOverwriteMode": "DYNAMIC",
    "spark.hadoop.hive.exec.dynamic.partition": "true",
    "spark.hadoop.hive.exec.dynamic.partition.mode": "nonstrict",
    "hive.exec.dynamic.partition.mode": "nonstrict",
    "spark.dynamicAllocation.enabled": "true",
    "spark.dynamicAllocation.initialExecutors": DEFAULT_NUM_EXECUTORS,
    "spark.dynamicAllocation.maxExecutors": 900,
    "spark.dynamicAllocation.minExecutors": 1,
    "java-runtime-version": DEFAULT_JAVA_RUNTIME_VERSION,
    "spark.driverEnv.JAVA_HOME": DEFAULT_SPARK_DRIVER_ENV_JAVA_HOME,
    "spark.yarn.appMasterEnv.JAVA_HOME": DEFAULT_SPARK_YARN_APP_MASTER_ENV_JAVA_HOME,
    "spark.executorEnv.JAVA_HOME": DEFAULT_SPARK_EXECUTOR_ENV_JAVA_HOME
}

SPARK_CONF_APPEND_KEYS = [
    "spark.jars.packages",
]

SPARK_RESOURCE_KEYS = {
    "driver_memory": "spark.driver.memory",
    "driver_cores": "spark.driver.cores",
    "executor_memory": "spark.executor.memory",
    "executor_cores": "spark.executor.cores",
    "num_executors": "spark.executor.instances",
}

SERIALISE_DATAFRAME_TEMPLATE_SPARK = "{}.toJSON.collect.foreach(println)"

VALID_STATEMENT_KINDS = {
    StatementKind.SPARK,
    StatementKind.PYSPARK,
    StatementKind.SQL,
    StatementKind.SPARKR,
}


# AUTH related constants
DATAVAULT_TOKEN_PATH_KEY = "DATAVAULT_TOKEN_PATH"
GRESTIN_DIR_PATH_KEY = "GRESTIN_CERTS_DIR"

# Session reuse related constants
PERSISTED_SESSION_DETAILS_PATH_KEY = "SETU_SESSION_DETAILS_PATH"
DEFAULT_PERSISTED_SESSION_DETAILS_NAME = "setu_session_details.txt"

# Key for setting platform type for
PLATFORM_KEY = "LI_PLATFORM"
CERT_PATH = "GRESTIN_IDENTITY_CERTS_PATH"
KEY_PATH = "GRESTIN_IDENTITY_KEY_PATH"



# DAG configuration mappings: (environment_variable, spark_config_key)
DAG_CONFIG_MAPPINGS = [
    ("POOL", "spark.hadoop.pool"),
    ("TASK_ID", "spark.hadoop.task.id"),
    ("TASK_URN", "spark.hadoop.task.urn"),
    ("DAG_ID", "spark.hadoop.dag.id"),
    ("DAG_URN", "spark.hadoop.dag.urn"),
    ("DAG_RUN_URN", "spark.hadoop.dag.run.urn")
    ("CLUSTER_ID", "spark.hadoop.cluster.id"),
    ("TASK_RUN_URN", "spark.hadoop.task.run.urn"),
    ("ORCHESTRATOR", "spark.hadoop.orchestrator"),
]

PYSPARK_MARKER = f"$${StatementKind.PYSPARK.value}$$"
SPARK_MARKER = f"$${StatementKind.SPARK}$$"

class Platform(Enum):
    # Platforms which can be set as env variable
    # this enum is being used for darwin auth and setu session reuse currently
    # e.g in for darwin -  export LI_PLATFORM=DARWIN is set
    # this ensures we persist session details in a file and use DV/Grestin from respective locations in darwin
    DEFAULT_PLATFORM = "LOCAL"
    DARWIN_PLATFORM = "DARWIN"
    GIT_PLATFORM = "GHA"
    AIRFLOW_PLATFORM = "AIRFLOW"
    # if set dynamic platform then arguments like certs path will be taken from env variable.
    DYNAMIC_PLATFORM = "DYNAMIC"
    AIRFLOW_TEST_PLATFORM = "TEST_AIRFLOW"

    def __str__(self):
        return str(self.value)

    @classmethod
    def get_platforms_supporting_session_reuse(cls):
        # TODO: Add oklahoma for session re-use if required
        return [cls.DEFAULT_PLATFORM, cls.DARWIN_PLATFORM]

    @classmethod
    def platform_key(cls):
        # Key for setting platform type
        # e.g export LI_PLATFORM=DARWIN
        return PLATFORM_KEY


class Oklahoma(Enum):
    # GRESTIN CERT PATH - Flow identity
    FLOW_IDENTITY_CERT = "/var/cluster/identity.cert"
    FLOW_IDENTITY_KEY = "/var/cluster/identity.key"

    # GRESTIN CERT PATH - MP identity
    MP_IDENTITY_CERT = "/var/cluster/mp/identity.cert"
    MP_IDENTITY_KEY = "/var/cluster/mp/identity.key"

    # FABRIC FOR CERT TO DV TOKEN
    DEFAULT_FABRIC = "prod-ltx1"

    DV_TOKEN_ADDRESS = "https://1.datavault-token-service.prod-ltx1.atd.prod.linkedin.com:4019"

    @classmethod
    def fabric(cls):
        return cls.DEFAULT_FABRIC
