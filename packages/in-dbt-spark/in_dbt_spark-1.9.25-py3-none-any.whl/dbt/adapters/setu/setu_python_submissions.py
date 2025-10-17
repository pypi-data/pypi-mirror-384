from typing import Dict, Any, Optional
from dbt.adapters.base.impl import PythonJobHelper
from dbt.adapters.setu.session_cursor import SetuStatementCursor
from dbt.adapters.setu.client import SetuClient
from dbt.adapters.setu.constants import PYSPARK_MARKER
from dbt.adapters.setu.models import StatementKind
from dbt.adapters.setu.session import SetuSession
from dbt_common.exceptions import DbtRuntimeError
from dbt.adapters.spark import ExtendedSparkCredentials
from dbt.adapters.setu.python_platform_code import PYTHON_PLATFORM_CODE
import time
import logging

logger = logging.getLogger(__name__)


class SetuPythonJobHelper(PythonJobHelper):
    """
    Python Job Helper for Setu sessions.
    This helper executes Python code directly in the Setu session instead of submitting it to a cluster.
    
    The implementation converts Python models to SQL that can be executed directly in the Spark session.
    This bypasses the standard Python model execution path by directly handling Python models differently.
    """

    def __init__(self, model: Dict[str, Any], credentials: ExtendedSparkCredentials):
        # Don't call super().__init__() as it raises NotImplementedError
        self.model = model
        self.credentials = credentials   
        
    def submit(self, compiled_code: str) -> Dict[str, Any]:
        """
        Execute the Python code directly in the Setu session.
        
        This implementation processes the compiled code to work with Setu's specific
        PySpark execution syntax ($$pyspark$$) and executes it in the Setu session.
        
        Args:
            compiled_code: The compiled Python code to execute.
            
        Returns:
            A dictionary containing the execution result.
        """
        # Log that we're using the Setu Python job helper
        logger.info(f"Using SetuPythonJobHelper for model: {self.model.get('name')}")
        
        start_time = time.time()
        
        try:
            # Extract model information
            model_name = self.model.get('name', 'unknown_model')
            schema_name = self.model.get('schema', 'default_schema')
            
            # Log information about the model being processed
            logger.info(f"Processing Python model: {model_name} in schema: {schema_name}")
            
            # For debugging - print information about the credentials and model
            logger.info(f"Credentials type: {type(self.credentials)}")
            logger.info(f"Model keys: {self.model.keys() if isinstance(self.model, dict) else 'Not a dict'}")
            
            connection = None
            setu_client = None
            session_id = None
            
            # Print all attributes of credentials for debugging
            for attr in dir(self.credentials):
                if not attr.startswith('_'):
                    try:
                        value = getattr(self.credentials, attr)
                        logger.info(f"Credentials.{attr} = {value}")
                    except Exception as e:
                        logger.info(f"Error getting {attr}: {e}")
            
            # Try to get the connection from the credentials directly
            if hasattr(self.credentials, 'handle') and self.credentials.handle:
                connection = self.credentials.handle
                logger.info(f"Found connection in credentials.handle: {connection}")
                
                # If we have a connection, try to get the client and session_id from it
                if hasattr(connection, 'client') and hasattr(connection, 'session_id'):
                    setu_client = connection.client
                    session_id = connection.session_id
                    logger.info(f"Found Setu client and session_id from connection: {session_id}")
            
            # Try to access the Setu session manager directly
            if not connection or not setu_client or not session_id:
                try:
                    # Import the session manager to access the current session
                    from dbt.adapters.setu.session_manager import SetuSessionManager
                    
                    # Get the session ID from the session manager
                    if SetuSessionManager.session_id:
                        session_id = SetuSessionManager.session_id
                        logger.info(f"Found session_id from SetuSessionManager: {session_id}")
                        
                        # Create a client for this session
                        # For Setu connections, the URL is stored in the url field, not the host field
                        url = self.credentials.url
                        token = self.credentials.token
                        
                        # Ensure URL is not None
                        if not url:
                            raise DbtRuntimeError("URL is None. Cannot create Setu client.")
                            
                        setu_client = SetuClient(url=url, auth=token, verify=False)
                except Exception as e:
                    logger.info(f"Error getting session from SetuSessionManager: {e}")
            
            # Try to create a new client and use existing session ID
            if not setu_client or not session_id:
                try:
                    # Create a new Setu client
                    # For Setu connections, the URL is stored in the url field, not the host field
                    url = self.credentials.url
                    token = self.credentials.token
                    
                    # Ensure URL is not None
                    if not url:
                        raise DbtRuntimeError("URL is None. Cannot create Setu client.")
                        
                    logger.info(f"Creating new Setu client with url={url}")
                    setu_client = SetuClient(url=url, auth=token, verify=False)
                    
                    # Try to get the session ID from various sources
                    if hasattr(self.credentials, 'session_id') and self.credentials.session_id:
                        session_id = self.credentials.session_id
                        logger.info(f"Using session_id from credentials: {session_id}")
                    elif connection and hasattr(connection, 'session_id'):
                        session_id = connection.session_id
                        logger.info(f"Using session_id from connection: {session_id}")
                    
                    # If we still don't have a session ID, try to get it from the model context
                    if not session_id and 'context' in self.model:
                        context = self.model['context']
                        if hasattr(context, 'adapter') and hasattr(context.adapter, 'connections'):
                            try:
                                # Try to get the session ID from the adapter's connection
                                conn = context.adapter.connections.get_thread_connection()
                                if conn and hasattr(conn, 'handle') and hasattr(conn.handle, 'session_id'):
                                    session_id = conn.handle.session_id
                                    logger.info(f"Using session_id from context.adapter.connections: {session_id}")
                            except Exception as e:
                                logger.info(f"Error getting session_id from context.adapter.connections: {e}")
                    
                    # If we still don't have a session ID, we can't proceed
                    if not session_id:
                        raise DbtRuntimeError("Could not find existing Setu session. Make sure a Setu session is active before running Python models.")
                except Exception as e:
                    raise DbtRuntimeError(f"Error creating Setu client or finding session ID: {str(e)}")
            
            if not setu_client or not session_id:
                raise DbtRuntimeError("Missing Setu client or session ID for Python execution")

            # Ensure compiled_code is not None
            if compiled_code is None:
                raise DbtRuntimeError("Compiled code is None. Cannot execute Python model.")
            
            # Ensure the code has the $$pyspark$$ marker at the beginning
            if not compiled_code.strip().startswith(PYSPARK_MARKER):
                compiled_code = f"{PYSPARK_MARKER}\n{compiled_code}"
            
            # Add platform code
            compiled_code = compiled_code + "\n\n" + PYTHON_PLATFORM_CODE
            
            # Create a Setu statement cursor to execute the code
            cursor = SetuStatementCursor(setu_client, session_id)
            
            # Execute the Python code in the Setu session
            logger.info(f"Executing Python model {model_name} in Setu session")
            output = cursor.execute(compiled_code)
            
            # Process the execution result
            if output.execution_success:
                logger.info(f"Python model {model_name} executed successfully in Setu session")
                
                # No need to fetch results as table creation happens in the submitted code
                end_time = time.time()
                execution_time = end_time - start_time
                
                return {
                    "status": "SUCCESS",
                    "execution_time": execution_time,
                    "message": f"Python model {model_name} executed successfully in Setu session",
                    "data": None
                }
            else:
                error_message = f"Python execution failed: {output.error if output.error else 'Unknown error'}"
                logger.error(error_message)
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                raise DbtRuntimeError(error_message)
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            error_message = f"Error executing Python model in Setu session: {str(e)}"
            logger.error(error_message)
            
            raise DbtRuntimeError(error_message)
