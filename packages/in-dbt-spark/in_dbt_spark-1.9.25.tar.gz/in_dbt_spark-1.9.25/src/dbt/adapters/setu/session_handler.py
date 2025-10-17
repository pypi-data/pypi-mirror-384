from typing import Optional

from dbt.adapters.setu.session_cursor import SetuStatementCursor

from dbt.adapters.setu.session import SetuSession
from dbt_common.utils.encoding import DECIMALS
from dbt.adapters.events.logging import AdapterLogger

NUMBERS = DECIMALS + (int, float)
logger = AdapterLogger("Spark")


class SetuSessionHandler:
    """
    Setu session handler responsible for creating and executing statements.
    :param handle: Setu session
    """

    def __init__(self, handle: SetuSession):
        self.handle: SetuSession = handle
        self._cursor: Optional[SetuStatementCursor] = None

    def cursor(self):
        logger.info("creating new Setu statement")
        self._cursor = self.handle.cursor()
        return self

    def rollback(self, *args, **kwargs):
        logger.debug("cursor rollback not implemented for spark")

    @property
    def description(self):
        return self._cursor.description()

    def fetchall(self):
        logger.info("fetch all on Setu statement")
        return self._cursor.fetchall()

    def cancel(self):
        if self._cursor:
            try:
                logger.info("cancelled the Setu statement")
                self._cursor.close()
            except EnvironmentError as exc:
                logger.exception("Exception while cancelling Setu statement", exc)

    def close(self):
        if self._cursor:
            try:
                logger.info("closing the Setu statement")
                self._cursor.close()
            except EnvironmentError as exc:
                logger.exception("Exception while closing Setu statement", exc)

    def execute(self, sql: str, bindings=None):
        """
        execute the DBT macro SQL statements
        """
        if sql.strip().endswith(";"):
            sql = sql.strip()[:-1]
        if self._cursor is not None:
            self._cursor.execute(code=sql)
