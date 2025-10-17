import json
import time
import logging
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from .logapi import (
    LogEntry,
    LogRequest,
    LogResponse,
    EventType,
    TestStatus,
    create_session_start_log,
    create_session_end_log,
    create_llm_call_log,
    create_llm_response_log,
    create_test_result_log,
    create_error_log,
    # Backward compatibility imports (deprecated)
    LogEntryHeader,
    RunStartLog,
    RunEndLog,
    LlmCallLog,
    TestResultLog,
    OtherLog
)

class CoagentClientError(Exception):
    """Base exception for CoagentClient errors."""
    pass


class CoagentClient:
    """
    Client for interacting with the Coagent logging API endpoints.

    This class provides methods to store, retrieve, and filter log entries
    through the Coagent API.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3000/api/v1",
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.3,
        debug: bool = False
    ):
        """
        Initialize the CoagentClient.

        Args:
            base_url: Base URL for the API (default: http://localhost:3000/api/v1)
            auth_token: Optional authentication token for API requests
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries for failed requests (default: 3)
            retry_backoff_factor: Backoff factor for retries (default: 0.3)
            debug: Enable debug logging (default: False)
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.debug = debug

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        # Configure session without retry strategy (we handle retries manually)
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        if auth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {auth_token}"
            })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            Response object

        Raises:
            CoagentClientError: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        if self.debug:
            self.logger.debug(f"Making {method} request to {url}")
            if data:
                self.logger.debug(f"Request data: {json.dumps(data, indent=2)}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=self.timeout
            )

            if self.debug:
                self.logger.debug(f"Response status: {response.status_code}")
                self.logger.debug(f"Response headers: {response.headers}")

            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self.logger.error(error_msg)
            raise CoagentClientError(error_msg)

    def _validate_log_entry(
        self,
        log_entry: Union[LogEntry, RunStartLog, RunEndLog, LlmCallLog, TestResultLog, OtherLog]
    ) -> None:
        """
        Validate a log entry before sending to the API.
        Follows the LogEntry struct validation from coa-types/src/logs.rs.

        Args:
            log_entry: Log entry object to validate

        Raises:
            CoagentClientError: If the log entry is invalid
        """
        # Handle new LogEntry type - validate according to Rust LogEntry struct
        if isinstance(log_entry, LogEntry):
            # Required fields (non-optional in Rust struct)
            if not log_entry.version:
                raise CoagentClientError("LogEntry must have a version")
            if not log_entry.session_id:
                raise CoagentClientError("LogEntry must have a session_id")
            if log_entry.prompt_number is None:
                raise CoagentClientError("LogEntry must have a prompt_number")
            if log_entry.turn_number is None:
                raise CoagentClientError("LogEntry must have a turn_number")
            if not log_entry.event_id:
                raise CoagentClientError("LogEntry must have an event_id")
            if not log_entry.event_type:
                raise CoagentClientError("LogEntry must have an event_type")
            if log_entry.timestamp is None:
                raise CoagentClientError("LogEntry must have a timestamp")

            # All other fields are optional in Rust (marked with Option<T>) so no validation needed
            return

        # Handle legacy log entry types
        if not isinstance(log_entry, (RunStartLog, RunEndLog, LlmCallLog, TestResultLog, OtherLog)):
            raise CoagentClientError(f"Unsupported log entry type: {type(log_entry)}")

        # Validate header for legacy types
        if not log_entry.hdr.run_id:
            raise CoagentClientError("Log entry header must have a run_id")

        if not log_entry.hdr.timestamp:
            raise CoagentClientError("Log entry header must have a timestamp")

        # Type-specific validation for legacy types
        if isinstance(log_entry, RunStartLog):
            if not log_entry.prompt:
                raise CoagentClientError("RunStartLog must have a prompt")
        elif isinstance(log_entry, RunEndLog):
            if not log_entry.response:
                raise CoagentClientError("RunEndLog must have a response")
            if not log_entry.elapsed_msec:
                raise CoagentClientError("RunEndLog must have elapsed_msec")
        elif isinstance(log_entry, LlmCallLog):
            if not log_entry.context_name:
                raise CoagentClientError("LlmCallLog must have a context_name")
            if not log_entry.prompt:
                raise CoagentClientError("LlmCallLog must have a prompt")
            if not log_entry.response:
                raise CoagentClientError("LlmCallLog must have a response")
            if not log_entry.purpose:
                raise CoagentClientError("LlmCallLog must have a purpose")
        elif isinstance(log_entry, TestResultLog):
            if not log_entry.test_name:
                raise CoagentClientError("TestResultLog must have a test_name")
            if log_entry.success is None:
                raise CoagentClientError("TestResultLog must have a success value")
            if not log_entry.actual_output:
                raise CoagentClientError("TestResultLog must have actual_output")

    def _serialize_log_entry(
        self,
        log_entry: Union[LogEntry, RunStartLog, RunEndLog, LlmCallLog, TestResultLog, OtherLog]
    ) -> Dict[str, Any]:
        """
        Serialize a log entry to a dictionary for API submission.
        Follows the LogEntry struct serialization from coa-types/src/logs.rs.

        Args:
            log_entry: Log entry object to serialize

        Returns:
            Dictionary representation of the log entry wrapped in LogRequest format
        """
        self._validate_log_entry(log_entry)

        # Handle new LogEntry type - use LogRequest wrapper which flattens fields
        if isinstance(log_entry, LogEntry):
            # LogRequest now flattens the LogEntry fields to top-level
            log_request = LogRequest(entry=log_entry)
            return log_request.to_dict()

        log_dict = log_entry.to_dict()

        # For legacy entries, return the raw dict (not wrapped in LogRequest)
        # The API might expect different formats for backward compatibility
        return log_dict

    def _deserialize_log_response(self, response_data: Dict[str, Any]) -> LogResponse:
        """
        Deserialize API response to a LogResponse object.

        Args:
            response_data: Dictionary response from API

        Returns:
            LogResponse object
        """
        return LogResponse.from_dict(response_data)

    def _deserialize_log_entries(self, response_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deserialize API response containing log entries.

        Args:
            response_data: List of log entry dictionaries from API

        Returns:
            List of log entry dictionaries
        """
        return response_data

    def store_log(
        self,
        log_entry: Union[LogEntry, RunStartLog, RunEndLog, LlmCallLog, TestResultLog, OtherLog],
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Store a log entry via POST /logs.

        Args:
            log_entry: Log entry object to store
            max_retries: Maximum number of retries for this specific request (overrides client default)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> header = LogEntryHeader(run_id="run123")
            >>> log = RunStartLog(hdr=header, prompt="Hello world")
            >>> response = client.store_log(log)
            >>> print(response.success)
            True
        """
        # Use provided max_retries or fall back to client default
        retries = max_retries if max_retries is not None else self.max_retries

        if self.debug:
            self.logger.debug(f"Storing log entry of type {type(log_entry).__name__}")

        last_exception = None

        for attempt in range(retries + 1):
            try:
                # Validate and serialize the log entry
                log_data = self._serialize_log_entry(log_entry)

                if self.debug:
                    print("Serialized log data:", json.dumps(log_data, indent=2))

                # Make the request
                response = self._make_request("POST", "/logs", data=log_data)

                # Parse the response
                response_data = response.json()
                log_response = self._deserialize_log_response(response_data)

                if self.debug:
                    self.logger.debug(f"Successfully stored log entry. Response: {log_response.to_dict()}")

                return log_response

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else "Unknown"
                error_msg = f"HTTP error {status_code}"
                self.logger.warning(f"{error_msg} (attempt {attempt + 1}/{retries + 1})")
                last_exception = CoagentClientError(f"{error_msg}: {str(e)}")

                # Don't retry client errors (4xx) except for rate limiting (429)
                if hasattr(e, 'response') and e.response and 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    break

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                error_msg = str(e)
                self.logger.warning(f"Request failed: {error_msg} (attempt {attempt + 1}/{retries + 1})")
                last_exception = CoagentClientError(f"Request failed: {error_msg}")

            except json.JSONDecodeError as e:
                error_msg = str(e)
                self.logger.error(f"Invalid JSON: {error_msg}")
                last_exception = CoagentClientError(f"Invalid JSON: {error_msg}")
                break  # Don't retry JSON parsing errors

            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"Request failed: {error_msg}")
                last_exception = CoagentClientError(f"Request failed: {error_msg}")
                break  # Don't retry unexpected errors

            # If we're going to retry, wait with exponential backoff
            if attempt < retries:
                wait_time = self.retry_backoff_factor * (2 ** attempt)
                self.logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        else:
            raise CoagentClientError("Failed to store log after maximum retries")

    def get_runs(self) -> List[str]:
        """
        Get all run IDs via GET /runs.

        Returns:
            List of run ID strings

        Raises:
            CoagentClientError: If the request fails
        """
        try:
            response = self._make_request("GET", "/runs")
            return response.json()
        except Exception as e:
            raise CoagentClientError(f"Failed to get runs: {str(e)}")

    def log_run_start(
        self,
        run_id: str,
        prompt: str,
        meta: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store a RunStartLog.

        Args:
            run_id: Identifier for the run
            prompt: The initial prompt that started the run
            meta: Flexible metadata dictionary (default: None)
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_run_start("run123", "Hello world")
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating RunStartLog for run_id: {run_id}")

        log_entry = RunStartLog.create(
            run_id=run_id,
            prompt=prompt,
            meta=meta
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_run_end(
        self,
        run_id: str,
        response: str,
        elapsed_msec: Union[str, int, float],
        meta: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store a RunEndLog.

        Args:
            run_id: Identifier for the run
            response: The final response of the run
            elapsed_msec: The elapsed time in milliseconds (can be string, int, or float)
            meta: Flexible metadata dictionary (default: None)
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_run_end("run123", "Hello back", 1500)
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating RunEndLog for run_id: {run_id}")

        # Convert elapsed_msec to string if it's not already
        elapsed_msec_str = str(elapsed_msec)

        log_entry = RunEndLog.create(
            run_id=run_id,
            response=response,
            elapsed_msec=elapsed_msec_str,
            meta=meta
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_llm_call(
        self,
        run_id: str,
        context_name: str,
        prompt: str,
        response: str,
        purpose: str,
        meta: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store an LlmCallLog.

        Args:
            run_id: Identifier for the run
            context_name: Name of the context in which the LLM call was made
            prompt: The prompt sent to the LLM
            response: The response received from the LLM
            purpose: The purpose of the LLM call
            meta: Flexible metadata dictionary (default: None)
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_llm_call(
            ...     "run123", "chat", "Hello", "Hi there", "greeting"
            ... )
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating LlmCallLog for run_id: {run_id}")

        log_entry = create_llm_call_log(
            session_id=run_id,
            prompt=prompt,
            prompt_number = 1,
            turn_number = 1,
            issuer = None,
            history = None,
            system_prompt = None,
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_test_result(
        self,
        run_id: str,
        test_name: str,
        success: bool,
        actual_output: str,
        error_message: Optional[str] = None,
        execution_time: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store a TestResultLog.

        Args:
            run_id: Identifier for the run
            test_name: Name of the test
            success: Whether the test passed or failed
            actual_output: The actual output from the test
            error_message: Optional error message if the test failed (default: None)
            execution_time: Optional execution time in seconds (default: None)
            meta: Flexible metadata dictionary (default: None)
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_test_result(
            ...     "run123", "test_hello", True, "Hello world"
            ... )
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating TestResultLog for run_id: {run_id}")

        log_entry = TestResultLog.create(
            run_id=run_id,
            test_name=test_name,
            success=success,
            actual_output=actual_output,
            error_message=error_message,
            execution_time=execution_time,
            meta=meta
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_other(
        self,
        run_id: str,
        meta: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store an OtherLog.

        Args:
            run_id: Identifier for the run
            meta: Flexible metadata dictionary (default: None)
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_other("run123", {"event": "custom_event"})
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating OtherLog for run_id: {run_id}")

        log_entry = OtherLog.create(
            run_id=run_id,
            meta=meta
        )

        return self.store_log(log_entry, max_retries=max_retries)

    # ============================================================================
    # NEW API METHODS USING LogEntry
    # ============================================================================

    def log_session_start(
        self,
        session_id: str,
        prompt: str,
        prompt_number: int = 1,
        turn_number: int = 0,
        meta: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store a session start log using the new LogEntry API.

        Args:
            session_id: Identifier for the session
            prompt: The initial prompt that started the session
            prompt_number: Sequential number of the prompt within the session
            turn_number: Turn number within the current prompt
            meta: Flexible metadata dictionary (default: None)
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_session_start("session123", "Hello world")
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating session start log for session_id: {session_id}")

        log_entry = create_session_start_log(
            session_id=session_id,
            prompt=prompt,
            prompt_number=prompt_number,
            turn_number=turn_number,
            meta=meta
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_session_end(
        self,
        session_id: str,
        response: str,
        prompt_number: int,
        turn_number: int = 0,
        elapsed_time_ms: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store a session end log using the new LogEntry API.

        Args:
            session_id: Identifier for the session
            response: The final response of the session
            prompt_number: Sequential number of the prompt within the session
            turn_number: Turn number within the current prompt
            elapsed_time_ms: Elapsed time in milliseconds
            meta: Flexible metadata dictionary (default: None)
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_session_end("session123", "Goodbye", 1, elapsed_time_ms=1500)
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating session end log for session_id: {session_id}")

        log_entry = create_session_end_log(
            session_id=session_id,
            response=response,
            prompt_number=prompt_number,
            turn_number=turn_number,
            elapsed_time_ms=elapsed_time_ms,
            meta=meta
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_llm_call_new(
        self,
        session_id: str,
        prompt: str,
        prompt_number: int,
        turn_number: int,
        issuer: Optional[str] = None,
        history: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store an LLM call log using the new LogEntry API.

        Args:
            session_id: Identifier for the session
            prompt: The prompt sent to the LLM
            prompt_number: Sequential number of the prompt within the session
            turn_number: Turn number within the current prompt
            issuer: Who issued the call
            history: Conversation history
            system_prompt: System prompt used
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_llm_call_new("session123", "Hello", 1, 1, issuer="user")
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating LLM call log for session_id: {session_id}")

        log_entry = create_llm_call_log(
            session_id=session_id,
            prompt=prompt,
            prompt_number=prompt_number,
            turn_number=turn_number,
            issuer=issuer,
            history=history,
            system_prompt=system_prompt
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_llm_response(
        self,
        session_id: str,
        response: str,
        prompt_number: int,
        turn_number: int,
        tool_calls: Optional[Dict[str, Any]] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store an LLM response log using the new LogEntry API.

        Args:
            session_id: Identifier for the session
            response: The response from the LLM
            prompt_number: Sequential number of the prompt within the session
            turn_number: Turn number within the current prompt
            tool_calls: Tool calls made by the LLM
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            total_tokens: Total number of tokens used
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_llm_response("session123", "Hi there", 1, 1, input_tokens=10, output_tokens=15)
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating LLM response log for session_id: {session_id}")

        log_entry = create_llm_response_log(
            session_id=session_id,
            response=response,
            prompt_number=prompt_number,
            turn_number=turn_number,
            tool_calls=tool_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_test_result_new(
        self,
        session_id: str,
        prompt_number: int,
        turn_number: int,
        status: TestStatus,
        total_tests: int,
        passed_tests: int,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store a test result log using the new LogEntry API.

        Args:
            session_id: Identifier for the session
            prompt_number: Sequential number of the prompt within the session
            turn_number: Turn number within the current prompt
            status: Overall test status
            total_tests: Total number of tests run
            passed_tests: Number of tests that passed
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> from coagent_client.logapi import TestStatus
            >>> client = CoagentClient()
            >>> response = client.log_test_result_new("session123", 1, 1, TestStatus.PASSED, 10, 10)
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating test result log for session_id: {session_id}")

        log_entry = create_test_result_log(
            session_id=session_id,
            prompt_number=prompt_number,
            turn_number=turn_number,
            status=status,
            total_tests=total_tests,
            passed_tests=passed_tests
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def log_error(
        self,
        session_id: str,
        prompt_number: int,
        turn_number: int,
        error_message: str,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        max_retries: Optional[int] = None
    ) -> LogResponse:
        """
        Create and store an error log using the new LogEntry API.

        Args:
            session_id: Identifier for the session
            prompt_number: Sequential number of the prompt within the session
            turn_number: Turn number within the current prompt
            error_message: Description of the error
            error_type: Type/category of error
            stack_trace: Stack trace if available
            max_retries: Maximum number of retries for this specific request (default: None)

        Returns:
            LogResponse object indicating success/failure

        Raises:
            CoagentClientError: If the request fails after all retries

        Example:
            >>> client = CoagentClient()
            >>> response = client.log_error("session123", 1, 1, "Connection failed", error_type="network")
            >>> print(response.success)
            True
        """
        if self.debug:
            self.logger.debug(f"Creating error log for session_id: {session_id}")

        log_entry = create_error_log(
            session_id=session_id,
            prompt_number=prompt_number,
            turn_number=turn_number,
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace
        )

        return self.store_log(log_entry, max_retries=max_retries)

    def get_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all logs for a specific session via GET /logs/{session_id}.

        Args:
            session_id: Session ID to retrieve logs for (maps to run_id for API compatibility)

        Returns:
            List of log entry dictionaries

        Raises:
            CoagentClientError: If the request fails
        """
        try:
            # For backward compatibility, the API still uses run_id
            response = self._make_request("GET", f"/logs/{session_id}")
            response_data = response.json()
            return self._deserialize_log_entries(response_data)
        except Exception as e:
            raise CoagentClientError(f"Failed to get logs for session {session_id}: {str(e)}")

    def filter_logs(self, session_id: str, jmespath_query: str) -> List[Dict[str, Any]]:
        """
        Filter logs for a specific session using JMESPath via GET /filter_logs/{session_id}.

        Args:
            session_id: Session ID to filter logs for (maps to run_id for API compatibility)
            jmespath_query: JMESPath query string for filtering

        Returns:
            List of filtered log entry dictionaries

        Raises:
            CoagentClientError: If the request fails
        """
        try:
            params = {"pre": jmespath_query}
            # For backward compatibility, the API still uses run_id
            response = self._make_request("GET", f"/filter_logs/{session_id}", params=params)
            response_data = response.json()
            return self._deserialize_log_entries(response_data)
        except Exception as e:
            raise CoagentClientError(f"Failed to filter logs for session {session_id}: {str(e)}")

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
