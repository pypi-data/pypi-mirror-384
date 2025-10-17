import copy

from dbt.adapters.events.logging import AdapterLogger
from typing import Any, Dict, List, Optional
from threading import Lock
from dbt.adapters.setu.client import SetuClient, Auth, Verify
from dbt.adapters.setu.session import SetuSession
from dbt.adapters.setu.constants import (
    SPARK_RESOURCE_KEYS,
    DEFAULT_DRIVER_MEMORY,
    DEFAULT_EXECUTOR_MEMORY,
    DEFAULT_NUM_EXECUTORS,
    DEFAULT_EXECUTOR_CORES,
    DEFAULT_DRIVER_CORES,
    DEFAULT_SPARK_VERSION,
    DEFAULT_SPARK_APPLICATION_NAME,
    DEFAULT_YARN_QUEUE,
    DEFAULT_HEARTBEAT_TIMEOUT,
)

from dbt.adapters.setu.models import (
    SessionDetails,
    SessionInitializationConfig,
    SESSION_STATE_READY,
)

from dbt.adapters.setu.utils import (
    generate_unique_session_name,
    get_session_details_file_path,
    get_platform,
    platform_supports_setu_session_reuse,
    set_execution_tags_with_defaults,
    set_spark_conf_with_defaults,
    set_session_runtime_metadata,
    get_jars,
)

logger = AdapterLogger("Spark")


