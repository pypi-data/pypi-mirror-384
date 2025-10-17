import os
import aiohttp
import logging
import math
import asyncio
import time
from datetime import datetime, timezone, timedelta
import jwt

logger = logging.getLogger("core.task")

def _generate_storage_path(powerlink_key: str, task_key: str, app_name: str) -> str:
        """Generate the S3 storage path using reversed timestamp logic."""
        max_timestamp = 9999999999999  # Maximum 13-digit timestamp
        original_timestamp = int(time.time() * 1000)  # Get current timestamp in milliseconds
        reversed_timestamp = max_timestamp - original_timestamp  # Reverse timestamp

        # Ensure timestamp is interpreted in UTC
        folder_timestamp = datetime.fromtimestamp(original_timestamp / 1000, tz=timezone.utc).strftime("%Y%m%d%H%M%S")

        # Construct the storage path
        storage_path = f"{powerlink_key}/{reversed_timestamp}/{task_key}/{app_name}/{folder_timestamp}"
        print(f"📂 S3 Storage Path: {storage_path}")  # Debugging output
        return storage_path

#===================================================================================================
#TODO AGENT_NAME can be empty if actions will use the cookie
class Core:
    """Handles the calls to core APIs for task authentication, execution, and lifecycle management."""

    def __init__(
        self, 
        AGENT_NAME: str | None = None, 
        CORE_API: str = None, 
        JWT_TOKEN: str | None = None,
        AGENT_DISPLAY_NAME: str = None
    ):
        """
        Initialize Core API handler with agent credentials and base API URL.

        Args:
            AGENT_NAME (str): The agent's username for authentication.
            CORE_API (str): Base URL of the Core API service.
            JWT_TOKEN (str | None): If provided, skips the need for login() before accessing protected APIs.


        Raises:
            ValueError: If AGENT_NAME or CORE_API is missing or empty.
        """

        # if not AGENT_NAME:
        #     raise ValueError("[INIT] AGENT_NAME is required and cannot be empty.")
        if not CORE_API:
            raise ValueError("[INIT] CORE_API is required and cannot be empty.")

        self.CORE_API = CORE_API.rstrip("/")
        self.AGENT_NAME = AGENT_NAME
        self.JWT_TOKEN = JWT_TOKEN
        self._PASSWORD: str = None  # Store password for future use
        self.AGENT_DISPLAY_NAME: str = AGENT_DISPLAY_NAME
        self.RUNTIME_VARIABLES: dict[str, str | None] = {}
    
    def is_token_valid(self) -> bool:
        if not self.JWT_TOKEN:
            logger.info("[CORE] JWT Token is missing, cannot validate.")
            return False
        try:
            payload = jwt.decode(self.JWT_TOKEN, options={"verify_signature": False})
            exp = payload.get("exp")
            if not exp:
                return False
            expiry_time = datetime.fromtimestamp(exp, timezone.utc)
            now = datetime.now(timezone.utc)

            # Add small buffer to avoid edge re-logins
            if expiry_time <= now + timedelta(seconds=5):
                logger.warning(f"[CORE] Token near or past expiry: exp={expiry_time}, now={now}")
                return False
            return True
        except Exception as e:
            logger.error(f"[CORE] Failed to parse JWT: {e}")
            return False
        
    @classmethod
    def from_env(cls) -> "Core":
        """
        Constructs a Core instance from environment variables.
        Handles JWT reuse and automatic re-login if token is expired.
        Returns:
            Core: Initialized and authenticated Core instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        agent_name = os.environ.get("AGENT_NAME")
        core_api = os.environ.get("CORE_API")
        jwt_token = os.environ.get("AGENTIX_CORE_JWT_TOKEN")
        agent_display_name = os.environ.get("AGENT_DISPLAY_NAME")
        password = os.environ.get("CORE_PASSWORD")

        print("📜 Initializing Core from environment variables ... ")
        if not agent_name:
            print("❌ Environment variable 'AGENT_NAME' is not set.")
        
        if not core_api:
            print("❌ Environment variable 'CORE_API' is not set.")

        if not jwt_token:
            print("❌ Environment variable 'AGENTIX_CORE_JWT_TOKEN' is not set. Will need to login to Core.")
        
        if not password:
            print("❌ Environment variable 'CORE_PASSWORD' is not set. Will need to login to Core.")

        core = cls(
            AGENT_NAME=agent_name,
            CORE_API=core_api,
            JWT_TOKEN=jwt_token,
            AGENT_DISPLAY_NAME=agent_display_name
        )
        core._PASSWORD = password
        return core
        
    #================================================================================================
    # Get Runtime Variable by Key
    #================================================================================================
    def get_runtime_variable(self, key: str, default: str | None = None) -> str | None:
        """
        Retrieve the value of a runtime variable by key.

        Args:
            key (str): The key of the variable to fetch.
            default (str | None): Default value if key is not found.

        Returns:
            str | None: The variable value or default.
        """
        if not self.RUNTIME_VARIABLES or not isinstance(self.RUNTIME_VARIABLES, dict):
            return default
        return self.RUNTIME_VARIABLES.get(key, default)

    #================================================================================================
    # Fetch Runtime Variables from Core
    #================================================================================================
    async def fetch_runtime_variables(self):
        """
        Fetches runtime variables from Core backend and stores them in self.RUNTIME_VARIABLES.
        """

        if not self.JWT_TOKEN:
            raise ValueError("JWT_TOKEN is missing")
        
        url = f"{self.CORE_API}/v1/powerlink/{self.AGENT_NAME}/runtime-variables"
        headers = {
            "Authorization": f"Bearer {self.JWT_TOKEN}",
            "Referer": self.CORE_API
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        variables = result.get("variables", [])

                        self.RUNTIME_VARIABLES = {
                            item["key"]: item["value"] for item in variables
                        }

                        logger.info(f"✅ Loaded {len(self.RUNTIME_VARIABLES)} runtime variables for slug: {self.AGENT_NAME}")
                    else:
                        logger.error(f"❌ Failed to fetch runtime variables: {response.status} - {await response.text()}")
                        raise RuntimeError(f"Failed to fetch runtime variables: {response.status}")

        except Exception as e:
            logger.error(f"❌ Error loading runtime variables: {e}")
            raise

    #================================================================================================
    # login to Core and get JWT
    #================================================================================================
    async def login(self, PASSWORD: str = None) -> bool:
        """
        Authenticate the agent to Core using username/password and store JWT token.

        Args:
            PASSWORD (str): Password for the agent.

        Returns:
            bool: True if login is successful.

        Raises:
            ValueError: If password is not provided.
            RuntimeError: If authentication fails after retries.
        """

        logger.info(f"🔑 [LOGIN] Authenticating to Core API with user: {self.AGENT_NAME}")
        
        if self.is_token_valid():
            logger.info("✅ [LOGIN] JWT Token is valid, no need to re-login.")
            await self.fetch_runtime_variables()
            return True
        else:
            logger.info("❌ [LOGIN] JWT Token is expired or missing, proceeding with login.")

        if not PASSWORD and not self._PASSWORD:
            raise ValueError("[LOGIN] PASSWORD must be provided to login.")
        
        if not self.CORE_API:
            raise ValueError("[LOGIN] CORE_API must be set to login to Core.")
        
        if not self.AGENT_NAME:
            raise ValueError("[LOGIN] AGENT_NAME must be set to login to Core.")
        

        logger.info("🔐 [LOGIN] Using username and password for logging to Core.")

        login_url = f"{self.CORE_API}/auth"
        headers = {"Referer": self.CORE_API}

        auth_payload = {
            "identifier": self.AGENT_NAME,
            "password": PASSWORD or self._PASSWORD
        }

        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(login_url, json=auth_payload, headers=headers) as login_response:
                        login_json = await login_response.json()
                        if login_response.status == 200 and "jwt" in login_json:
                            self.JWT_TOKEN = login_json["jwt"]
                            self._PASSWORD = PASSWORD  # Store password for future use
                            self.AGENT_DISPLAY_NAME = f"{login_json.get('user', {}).get('firstName', '') or ''} {login_json.get('user', {}).get('lastName', '') or ''}".strip()
                            os.environ["AGENTIX_CORE_JWT_TOKEN"] = self.JWT_TOKEN
                            os.environ["AGENT_DISPLAY_NAME"] = self.AGENT_DISPLAY_NAME

                            logger.info(f"✅ [LOGIN] Login succeeded on attempt {attempt}")
                            break
                        else:
                            logger.warning(f"⚠️ [LOGIN] Login failed on attempt {attempt}: {login_response.status} - {login_json}")
            except Exception as e:
                logger.error(f"❌ [LOGIN] Login error on attempt {attempt}: {e}")

            if attempt < max_retries:
                logger.info("🔁 [LOGIN] Retrying in 2 seconds...")
                await asyncio.sleep(2)
            else:
                raise RuntimeError("[LOGIN] ❌ Authentication failed after maximum retry attempts.")

        if self.JWT_TOKEN:
            await self.fetch_runtime_variables()
        else:
            logger.error("❌ [LOGIN] JWT token not received after login attempts.")

        return True
    
    #================================================================================================
    # Connect to Task in Core
    #================================================================================================
    #TODO: Decorator of ensure Token here
    async def connect_task(self, task_key: str) -> dict:
        """
        Establishes a session for the given task and returns job cookies.

        Args:
            task_key (str): Task key to identify the task session.

        Returns:
            dict: Dictionary of job cookies from the response.

        Raises:
            ValueError: If task_key is not provided or JWT is missing.
            RuntimeError: If the connection fails or cookies are missing.
        """
        logger.info(f"🔑 Authenticating to Core API with user: {self.AGENT_NAME}")

        if not self.JWT_TOKEN:
            logger.error("🔐 [CONNECT] Must login to Core before connecting to task.")
            raise ValueError("[CONNECT] Must login to Core before connecting to task.")
        
        if not task_key:
            logger.error("🔐 [CONNECT] Must provide task_key to connect.")
            raise ValueError("[CONNECT] task_key must be provided to connect.")
        
        connect_url = f"{self.CORE_API}/v1/tasks/{task_key}/connect"
    
        try:
            connect_headers = {
                "Authorization": f"Bearer {self.JWT_TOKEN}",
                "Referer": self.CORE_API
            }

            async with aiohttp.ClientSession() as connect_session:
                async with connect_session.post(connect_url, headers=connect_headers) as connect_response:
                    if connect_response.status != 200:
                        raise RuntimeError(f"❌ [CONNECT] Connect failed: {connect_response.status} - {await connect_response.text()}")

                    JOB_COOKIE = connect_session.cookie_jar.filter_cookies(self.CORE_API)
                    JOB_COOKIE = {k: morsel.value for k, morsel in JOB_COOKIE.items()}

                    if not JOB_COOKIE:
                        logger.error("❌ [CONNECT] No cookies found in the response.")
                        raise RuntimeError("❌ [CONNECT] No cookies found in the response.")
                    
                    logger.info("✅ JOB_COOKIE successfully returned from connect response")
                    return JOB_COOKIE

        except Exception as e:
            logger.error(f"[CONNECT] ❌ Error during connect request: {e}")
            raise RuntimeError(f"[CONNECT] ❌ Error during connect request: {e}")

    #================================================================================================
    # Start Task in Core
    #================================================================================================
    async def start_task(self, JOB_COOKIE: dict, task_key: str, reterive_agent_assignment: bool = False) -> dict:
        """
        Starts a task in Core by calling the `/start` endpoint.

        Args:
            JOB_COOKIE (dict): Dictionary of cookies required for session authentication.
            task_key (str): Unique identifier of the task to start.
            reterive_agent_assignment (bool, optional): If True, Core will return agent assignment details.

        Returns:
            dict: JSON response returned by Core, typically containing updated task state or assignment data.

        Raises:
            ValueError: If JOB_COOKIE or task_key is missing or invalid.
            RuntimeError: If the HTTP request fails or response is invalid.
        """
        if not JOB_COOKIE or not isinstance(JOB_COOKIE, dict):
            logger.error("❌ [START-TASK] JOB_COOKIE is required and must be a non-empty dictionary.")
            raise ValueError("❌ [START-TASK] JOB_COOKIE is required and must be a non-empty dictionary.")
        
        if not task_key:
            logger.error("❌ [START-TASK] task_key is required and cannot be empty.")
            raise ValueError("❌ [START-TASK] task_key is required and cannot be empty.")

        try:
            logger.info(f">>> [START-TASK] Starting Task: {task_key}")

            start_task_url = f"{self.CORE_API}/v1/tasks/{task_key}/start"
            headers = {"Referer": f"{self.CORE_API}"}
            request_body = {
                "data": {
                    "metadata": f"Starting Task from {self.AGENT_NAME}",
                    "retrieveAgentAssignment": reterive_agent_assignment
                }
            }

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.post(start_task_url, headers=headers, json=request_body, allow_redirects=False) as response:
                    response_json = await response.json() if "application/json" in response.headers.get("Content-Type", "") else None

                    if response.status == 200 and response_json is not None:
                        logger.info(f"<<<<< ✅ [START-TASK] Task Started!")
                        return response_json
                    else:
                        redirect_url = response.headers.get("Location")
                        redirect_note = f"Redirect to: {redirect_url}" if redirect_url else "No redirect location provided."
                        
                        logger.error(f"❌ [START-TASK] Failed to start task. "
                                    f"HTTP Status: {response.status} - {response_json} - {redirect_note}")
                        
                        raise RuntimeError(f"❌ [START-TASK] Failed to start task. HTTP Status: {response.status} - {response_json} - {redirect_note}")
                    
        except Exception as e:
            logger.error(f"❌ [START-TASK] Error calling Start Task API: {e}")
            raise RuntimeError(f"❌ [START-TASK] Error calling Start Task API: {e}")

    #================================================================================================
    # Submit Task in Core
    #================================================================================================
    async def submit_task(self, JOB_COOKIE: dict, task_key: str, output: list[dict] | None = None, metadata: str = None, notifiy_launchpad_worker: bool = False) -> bool:
        """
        Submits a task in Core by calling the `/submit` endpoint.

        Args:
            JOB_COOKIE (dict): Dictionary of cookies required for session authentication.
            task_key (str): Unique identifier of the task to submit.

        Returns:
            bool: True if task submission succeeds.

        Raises:
            ValueError: If JOB_COOKIE or task_key is missing or invalid.
            RuntimeError: If the HTTP request fails or submission is rejected.
        """

        if not JOB_COOKIE or not isinstance(JOB_COOKIE, dict):
            logger.error("❌ [SUBMIT-TASK] JOB_COOKIE is required and must be a non-empty dictionary.")
            raise ValueError("❌ [SUBMIT-TASK] JOB_COOKIE is required and must be a non-empty dictionary.")
        
        if not task_key:
            logger.error("❌ [SUBMIT-TASK] task_key is required and cannot be empty.")
            raise ValueError("❌ [SUBMIT-TASK] task_key is required and cannot be empty.")

        try:
            logger.info(f">>> [SUBMIT-TASK] Submit Task: {task_key}")

            url = f"{self.CORE_API}/v1/tasks/{task_key}/submit?noRedirect=true&notifiyLaunchpadWorker={notifiy_launchpad_worker}"
            headers = {"Referer": f"{self.CORE_API}"}
            request_body = {
                "data": {
                    "metadata": f"Submitting Task from {self.AGENT_NAME} {metadata}"
                }
            }
            
            # Add output only if it's a non-empty list
            if output and isinstance(output, list):
                request_body["data"]["output"] = output

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.post(url, headers=headers, json=request_body, allow_redirects=False) as response:
                    response_json = await response.json() if "application/json" in response.headers.get("Content-Type", "") else None
                    
                    if response.status in [302, 301]:
                        redirect_url = response.headers.get("Location")
                        if redirect_url and "done" in redirect_url.lower():
                            logger.info(f"<<<<< ✅ Job Already submitted! Redirected to: {redirect_url}")
                            return True
                    
                    if response.status != 200:
                        logger.error(f"❌ [SUBMIT-TASK]Failed to submit task. HTTP Status: {response.status} - {response_json}")
                        raise RuntimeError(f"❌ [SUBMIT-TASK] Failed to submit task. HTTP Status: {response.status} - {response_json}")
                    
                    logger.info(f"<<<<< ✅ [SUBMIT-TASK] Task Submitted!")
                    return True

        except Exception as e:
            logger.error(f"❌ [SUBMIT-TASK] Error calling Submit Task API: {e}")
            raise RuntimeError(f"❌ [SUBMIT-TASK] Error calling Submit Task API: {e}")

    #================================================================================================
    # Reject Task in Core
    #================================================================================================
    async def reject_task(self, JOB_COOKIE: dict, task_key: str, rejection_reason: str = "No reason provided", metadata: str = None, notifiy_launchpad_worker: bool = False) -> bool:
        """
        Rejects a task in Core by calling the `/reject` endpoint.

        Args:
            JOB_COOKIE (dict): Dictionary of cookies required for session authentication.
            task_key (str): Unique identifier of the task to reject.
            rejection_reason (str, optional): Reason for rejecting the task. Defaults to "No reason provided".

        Returns:
            bool: True if task rejection succeeds.

        Raises:
            ValueError: If JOB_COOKIE or task_key is missing or invalid.
            RuntimeError: If the HTTP request fails or rejection is unsuccessful.
        """

        if not JOB_COOKIE or not isinstance(JOB_COOKIE, dict):
            logger.error("❌ [REJECT-TASK] JOB_COOKIE is required and must be a non-empty dictionary.")
            raise ValueError("❌ [REJECT-TASK] JOB_COOKIE is required and must be a non-empty dictionary.")

        if not task_key:
            logger.error("❌ [REJECT-TASK] task_key is required and cannot be empty.")
            raise ValueError("❌ [REJECT-TASK] task_key is required and cannot be empty.")
        
        try:
            logger.info(f">>> Reject Task: {task_key}")

            url = f"{self.CORE_API}/v1/tasks/{task_key}/reject?noRedirect=true&notifiyLaunchpadWorker={notifiy_launchpad_worker}"
            headers = {"Referer": f"{self.CORE_API}"}
            request_body = {
                "data": {
                    "metadata": f"Rejecting Task from {self.AGENT_NAME} {metadata}",
                    "reason": rejection_reason
                }
            }

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.post(url, headers=headers, json=request_body, allow_redirects=False) as response:
                    response_json = await response.json() if "application/json" in response.headers.get("Content-Type", "") else None
                    
                    if response.status in [302, 301]:
                        redirect_url = response.headers.get("Location")
                        if redirect_url and "rejected" in redirect_url.lower():
                            logger.info(f"<<<<< ✅ Job Already Rejected! Redirected to: {redirect_url}")
                            return True
  
                    if response.status != 200:
                        logger.error(f" ❌ [REJECT-TASK] Failed to reject task. HTTP Status: {response.status} - {response_json}")
                        raise RuntimeError(f"❌ [REJECT-TASK] Failed to reject task. HTTP Status: {response.status} - {response_json}")
                    
                    logger.info(f"<<<<< ✅ Task Rejected Successfully!")
                    
                    return True

        except Exception as e:
            logger.error(f"❌ [REJECT-TASK] Error calling Reject Task API: {e}")
            raise RuntimeError(f"❌ [REJECT-TASK] Error calling Reject Task API: {e}")

    #================================================================================================
    # Update Task Usage in Core
    #================================================================================================
    async def update_usage(self, JOB_COOKIE: dict, task_key: str, duration_seconds: int):
        """
        Updates the usage time of a task in Core by calling the `/usage` endpoint.
        Duration is rounded up to the nearest full minute.

        Args:
            JOB_COOKIE (dict): Dictionary of cookies required for session authentication.
            task_key (str): Unique identifier of the task.
            duration_seconds (int): Number of seconds the task has been active.

        Returns:
            bool: True if the usage update is successful.

        Raises:
            ValueError: If JOB_COOKIE or task_key is missing or invalid.
            RuntimeError: If the HTTP request fails or the update is rejected.
        """

        if not JOB_COOKIE or not isinstance(JOB_COOKIE, dict):
            logger.error("❌ [USAGE] JOB_COOKIE is required and must be a non-empty dictionary.")
            raise ValueError("❌ [USAGE] JOB_COOKIE is required and must be a non-empty dictionary.")

        if not task_key:
            logger.error("❌ [USAGE] task_key is required and cannot be empty.")
            raise ValueError("❌ [USAGE] task_key is required and cannot be empty.")
        
        try:
            duration_minutes = math.ceil(duration_seconds / 60)
            logger.info(f">>> Update Usage for Task: {task_key}, Duration: {duration_seconds}s (~{duration_minutes} min)")

            url = f"{self.CORE_API}/v1/tasks/{task_key}/usage"
            headers = {"Referer": f"{self.CORE_API}"}
            request_body = {"amount": duration_minutes}

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.post(url, headers=headers, json=request_body, allow_redirects=False) as response:
                    response_json = await response.json() if "application/json" in response.headers.get("Content-Type", "") else None

                    if response.status not in [200, 201, 202, 203, 204]:
                        logger.error(f"❌ [USAGE] Failed to update usage. HTTP Status: {response.status} - {response_json}")
                        raise RuntimeError(f"❌ [USAGE] Failed to update usage. HTTP Status: {response.status} - {response_json}")
                    
                    logger.info("✅ [USAGE] Usage updated successfully!")
                    
                    return True

        except Exception as e:
            logger.error(f"❌ [USAGE] Error calling Update Usage API: {e}")
            raise RuntimeError(f"❌ [USAGE] Error calling Update Usage API: {e}")

    #================================================================================================
    # Download file from task API
    #================================================================================================
    async def download_file(self, JOB_COOKIE: dict, task_key: str, key: str, type: str, output_dir: str) -> str:
        """
        Downloads a file from the Core task API and saves it locally.

        Args:
            JOB_COOKIE (dict): Session cookies returned from `connect_task()`.
            task_key (str): The task key to identify the task.
            key (str): The file key (S3-style).
            file_type (str): The type/category of the file (e.g., "config", "media").
            output_dir (str): The local directory to save the file.

        Returns:
            str: Path to the saved local file.
        """
        logger.info(f"📥 Download request for task_key: {task_key} - file_key: {key} - type: {type} - into output folder: {output_dir}")
        
        if not JOB_COOKIE or not isinstance(JOB_COOKIE, dict):
            logger.error("❌ [DOWNLOAD] JOB_COOKIE must be a valid dictionary.")
            raise ValueError("❌ [DOWNLOAD] JOB_COOKIE must be a valid dictionary.")

        if not task_key or not key or not type or not output_dir:
            raise ValueError("❌ [DOWNLOAD] task_key, key, file_type, and output_dir are required.")

        download_url = f"{self.CORE_API}/v1/tasks/{task_key}/file?key={key}&type={type}"
        headers = {"Referer": self.CORE_API}

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Use base filename from key
        local_file_path = os.path.join(output_dir, os.path.basename(key))

        try:
            logger.info(f"📥 [DOWNLOAD] Downloading {key} from task API to {local_file_path} ...")

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.get(download_url, headers=headers) as response:
                    if response.status == 200:
                        file_data = await response.read()
                        with open(local_file_path, 'wb') as f:
                            f.write(file_data)

                        logger.info(f"✅ [DOWNLOAD] File saved to {local_file_path}")
                        return local_file_path

                    else:
                        logger.error(f"❌ [DOWNLOAD] Failed to fetch file. Status: {response.status}")
                        raise RuntimeError(f"❌ [DOWNLOAD] Failed to download file. HTTP Status: {response.status}")

        except Exception as e:
            logger.error(f"❌ [DOWNLOAD] Exception while downloading file: {e}")
            raise RuntimeError(f"❌ [DOWNLOAD] Error while downloading file: {e}")

    #================================================================================================
    # Create New Job in Core
    #================================================================================================
    #TODO: Decorator of ensure Token here
    async def new_job(self, workflow_id: int, customer: dict, language: str = "en", valid_until: int = 60, metadata: str = None, external_ref_number: str = None, input_data: list = None) -> dict:
        """
        Creates a new job in the Core system using the specified workflow and customer info.

        Args:
            workflow_id (int): The ID of the workflow to trigger.
            customer (dict): Dictionary containing customer details.
            language (str, optional): Job language code. Defaults to "en".
            valid_until (int, optional): Job expiration in seconds. Defaults to 60.
            metadata (str, optional): Optional metadata string to include in the job.
            external_ref_number (str, optional): Optional external reference number.
            input_data (list, optional): Optional list of input dictionaries.

        Returns:
            dict: The created job data returned by the API.

        Raises:
            ValueError: If required parameters are missing or invalid.
            RuntimeError: If job creation fails.
        """
        logger.info(f"🚀 Creating new job for workflow: {workflow_id}")

        if not self.JWT_TOKEN:
            raise ValueError("❌ [NEW-JOB] Must login to Core before creating a job.")

        if not isinstance(workflow_id, int):
            raise ValueError("❌ [NEW-JOB] workflow_id must be an integer.")

        if not isinstance(customer, dict):
            raise ValueError("❌ [NEW-JOB] customer must be a dictionary.")

        url = f"{self.CORE_API}/v1/jobs"
        headers = {
            "Authorization": f"Bearer {self.JWT_TOKEN}",
            "Referer": self.CORE_API,
            "Content-Type": "application/json"
        }

        payload = {
            "data": {
                "workflow": workflow_id,
                "validUntil": valid_until,
                "language": language,
                "customer": customer
            }
        }

        # 🔧 Optionally add metadata, externalRefNumber, and input to payload
        if metadata:
            payload["data"]["metadata"] = metadata

        if external_ref_number:
            payload["data"]["externalRefNumber"] = external_ref_number

        if input_data:
            payload["data"]["input"] = input_data

        print(payload)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_json = await response.json()

                    if response.status in [200, 201, 202, 203, 204]:
                        logger.info("✅ [NEW-JOB] Job created successfully.")
                        return response_json
                    else:
                        logger.error(f"❌ [NEW-JOB] Failed to create job. Status: {response.status}, Response: {response_json}")
                        raise RuntimeError(f"❌ [NEW-JOB] Failed to create job. Status: {response.status}, Response: {response_json}")

        except Exception as e:
            logger.error(f"❌ [NEW-JOB] Exception during job creation: {e}")
            raise RuntimeError(f"❌ [NEW-JOB] Exception during job creation: {e}")


    #================================================================================================
    # Start Job in Core
    #================================================================================================
    async def start_job(self, job_key: str, access_key: str | None = None, metadata: str = "", JOB_COOKIE: dict | None = None) -> tuple:
        """
        Starts a job using jobKey and accessKey, returning job cookies and the response JSON.

        Args:
            job_key (str): The job key string.
            access_key (str): The access key string.
            metadata (str): Metadata string to be included in the request.

        Returns:
            tuple: (job_cookie_dict, response_json)
        """

        if not job_key:
            raise ValueError("[START-JOB] job_key must be provided.")
        
        if not access_key and not JOB_COOKIE:
            raise ValueError("[START-JOB] access_key or JOB_COOKIE must be provided.")
        
         # URL depends on cookie presence
        if JOB_COOKIE:
            url = f"{self.CORE_API}/v1/jobs/{job_key}/start?noRedirect=true"
        else:
            url = f"{self.CORE_API}/v1/jobs/{job_key}/{access_key}/start?noRedirect=true"

        headers = {
            "Referer": self.CORE_API
        }
        body = {
            "data": {
                "metadata": metadata
            }
        }

        try:
            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.post(url, headers=headers, json=body, allow_redirects=False) as response:
                    response_json = await response.json()
                    if response.status != 200:
                        raise RuntimeError(f"❌ [START-JOB] Failed: {response.status} - {response_json}")

                    cookies = session.cookie_jar.filter_cookies(self.CORE_API)
                    job_cookie = {k: v.value for k, v in cookies.items()}

                    if not job_cookie:
                        raise RuntimeError("❌ [START-JOB] No job cookies returned.")

                    logger.info("✅ [START-JOB] Job started and cookies obtained.")
                    return job_cookie, response_json
        except Exception as e:
            logger.error(f"❌ [START-JOB] Error: {e}")
            raise RuntimeError(f"❌ [START-JOB] Error: {e}")



    #================================================================================================
    # Notify Job in Core
    #================================================================================================
    async def notify_job (self, job_key: str, metadata: str = "") -> dict:
        """
        Notifies the Core system about the current job status.

        Args:
            job_key (str): The job identifier.
            metadata (str): Optional metadata to send along with the notification.

        Returns:
            dict: A dictionary containing the API response.

        Raises:
            RuntimeError: If the notification fails or an exception occurs.
        """
        logger.info("🔔 [NOTIFY-JOB] Sending job notification to Core...")

        if not self.JWT_TOKEN:
            raise ValueError("❌ [NOTIFY-JOB] Must login to Core before notifying a job.")

        url = f"{self.CORE_API}/v1/jobs/{job_key}/notify"  # 🛠️ Fix: missing slash before job_key
        headers = {
            "Authorization": f"Bearer {self.JWT_TOKEN}",
            "Referer": self.CORE_API,
            "Content-Type": "application/json"
        }

        payload = {
            "data": {
                "metadata": metadata
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    content_type = response.headers.get("Content-Type", "")
                    response_json = await response.json() if "application/json" in content_type else {}

                    if response.status == 200:
                        logger.info("✅ [NOTIFY-JOB] Job notification sent successfully.")
                        return response_json
                    else:
                        logger.error(f"❌ [NOTIFY-JOB] Failed. Status: {response.status}, Response: {response_json}")
                        raise RuntimeError(f"[NOTIFY-JOB] Failed with status {response.status}. Response: {response_json}")
        except Exception as e:
            logger.exception(f"❌ [NOTIFY-JOB] Exception occurred: {e}")
            raise RuntimeError(f"[NOTIFY-JOB] Exception: {e}")
        

    #================================================================================================
    # Save File to task
    #================================================================================================
    async def save_file(
        self,
        JOB_COOKIE: dict,
        task_key: str,
        output_key: str,
        file_name: str,
        powerlink_key: str,
        app_name: str,
        storage_path: str | None = None
    ):
        """
        Uploads a file to a task and appends its key to the task data.

        Args:
            JOB_COOKIE (dict): Session cookies returned from `connect_task()`.
            task_key (str): The task key to identify the task.
            output_key (str): The key under which the file will be stored in task data.
            file_name (str): The local path of the file to upload.
            powerlink_key (str): The powerlink key to use for storage path generation.
            app_name (str): The name of the application uploading the file.
        
        Raises:
            ValueError: If any required parameters are missing or invalid.
            RuntimeError: If the upload or append operation fails.          
        """
        if not JOB_COOKIE or not isinstance(JOB_COOKIE, dict):
            raise ValueError("❌ [SAVE-FILE] JOB_COOKIE must be a valid non-empty dictionary.")

        if not task_key:
            raise ValueError("❌ [SAVE-FILE] task_key is required and cannot be empty.")
        
        if not output_key:
            raise ValueError("❌ [SAVE-FILE] output_key is required and cannot be empty.")
        
        if not file_name or not os.path.isfile(file_name):
            raise ValueError(f"❌ [SAVE-FILE] file_name must be a valid file path. Provided: {file_name}")
        
        if not powerlink_key:
            raise ValueError("❌ [SAVE-FILE] powerlink_key is required and cannot be empty.")
        
        if not app_name:
            raise ValueError("❌ [SAVE-FILE] app_name is required and cannot be empty.")

        try:
            if not storage_path:
                storage_path = _generate_storage_path(powerlink_key= powerlink_key, task_key=task_key, app_name=app_name)
                logger.info(f"📁 No storage_path provided. Generated storage path: {storage_path}")
            
            logger.info(f"📁 Saving file to task data: {file_name} at {storage_path}")

            # 1. Upload File
            upload_url = f"{self.CORE_API}/v1/tasks/{task_key}/uploadFile"
            headers = {"Referer": self.CORE_API}

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                with open(file_name, "rb") as file:
                    form_data = aiohttp.FormData()
                    form_data.add_field("file", file, filename=os.path.basename(file_name))
                    form_data.add_field("path", storage_path)
                    form_data.add_field("metadata", f"File: [{file_name}] Uploaded by AI Agent: [{self.AGENT_NAME}] into path: [{storage_path}]")

                    async with session.post(upload_url, data=form_data, headers=headers, allow_redirects=False) as upload_resp:
                        content_type = upload_resp.headers.get("Content-Type", "")
                        if upload_resp.status in [302, 301]:
                            redirect_url = upload_resp.headers.get("Location")
                            logger.error(f"❌ [SAVE-FILE] Session expired or redirected. Redirected to: {redirect_url}")
                            raise RuntimeError(f"Session expired. Redirected to: {redirect_url}")

                        if "application/json" not in content_type:
                            text = await upload_resp.text()
                            logger.error(f"❌ [SAVE-FILE] Unexpected response type: {content_type}. Response: {text}")
                            raise RuntimeError(f"Unexpected content-type: {content_type}")

                        upload_json = await upload_resp.json()
                        uploaded_file_key = upload_json.get("data", {}).get("key")
                        if not uploaded_file_key:
                            raise RuntimeError("❌ [SAVE-FILE] Upload response missing file key.")
                        logger.info(f"✅ File uploaded successfully. KEY: {uploaded_file_key}")

            # 2. Append Task Data
            append_url = f"{self.CORE_API}/v1/tasks/{task_key}/append"
            append_payload = {
                "data": {
                    "metadata": f"App [{app_name}] updated task [{task_key}] with file [{file_name}]",
                    "output": [
                        {
                            "key": output_key,
                            "value": uploaded_file_key,
                            "type": "MEDIA",
                            "description": f"Media file uploaded from app: {app_name}"
                        }
                    ]
                }
            }

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.post(append_url, json=append_payload, headers=headers, allow_redirects=False) as append_resp:
                    if append_resp.status != 200:
                        text = await append_resp.text()
                        logger.error(f"❌ [SAVE-FILE] Failed to append task data. Status: {append_resp.status}, Response: {text}")
                        raise RuntimeError(f"❌ Failed to append task data. Status: {append_resp.status}")
                    logger.info("✅ Task data appended successfully.")

        except Exception as e:
            logger.error(f"❌ [SAVE-FILE] Exception: {e}")
            raise


    #================================================================================================
    # Add task action in Core
    #================================================================================================
    async def add_task_action(
        self,
        JOB_COOKIE: dict,
        task_key: str,
        name: str,
        origin_identity: str,
        origin_name: str,
        destination_identity: str,
        destination_name: str,
        input_data: dict,
        output_data: dict,
        status: str = "SUCCESS",
        description: str = "",
        type: str = ""
    ) -> bool:
        """
        Adds a task action entry for a specific task in Core.

        Args:
            JOB_COOKIE (dict): Dictionary of cookies required for session authentication.
            task_key (str): Unique identifier of the task.
            name (str): Action name (e.g., 'get_user_location').
            origin_identity (str): Origin identity of the action.
            origin_name (str): Human-readable name of origin.
            destination_identity (str): Destination identity.
            destination_name (str): Human-readable name of destination.
            input_data (dict): Dictionary to send as the action input.
            output_data (dict): Dictionary to send as the action output.
            status (str): Status of the action, default is "SUCCESS".
            description (str): Optional description of the action.
            type (str): Optional type of the action.

        Returns:
            bool: True if action is added successfully.
        """
        if not JOB_COOKIE or not isinstance(JOB_COOKIE, dict):
            logger.error("❌ [TASK-ACTION] JOB_COOKIE is required and must be a non-empty dictionary.")
            raise ValueError("❌ [TASK-ACTION] JOB_COOKIE is required and must be a non-empty dictionary.")

        if not task_key:
            logger.error("❌ [TASK-ACTION] task_key is required and cannot be empty.")
            raise ValueError("❌ [TASK-ACTION] task_key is required and cannot be empty.")

        try:
            logger.info(f">>> [TASK-ACTION] Add Task Action to Task: {task_key}")

            url = f"{self.CORE_API}/v1/tasks/{task_key}/actions"
            headers = {"Referer": f"{self.CORE_API}"}

            request_body = {
                "data": {
                    "name": name,
                    "description": description,
                    "originIdentity": origin_identity,
                    "originName": origin_name,
                    "destinationIdentity": destination_identity,
                    "destinationName": destination_name,
                    "input": input_data,
                    "status": status,
                    "output": output_data,
                    "type": type
                }
            }

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.post(url, headers=headers, json=request_body, allow_redirects=False) as response:
                    response_json = await response.json() if "application/json" in response.headers.get("Content-Type", "") else None

                    if response.status not in [200, 201, 202]:
                        logger.error(f"❌ [TASK-ACTION] Failed to add task action. HTTP Status: {response.status} - {response_json}")
                        raise RuntimeError(f"❌ [TASK-ACTION] Failed to add task action. HTTP Status: {response.status} - {response_json}")

                    logger.info("✅ [TASK-ACTION] Task action added successfully!")
                    return True

        except Exception as e:
            logger.error(f"❌ [TASK-ACTION] Error adding task action: {e}")
            raise RuntimeError(f"❌ [TASK-ACTION] Error adding task action: {e}")


    # ================================================================================================
    # Append task data in Core
    # ================================================================================================
    async def append_task_data(
        self,
        JOB_COOKIE: dict,
        task_key: str,
        metadata: str,
        input_data: list | None = None,
        output_data: list | None = None
    ) -> bool:
        if not JOB_COOKIE or not isinstance(JOB_COOKIE, dict):
            logger.error("❌ [APPEND-TASK] JOB_COOKIE is required and must be a non-empty dictionary.")
            raise ValueError("❌ [APPEND-TASK] JOB_COOKIE is required and must be a non-empty dictionary.")

        if not task_key:
            logger.error("❌ [APPEND-TASK] task_key is required and cannot be empty.")
            raise ValueError("❌ [APPEND-TASK] task_key is required and cannot be empty.")

        try:
            logger.info(f">>> [APPEND-TASK] Appending Data to Task: {task_key}")
            url = f"{self.CORE_API}/v1/tasks/{task_key}/append"
            headers = {"Referer": f"{self.CORE_API}"}

            data_block = {"metadata": metadata}
            if input_data:
                data_block["input"] = input_data
            if output_data:
                data_block["output"] = output_data

            request_body = {"data": data_block}

            async with aiohttp.ClientSession(cookies=JOB_COOKIE) as session:
                async with session.post(url, headers=headers, json=request_body, allow_redirects=False) as response:
                    response_json = await response.json() if "application/json" in response.headers.get("Content-Type", "") else None

                    if response.status not in [200, 201, 202]:
                        logger.error(f"❌ [APPEND-TASK] Failed to append task data. HTTP Status: {response.status} - {response_json}")
                        raise RuntimeError(f"❌ [APPEND-TASK] Failed to append task data. HTTP Status: {response.status} - {response_json}")

                    logger.info("✅ [APPEND-TASK] Task data appended successfully!")
                    return True

        except Exception as e:
            logger.error(f"❌ [APPEND-TASK] Error calling Append Task API: {e}")
            raise RuntimeError(f"❌ [APPEND-TASK] Error calling Append Task API: {e}")