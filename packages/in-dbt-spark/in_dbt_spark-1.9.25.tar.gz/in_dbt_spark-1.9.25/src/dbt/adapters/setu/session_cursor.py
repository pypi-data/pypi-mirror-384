import os
import time
from typing import Optional
import re

import dbt_common.exceptions
from dbt.adapters.setu.client import SetuClient
from dbt.adapters.events.logging import AdapterLogger
from dbt.adapters.setu.constants import VALID_STATEMENT_KINDS
from dbt.adapters.setu.models import StatementKind, Output, StatementState, Statement
from dbt.adapters.setu.utils import (
    polling_intervals,
    waiting_for_output,
    get_data_from_json_output,
)
from dbt.adapters.setu.setu_indbt_utils import format_python_code

logger = AdapterLogger("Spark")


class SetuStatementCursor:
    """
    Manage SETU statement and high-level interactions with it.
    :param client: setu client for managing statements
    :param session_id: setu session ID
    """

    def __init__(self, client: SetuClient, session_id: str):
        self.session_id: str = session_id
        self.client: SetuClient = client
        self.statement: Optional[Statement] = None

    def description(self):
        self.fetchall()
        json_output = self.statement.output.json
        columns = json_output["schema"]["fields"]

        # Old behavior but with an added index field["type"]
        return [[column["name"], column["type"]] for column in columns]

    def execute(self, code: str) -> Output:
        statement_kind: StatementKind = self.get_statement_kind(code)
        logger.info(f"statement_kind = {statement_kind} ")

        # handle the code formatting based on the statement kind
        # For PySpark, we need to preserve the original indentation and empty lines
        # For SQL and Spark, we add a space to each line and filter out empty lines

        if statement_kind == StatementKind.PYSPARK:
            formatted_code:str = self.get_formatted_code(code)
            formatted_code = format_python_code(formatted_code)
            logger.info("############# <PYSPARK CODE> #############")
            logger.info(f'\n{formatted_code}')
            logger.info("############# </PYSPARK CODE> #############")
        else:
            formatted_code: str = self.get_formatted_code(code)
            logger.info(f"formatted_code = {formatted_code} ")
        if statement_kind not in VALID_STATEMENT_KINDS:
            raise ValueError(
                f"{statement_kind} is not a valid statement kind for a SETU server of "
                f"(should be one of {VALID_STATEMENT_KINDS})"
            )
        self.statement = self.client.create_statement(
            self.session_id, formatted_code, statement_kind
        )
        intervals = polling_intervals([1, 2, 3, 5], 10)
        while waiting_for_output(self.statement):
            logger.info(
                " Setu statement progress {} : {}".format(
                    self.statement.statement_id, self.statement.progress
                )
            )
            time.sleep(next(intervals))
            self.statement = self.client.get_statement(
                self.statement.session_id, self.statement.statement_id
            )
        if self.statement.output is None:
            logger.error(f" Setu Statement {self.statement.statement_id} had no output ")
            raise dbt_common.exceptions.DbtRuntimeError(
                f"Setu Statement {self.statement.statement_id} had no output"
            )
        logger.info(
            "Setu Statement {} state is : {}".format(
                self.statement.statement_id, self.statement.state
            )
        )
        try:
            self.statement.output.raise_for_status()
        except dbt_common.exceptions.DbtRuntimeError as e:
            error_message = str(e)
            # Use regex to check for the specific non-fatal error message
            if (re.search(r"User .* is in too many groups already and cannot be added to more", error_message)
                    or re.search(r"User .* does not exist in Grid LDAP", error_message)):
                logger.warning(
                    f"Non-fatal error during Setu Statement {self.statement.statement_id} execution: {error_message}"
                    " This error is being treated as non-fatal as per requirements."
                )
                return self.statement.output
            else:
                raise e
        except Exception as e:
            raise dbt_common.exceptions.DbtRuntimeError(
                f"An unexpected error occurred during Setu Statement {self.statement.statement_id} status check: {e}"
            )
        if not self.statement.output.execution_success:
            logger.error(
                "Setu Statement {} output Error : {}".format(
                    self.statement.statement_id, self.statement.output
                )
            )
            raise dbt_common.exceptions.DbtRuntimeError(
                f"Error during Setu Statement {self.statement.statement_id} execution : {self.statement.output.error}"
            )
        return self.statement.output

    def close(self):
        if self.statement is not None and self.statement.state in [
            StatementState.WAITING,
            StatementState.RUNNING,
        ]:
            try:
                logger.info("closing Setu Statement id : {} ".format(self.statement.statement_id))
                self.client.cancel_statement(
                    self.statement.session_id, self.statement.statement_id
                )
                logger.info("Setu Statement closed")
            except Exception as e:
                logger.exception("Setu Statement already closed ", e)

    def fetchall(self):
        if self.statement is not None and self.statement.state in [
            StatementState.WAITING,
            StatementState.RUNNING,
        ]:
            intervals = polling_intervals([1, 2, 3, 5], 10)
            while waiting_for_output(self.statement):
                logger.info(
                    " Setu statement {} progress : {}".format(
                        self.statement.statement_id, self.statement.progress
                    )
                )
                time.sleep(next(intervals))
                self.statement = self.client.get_statement(
                    self.statement.session_id, self.statement.statement_id
                )
            if self.statement.output is None:
                logger.error(f"Setu Statement {self.statement.statement_id} had no output")
                raise dbt_common.exceptions.DbtRuntimeError(
                    f"Setu Statement {self.statement.statement_id} had no output"
                )
            self.statement.output.raise_for_status()
            if self.statement.output.json is None:
                logger.error(f"Setu statement {self.statement.statement_id} had no JSON output")
                raise dbt_common.exceptions.DbtRuntimeError(
                    f"Setu statement {self.statement.statement_id} had no JSON output"
                )
            return get_data_from_json_output(self.statement.output.json)
        elif self.statement is not None:
            self.statement.output.raise_for_status()
            return get_data_from_json_output(self.statement.output.json)
        else:
            raise dbt_common.exceptions.DbtRuntimeError(
                "Setu statement response : {} ".format(self.statement)
            )

    def get_formatted_code(self, code: str) -> str:
        """
        Format the code for execution in the Setu session.
        
        This method handles different types of code (SQL, Spark, PySpark) differently:
        - For PySpark code, it preserves the original indentation and empty lines
        - For SQL and Spark code, it adds a space to each line and filters out empty lines
        
        It also removes the statement kind markers ($$spark$$ or $$pyspark$$) from the code.
        
        Args:
            code: The code to format
            
        Returns:
            The formatted code ready for execution
        """
        # First, determine the statement kind
        statement_kind = self.get_statement_kind(code)
        
        # For PySpark, we need to handle the code differently to preserve indentation
        if statement_kind == StatementKind.PYSPARK:
            # For Python code, we need to be very careful with indentation
            # First, completely remove the marker line if it's on its own line
            pyspark_marker = "$$" + StatementKind.PYSPARK.value + "$$"
            lines = code.splitlines()
            clean_lines = []
            marker_removed = False
            
            # First pass: find and remove the marker line if it's alone
            for i, line in enumerate(lines):
                stripped = line.strip()
                if not marker_removed and stripped == pyspark_marker:
                    # Skip this line entirely as it only contains the marker
                    marker_removed = True
                    continue
                elif not marker_removed and pyspark_marker in line:
                    # The marker is in this line but not alone
                    # Remove the marker without changing indentation
                    clean_lines.append(line.replace(pyspark_marker, ""))
                    marker_removed = True
                else:
                    # Regular line, keep it as is
                    clean_lines.append(line)
            
            # Skip depends_on statements
            code_lines = [line for line in clean_lines if not line.strip().startswith("-- depends_on:")]
            
            # Remove blank lines at the beginning
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            
            # Strip indentation from lines till "</inDBT Pre-Inserted>"
            if code_lines:
                for i in range(len(code_lines)):
                    if "</inDBT Pre-Inserted>" in code_lines[i]:
                        # Strip current, one more line and break
                        code_lines[i] = code_lines[i].strip()
                        code_lines[i+1] = code_lines[i+1].strip()
                        break
                    code_lines[i] = code_lines[i].strip()
            
            # Join the lines with the appropriate line separator
            return os.linesep.join(code_lines)
        else:
            # For SQL and Spark, use the original approach
            code_lines = []
            marker_removed = False
            
            for line in code.splitlines():
                # Check for and remove the statement kind markers
                if not marker_removed:
                    # Check for markers
                    spark_marker = "$$" + StatementKind.SPARK.value + "$$"
                    if spark_marker in line:
                        line = line.replace(spark_marker, "")
                        marker_removed = True
                
                # Ignore depends_on statements
                if line.strip().startswith("-- depends_on:"):
                    continue
                
                # Add a space to each line
                code_lines.append(" " + line.strip())
            
            # Join the lines, filtering out empty ones
            return os.linesep.join([s for s in code_lines if s.strip()])

    def get_statement_kind(self, code: str) -> StatementKind:
        for line in code.splitlines():
            line = line.strip()
            # Ignore depends_on statements in model files
            if not line or line.startswith("-- depends_on:"):
                continue
            """
            StatementKind inference logic (sql/scala/pyspark)
            If Macro sql contains $$spark$$ in the beginning of the line, then spark
            Else If Macro sql contains $$pyspark$$ in the beginning of the line, then pyspark
            Else sql
            """
            if line.startswith("$$" + StatementKind.SPARK.value + "$$"):
                return StatementKind.SPARK
            elif line.startswith("$$" + StatementKind.PYSPARK.value + "$$"):
                return StatementKind.PYSPARK
            else:
                return StatementKind.SQL
        return StatementKind.SQL
