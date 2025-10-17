import json
from typing import List, Optional, Dict, Any


class JobParameters:
    driverMemory: str
    executorMemory: str
    driverCores: int
    executorCores: int
    numExecutors: int
    sparkVersion: str

    def __init__(
            self,
            driver_memory: str,
            executor_memory: str,
            driver_cores: int,
            executor_cores: int,
            num_executors: int,
            spark_version: str,
    ) -> None:
        self.driverMemory = driver_memory
        self.executorMemory = executor_memory
        self.driverCores = driver_cores
        self.executorCores = executor_cores
        self.numExecutors = num_executors
        self.sparkVersion = spark_version

    def to_json(self):
        return json.dumps(
            self,
            default=lambda o: dict((key, value) for key, value in o.__dict__.items() if value),
            sort_keys=True,
            indent=4,
        )


class Config:
    proxyUser: str
    sessionName: str
    enableSsl: bool
    executionTags: Optional[Dict[str, Any]]
    jobParameters: JobParameters
    otherConfs: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    heartbeatTimeoutInSeconds: int

    def __init__(
            self,
            proxy_user: str,
            session_name: str,
            enable_ssl: bool,
            execution_tags: Optional[Dict[str, Any]],
            job_parameters: JobParameters,
            other_confs: Optional[Dict[str, Any]],
            metadata: Optional[Dict[str, Any]],
            heartbeat_timeout_in_seconds: int,
    ) -> None:
        self.proxyUser = proxy_user
        self.sessionName = session_name
        self.enableSsl = enable_ssl
        self.executionTags = execution_tags
        self.jobParameters = job_parameters
        self.otherConfs = other_confs
        self.metadata = metadata
        self.heartbeatTimeoutInSeconds = heartbeat_timeout_in_seconds

    def to_json(self):
        return json.dumps(
            self,
            default=lambda o: dict((key, value) for key, value in o.__dict__.items() if value),
            sort_keys=True,
            indent=4,
        )


class Dependencies:
    jars: Optional[List[str]]
    files: Optional[List[str]]
    archives: Optional[List[str]]
    pyFiles: Optional[List[str]]

    def __init__(
            self,
            jars: Optional[List[str]],
            files: Optional[List[str]],
            archives: Optional[List[str]],
            py_files: Optional[List[str]],
    ) -> None:
        self.jars = jars
        self.files = files
        self.archives = archives
        self.pyFiles = py_files

    def to_json(self):
        return json.dumps(
            self,
            default=lambda o: dict((key, value) for key, value in o.__dict__.items() if value),
            sort_keys=True,
            indent=4,
        )


class Dependency:
    dependencies: Dependencies
    manifestFileLocation: Optional[str]

    def __init__(self, dependencies: Dependencies, manifest_file_location: Optional[str]) -> None:
        self.dependencies = dependencies
        self.manifestFileLocation = manifest_file_location

    def to_json(self):
        return json.dumps(
            self,
            default=lambda o: dict((key, value) for key, value in o.__dict__.items() if value),
            sort_keys=True,
            allow_nan=False,
            indent=4,
        )


"""
Setu session request payload to create a new spark interactive session.

    SessionRequest:
      type: object
      properties:
        dependency:
          $ref: 'DependencySpec'
        config:
          $ref: 'ConfigSpec'

    DependencySpec:
      type: object
      properties:
        dependencies:
          $ref: 'Dependencies'
        manifestFileLocation:
          type: string
          description: The ivy coordinate of the file listing dependencies required by the spark app.
          This file will be mostly auto-generated using a provide gradle plugin.
          example: com.linkedin.setu-example:setu-demo-manifest:0.0.7

    Dependencies:
      type: object
      properties:
        jars:
          type: array
          items:
            type: string
          example: ["com.linkedin.setu-example:setu-demo-manifest:0.0.7",
           "com.linkedin.spark-service-plugins:spark-jobs_2.11:0.0.7?transitive=true"]
          description: List of ivy coordinates of the artifacts. Added to the java classpath for drivers and executors.
        files:
          type: array
          items:
            type: string
          description: List of ivy coordinates of the artifacts. Placed in the working directory of each executor.
        archives:
          type: array
          items:
            type: string
          description: List of ivy coordinates of the artifacts. Extracted into the working directory of each executor.
        pyFiles:
          type: array
          items:
            type: string
          description: List of ivy coordinates of the artifacts. Added to the PYTHONPATH

    ConfigSpec:
      type: object
      required:
        - proxyUser
        - executionTags
      properties:
        proxyUser:
          type: string
          description: The User to impersonate when executing the spark application.
          example: griddev
        sessionName:
          type: string
          description: Multiple sessions for the same logical entity should have the same sessionName
        enableSSL:
          type: boolean
          default: false
          description: "If true, grestin cert for proxy-user will be available to spark app as part of credentials object."
        executionTags:
          type: object
          description: Used to determine the target execution env (cluster) dynamically at runtime.
          required:
            - gpu
            - pool
          properties:
            gpu:
              type: boolean
              default: false
              description: If the spark job requires gpu for processing.
            pool:
              type: string
              description: Execution environment for the job.
              enum:
                - dev
                - prod
                - obfs
                - gridtest
        jobParameters:
          $ref: 'JobParameters'
        otherConfs:
          type: object
          description: Additional configs that may be needed for spark app execution but not covered as dedicated field.
           [Example](https://spark.apache.org/docs/latest/configuration.html).
           These configs are pass-through (as it is to yarn, k8s, etc.)
          additionalProperties:
            type: string
          example:
            "spark.local.dir": "/tmp"
            "spark.python.worker.reuse": "true"
        metadata:
          type: object
          description: High-level tracking metadata used to provide contextual information about the application.
           For example, audit-related information like an Azkaban execution ID, flow name, etc.
            This metadata will be part of tracking/monitoring events.
          additionalProperties:
            type: string
          example:
            "airflow.run.id": "12345"
            "airflow.execution.date": "12345"
            "dbt.project.name": "dbt_hello_world"

    JobParameters:
      type: object
      description: Important parameters for spark jobs. Spark defaults will be applied to optional fields.
      properties:
        driverMemory:
          type: string
          description: Amount of memory to use for driver process.
          example: "5G"
        executorMemory:
          type: string
          description: Amount of memory to use for executor process.
          example: "3G"
        driverCores:
          type: integer
          description: Number of cores to use for driver process.
          example: 3
        executorCores:
          type: integer
          description: Number of cores to use for executor process.
          example: 5
        numExecutors:
          type: integer
          description: Number of executors.
          example: 100
        sparkVersion:
          type: string
          description: Spark version for the application.
          example: "3.1"
"""


class SetuSessionRequest:
    def __init__(self, dependency: Dependency, config: Config) -> None:
        self.dependency = dependency
        self.config = config

    def to_json(self):
        return json.dumps(
            self,
            default=lambda o: dict((key, value) for key, value in o.__dict__.items() if value),
            sort_keys=True,
            indent=4,
        )
