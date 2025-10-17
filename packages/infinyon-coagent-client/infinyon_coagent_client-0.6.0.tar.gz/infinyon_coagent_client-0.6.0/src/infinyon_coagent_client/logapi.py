"""
Unified logging API for coagent-client.
"""

import json

from abc import ABC, abstractmethod
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, Any, Optional, TypeVar, Type, List, Union

# Type variable for generic methods
T = TypeVar('T')


# ============================================================================
# ENUMS MATCHING RUST TYPES
# ============================================================================

class EventType(Enum):
    """Event types matching the Rust EventType enum."""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    USER_INPUT = "user_input"
    COMPONENT_ENTER = "component_enter"
    COMPONENT_EXIT = "component_exit"
    ROUTING = "routing"
    CONSENSUS_SUCCESS = "consensus_success"
    CONSENSUS_FAILURE = "consensus_failure"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    ERROR = "error"
    RECOVERY = "recovery"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    HUMAN_OVERSIGHT = "human_oversight"
    TEST_RESULT = "test_result"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"


class ComponentType(Enum):
    """Component types matching the Rust ComponentType enum."""
    ORCHESTRATOR = "orchestrator"
    NODE = "node"
    LLM_AGENT = "llm_agent"
    USER_INPUT = "user_input"


class TestStatus(Enum):
    """Test status matching the Rust TestStatus enum."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RoutingType(Enum):
    """Routing type matching the Rust RoutingType enum."""
    INVOKE = "invoke"
    RETURN = "return"
    TRANSFER = "transfer"


class ErrorSeverity(Enum):
    """Error severity matching the Rust ErrorSeverity enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# STRUCTURED DATA CLASSES
# ============================================================================

class SourceComponent:
    """Source component information matching the Rust SourceComponent struct."""

    def __init__(
        self,
        id: str,
        name: str,
        component_type: ComponentType,
        role: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        model: Optional[str] = None,
        trust_level: Optional[float] = None,
        interface_type: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.component_type = component_type
        self.role = role
        self.capabilities = capabilities
        self.model = model
        self.trust_level = trust_level
        self.interface_type = interface_type

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "component_type": self.component_type.value
        }
        if self.role is not None:
            result["role"] = self.role
        if self.capabilities is not None:
            result["capabilities"] = self.capabilities
        if self.model is not None:
            result["model"] = self.model
        if self.trust_level is not None:
            result["trust_level"] = self.trust_level
        if self.interface_type is not None:
            result["interface_type"] = self.interface_type
        return result


class TargetComponent:
    """Target component information matching the Rust TargetComponent struct."""

    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        component_type: Optional[ComponentType] = None
    ):
        self.id = id
        self.name = name
        self.component_type = component_type

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.id is not None:
            result["id"] = self.id
        if self.name is not None:
            result["name"] = self.name
        if self.component_type is not None:
            result["component_type"] = self.component_type.value
        return result


class ToolCall:
    """Tool call information matching the Rust ToolCall struct."""

    def __init__(
        self,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        self.tool_name = tool_name
        self.parameters = parameters

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.tool_name is not None:
            result["tool_name"] = self.tool_name
        if self.parameters is not None:
            result["parameters"] = self.parameters
        return result


class ToolResponse:
    """Tool response information matching the Rust ToolResponse struct."""

    def __init__(
        self,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        error_message: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ):
        self.tool_name = tool_name
        self.parameters = parameters
        self.result = result
        self.success = success
        self.error_message = error_message
        self.execution_time_ms = execution_time_ms

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.tool_name is not None:
            result["tool_name"] = self.tool_name
        if self.parameters is not None:
            result["parameters"] = self.parameters
        if self.result is not None:
            result["result"] = self.result
        if self.success is not None:
            result["success"] = self.success
        if self.error_message is not None:
            result["error_message"] = self.error_message
        if self.execution_time_ms is not None:
            result["execution_time_ms"] = self.execution_time_ms
        return result


class ErrorInfo:
    """Error information matching the Rust ErrorInfo struct."""

    def __init__(
        self,
        error_id: Optional[str] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        error_severity: Optional[ErrorSeverity] = None,
        stack_trace: Optional[str] = None,
        component_id: Optional[str] = None,
        recovery_strategy: Optional[str] = None,
        recovery_actions: Optional[List[str]] = None,
        recovery_successful: Optional[bool] = None,
        human_intervention_required: Optional[bool] = None,
        impact_assessment: Optional[str] = None,
        root_cause: Optional[str] = None
    ):
        self.error_id = error_id
        self.error_type = error_type
        self.error_message = error_message
        self.error_severity = error_severity
        self.stack_trace = stack_trace
        self.component_id = component_id
        self.recovery_strategy = recovery_strategy
        self.recovery_actions = recovery_actions
        self.recovery_successful = recovery_successful
        self.human_intervention_required = human_intervention_required
        self.impact_assessment = impact_assessment
        self.root_cause = root_cause

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.error_id is not None:
            result["error_id"] = self.error_id
        if self.error_type is not None:
            result["error_type"] = self.error_type
        if self.error_message is not None:
            result["error_message"] = self.error_message
        if self.error_severity is not None:
            result["error_severity"] = self.error_severity.value
        if self.stack_trace is not None:
            result["stack_trace"] = self.stack_trace
        if self.component_id is not None:
            result["component_id"] = self.component_id
        if self.recovery_strategy is not None:
            result["recovery_strategy"] = self.recovery_strategy
        if self.recovery_actions is not None:
            result["recovery_actions"] = self.recovery_actions
        if self.recovery_successful is not None:
            result["recovery_successful"] = self.recovery_successful
        if self.human_intervention_required is not None:
            result["human_intervention_required"] = self.human_intervention_required
        if self.impact_assessment is not None:
            result["impact_assessment"] = self.impact_assessment
        if self.root_cause is not None:
            result["root_cause"] = self.root_cause
        return result


class PerformanceMetrics:
    """Performance metrics matching the Rust PerformanceMetrics struct."""

    def __init__(
        self,
        success_rate: Optional[float] = None,
        confidence_score: Optional[float] = None,
        accuracy_score: Optional[float] = None,
        cost: Optional[float] = None,
        tokens_used: Optional[int] = None,
        memory_usage_mb: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None,
        network_bytes: Optional[int] = None
    ):
        self.success_rate = success_rate
        self.confidence_score = confidence_score
        self.accuracy_score = accuracy_score
        self.cost = cost
        self.tokens_used = tokens_used
        self.memory_usage_mb = memory_usage_mb
        self.cpu_usage_percent = cpu_usage_percent
        self.network_bytes = network_bytes

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.success_rate is not None:
            result["success_rate"] = self.success_rate
        if self.confidence_score is not None:
            result["confidence_score"] = self.confidence_score
        if self.accuracy_score is not None:
            result["accuracy_score"] = self.accuracy_score
        if self.cost is not None:
            result["cost"] = self.cost
        if self.tokens_used is not None:
            result["tokens_used"] = self.tokens_used
        if self.memory_usage_mb is not None:
            result["memory_usage_mb"] = self.memory_usage_mb
        if self.cpu_usage_percent is not None:
            result["cpu_usage_percent"] = self.cpu_usage_percent
        if self.network_bytes is not None:
            result["network_bytes"] = self.network_bytes
        return result


class TestResults:
    """Test results matching the Rust TestResults struct."""

    def __init__(
        self,
        status: TestStatus,
        total_tests: int,
        passed_tests: int
    ):
        self.status = status
        self.total_tests = total_tests
        self.passed_tests = passed_tests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests
        }


