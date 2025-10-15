import requests
import urllib3
import json
from typing import Union, List, Tuple, Optional
from urllib3.exceptions import InsecureRequestWarning


from dbt.adapters.setu.models import StatementKind
from dbt.adapters.events.logging import AdapterLogger
from dbt.adapters.setu.models import (
    Session,
    SessionInitializationConfig,
    Statement,
)
from dbt.adapters.setu.setu_session_request import (
    SetuSessionRequest,
    Dependency,
    Dependencies,
    Config,
    JobParameters,
)
from dbt.adapters.setu.constants import Platform
from dbt.adapters.setu.utils import get_platform

from dbt.adapters.setu.utils import get_datavault_token, get_grestin_certs

logger = AdapterLogger("Spark")
Auth = Union[requests.auth.AuthBase, Tuple[str, str]]
Verify = Union[bool, str]
Cert = Tuple[str, str]
urllib3.disable_warnings(InsecureRequestWarning)


class JsonClient:
    """
    A wrapper for a requests session for JSON formatted requests.

    This client handles appending endpoints on to a common hostname,
    deserializing the response as JSON and raising an exception when an error
    HTTP code is received.
    """

    def __init__(
        self,
        url: str,
        auth: Optional[Auth] = None,
        verify: Verify = False,
        requests_session: Optional[requests.Session] = None,
        cert: Optional[Cert] = None,
        datavault_token: Optional[str] = None,
    ) -> None:
        self.url = url
        self.auth = auth
        self.verify = verify
        self.headers = {"Content-Type": "application/json", "Accept-Encoding": "identity"}
        if datavault_token:
            self.headers["DVToken"] = datavault_token
        self.cert = cert
        if requests_session is None:
            self.session = requests.Session()
            self.managed_session = True
        else:
            self.session = requests_session
            self.managed_session = False

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        if self.managed_session:
            self.session.close()

    def get(self, endpoint: str = "", params: Optional[dict] = None) -> dict:
        return self._request("GET", endpoint, params=params, headers=self.headers, cert=self.cert)

    def post(self, endpoint: str, data: Optional[dict] = None) -> dict:
        return self._request("POST", endpoint, data, headers=self.headers, cert=self.cert)

    def delete(self, endpoint: str = "") -> dict:
        return self._request("DELETE", endpoint, headers=self.headers, cert=self.cert)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        cert: Optional[Tuple[str, str]] = None,
    ) -> dict:
        url = self.url.rstrip("/") + "/" + endpoint.lstrip("/")
        response = self.session.request(
            method,
            url,
            auth=self.auth,
            verify=self.verify,
            json=data,
            params=params,
            headers=headers,
            cert=cert,
        )
        response.raise_for_status()
        return response.json()


