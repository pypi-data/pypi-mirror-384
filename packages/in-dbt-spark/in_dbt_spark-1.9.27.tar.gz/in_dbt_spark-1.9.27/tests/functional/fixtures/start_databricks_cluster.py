from base64 import standard_b64encode
import os # Ensure os is imported
from os import getenv
from time import sleep

import pytest

# --- Start of modification ---
# Defensively get the environment variable, provide a default empty string
# or a placeholder if it's None during import.
# This prevents the TypeError during the initial import phase.
# Use a temporary variable for the host name
_dbt_databricks_host_name = getenv("DBT_DATABRICKS_HOST_NAME") or "" # Provide an empty string if None

# Use the defensively retrieved value to build the HOST string
# The actual connection will likely fail later if the value is still empty or wrong,
# but the import won't crash.
HOST = "https://" + _dbt_databricks_host_name

# Get other environment variables needed at the module level
CLUSTER = getenv("DBT_DATABRICKS_CLUSTER_NAME")
TOKEN = getenv("DBT_DATABRICKS_TOKEN")
PORT = 443
ORGANIZATION = "0"
# --- End of modification ---

try:
    from pyhive import hive
    from thrift.transport.THttpClient import THttpClient
    from thrift.Thrift import TApplicationException
except ImportError:
    # These imports are optional dependencies, so handle if they're not installed
    pass


from dbt.adapters.spark.connections import SparkConnectionManager


# Running this should prevent tests from needing to be retried because the Databricks cluster isn't available
@pytest.fixture(scope="session", autouse=True)
def start_databricks_cluster(request):

    profile = request.config.getoption("--profile")

    if profile.startswith("databricks"):
        # Ensure we wait for the cluster only if a databricks profile is used
        _wait_for_databricks_cluster()

    yield


def _wait_for_databricks_cluster() -> None:
    """
    It takes roughly 3-5 minutes for the cluster to start, to be safe we'll wait for 10 minutes
    """
    # Check if necessary environment variables are set before attempting connection
    if not HOST or not TOKEN or not CLUSTER:
         # If variables are missing, skip waiting or raise a specific error
         # depending on desired test behavior when connection info is absent.
         # For now, we'll assume the defensive check during import is sufficient
         # to prevent crashing, but a real connection attempt would fail later.
         print("Skipping Databricks cluster wait due to missing connection info.")
         return # Or raise a more informative error

    transport_client = _transport_client()

    # Attempt to connect multiple times
    for attempt in range(20):
        try:
            # Attempt connection using the transport client
            hive.connect(thrift_transport=transport_client)
            print(f"Databricks cluster connected after {attempt * 30} seconds.")
            return # Connection successful
        except TApplicationException as e:
            # Handle Thrift application exceptions (e.g., authentication failures)
            print(f"Attempt {attempt+1} failed: {e}")
            sleep(30) # Wait before retrying
        except Exception as e:
            # Handle other potential exceptions during connection
            print(f"Attempt {attempt+1} failed with unexpected error: {e}")
            sleep(30) # Wait before retrying


    # If loop finishes without returning, cluster did not become available
    raise Exception("Databricks cluster did not start in time after multiple attempts")


def _transport_client():
    # Construct the connection URL using the module-level variables
    # Ensure HOST, CLUSTER, PORT, ORGANIZATION are defined at module level
    conn_url = SparkConnectionManager.SPARK_CONNECTION_URL.format(
        host=HOST,
        cluster=CLUSTER,
        port=PORT,
        organization=ORGANIZATION,
    )

    # Create the HTTP transport client
    transport_client = THttpClient(conn_url)

    # Prepare the token for basic authentication
    # Ensure TOKEN is defined at module level
    if not TOKEN:
        raise ValueError("DBT_DATABRICKS_TOKEN environment variable is not set.")

    raw_token = f"token:{TOKEN}".encode('utf-8') # Encode token to bytes
    token_base64 = standard_b64encode(raw_token).decode('utf-8') # Encode to base64 and decode to string

    # Set the Authorization header
    transport_client.setCustomHeaders({"Authorization": f"Basic {token_base64}"})

    return transport_client
