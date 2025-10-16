"""SDK initialization module.

This module handles SDK initialization, separating concerns from the main __init__.py
"""
import uuid
from typing import List, Optional
import asyncio
import threading
from weakref import WeakKeyDictionary

from ..api.client import HttpClient
from ..api.resources.event import EventResource
from ..api.resources.session import SessionResource
from ..api.resources.dataset import DatasetResource
from ..core.config import SDKConfig, get_config, set_config
from ..utils.queue import EventQueue
from ..utils.logger import debug, info, warning, error, truncate_id
from .context import set_active_session, current_session_id
from .error_boundary import register_cleanup_handler
from .shutdown_manager import get_shutdown_manager, SessionState
from ..telemetry.telemetry_init import instrument_providers
from opentelemetry.sdk.trace import TracerProvider


class SDKState:
    """Container for SDK runtime state."""

    def __init__(self):
        self.http: Optional[HttpClient] = None
        self.event_queue: Optional[EventQueue] = None
        self.session_id: Optional[str] = None
        self.tracer_provider: Optional[TracerProvider] = None
        self.resources = {}
        # Task-local storage for async task isolation
        self.task_sessions: WeakKeyDictionary = WeakKeyDictionary()
        # Thread-local storage for thread isolation
        self.thread_local = threading.local()

    def reset(self):
        """Reset SDK state."""
        # Shutdown telemetry first to ensure all spans are exported
        if self.tracer_provider:
            try:
                # Force flush all pending spans with 5 second timeout
                debug("[SDK] Flushing OpenTelemetry spans...")
                self.tracer_provider.force_flush(timeout_millis=5000)
                # Shutdown the tracer provider and all processors
                self.tracer_provider.shutdown()
                debug("[SDK] TracerProvider shutdown complete")
            except Exception as e:
                error(f"[SDK] Error shutting down TracerProvider: {e}")

        if self.event_queue:
            self.event_queue.shutdown()
        if self.http:
            self.http.close()

        self.http = None
        self.event_queue = None
        self.session_id = None
        self.tracer_provider = None
        self.resources = {}
        self.task_sessions.clear()
        # Clear thread-local storage for current thread
        if hasattr(self.thread_local, 'session_id'):
            delattr(self.thread_local, 'session_id')


# Global SDK state
_sdk_state = SDKState()


def init(
    session_name: Optional[str] = None,
    session_id: Optional[str] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    task: Optional[str] = None,
    providers: Optional[List[str]] = None,
    production_monitoring: bool = False,
    experiment_id: Optional[str] = None,
    evaluators: Optional[List] = None,
    tags: Optional[List] = None,
    datasetitem_id: Optional[str] = None,
    masking_function: Optional[callable] = None,
    auto_end: bool = True,
    capture_uncaught: bool = True,
) -> str:
    """Initialize the Lucidic SDK.
    
    Args:
        session_name: Name for the session
        session_id: Custom session ID (optional)
        api_key: API key (uses env if not provided)
        agent_id: Agent ID (uses env if not provided)
        task: Task description
        providers: List of telemetry providers to instrument
        production_monitoring: Enable production monitoring
        experiment_id: Experiment ID to associate with session
        evaluators: Ealuators to use
        tags: Session tags
        datasetitem_id: Dataset item ID
        masking_function: Function to mask sensitive data
        auto_end: Automatically end session on exit
        capture_uncaught: Capture uncaught exceptions
        
    Returns:
        Session ID
        
    Raises:
        APIKeyVerificationError: If API credentials are invalid
    """
    global _sdk_state
    
    # Create or update configuration
    config = SDKConfig.from_env(
        api_key=api_key,
        agent_id=agent_id,
        auto_end=auto_end,
        production_monitoring=production_monitoring
    )
    
    if providers:
        config.telemetry.providers = providers
    
    config.error_handling.capture_uncaught = capture_uncaught
    
    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Invalid configuration: {', '.join(errors)}")
    
    # Set global config
    set_config(config)
    
    # Initialize HTTP client
    if not _sdk_state.http:
        debug("[SDK] Initializing HTTP client")
        _sdk_state.http = HttpClient(config)
    
    # Initialize resources
    if not _sdk_state.resources:
        _sdk_state.resources = {
            'events': EventResource(_sdk_state.http),
            'sessions': SessionResource(_sdk_state.http),
            'datasets': DatasetResource(_sdk_state.http)
        }
    
    # Initialize event queue
    if not _sdk_state.event_queue:
        debug("[SDK] Initializing event queue")
        # Create a mock client object for backward compatibility
        # The queue needs a client with make_request method
        class ClientAdapter:
            def make_request(self, endpoint, method, data):
                return _sdk_state.http.request(method, endpoint, json=data)
        
        _sdk_state.event_queue = EventQueue(ClientAdapter())
        
        # Register cleanup handler
        register_cleanup_handler(lambda: _sdk_state.event_queue.force_flush())
        debug("[SDK] Event queue initialized and cleanup handler registered")
    
    # Create or retrieve session
    if session_id:
        # Use provided session ID
        real_session_id = session_id
    else:
        # Create new session
        real_session_id = str(uuid.uuid4())
    
    # Create session via API - only send non-None values
    session_params = {
        'session_id': real_session_id,
        'session_name': session_name or 'Unnamed Session',
        'agent_id': config.agent_id,
    }
    
    # Only add optional fields if they have values
    if task:
        session_params['task'] = task
    if tags:
        session_params['tags'] = tags
    if experiment_id:
        session_params['experiment_id'] = experiment_id
    if datasetitem_id:
        session_params['datasetitem_id'] = datasetitem_id
    if evaluators:
        session_params['evaluators'] = evaluators
    if production_monitoring:
        session_params['production_monitoring'] = production_monitoring
    
    debug(f"[SDK] Creating session with params: {session_params}")
    session_resource = _sdk_state.resources['sessions']
    session_data = session_resource.create_session(session_params)
    
    # Use the session_id returned by the backend
    real_session_id = session_data.get('session_id', real_session_id)
    _sdk_state.session_id = real_session_id
    
    info(f"[SDK] Session created: {truncate_id(real_session_id)} (name: {session_name or 'Unnamed Session'})")
    
    # Set active session in context
    set_active_session(real_session_id)
    
    # Register session with shutdown manager
    debug(f"[SDK] Registering session with shutdown manager (auto_end={auto_end})")
    shutdown_manager = get_shutdown_manager()
    session_state = SessionState(
        session_id=real_session_id,
        http_client=_sdk_state.resources,  # Pass resources dict which has sessions
        event_queue=_sdk_state.event_queue,
        auto_end=auto_end
    )
    shutdown_manager.register_session(real_session_id, session_state)
    
    # Initialize telemetry if providers specified
    if providers:
        debug(f"[SDK] Initializing telemetry for providers: {providers}")
        _initialize_telemetry(providers)
    
    return real_session_id