class LlmResponse:
    """LLM response matching the Rust LlmResponse struct."""

    def __init__(
        self,
        response: str,
        tool_calls: Optional[Dict[str, Any]] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None
    ):
        self.response = response
        self.tool_calls = tool_calls
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens

    def to_dict(self) -> Dict[str, Any]:
        result = {"response": self.response}
        if self.tool_calls is not None:
            result["tool_calls"] = self.tool_calls
        if self.input_tokens is not None:
            result["input_tokens"] = self.input_tokens
        if self.output_tokens is not None:
            result["output_tokens"] = self.output_tokens
        if self.total_tokens is not None:
            result["total_tokens"] = self.total_tokens
        return result


class LlmCall:
    """LLM call matching the Rust LlmCall struct."""

    def __init__(
        self,
        issuer: Optional[str] = None,
        history: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ):
        self.issuer = issuer
        self.history = history
        self.system_prompt = system_prompt

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.issuer is not None:
            result["issuer"] = self.issuer
        if self.history is not None:
            result["history"] = self.history
        if self.system_prompt is not None:
            result["system_prompt"] = self.system_prompt
        return result


class Meta:
    """Meta information matching the Rust Meta struct."""

    def __init__(
        self,
        source_component: Optional[SourceComponent] = None,
        trace: Optional[Dict[str, Any]] = None,
        framework: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.source_component = source_component
        self.trace = trace
        self.framework = framework
        self.context = context

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.source_component is not None:
            result["source_component"] = self.source_component.to_dict()
        if self.trace is not None:
            result["trace"] = self.trace
        if self.framework is not None:
            result["framework"] = self.framework
        if self.context is not None:
            result["context"] = self.context
        return result


# ============================================================================
# LOG ENTRY HEADER CLASS (MATCHES RUST LogEntryHeader)
# ============================================================================

class LogEntryHeader:
    """
    LogEntryHeader class matching the Rust LogEntryHeader struct.

    Contains the core header fields that are present in every log entry:
    - version: Version of the log format
    - session_id: Identifier for the session
    - prompt_number: Sequential number of the prompt within the session
    - turn_number: Turn number within the current prompt
    - event_id: Unique identifier for this event
    - event_type: Type of event being logged
    - timestamp: Unix timestamp in milliseconds
    """

    def __init__(
        self,
        session_id: str,
        prompt_number: int,
        turn_number: int,
        event_type: EventType,
        timestamp: Optional[int] = None,
        version: str = "2.0.0",
        event_id: Optional[str] = None
    ):
        """
        Initialize a LogEntryHeader.

        Args:
            session_id: Identifier for the session
            prompt_number: Sequential number of the prompt within the session
            turn_number: Turn number within the current prompt
            event_type: Type of event being logged
            timestamp: Unix timestamp in milliseconds (current time if None)
            version: Version of the log format
            event_id: Unique identifier for this event (UUID if None)
        """
        import uuid
        import time

        self.version = version
        self.session_id = session_id
        self.prompt_number = prompt_number
        self.turn_number = turn_number
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.timestamp = timestamp or int(time.time() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the LogEntryHeader to a dictionary."""
        return {
            "version": self.version,
            "session_id": self.session_id,
            "prompt_number": self.prompt_number,
            "turn_number": self.turn_number,
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """Convert the LogEntryHeader to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegacyLogEntryHeader':
        """Create a LegacyLogEntryHeader from a dictionary."""
        return cls(
            session_id=data["session_id"],
            prompt_number=data["prompt_number"],
            turn_number=data["turn_number"],
            event_type=EventType(data["event_type"]),
            timestamp=data.get("timestamp"),
            version=data.get("version", "2.0.0"),
            event_id=data.get("event_id")
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'LegacyLogEntryHeader':
        """Create a LegacyLogEntryHeader from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ============================================================================
# MAIN LOG ENTRY CLASS
# ============================================================================

class LogEntry(LogEntryHeader):
    """
    Main log entry class matching the Rust LogEntry struct.

    This represents a single log entry with all possible fields from the Rust implementation.
    """

    def __init__(
        self,
        session_id: str,
        prompt_number: int,
        turn_number: int,
        event_type: EventType,
        timestamp: Optional[int] = None,
        version: str = "2.0.0",
        event_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
        target_component: Optional[TargetComponent] = None,
        conversation_context: Optional[Dict[str, Any]] = None,
        routing_type: Optional[RoutingType] = None,
        consensus_info: Optional[Dict[str, Any]] = None,
        tool_call: Optional[ToolCall] = None,
        tool_response: Optional[ToolResponse] = None,
        error_info: Optional[ErrorInfo] = None,
        graph_context: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[PerformanceMetrics] = None,
        test_result: Optional[TestResults] = None,
        llm_response: Optional[LlmResponse] = None,
        llm_call: Optional[LlmCall] = None,
        additional_properties: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a LogEntry.

        Args:
            session_id: Identifier for the session
            prompt_number: Sequential number of the prompt within the session
            turn_number: Turn number within the current prompt
            event_type: Type of event being logged
            timestamp: Unix timestamp in milliseconds (current time if None)
            version: Version of the log format
            event_id: Unique identifier for this event (UUID if None)
            meta: Flexible metadata object
            prompt: The prompt content (for applicable event types)
            input_data: Input data for the event
            output_data: Output data for the event
            custom_metadata: Additional custom metadata
            target_component: Information about the target component
            conversation_context: Context of the conversation
            routing_type: Type of routing operation
            consensus_info: Information about consensus operations
            tool_call: Information about tool calls
            tool_response: Information about tool responses
            error_info: Error information
            graph_context: Graph-related context
            performance_metrics: Performance metrics
            test_result: Test result information
            llm_response: LLM response information
            llm_call: LLM call information
            additional_properties: Additional arbitrary properties
        """
        # Initialize the header fields via parent constructor
        super().__init__(
            session_id=session_id,
            prompt_number=prompt_number,
            turn_number=turn_number,
            event_type=event_type,
            timestamp=timestamp,
            version=version,
            event_id=event_id
        )

        # Initialize additional LogEntry-specific fields
        self.meta = meta
        self.prompt = prompt
        self.input_data = input_data
        self.output_data = output_data
        self.custom_metadata = custom_metadata
        self.target_component = target_component
        self.conversation_context = conversation_context
        self.routing_type = routing_type
        self.consensus_info = consensus_info
        self.tool_call = tool_call
        self.tool_response = tool_response
        self.error_info = error_info
        self.graph_context = graph_context
        self.performance_metrics = performance_metrics
        self.test_result = test_result
        self.llm_response = llm_response
        self.llm_call = llm_call
        self.additional_properties = additional_properties or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the LogEntry to a dictionary."""
        # Start with the header fields from parent class
        result = super().to_dict()

        # Add optional fields if they exist
        if self.meta is not None:
            result["meta"] = self.meta
        if self.prompt is not None:
            result["prompt"] = self.prompt
        if self.input_data is not None:
            result["input_data"] = self.input_data
        if self.output_data is not None:
            result["output_data"] = self.output_data
        if self.custom_metadata is not None:
            result["custom_metadata"] = self.custom_metadata
        if self.target_component is not None:
            result["target_component"] = self.target_component.to_dict()
        if self.conversation_context is not None:
            result["conversation_context"] = self.conversation_context
        if self.routing_type is not None:
            result["routing_type"] = self.routing_type.value
        if self.consensus_info is not None:
            result["consensus_info"] = self.consensus_info
        if self.tool_call is not None:
            result["tool_call"] = self.tool_call.to_dict()
        if self.tool_response is not None:
            result["tool_response"] = self.tool_response.to_dict()
        if self.error_info is not None:
            result["error_info"] = self.error_info.to_dict()
        if self.graph_context is not None:
            result["graph_context"] = self.graph_context
        if self.performance_metrics is not None:
            result["performance_metrics"] = self.performance_metrics.to_dict()
        if self.test_result is not None:
            result["test_result"] = self.test_result.to_dict()
        if self.llm_response is not None:
            result["llm_response"] = self.llm_response.to_dict()
        if self.llm_call is not None:
            result["llm_call"] = self.llm_call.to_dict()

        # Add additional properties at the top level
        result.update(self.additional_properties)

        return result

    def to_json(self) -> str:
        """Convert the LogEntry to a JSON string."""
        print(f'Converting LogEntry to JSON {json.dumps(self.to_dict(), indent=2)}')
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create a LogEntry from a dictionary."""
        # Helper function to parse enums
        def parse_enum(enum_class, value):
            if value is None:
                return None
            if isinstance(value, enum_class):
                return value
            return enum_class(value)

        # Helper function to parse nested objects
        def parse_nested_object(obj_class, data):
            if data is None:
                return None
            if isinstance(data, dict):
                return obj_class.from_dict(data)
            return data

        kwargs = {
            "session_id": data["session_id"],
            "prompt_number": data["prompt_number"],
            "turn_number": data["turn_number"],
            "event_type": parse_enum(EventType, data["event_type"]),
            "version": data.get("version", "2.0.0"),
            "event_id": data.get("event_id"),
            "timestamp": data.get("timestamp"),
            "meta": data.get("meta"),
            "prompt": data.get("prompt"),
            "input_data": data.get("input_data"),
            "output_data": data.get("output_data"),
            "custom_metadata": data.get("custom_metadata"),
            "conversation_context": data.get("conversation_context"),
            "routing_type": parse_enum(RoutingType, data.get("routing_type")),
            "consensus_info": data.get("consensus_info"),
            "graph_context": data.get("graph_context"),
        }

        # Handle nested objects
        if "target_component" in data and data["target_component"]:
            tc = data["target_component"]
            kwargs["target_component"] = TargetComponent(
                id=tc.get("id"),
                name=tc.get("name"),
                component_type=parse_enum(ComponentType, tc.get("component_type"))
            )

        if "tool_call" in data and data["tool_call"]:
            tc = data["tool_call"]
            kwargs["tool_call"] = ToolCall(
                tool_name=tc.get("tool_name"),
                parameters=tc.get("parameters")
            )

        if "tool_response" in data and data["tool_response"]:
            tr = data["tool_response"]
            kwargs["tool_response"] = ToolResponse(
                tool_name=tr.get("tool_name"),
                parameters=tr.get("parameters"),
                result=tr.get("result"),
                success=tr.get("success"),
                error_message=tr.get("error_message"),
                execution_time_ms=tr.get("execution_time_ms")
            )

        if "error_info" in data and data["error_info"]:
            ei = data["error_info"]
            kwargs["error_info"] = ErrorInfo(
                error_id=ei.get("error_id"),
                error_type=ei.get("error_type"),
                error_message=ei.get("error_message"),
                error_severity=parse_enum(ErrorSeverity, ei.get("error_severity")),
                stack_trace=ei.get("stack_trace"),
                component_id=ei.get("component_id"),
                recovery_strategy=ei.get("recovery_strategy"),
                recovery_actions=ei.get("recovery_actions"),
                recovery_successful=ei.get("recovery_successful"),
                human_intervention_required=ei.get("human_intervention_required"),
                impact_assessment=ei.get("impact_assessment"),
                root_cause=ei.get("root_cause")
            )

        if "performance_metrics" in data and data["performance_metrics"]:
            pm = data["performance_metrics"]
            kwargs["performance_metrics"] = PerformanceMetrics(
                success_rate=pm.get("success_rate"),
                confidence_score=pm.get("confidence_score"),
                accuracy_score=pm.get("accuracy_score"),
                cost=pm.get("cost"),
                tokens_used=pm.get("tokens_used"),
                memory_usage_mb=pm.get("memory_usage_mb"),
                cpu_usage_percent=pm.get("cpu_usage_percent"),
                network_bytes=pm.get("network_bytes")
            )

        if "test_result" in data and data["test_result"]:
            tr = data["test_result"]
            kwargs["test_result"] = TestResults(
                status=parse_enum(TestStatus, tr["status"]),
                total_tests=tr["total_tests"],
                passed_tests=tr["passed_tests"]
            )

        if "llm_response" in data and data["llm_response"]:
            lr = data["llm_response"]
            kwargs["llm_response"] = LlmResponse(
                response=lr["response"],
                tool_calls=lr.get("tool_calls"),
                input_tokens=lr.get("input_tokens"),
                output_tokens=lr.get("output_tokens"),
                total_tokens=lr.get("total_tokens")
            )

        if "llm_call" in data and data["llm_call"]:
            lc = data["llm_call"]
            kwargs["llm_call"] = LlmCall(
                issuer=lc.get("issuer"),
                history=lc.get("history"),
                system_prompt=lc.get("system_prompt")
            )

        # Collect additional properties (fields not in the defined schema)
        defined_fields = {
            "version", "session_id", "prompt_number", "turn_number", "event_id",
            "event_type", "timestamp", "meta", "prompt", "input_data", "output_data",
            "custom_metadata", "target_component", "conversation_context",
            "routing_type", "consensus_info", "tool_call", "tool_response",
            "error_info", "graph_context", "performance_metrics", "test_result",
            "llm_response", "llm_call"
        }
        additional_properties = {k: v for k, v in data.items() if k not in defined_fields}
        kwargs["additional_properties"] = additional_properties

        return cls(**kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> 'LogEntry':
        """Create a LogEntry from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ============================================================================
# LOG REQUEST/RESPONSE WRAPPER CLASSES
# ============================================================================

class LogRequest:
    """Log request wrapper that flattens LogEntry fields to top-level."""

    def __init__(self, entry: LogEntry):
        """
        Initialize a LogRequest.

        Args:
            entry: The LogEntry to be flattened in the request
        """
        # Store the LogEntry fields directly instead of nesting under 'entry'
        self.version = entry.version
        self.session_id = entry.session_id
        self.prompt_number = entry.prompt_number
        self.turn_number = entry.turn_number
        self.event_id = entry.event_id
        self.event_type = entry.event_type
        self.timestamp = entry.timestamp

        # Optional fields
        self.meta = entry.meta
        self.prompt = entry.prompt
        self.input_data = entry.input_data
        self.output_data = entry.output_data
        self.custom_metadata = entry.custom_metadata
        self.target_component = entry.target_component
        self.conversation_context = entry.conversation_context
        self.routing_type = entry.routing_type
        self.consensus_info = entry.consensus_info
        self.tool_call = entry.tool_call
        self.tool_response = entry.tool_response
        self.error_info = entry.error_info
        self.graph_context = entry.graph_context
        self.performance_metrics = entry.performance_metrics
        self.test_result = entry.test_result
        self.llm_response = entry.llm_response
        self.llm_call = entry.llm_call
        self.additional_properties = entry.additional_properties

    def to_dict(self) -> Dict[str, Any]:
        """Convert the LogRequest to a dictionary with flattened fields."""
        # Return the LogEntry fields directly at the top level
        result = {
            "version": self.version,
            "session_id": self.session_id,
            "prompt_number": self.prompt_number,
            "turn_number": self.turn_number,
            "event_id": self.event_id,
            "event_type": self.event_type.value if hasattr(self.event_type, 'value') else str(self.event_type),
            "timestamp": self.timestamp,
        }

        # Add optional fields only if they are not None
        optional_fields = [
            ("meta", self.meta),
            ("prompt", self.prompt),
            ("input_data", self.input_data),
            ("output_data", self.output_data),
            ("custom_metadata", self.custom_metadata),
            ("target_component", self.target_component),
            ("conversation_context", self.conversation_context),
            ("routing_type", self.routing_type),
            ("consensus_info", self.consensus_info),
            ("tool_call", self.tool_call),
            ("tool_response", self.tool_response),
            ("error_info", self.error_info),
            ("graph_context", self.graph_context),
            ("performance_metrics", self.performance_metrics),
            ("test_result", self.test_result),
            ("llm_response", self.llm_response),
            ("llm_call", self.llm_call),
        ]

        for field_name, value in optional_fields:
            if value is not None:
                if hasattr(value, 'value'):  # Handle enums
                    result[field_name] = value.value
                elif hasattr(value, 'to_dict'):  # Handle complex objects
                    result[field_name] = value.to_dict()
                else:
                    result[field_name] = value

        # Add additional properties at the top level
        if self.additional_properties:
            result.update(self.additional_properties)

        return result

    def to_json(self) -> str:
        """Convert the LogRequest to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogRequest':
        """Create a LogRequest from a dictionary with flattened fields."""
        # Create a LogEntry from the flattened data
        entry = LogEntry.from_dict(data)
        return cls(entry=entry)

    @classmethod
    def from_json(cls, json_str: str) -> 'LogRequest':
        """Create a LogRequest from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class LogResponse:
    """Log response matching the Rust LogResponse struct."""

    def __init__(
        self,
        success: bool,
        message: str
    ):
        """
        Initialize a LogResponse.

        Args:
            success: Whether the log operation was successful
            message: Message describing the result of the operation
        """
        self.success = success
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert the LogResponse to a dictionary."""
        return {
            "success": self.success,
            "message": self.message
        }

    def to_json(self) -> str:
        """Convert the LogResponse to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogResponse':
        """Create a LogResponse from a dictionary."""
        return cls(
            success=data["success"],
            message=data["message"]
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'LogResponse':
        """Create a LogResponse from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# ============================================================================
# HELPER FUNCTIONS FOR CREATING LOG ENTRIES
# ============================================================================

def create_session_start_log(
    session_id: str,
    prompt: str,
    prompt_number: int = 1,
    turn_number: int = 0,
    meta: Optional[Dict[str, Any]] = None,
    **kwargs
) -> LogEntry:
    """
    Create a session start log entry.

    Args:
        session_id: Identifier for the session
        prompt: The initial prompt that started the session
        prompt_number: Sequential number of the prompt within the session
        turn_number: Turn number within the current prompt
        meta: Flexible metadata object
        **kwargs: Additional arguments passed to LogEntry constructor

    Returns:
        A new LogEntry for session start
    """
    return LogEntry(
        session_id=session_id,
        prompt_number=prompt_number,
        turn_number=turn_number,
        event_type=EventType.SESSION_START,
        prompt=prompt,
        meta=meta,
        **kwargs
    )


def create_session_end_log(
    session_id: str,
    response: str,
    prompt_number: int,
    turn_number: int = 0,
    elapsed_time_ms: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
    **kwargs
) -> LogEntry:
    """
    Create a session end log entry.

    Args:
        session_id: Identifier for the session
        response: The final response of the session
        prompt_number: Sequential number of the prompt within the session
        turn_number: Turn number within the current prompt
        elapsed_time_ms: Elapsed time in milliseconds
        meta: Flexible metadata object
        **kwargs: Additional arguments passed to LogEntry constructor

    Returns:
        A new LogEntry for session end
    """
    # Store elapsed time in meta if provided
    if elapsed_time_ms is not None:
        if meta is None:
            meta = {}
        meta = dict(meta)  # Copy to avoid modifying original
        meta["elapsed_time_ms"] = elapsed_time_ms

    return LogEntry(
        session_id=session_id,
        prompt_number=prompt_number,
        turn_number=turn_number,
        event_type=EventType.SESSION_END,
        output_data={"response": response},
        meta=meta,
        **kwargs
    )


def create_llm_call_log(
    session_id: str,
    prompt: str,
    prompt_number: int,
    turn_number: int,
    issuer: Optional[str] = None,
    history: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    **kwargs
) -> LogEntry:
    """
    Create an LLM call log entry.

    Args:
        session_id: Identifier for the session
        prompt: The prompt sent to the LLM
        prompt_number: Sequential number of the prompt within the session
        turn_number: Turn number within the current prompt
        issuer: Who issued the call
        history: Conversation history
        system_prompt: System prompt used
        **kwargs: Additional arguments passed to LogEntry constructor

    Returns:
        A new LogEntry for LLM call
    """
    return LogEntry(
        session_id=session_id,
        prompt_number=prompt_number,
        turn_number=turn_number,
        event_type=EventType.LLM_CALL,
        prompt=prompt,
        llm_call=LlmCall(
            issuer=issuer,
            history=history,
            system_prompt=system_prompt
        ),
        **kwargs
    )


def create_llm_response_log(
    session_id: str,
    response: str,
    prompt_number: int,
    turn_number: int,
    tool_calls: Optional[Dict[str, Any]] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    **kwargs
) -> LogEntry:
    """
    Create an LLM response log entry.

    Args:
        session_id: Identifier for the session
        response: The response from the LLM
        prompt_number: Sequential number of the prompt within the session
        turn_number: Turn number within the current prompt
        tool_calls: Tool calls made by the LLM
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        total_tokens: Total number of tokens used
        **kwargs: Additional arguments passed to LogEntry constructor

    Returns:
        A new LogEntry for LLM response
    """
    return LogEntry(
        session_id=session_id,
        prompt_number=prompt_number,
        turn_number=turn_number,
        event_type=EventType.LLM_RESPONSE,
        llm_response=LlmResponse(
            response=response,
            tool_calls=tool_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens
        ),
        **kwargs
    )


def create_tool_call_log(
    session_id: str,
    prompt_number: int,
    turn_number: int,
    tool_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    **kwargs
) -> LogEntry:
    """
    Create a tool call log entry.

    Args:
        session_id: Identifier for the session
        prompt_number: Sequential number of the prompt within the session
        turn_number: Turn number within the current prompt
        tool_name: Name of the tool being called
        parameters: Parameters passed to the tool
        **kwargs: Additional arguments passed to LogEntry constructor

    Returns:
        A new LogEntry for tool call
    """
    return LogEntry(
        session_id=session_id,
        prompt_number=prompt_number,
        turn_number=turn_number,
        event_type=EventType.TOOL_CALL,
        tool_call=ToolCall(
            tool_name=tool_name,
            parameters=parameters
        ),
        **kwargs
    )


def create_tool_response_log(
    session_id: str,
    prompt_number: int,
    turn_number: int,
    tool_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    success: Optional[bool] = None,
    error_message: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
    **kwargs
) -> LogEntry:
    """
    Create a tool response log entry.

    Args:
        session_id: Identifier for the session
        prompt_number: Sequential number of the prompt within the session
        turn_number: Turn number within the current prompt
        tool_name: Name of the tool that was called
        parameters: Parameters that were passed to the tool
        result: Result from the tool
        success: Whether the tool call was successful
        error_message: Error message if the tool call failed
        execution_time_ms: Execution time in milliseconds
        **kwargs: Additional arguments passed to LogEntry constructor

    Returns:
        A new LogEntry for tool response
    """
    return LogEntry(
        session_id=session_id,
        prompt_number=prompt_number,
        turn_number=turn_number,
        event_type=EventType.TOOL_RESPONSE,
        tool_response=ToolResponse(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            success=success,
            error_message=error_message,
            execution_time_ms=execution_time_ms
        ),
        **kwargs
    )


def create_test_result_log(
    session_id: str,
    prompt_number: int,
    turn_number: int,
    status: TestStatus,
    total_tests: int,
    passed_tests: int,
    **kwargs
) -> LogEntry:
    """
    Create a test result log entry.

    Args:
        session_id: Identifier for the session
        prompt_number: Sequential number of the prompt within the session
        turn_number: Turn number within the current prompt
        status: Overall test status
        total_tests: Total number of tests run
        passed_tests: Number of tests that passed
        **kwargs: Additional arguments passed to LogEntry constructor

    Returns:
        A new LogEntry for test result
    """
    return LogEntry(
        session_id=session_id,
        prompt_number=prompt_number,
        turn_number=turn_number,
        event_type=EventType.TEST_RESULT,
        test_result=TestResults(
            status=status,
            total_tests=total_tests,
            passed_tests=passed_tests
        ),
        **kwargs
    )


def create_error_log(
    session_id: str,
    prompt_number: int,
    turn_number: int,
    error_message: str,
    error_type: Optional[str] = None,
    error_severity: Optional[ErrorSeverity] = None,
    stack_trace: Optional[str] = None,
    component_id: Optional[str] = None,
    **kwargs
) -> LogEntry:
    """
    Create an error log entry.

    Args:
        session_id: Identifier for the session
        prompt_number: Sequential number of the prompt within the session
        turn_number: Turn number within the current prompt
        error_message: Description of the error
        error_type: Type/category of error
        error_severity: Severity level of the error
        stack_trace: Stack trace if available
        component_id: ID of the component that generated the error
        **kwargs: Additional arguments passed to LogEntry constructor

    Returns:
        A new LogEntry for error
    """
    return LogEntry(
        session_id=session_id,
        prompt_number=prompt_number,
        turn_number=turn_number,
        event_type=EventType.ERROR,
        error_info=ErrorInfo(
            error_type=error_type,
            error_message=error_message,
            error_severity=error_severity,
            stack_trace=stack_trace,
            component_id=component_id
        ),
        **kwargs
    )


# ============================================================================
# BACKWARD COMPATIBILITY CLASSES
# ============================================================================

# Maintain backward compatibility for existing code
class LegacyLogEntryHeader:
    """
    DEPRECATED: Legacy LogEntryHeader class for backward compatibility.

    Use LogEntry directly or the helper functions instead.
    This maps run_id to session_id for compatibility.
    """

    def __init__(
        self,
        run_id: str,
        timestamp: str = None,
        meta: Dict[str, Any] = None,
        _generate_timestamp: bool = True
    ):
        """
        Initialize a LogEntryHeader (DEPRECATED).

        Args:
            run_id: Identifier for the run (maps to session_id)
            timestamp: Timestamp of the log entry (ISO format string)
            meta: Flexible metadata dictionary
            _generate_timestamp: Internal flag to control timestamp generation
        """
        import time
        import warnings

        warnings.warn(
            "LogEntryHeader is deprecated. Use LogEntry and helper functions instead.",
            DeprecationWarning,
            stacklevel=2
        )

        self.run_id = run_id  # This maps to session_id in the new system
        if timestamp is not None:
            self.timestamp = timestamp
        elif _generate_timestamp:
            self.timestamp = int(time.time() * 1000)
        else:
            self.timestamp = None
        self.meta = dict(meta) if meta is not None else {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the LogEntryHeader to a dictionary."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "meta": self.meta
        }

    def to_json(self) -> str:
        """Convert the LogEntryHeader to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegacyLogEntryHeader':
        """Create a LegacyLogEntryHeader from a dictionary."""
        kwargs = {
            "run_id": data["run_id"],
            "meta": data.get("meta", {}),
            "_generate_timestamp": False
        }
        if "timestamp" in data:
            kwargs["timestamp"] = data["timestamp"]
        return cls(**kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> 'LegacyLogEntryHeader':
        """Create a LegacyLogEntryHeader from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Legacy classes - these map to the new LogEntry system
class RunStartLog:
    """DEPRECATED: Use create_session_start_log() instead."""

    def __init__(self, hdr: LegacyLogEntryHeader, prompt: str):
        import warnings
        warnings.warn(
            "RunStartLog is deprecated. Use create_session_start_log() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.hdr = hdr
        self.prompt = prompt
        self.log_type = "run_start"

    def to_dict(self) -> Dict[str, Any]:
        result = {"log_type": self.log_type, "prompt": self.prompt}
        result.update(self.hdr.to_dict())
        return result

    @classmethod
    def create(cls, run_id: str, prompt: str, timestamp: str = None, meta: Dict[str, Any] = None) -> 'RunStartLog':
        hdr = LegacyLogEntryHeader(run_id=run_id, timestamp=timestamp, meta=meta)
        return cls(hdr=hdr, prompt=prompt)


class RunEndLog:
    """DEPRECATED: Use create_session_end_log() instead."""

    def __init__(self, hdr: LegacyLogEntryHeader, response: str, elapsed_msec: str):
        import warnings
        warnings.warn(
            "RunEndLog is deprecated. Use create_session_end_log() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.hdr = hdr
        self.response = response
        self.elapsed_msec = elapsed_msec
        self.log_type = "run_end"

    def to_dict(self) -> Dict[str, Any]:
        result = {"log_type": self.log_type, "response": self.response, "elapsed_msec": self.elapsed_msec}
        result.update(self.hdr.to_dict())
        return result

    @classmethod
    def create(cls, run_id: str, response: str, elapsed_msec: str, timestamp: str = None, meta: Dict[str, Any] = None) -> 'RunEndLog':
        hdr = LegacyLogEntryHeader(run_id=run_id, timestamp=timestamp, meta=meta)
        return cls(hdr=hdr, response=response, elapsed_msec=elapsed_msec)


class LlmCallLog:
    """DEPRECATED: Use create_llm_call_log() instead."""

    def __init__(self, hdr: LegacyLogEntryHeader, context_name: str, prompt: str, response: str, purpose: str):
        import warnings
        warnings.warn(
            "LlmCallLog is deprecated. Use create_llm_call_log() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.hdr = hdr
        self.context_name = context_name
        self.prompt = prompt
        self.response = response
        self.purpose = purpose
        self.log_type = "llm_call"

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "log_type": self.log_type,
            "context_name": self.context_name,
            "prompt": self.prompt,
            "response": self.response,
            "purpose": self.purpose
        }
        result.update(self.hdr.to_dict())
        return result

    @classmethod
    def create(cls, run_id: str, context_name: str, prompt: str, response: str, purpose: str, timestamp: str = None, meta: Dict[str, Any] = None) -> 'LlmCallLog':
        hdr = LegacyLogEntryHeader(run_id=run_id, timestamp=timestamp, meta=meta)
        return cls(hdr=hdr, context_name=context_name, prompt=prompt, response=response, purpose=purpose)


class TestResultLog:
    """DEPRECATED: Use create_test_result_log() instead."""

    def __init__(self, hdr: LegacyLogEntryHeader, test_name: str, success: bool, actual_output: str,
                 error_message: Optional[str] = None, execution_time: Optional[float] = None):
        import warnings
        warnings.warn(
            "TestResultLog is deprecated. Use create_test_result_log() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.hdr = hdr
        self.test_name = test_name
        self.success = success
        self.actual_output = actual_output
        self.error_message = error_message
        self.execution_time = execution_time
        self.log_type = "test_result"

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "log_type": self.log_type,
            "test_name": self.test_name,
            "success": self.success,
            "actual_output": self.actual_output
        }
        if self.error_message is not None:
            result["error_message"] = self.error_message
        if self.execution_time is not None:
            result["execution_time"] = self.execution_time
        result.update(self.hdr.to_dict())
        return result

    @classmethod
    def create(cls, run_id: str, test_name: str, success: bool, actual_output: str,
               error_message: Optional[str] = None, execution_time: Optional[float] = None,
               timestamp: str = None, meta: Dict[str, Any] = None) -> 'TestResultLog':
        hdr = LegacyLogEntryHeader(run_id=run_id, timestamp=timestamp, meta=meta)
        return cls(hdr=hdr, test_name=test_name, success=success, actual_output=actual_output,
                   error_message=error_message, execution_time=execution_time)


class OtherLog:
    """DEPRECATED: Use LogEntry directly instead."""

    def __init__(self, hdr: LegacyLogEntryHeader):
        import warnings
        warnings.warn(
            "OtherLog is deprecated. Use LogEntry directly instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.hdr = hdr
        self.log_type = "other"

    def to_dict(self) -> Dict[str, Any]:
        result = {"log_type": self.log_type}
        result.update(self.hdr.to_dict())
        return result

    @classmethod
    def create(cls, run_id: str, timestamp: str = None, meta: Dict[str, Any] = None) -> 'OtherLog':
        hdr = LegacyLogEntryHeader(run_id=run_id, timestamp=timestamp, meta=meta)
        return cls(hdr=hdr)


# ============================================================================
# EXPORTS AND COMPATIBILITY
# ============================================================================

# Export all the new types and helper functions for easy access
__all__ = [
    # Main entry types
    "LogEntry", "LogRequest", "LogResponse",

    # Enums
    "EventType", "ComponentType", "TestStatus", "RoutingType", "ErrorSeverity",

    # Data classes
    "SourceComponent", "TargetComponent", "ToolCall", "ToolResponse",
    "ErrorInfo", "PerformanceMetrics", "TestResults", "LlmResponse", "LlmCall", "Meta",

    # Helper functions
    "create_session_start_log", "create_session_end_log",
    "create_llm_call_log", "create_llm_response_log",
    "create_tool_call_log", "create_tool_response_log",
    "create_test_result_log", "create_error_log",

    # New LogEntryHeader class (matches Rust struct)
    "LogEntryHeader",

    # Backward compatibility classes (deprecated but still available)
    "RunStartLog", "RunEndLog", "LlmCallLog", "TestResultLog", "OtherLog"
]


# ============================================================================
# BACKWARD COMPATIBILITY ALIAS
# ============================================================================

# For external imports, maintain the ability to import the new LogEntryHeader
# (The legacy classes above use LegacyLogEntryHeader internally)

# Test that the inheritance works correctly
if __name__ == "__main__":
    # Test creating a LogEntry (which inherits from LogEntryHeader)
    log_entry = LogEntry(
        session_id="test-123",
        prompt_number=1,
        turn_number=0,
        event_type=EventType.SESSION_START,
        prompt="Hello world"
    )

    # Test that LogEntry has all LogEntryHeader fields
    assert hasattr(log_entry, 'version')
    assert hasattr(log_entry, 'session_id')
    assert hasattr(log_entry, 'prompt_number')
    assert hasattr(log_entry, 'turn_number')
    assert hasattr(log_entry, 'event_id')
    assert hasattr(log_entry, 'event_type')
    assert hasattr(log_entry, 'timestamp')

    # Test that LogEntry has its own fields
    assert hasattr(log_entry, 'prompt')
    assert hasattr(log_entry, 'meta')

    # Test that it's an instance of LogEntryHeader
    assert isinstance(log_entry, LogEntryHeader)

    print("✅ LogEntry properly inherits from LogEntryHeader")
    print("✅ All fields from Rust LogEntryHeader are present")
    print("✅ LogEntry includes additional fields for full log entries")
