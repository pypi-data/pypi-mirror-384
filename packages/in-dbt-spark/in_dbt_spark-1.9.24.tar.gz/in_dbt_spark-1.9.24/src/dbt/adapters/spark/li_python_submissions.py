from dbt_common.exceptions import DbtRuntimeError
from dbt.adapters.spark import ExtendedSparkCredentials
from dbt.adapters.spark.python_submissions import DBContext, DBCommand, BaseDatabricksHelper
from dbt.adapters.spark import __version__
from typing import Dict

DEFAULT_POLLING_INTERVAL = 10
SUBMISSION_LANGUAGE = "python"
DEFAULT_TIMEOUT = 60 * 60 * 24
DBT_SPARK_VERSION = __version__.version


class ExtendedBaseDatabricksHelper(BaseDatabricksHelper):
    def __init__(self, parsed_model: Dict, credentials: ExtendedSparkCredentials) -> None:
        self.credentials = credentials
        self.identifier = parsed_model["alias"]
        self.schema = parsed_model["schema"]
        self.parsed_model = parsed_model
        self.timeout = self.get_timeout()
        self.polling_interval = DEFAULT_POLLING_INTERVAL
        self.check_credentials()
        self.auth_header = {
            "Authorization": f"Bearer {self.credentials.token}",
            "User-Agent": f"dbt-labs-dbt-spark/{DBT_SPARK_VERSION} (Databricks)",
        }


class ExtendedDBContext(DBContext):
    def __init__(
        self, credentials: ExtendedSparkCredentials, cluster_id: str, auth_header: dict
    ) -> None:
        self.auth_header = auth_header
        self.cluster_id = cluster_id
        self.host = credentials.host


class ExtendedDBCommand(DBCommand):
    def __init__(
        self, credentials: ExtendedSparkCredentials, cluster_id: str, auth_header: dict
    ) -> None:
        self.auth_header = auth_header
        self.cluster_id = cluster_id
        self.host = credentials.host


class ExtendedJobClusterPythonJobHelper(ExtendedBaseDatabricksHelper):
    def check_credentials(self) -> None:
        if not self.parsed_model["config"].get("job_cluster_config", None):
            raise ValueError("job_cluster_config is required for commands submission method.")

    def submit(self, compiled_code: str) -> None:
        cluster_spec = {"new_cluster": self.parsed_model["config"]["job_cluster_config"]}
        self._submit_through_notebook(compiled_code, cluster_spec)


class ExtendedAllPurposeClusterPythonJobHelper(ExtendedBaseDatabricksHelper):
    def check_credentials(self) -> None:
        if not self.cluster_id:
            raise ValueError(
                "Databricks cluster_id is required for all_purpose_cluster submission method with running with notebook."
            )

    def submit(self, compiled_code: str) -> None:
        if self.parsed_model["config"].get("create_notebook", False):
            self._submit_through_notebook(compiled_code, {"existing_cluster_id": self.cluster_id})
        else:
            context = DBContext(self.credentials, self.cluster_id, self.auth_header)
            command = DBCommand(self.credentials, self.cluster_id, self.auth_header)
            context_id = context.create()
            try:
                command_id = command.execute(context_id, compiled_code)
                # poll until job finish
                response = self.polling(
                    status_func=command.status,
                    status_func_kwargs={
                        "context_id": context_id,
                        "command_id": command_id,
                    },
                    get_state_func=lambda response: response["status"],
                    terminal_states=("Cancelled", "Error", "Finished"),
                    expected_end_state="Finished",
                    get_state_msg_func=lambda response: response.json()["results"]["data"],
                )
                if response["results"]["resultType"] == "error":
                    raise DbtRuntimeError(
                        f"Python model failed with traceback as:\n"
                        f"{response['results']['cause']}"
                    )
            finally:
                context.destroy(context_id)
