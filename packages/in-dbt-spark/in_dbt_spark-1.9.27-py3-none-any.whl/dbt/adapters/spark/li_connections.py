from dbt.adapters.contracts.connection import ConnectionState
from dbt.adapters.events.logging import AdapterLogger
from dbt.adapters.exceptions import FailedToConnectError
from dbt.adapters.sql import SQLConnectionManager
import dbt_common.exceptions
from dbt.adapters.spark.connections import (
    SparkConnectionManager,
    SparkCredentials,
    SparkConnectionWrapper,
)
from dbt.adapters.setu.session_manager import SetuSessionManager
from dbt.adapters.setu.imports import SetuCluster
from dbt.adapters.setu.session_handler import SetuSessionHandler
from dbt.adapters.setu.constants import DEFAULT_HEARTBEAT_TIMEOUT
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from dbt_common.dataclass_schema import StrEnum

logger = AdapterLogger("Spark")
DEFAULT_CATALOG = "openhouse"


class ExtendedSparkConnectionMethod(StrEnum):
    THRIFT = "thrift"
    HTTP = "http"
    ODBC = "odbc"
    SESSION = "session"
    SETU = "setu"  # OSS Apache Livy offering @ LinkedIn


class ExtendedSparkConnectionManager(SparkConnectionManager):
    def open(cls, connection):
        if connection.state == ConnectionState.OPEN:
            logger.debug("Connection is already open, skipping open.")
            return connection

        creds = connection.credentials
        handle: SparkConnectionWrapper
        try:
            if creds.method == ExtendedSparkConnectionMethod.SETU:
                for i in range(1 + creds.connect_retries):
                    logger.info("validate credentials to connect with SETU")
                    cls.validate_creds(
                        creds,
                        ["schema", "session_name", "proxy_user"],
                    )
                    if not creds.url:
                        connection.credentials.url = SetuCluster(
                            connection.credentials.cluster
                        ).get_url()

                    setu_session = SetuSessionManager.create_session(
                        url=creds.url,
                        proxy_user=creds.proxy_user,
                        queue=creds.queue,
                        execution_tags=creds.execution_tags,
                        metadata=creds.metadata,
                        enable_ssl=creds.use_ssl,
                        spark_conf=creds.spark_conf,
                        spark_version=creds.spark_version,
                        setu_session_name=creds.session_name,
                        jars=creds.jars,
                        py_files=creds.py_files,
                        archives=creds.archives,
                        files=creds.files,
                        manifest_file_location=creds.manifest_file_location,
                        heartbeat_timeout_in_seconds=creds.heartbeat_timeout_in_seconds,
                    )
                    if setu_session.session_id is None:
                        logger.error("Error creating Setu session")
                        raise dbt_common.exceptions.DbtRuntimeError(
                            f"Error creating Setu session : {setu_session}"
                        )
                    setu_session.wait_till_ready()
                    logger.info(f"Setu session {setu_session.session_id} creation complete")
                    handle = SetuSessionHandler(handle=setu_session)
                    connection.handle = handle
                    break

            else:
                connection = super().open(creds)

            connection.state = ConnectionState.OPEN
            return connection

        except Exception as e:
            if isinstance(e, EOFError):
                # The user almost certainly has invalid credentials.
                # Perhaps a token expired, or something
                msg = "Failed to connect"
                if creds.token is not None:
                    msg += ", is your token valid?"
                raise FailedToConnectError(msg) from e
            else:
                raise FailedToConnectError("failed to connect") from e

    def cleanup_all(self) -> None:
        connection = SQLConnectionManager.get_if_exists(self)

        if connection is not None:
            SQLConnectionManager.cleanup_all(self)
            if connection.credentials.method == ExtendedSparkConnectionMethod.SETU:
                logger.info("closing Setu session")
                SetuSessionManager.close_session(
                    url=connection.credentials.url,
                    verify=False,
                )


@dataclass
class ExtendedSparkCredentials(SparkCredentials):
    method: ExtendedSparkConnectionMethod = ExtendedSparkConnectionMethod.SETU  # type: ignore
    host: Optional[str] = None
    database: Optional[str] = None  # type: ignore
    #  **********   setu specific configs   **********
    url: Optional[str] = None
    session_name: Optional[str] = None
    schema: Optional[str] = None  # type: ignore
    queue: Optional[str] = None
    proxy_user: Optional[str] = None
    jars: Optional[List[str]] = None
    py_files: Optional[List[str]] = None
    archives: Optional[List[str]] = None
    files: Optional[List[str]] = None
    manifest_file_location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_tags: Dict[str, Any] = field(default_factory=dict)
    spark_conf: Dict[str, Any] = field(default_factory=dict)
    spark_version: Optional[str] = None
    heartbeat_timeout_in_seconds: int = DEFAULT_HEARTBEAT_TIMEOUT
    #  **********   setu specific configs   **********
    _ALIASES = {
        "catalog": "database",
    }

    @classmethod
    def __pre_deserialize__(cls, data):
        if "schema" in data and "." not in data["schema"]:
            data["schema"] = DEFAULT_CATALOG + "." + data["schema"]
        data = super().__pre_deserialize__(data)
        return data

    def __post_init__(self):
        if self.method == ExtendedSparkConnectionMethod.SETU:
            if self.schema is None or self.session_name is None or self.proxy_user is None:
                logger.error(
                    " `schema`, `session_name`, `proxy_user` must be set in profile config"
                )
                raise dbt_common.exceptions.DbtRuntimeError(
                    " `schema`, `session_name`, `proxy_user` must be set when"
                    f" using {self.method} method to connect to Spark"
                )
        else:
            super().__post_init__()

    @property
    def unique_field(self):
        if self.method == ExtendedSparkConnectionMethod.SETU:
            if not self.cluster:
                raise dbt_common.exceptions.DbtRuntimeError(
                    "`cluster` must be set when using the Setu method to connect to Spark"
                )
            return self.cluster
        else:
            return self.host

    def _connection_keys(self):
        if self.method == ExtendedSparkConnectionMethod.SETU:
            return ("url", "schema", "session_name")
        else:
            return ("host", "port", "cluster", "endpoint", "schema", "organization")
