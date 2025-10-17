import ast
import json
import os
import dbt_common.exceptions
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from dbt.adapters.events.logging import AdapterLogger

logger = AdapterLogger("Spark")


@dataclass
class Output:
    json: Optional[dict]
    execution_success: bool
    error: Optional[str]

    @classmethod
    def from_json(cls, data: dict) -> "Output":
        if "outputData" not in data or not type(data.get("outputData")) is dict:
            try:
                data["outputData"] = json.loads(str(data.get("outputData")))
            except ValueError:
                logger.error(f"Error while json parsing outputData = {data.get('outputData')}")
                return cls(
                    None,
                    json.loads(str(data.get("executionSuccess")).lower()),
                    data.get("error"),
                )
        return cls(
            ast.literal_eval(str(data.get("outputData"))).get("application/json"),
            json.loads(str(data.get("executionSuccess")).lower()),
            data.get("error"),
        )

    def raise_for_status(self) -> None:
        if not self.execution_success:
            logger.error(f"Spark Runtime Error : {self.error}")
            components = []
            if self.error is not None:
                components.append(f"Error ={self.error}")
            raise dbt_common.exceptions.DbtRuntimeError(f'({", ".join(components)})')


class StatementKind(Enum):
    SPARK = "spark"
    PYSPARK = "pyspark"
    SPARKR = "sparkr"
    SQL = "sql"


class StatementState(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    AVAILABLE = "available"
    ERROR = "error"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"


@dataclass
class Statement:
    session_id: str
    statement_id: int
    state: StatementState
    code: str
    output: Optional[Output]
    progress: Optional[float]

    @classmethod
    def from_json(cls, session_id: str, data: dict) -> "Statement":
        if data["outputData"] is None:
            output = None
        else:
            output = Output.from_json(data)

        return cls(
            session_id,
            data["id"],
            StatementState(data["state"]),
            data["code"],
            output,
            data.get("progress"),
        )


class SessionState(Enum):
    NOT_STARTED = "not_started"
    STARTING = "starting"
    RECOVERING = "recovering"
    IDLE = "idle"
    RUNNING = "running"
    BUSY = "busy"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"
    DEAD = "dead"
    KILLED = "killed"
    SUCCESS = "success"
    SUBMITTING = "submitting"
    SUBMITTED = "submitted"


SESSION_STATE_NOT_READY = {
    SessionState.NOT_STARTED,
    SessionState.STARTING,
    SessionState.SUBMITTING,
    SessionState.SUBMITTED,
}
SESSION_INVALID_STATE = {
    SessionState.ERROR,
    SessionState.DEAD,
    SessionState.KILLED,
}
SESSION_STATE_FINISHED = {
    SessionState.ERROR,
    SessionState.DEAD,
    SessionState.KILLED,
    SessionState.SUCCESS,
}
SESSION_STATE_READY = {
    SessionState.BUSY,
    SessionState.IDLE,
}


@dataclass
class SessionAppInfo:
    sparkUiUrl: str
    yarnQueue: str

    @classmethod
    def from_json(cls, data: dict) -> "SessionAppInfo":
        return cls(data["appUrl"], data["queue"])


@dataclass
class Session:
    session_id: str
    session_name: str
    session_owner: str
    proxy_user: str
    state: SessionState
    application_id: str
    app_info: Optional[SessionAppInfo]
    diagnostics: str

    @classmethod
    def from_json(cls, data: dict) -> "Session":
        if data["appInfo"] is None:
            output = None
        else:
            output = SessionAppInfo.from_json(data["appInfo"])
        return cls(
            data["id"],
            data["name"],
            data["owner"],
            data["proxyUser"],
            SessionState(data["state"]),
            data["appId"],
            output,
            data["diagnostics"],
        )


@dataclass
class SessionInitializationConfig:
    proxy_user: str
    jars: List[str]
    py_files: List[str]
    files: List[str]
    archives: List[str]
    manifest_file_location: str
    driver_memory: str
    driver_cores: int
    executor_memory: str
    executor_cores: int
    num_executors: int
    queue: str
    session_name: str
    spark_version: str
    execution_tags: Dict[str, Any]
    spark_conf: Dict[str, Any]
    metadata: Dict[str, Any]
    heartbeat_timeout_in_seconds: int
    enable_ssl: bool

    @classmethod
    def check_if_confs_are_deep_equal(cls, config1: dict, config2: dict, path: str = "") -> bool:
        # =====================
        # function to check if 2 configs are equal or not
        # in case they are not equal, return False and log which key is different
        # return true if equal
        # =====================
        # Function Logic -
        # compares all keys attributes to check if they are equal
        # in case attribute is dict, recursively checks that
        # d1, d2 - dictionaries for comparison
        # path - recursive path to log when key mismatch is found
        for k in config1:
            if k in config2:
                if type(config1[k]) is dict:
                    cls.check_if_confs_are_deep_equal(
                        config1[k], config2[k], "%s -> %s" % (path, k) if path else k
                    )
                if config1[k] != config2[k]:
                    result = [
                        "%s: " % path,
                        " - %s : %s" % (k, config1[k]),
                        " + %s : %s" % (k, config2[k]),
                    ]
                    logger.info("\n".join(result))
                    return False
            else:
                logger.info("%s%s as key not in d2\n" % ("%s: " % path if path else "", k))
                return False
        return True

    def __eq__(self, other):
        if isinstance(other, SessionInitializationConfig):
            # equality operator for SessionInitializationConfig objects
            # checks if details match other object

            first_dict = asdict(self)
            second_dict = asdict(other)

            # remove session name as it has randomly generated key as suffix and can be different
            first_dict = {i: first_dict[i] for i in first_dict if i != "session_name"}
            second_dict = {i: second_dict[i] for i in second_dict if i != "session_name"}

            # compare if all config attribute values are equal
            return SessionInitializationConfig.check_if_confs_are_deep_equal(
                first_dict, second_dict
            )
        return False


@dataclass
class SessionDetails:
    # data class used to manage session
    # this class is persisted to a file for setu session reuse

    session_id: str
    url: str
    session_initialization_config: SessionInitializationConfig

    def persist(self, file_path):
        # Persist class object as json to given file path

        # Serialize the dataclass as JSON
        json_string = json.dumps(asdict(self))

        # Write the JSON string to a file
        with open(file_path, "w") as json_file:
            json_file.write(json_string)

    @classmethod
    def get_persisted_session_details_if_exists(cls, file_path):
        # Return class obj if persisted session details exist at file_path

        session_details = None
        if os.path.isfile(file_path):
            # Read the JSON data from the file
            logger.info(
                "Reading persisted session from file - {file_path}".format(file_path=file_path)
            )

            with open(file_path, "r") as json_file:
                json_string = json_file.read()

            # Deserialize the JSON data as a dictionary
            json_dict = json.loads(json_string)

            # Create a SessionInitializationConfig from dict
            session_initialization_config_dict = json_dict["session_initialization_config"]
            session_initialization_config = SessionInitializationConfig(
                **session_initialization_config_dict
            )

            # Create a SessionDetails dataclass object using the dictionary data
            session_details = cls(
                session_id=json_dict["session_id"],
                url=json_dict["url"],
                session_initialization_config=session_initialization_config,
            )

            # Log the object to verify the data
            logger.info(
                "Persisted session exists with session id - {session_id}".format(
                    session_id=session_details.session_id
                )
            )
        else:
            logger.info(f"No persisted session exists at path : {file_path}")
            return None
        return session_details
