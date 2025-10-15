import time

import dbt_common.exceptions
from dbt.adapters.events.logging import AdapterLogger
from dbt.adapters.setu.client import SetuClient, Auth, Verify
from dbt.adapters.setu.models import SessionState, SESSION_STATE_READY, SESSION_INVALID_STATE
from dbt.adapters.setu.session_cursor import SetuStatementCursor
from dbt.adapters.setu.utils import (
    get_platform,
    platform_supports_setu_session_reuse,
    polling_intervals,
)
from typing import Optional

logger = AdapterLogger("Spark")


class SetuSession:
    """Manages a remote SETU session and high-level interactions with it.

    :param url: The Base URL of the SETU server.
    :param session_id: The ID of the SETU session.
    :param auth: A requests-compatible auth object to use when making requests.
    :param verify: Either a boolean, in which case it controls whether we
        verify the server’s TLS certificate, or a string, in which case it must
        be a path to a CA bundle to use. Defaults to ``True``.
    """

    def __init__(
        self,
        url: str,
        session_id: str,
        auth: Optional[Auth] = None,
        verify: Verify = False,
    ) -> None:
        self.client = SetuClient(url, auth, verify)
        self.session_id = session_id
        self.url = url
        self.diagnostics = "No diagnostics available."

    def __enter__(self) -> "SetuSession":
        self.wait_till_ready()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def print_session_details(self):
        """print SETU session information"""
        session = self.client.get_session(session_id=self.session_id)
        logger.info("SETU session INFO = {} ".format(session))

    def wait_till_ready(self) -> None:
        """Wait for the session to be ready."""
        intervals = polling_intervals([1, 2, 3, 5], 10)
        start_time = time.time()
        timeout_seconds = 1860  # setu session timeout is 30 minutes

        while self.state not in SESSION_STATE_READY:
            interval = next(intervals)
            logger.info(
                f"Waiting to get spark resources for setu session - {self.session_id}, current state - {self.state.value}"
            )
            logger.info(f"Sleeping for {interval} seconds..")
            time.sleep(interval)
            if self.state in SESSION_INVALID_STATE:
                # Log setu submit error for dead state
                if self.state == SessionState.DEAD:
                    logger.error(self.client.get_log(self.session_id))
                logger.error(f"Unable to create setu session with {self.session_id} with error:")
                logger.error(self.diagnostics)
                raise dbt_common.exceptions.DbtRuntimeError(
                    f" Setu session state = {self.state} Unable to create setu session with {self.session_id}"
                )

            # Add fail safe to avoid infinite loop
            if time.time() - start_time > timeout_seconds:
                logger.error("Timed out waiting for setu session to be ready")
                raise dbt_common.exceptions.DbtRuntimeError(
                    "Timed out waiting for setu session to be ready"
                )

        self.print_session_details()

    @property
    def state(self) -> SessionState:
        """The state of the managed SETU session."""
        session = self.client.get_session(self.session_id)
        if session is None:
            raise dbt_common.exceptions.DbtRuntimeError(
                "session not found - it may have been shut down"
            )

        if session.state in SESSION_INVALID_STATE:
            self.diagnostics = session.diagnostics
        return session.state

    def cursor(self) -> SetuStatementCursor:
        """create new SETU statement"""
        return SetuStatementCursor(session_id=self.session_id, client=self.client)

    def close(self):
        """Close the managed SETU client."""
        session = self.client.get_session(self.session_id)

        platform = get_platform()
        is_setu_reuse_platform = platform_supports_setu_session_reuse()
        if is_setu_reuse_platform:
            logger.info(
                f"Not cancelling session : {self.session_id} since Platform : {platform} will reuse session "
                f"for next run"
            )

        # is session is not present and platform doesn't support setu reuse
        if session is not None and not is_setu_reuse_platform:
            self.client.cancel_session(session_id=self.session_id)
            logger.info(f"cancelled session : {self.session_id}")
        self.client.close()