def _initialize_telemetry(providers: List[str]) -> None:
    """Initialize telemetry providers.
    
    Args:
        providers: List of provider names
    """
    global _sdk_state
    
    if not _sdk_state.tracer_provider:
        # Import here to avoid circular dependency
        from ..telemetry.lucidic_exporter import LucidicSpanExporter
        from ..telemetry.context_capture_processor import ContextCaptureProcessor
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        
        # Create tracer provider with our processors
        _sdk_state.tracer_provider = TracerProvider()
        
        # Add context capture processor FIRST to capture context before export
        context_processor = ContextCaptureProcessor()
        _sdk_state.tracer_provider.add_span_processor(context_processor)
        
        # Add exporter processor
        exporter = LucidicSpanExporter()
        export_processor = BatchSpanProcessor(exporter)
        _sdk_state.tracer_provider.add_span_processor(export_processor)
    
    # Instrument providers
    instrument_providers(providers, _sdk_state.tracer_provider, {})
    
    info(f"[Telemetry] Initialized for providers: {providers}")


def set_task_session(session_id: str) -> None:
    """Set session ID for current async task (if in async context)."""
    try:
        if task := asyncio.current_task():
            _sdk_state.task_sessions[task] = session_id
            debug(f"[SDK] Set task-local session {truncate_id(session_id)} for task {task.get_name()}")
    except RuntimeError:
        # Not in async context, ignore
        pass


def clear_task_session() -> None:
    """Clear session ID for current async task (if in async context)."""
    try:
        if task := asyncio.current_task():
            _sdk_state.task_sessions.pop(task, None)
            debug(f"[SDK] Cleared task-local session for task {task.get_name()}")
    except RuntimeError:
        # Not in async context, ignore
        pass


def set_thread_session(session_id: str) -> None:
    """Set session ID for current thread.

    This provides true thread-local storage that doesn't inherit from parent thread.
    """
    _sdk_state.thread_local.session_id = session_id
    current_thread = threading.current_thread()
    debug(f"[SDK] Set thread-local session {truncate_id(session_id)} for thread {current_thread.name}")


def clear_thread_session() -> None:
    """Clear session ID for current thread."""
    if hasattr(_sdk_state.thread_local, 'session_id'):
        delattr(_sdk_state.thread_local, 'session_id')
        current_thread = threading.current_thread()
        debug(f"[SDK] Cleared thread-local session for thread {current_thread.name}")


def get_thread_session() -> Optional[str]:
    """Get session ID from thread-local storage."""
    return getattr(_sdk_state.thread_local, 'session_id', None)


def is_main_thread() -> bool:
    """Check if we're running in the main thread."""
    return threading.current_thread() is threading.main_thread()


def get_session_id() -> Optional[str]:
    """Get the current session ID.

    Priority:
    1. Task-local session (for async tasks)
    2. Thread-local session (for threads) - NO FALLBACK for threads
    3. SDK state session (for main thread)
    4. Context variable session (fallback for main thread only)
    """
    # First check task-local storage for async isolation
    try:
        if task := asyncio.current_task():
            if task_session := _sdk_state.task_sessions.get(task):
                debug(f"[SDK] Using task-local session {truncate_id(task_session)}")
                return task_session
    except RuntimeError:
        # Not in async context
        pass

    # Check if we're in a thread
    if not is_main_thread():
        # For threads, ONLY use thread-local storage - no fallback!
        # This prevents inheriting the parent thread's session
        thread_session = get_thread_session()
        if thread_session:
            debug(f"[SDK] Using thread-local session {truncate_id(thread_session)}")
        else:
            debug(f"[SDK] Thread {threading.current_thread().name} has no thread-local session")
        return thread_session  # Return None if not set - don't fall back!

    # For main thread only: fall back to SDK state or context variable
    return _sdk_state.session_id or current_session_id.get()


def get_http() -> Optional[HttpClient]:
    """Get the HTTP client instance."""
    return _sdk_state.http


def get_event_queue() -> Optional[EventQueue]:
    """Get the event queue instance."""
    return _sdk_state.event_queue


def get_resources() -> dict:
    """Get API resource instances."""
    return _sdk_state.resources


def get_tracer_provider() -> Optional[TracerProvider]:
    """Get the tracer provider instance."""
    return _sdk_state.tracer_provider


def clear_state() -> None:
    """Clear SDK state (for testing)."""
    global _sdk_state
    debug("[SDK] Clearing SDK state")
    _sdk_state.reset()
    _sdk_state = SDKState()