class SetuSessionManager:
    session_id: Optional[str] = None
    session_lock = Lock()
    """
    Manages creation and closing of SETU sessions
    """

    @classmethod
    def create_session(
        cls,
        url: str,
        auth: Optional[Auth] = None,
        verify: Verify = False,
        proxy_user: Optional[str] = None,
        jars: Optional[List[str]] = None,
        py_files: Optional[List[str]] = None,
        archives: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        manifest_file_location: Optional[str] = None,
        queue: str = DEFAULT_YARN_QUEUE,
        setu_session_name: str = DEFAULT_SPARK_APPLICATION_NAME,
        spark_version: str = DEFAULT_SPARK_VERSION,
        execution_tags: Dict[str, Any] = dict(),
        spark_conf: Dict[str, Any] = dict(),
        metadata: Dict[str, Any] = dict(),
        heartbeat_timeout_in_seconds: int = DEFAULT_HEARTBEAT_TIMEOUT,
        enable_ssl: bool = False,
    ) -> "SetuSession":
        """Create a new SETU session.

        Ivy's for jars, py_files, files and archives arguments are all copied to
        the same working directory on the Spark cluster.

        The driver_memory and executor_memory arguments have the same format as
        JVM memory strings with a size unit suffix ("k", "m", "g" or "t") (e.g.
        512m, 2g).

        See https://spark.apache.org/docs/latest/configuration.html for more
        information on Spark configuration properties.

        :param url: SETU server URL.
        :param auth: A requests-compatible auth object to use when making
            requests.
        :param verify: Either a boolean, in which case it controls whether we
            verify the server’s TLS certificate, or a string, in which case it
            must be a path to a CA bundle to use. Defaults to ``True``.
        :param proxy_user: User to impersonate when starting the session.
        :param jars: Ivy's of jars to be used in this session.
        :param py_files: URLs of Python files to be used in this session.
        :param files: URLs of files to be used in this session.
        :param archives: URLs of archives to be used in this session.
        :param queue: The name of the YARN queue to which submitted.
        :param setu_session_name: The name of this session.
        :param spark_conf: Spark configuration properties.
        :param heartbeat_timeout_in_seconds: Optional Timeout in seconds to which session
            be automatically orphaned if no heartbeat is received.
        :param metadata: Dict of metadata for this SETU session
        :param enable_ssl: enable ssl configurations on driver and executors
        :param execution_tags: Dict of tags to be inferred by Infra
        :param spark_version: version of the spark session
        :param manifest_file_location: location of manifest file with all the dependencies
        """
        with cls.session_lock:
            session_initialization_config = SessionInitializationConfig(
                proxy_user=proxy_user,  # type: ignore
                # Unifying jars to dependencies else setu will fail the request as invalid config
                jars=get_jars(jars, spark_conf.pop("spark.jars.packages", None)),
                py_files=py_files,  # type: ignore
                files=files,  # type: ignore
                archives=archives,  # type: ignore
                manifest_file_location=manifest_file_location,  # type: ignore
                # Removing spark tuning configs after fetching from spark_conf, else
                # They will be duplicated in other configs and setu will fail the request as invalid config
                driver_memory=spark_conf.pop(
                    SPARK_RESOURCE_KEYS.get("driver_memory"), DEFAULT_DRIVER_MEMORY  # type: ignore
                ),
                driver_cores=spark_conf.pop(
                    SPARK_RESOURCE_KEYS.get("driver_cores"), DEFAULT_DRIVER_CORES  # type: ignore
                ),
                executor_memory=spark_conf.pop(
                    SPARK_RESOURCE_KEYS.get("executor_memory"),  # type: ignore
                    DEFAULT_EXECUTOR_MEMORY,
                ),
                executor_cores=spark_conf.pop(
                    SPARK_RESOURCE_KEYS.get("executor_cores"),  # type: ignore
                    DEFAULT_EXECUTOR_CORES,
                ),
                num_executors=spark_conf.pop(
                    SPARK_RESOURCE_KEYS.get("num_executors"), DEFAULT_NUM_EXECUTORS  # type: ignore
                ),
                queue=queue,
                session_name=generate_unique_session_name(setu_session_name),
                spark_version=spark_version,
                execution_tags=set_execution_tags_with_defaults(execution_tags),
                spark_conf=set_spark_conf_with_defaults(spark_conf),
                metadata=set_session_runtime_metadata(metadata),
                heartbeat_timeout_in_seconds=heartbeat_timeout_in_seconds,
                enable_ssl=enable_ssl,
            )

            # If session is requested for first time, fetch persisted session if exists
            if cls.session_id is None:
                # Fetch if persisted session exists with same initialization config
                persisted_session_details = cls.get_persisted_session_if_exists(
                    session_initialization_config, auth, verify
                )
                if persisted_session_details:
                    cls.session_id = persisted_session_details.session_id

            if cls.session_id is not None:
                logger.info(f"use existing session with id = {cls.session_id}")
                try:
                    logger.info("check if existing Setu session is active")
                    existing_setu_session = SetuSessionManager.get_session_if_active(
                        url=url,
                        session_id=cls.session_id,
                        verify=False,
                    )
                    if existing_setu_session is not None:
                        logger.info(f"existing Setu session {cls.session_id} is already active")
                        return existing_setu_session
                except Exception as ex:
                    logger.exception(f"Error while checking {cls.session_id} session exists", ex)

            logger.info("creating new Setu session")
            with SetuClient(url=url, auth=auth, verify=verify) as client:
                # sending a deep copy of session_initialization_config as it's modified in create_session function
                # if it's changed, it will create a mismatched config to be persisted
                # which will not match the details next time
                session = client.create_session(copy.deepcopy(session_initialization_config))
                cls.session_id = session.session_id

                # persist session details for next run
                cls.persist_session(session_initialization_config, url)

                return SetuSession(
                    url,
                    session.session_id,
                    auth,
                    verify,
                )

    @classmethod
    def close_session(
        cls,
        url: str,
        auth: Optional[Auth] = None,
        verify: Verify = False,
    ):
        """Close the managed SETU session."""
        logger.info(f"Trying to close session for : {cls.session_id}")
        if cls.session_id is None:
            logger.info("No setu session active")
            return

        # If session exists, cancel on setu
        # If sessions exists but code is executing in platform supporting reuse
        # e.g darwin, don't close session for session reuse
        platform = get_platform()
        if platform_supports_setu_session_reuse():
            logger.info(
                f"Not cancelling session : {cls.session_id} since Platform : {platform} will reuse session "
                f"for next run"
            )
            return

        # If sessions exists and code is NOT executing in platform supporting reuse
        with cls.session_lock:
            with SetuClient(url, auth, verify) as client:
                session = client.get_session(cls.session_id)
                if session is not None:
                    client.cancel_session(cls.session_id)
                    cls.session_id = None
                    logger.info(f"cancelled session : {cls.session_id}")
                client.close()

    @classmethod
    def get_session_if_active(
        cls,
        url: str,
        session_id: str,
        auth: Optional[Auth] = None,
        verify: Verify = False,
    ):
        """get SETU session if still active."""
        with SetuClient(url, auth, verify) as client:
            session = client.get_session(session_id)
        if session is not None and session.state in SESSION_STATE_READY:
            return SetuSession(url, session.session_id, auth, verify)
        return None

    @classmethod
    def get_persisted_session_if_exists(
        cls,
        session_initialization_config: SessionInitializationConfig,
        auth=None,
        verify=None,
    ) -> Optional[SessionDetails]:
        """
        get persisted session if it exists and has same config
        """

        # if platform is not supported, no need to persist and return
        if not platform_supports_setu_session_reuse():
            return None

        # fetch persisted session if it exists
        session_details_file_path = get_session_details_file_path()
        persisted_session_details = SessionDetails.get_persisted_session_details_if_exists(
            session_details_file_path
        )
        # If it doesn't exist, return None
        if not persisted_session_details:
            return None

        # check is persisted session is valid
        is_persisted_session_valid = False
        if (
            persisted_session_details
            and persisted_session_details.session_initialization_config
            == session_initialization_config
        ):
            is_persisted_session_valid = True

        logger.info("Is persisted session valid : " + str(is_persisted_session_valid))

        # if persisted session exists and is not valid, close persisted session
        if persisted_session_details and not is_persisted_session_valid:
            logger.info(
                "Closing the persisted session: " + str(persisted_session_details.session_id)
            )
            with SetuClient(url=persisted_session_details.url, auth=auth, verify=verify) as client:
                client.cancel_session(persisted_session_details.session_id)
            return None

        return persisted_session_details

    @classmethod
    def persist_session(
        cls,
        session_initialization_config: SessionInitializationConfig,
        url: Optional[str] = None,
    ):
        """return persisted setu session if present."""

        # if platform is not supported, return
        if not platform_supports_setu_session_reuse():
            return

        # persist session details for next run
        session_details_file_path = get_session_details_file_path()
        SessionDetails(
            session_id=cls.session_id,  # type: ignore
            url=url,  # type: ignore
            session_initialization_config=session_initialization_config,
        ).persist(session_details_file_path)