class SetuClient:
    """
    A Client wrapper for all SETU API interactions
    """

    def __init__(
        self,
        url: str,
        auth: Optional[Auth] = None,
        verify: Verify = True,
    ) -> None:
        self._client = JsonClient(
            url=url,
            auth=auth,
            verify=verify,
            cert=get_grestin_certs(),
            datavault_token=get_datavault_token(),
        )
        # Disable proxy redirect from the `requests` module.
        #  The GitHub Actions container uses a proxy server by default, which can cause "service not found" issues for Setu connections.
        # If you need to use a proxy, set the proxy settings explicitly.
        if get_platform() == Platform.GIT_PLATFORM:
            logger.info("disabling proxy server routing for  {0} platform".format(get_platform()))
            self._client.session.trust_env = False

    def __enter__(self) -> "SetuClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying requests session, if managed by this class."""
        self._client.close()

    def list_sessions(self) -> List[Session]:
        """List all the active sessions in SETU."""
        data = self._client.get("/sessions")
        return [Session.from_json(item) for item in data["sessions"]]

    def create_session(
        self, session_initialization_config: SessionInitializationConfig
    ) -> Session:
        """
        Create new SETU Interactive session.
        Spark app for this session exposes long-running Remote Spark Context and allows clients to submit
        un-compiled code snippets (scala or python or SQL) and get the output.
        Session will be alive unless explicitly cancelled or timedout.
        This is not a blocking call.
        """
        dependencies = Dependencies(
            jars=session_initialization_config.jars,
            files=session_initialization_config.files,
            py_files=session_initialization_config.py_files,
            archives=session_initialization_config.archives,
        )
        dependency = Dependency(
            dependencies=dependencies,
            manifest_file_location=session_initialization_config.manifest_file_location,
        )

        job_parameters = JobParameters(
            num_executors=session_initialization_config.num_executors,
            driver_memory=session_initialization_config.driver_memory,
            driver_cores=session_initialization_config.driver_cores,
            executor_memory=session_initialization_config.executor_memory,
            executor_cores=session_initialization_config.executor_cores,
            spark_version=session_initialization_config.spark_version,
        )
        session_initialization_config.spark_conf["spark.yarn.queue"] = (
            session_initialization_config.queue
        )
        config = Config(
            enable_ssl=session_initialization_config.enable_ssl,
            execution_tags=session_initialization_config.execution_tags,
            heartbeat_timeout_in_seconds=session_initialization_config.heartbeat_timeout_in_seconds,
            job_parameters=job_parameters,
            metadata=session_initialization_config.metadata,
            other_confs=session_initialization_config.spark_conf,
            proxy_user=session_initialization_config.proxy_user,
            session_name=session_initialization_config.session_name,
        )
        session_request = SetuSessionRequest(dependency=dependency, config=config)
        logger.info(f"Session create request body : \n {session_request.to_json()}")
        session_request = SetuSessionRequest(dependency=dependency, config=config)
        logger.info(f"Session create request body : \n {session_request.to_json()}")
        try:
            data = self._client.post("/sessions", data=json.loads(session_request.to_json()))
        except requests.HTTPError as e:
            logger.error("Failed while creating Spark Interactive session with error:")
            logger.error(e.response.text)
            logger.exception(f"Failed while creating Spark Interactive session with error {e}")
            raise
        return Session.from_json(data)

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get information about a specific session.
        :param session_id: The ID of the session.
        """
        try:
            data = self._client.get(f"/sessions/{session_id}")
        except requests.HTTPError as e:
            logger.exception(f"Failed to get the Setu session with id {session_id}", e)
            if e.response.status_code == 404:
                return None
            else:
                raise
        return Session.from_json(data)

    def get_log(self, session_id: str):
        """
        Get information about spark-submit yarn logs regarding specific session.
        :param session_id: The ID of the session.
        """
        try:
            data = self._client.get(f"/sessions/{session_id}/log")
        except requests.HTTPError as e:
            logger.error(
                f"Failed to fetch spark submit logs from Setu with session id {session_id}"
            )
            if e.response.status_code == 404:
                logger.error(f"Session {session_id} not found.")
            else:
                # Logging log API response
                logger.error(f"Setu /log API failed with error: {e}")

            # Not raising an exception at DBT end in case failed to fetch logs
            return None

        return "\n".join(data["logs"])

    def cancel_session(self, session_id: str) -> None:
        """
        Cancels the session (kills the respective spark app). The session resource itself will not be deleted,
        and will be available for a few days so users can access logs and get job info. (internal config).
        :param session_id: The ID of the session.
        """
        try:
            existing_session = self.get_session(session_id=session_id)
            if existing_session is not None and existing_session.session_id is not None:
                self._client.post(f"/sessions/{session_id}/cancel")
                logger.info(f"Session closed for session id : {session_id}")
            else:
                logger.info("session already closed ")
        except requests.HTTPError as e:
            logger.exception(f"Failed while cancelling setu session with id {session_id}", e)

    def list_statements(self, session_id: str) -> List[Statement]:
        """
        Get all the statements in a session.
        :param session_id: The ID of the session.
        """
        try:
            response = self._client.get(f"/sessions/{session_id}/statements")
        except requests.HTTPError as e:
            logger.exception(
                f"Failed while fetching list of statements of setu session with id {session_id}",
                e,
            )
            raise
        return [Statement.from_json(session_id, response) for data in response["statements"]]

    def create_statement(
        self, session_id: str, code: str, kind: Optional[StatementKind] = None
    ) -> Statement:
        """
        create a statement in a session. This is not a blocking call.
        :param session_id: The ID of the session.
        :param code: The code to execute.
        :param kind: The kind of code to execute.
        """
        data = {"code": code}
        if kind is not None:
            data["kind"] = kind.value
        try:
            response = self._client.post(f"/sessions/{session_id}/statements", data=data)
        except requests.HTTPError as e:
            logger.exception(
                f"Failed while creating statement for code : {code} in setu session {session_id}",
                e,
            )
            raise
        return Statement.from_json(session_id, response)

    def cancel_statement(self, session_id: str, statement_id: int):
        """
        cancel the specified statement in this session.
        :param session_id: The ID of the session.
        :param statement_id: The ID of the statement.
        """
        try:
            self._client.post(f"/sessions/{session_id}/statements/{statement_id}/cancel")
        except requests.HTTPError as e:
            logger.exception(
                f"Failed while cancelling statement with id {statement_id} in setu session {session_id}",
                e,
            )

    def get_statement(self, session_id: str, statement_id: int) -> Statement:
        """
        Get information about a statement in a session.
        :param session_id: The ID of the session.
        :param statement_id: The ID of the statement.
        """
        try:
            response = self._client.get(f"/sessions/{session_id}/statements/{statement_id}")
        except requests.HTTPError as e:
            logger.exception(
                f"Failed while getting information about statement with id {statement_id} in setu session {session_id}",
                e,
            )
            raise
        return Statement.from_json(session_id, response)
