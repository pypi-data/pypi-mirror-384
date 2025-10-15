import logging
import mimetypes
import os
import random
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Type, Optional, Any, List, Dict, Tuple

from langchain_core.tools import ToolException
from llm_sandbox import SandboxSession, SandboxBackend, ArtifactSandboxSession
from llm_sandbox.exceptions import SandboxTimeoutError
from llm_sandbox.security import SecurityPolicy
from pydantic import BaseModel, Field

from codemie_tools.base.codemie_tool import CodeMieTool
from codemie_tools.data_management.code_executor.security_policies import get_codemie_security_policy
from codemie_tools.data_management.file_system.tools_vars import CODE_EXECUTOR_TOOL, COMMON_SANDBOX_LIBRARIES

logger = logging.getLogger(__name__)


class SandboxConfig:
    """
    Centralized configuration for sandbox execution environment.

    This class encapsulates all sandbox-related configuration parameters,
    making it easier to manage and modify settings in one place.
    """

    # Working directory configuration
    WORKDIR_BASE: str = "/home/codemie"

    # Kubernetes configuration
    NAMESPACE: str = "default"
    DOCKER_IMAGE: str = "codemie-python:1.1"

    # Timeout configuration (in seconds)
    EXECUTION_TIMEOUT: float = 30.0  # Protects against infinite loops
    SESSION_TIMEOUT: float = 300.0  # Session lifetime (5 minutes)
    DEFAULT_TIMEOUT: float = 30.0  # Default operation timeout

    # Resource limits
    MEMORY_LIMIT: str = "128Mi"
    MEMORY_REQUEST: str = "128Mi"
    CPU_LIMIT: str = "1"
    CPU_REQUEST: str = "500m"

    # Pod pool for load distribution
    POD_POOL: list = [
        "codemie-executor-1",
        "codemie-executor-2",
        "codemie-executor-3"
    ]

    # Security configuration
    RUN_AS_USER: int = 1000
    RUN_AS_GROUP: int = 1000
    FS_GROUP: int = 1000
    VERBOSE: bool = True
    SKIP_ENVIRONMENT_SETUP: bool = False


class SandboxSessionManager:
    """
    Singleton manager for maintaining persistent sandbox sessions.

    Manages a pool of reusable sessions mapped to pod names, providing
    thread-safe access and automatic session lifecycle management.

    Attributes:
        _sessions: Dictionary mapping pod names to active sandbox sessions
        _session_locks: Per-pod locks for thread-safe session access
        _initialized: Flag indicating whether the singleton has been initialized
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Implement thread-safe singleton pattern with double-checked locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize session storage and per-pod locks."""
        if self._initialized:
            return

        self._sessions: Dict[str, SandboxSession] = {}
        self._session_locks: Dict[str, threading.Lock] = {
            pod: threading.Lock() for pod in SandboxConfig.POD_POOL
        }
        self._initialized = True
        logger.info("SandboxSessionManager initialized")

    def get_session(
            self,
            pod_name: str,
            workdir: str,
            pod_manifest: dict,
            security_policy: SecurityPolicy
    ):
        """
        Get or create a persistent session for the specified pod.

        This method provides thread-safe session acquisition with per-pod locking
        and automatic health checking to ensure session validity.

        Args:
            pod_name: Name of the pod to connect to
            workdir: Working directory for the session
            pod_manifest: Pod manifest for creating new pods
            security_policy: Security policy for code validation

        Returns:
            SandboxSession: Active session for the pod

        Raises:
            ToolException: If session creation fails
        """
        with self._session_locks[pod_name]:
            if pod_name in self._sessions and self._is_session_healthy(pod_name):
                logger.info(f"Reusing existing session for pod: {pod_name}")
                return self._sessions[pod_name]
            # Create new session if pod doesn't exist or session isn't healthy

            # Create new session
            logger.info(f"Creating new session for pod: {pod_name}")
            session = self._create_session(pod_name, workdir, pod_manifest, security_policy)
            self._sessions[pod_name] = session
            return session

    def _is_session_healthy(self, pod_name: str) -> bool:
        """
        Check if an existing session is still healthy and responsive.

        Args:
            pod_name: Name of the pod to check

        Returns:
            bool: True if session is healthy, False otherwise
        """
        session = self._sessions[pod_name]
        try:
            # Test if session is still alive with a simple command
            session.run("print('health_check')")
            return True
        except SandboxTimeoutError:
            logger.warning(f"Session for {pod_name} expired, will recreate")
            self._close_session(pod_name)
            return False
        except Exception as e:
            logger.warning(f"Existing session for {pod_name} is dead, will recreate: {e}")
            self._close_session(pod_name)
            return False

    def _create_session(
            self,
            pod_name: str,
            workdir: str,
            pod_manifest: dict,
            security_policy: SecurityPolicy
    ):
        """
        Create a new sandbox session by connecting to existing pod or creating new one.

        First attempts to connect to an existing pod. If the pod doesn't exist,
        creates a new pod using the provided manifest.

        Args:
            pod_name: Name of the pod
            workdir: Working directory
            pod_manifest: Pod manifest for new pod creation
            security_policy: Security policy for code validation

        Returns:
            SandboxSession: Newly created session

        Raises:
            ToolException: If session creation fails
        """
        # Try to connect to existing pod first
        try:
            session = self._connect_to_existing_pod(pod_name, workdir, security_policy)
            logger.info(f"✓ Connected to existing pod: {pod_name}")
            return session
        except Exception as connect_error:
            # Pod doesn't exist, create it
            logger.info(f"Pod {pod_name} not found, creating new pod: {connect_error}")
            return self._create_new_pod(pod_name, workdir, pod_manifest, security_policy)

    def _connect_to_existing_pod(
            self,
            pod_name: str,
            workdir: str,
            security_policy: SecurityPolicy
    ):
        """
        Connect to an existing pod without creating a new one.

        Args:
            pod_name: Name of the existing pod
            workdir: Working directory
            security_policy: Security policy for code validation

        Returns:
            SandboxSession: Connected session

        Raises:
            Exception: If connection fails
        """
        session_config = self._build_session_config(
            workdir=workdir,
            security_policy=security_policy,
            container_id=pod_name
        )
        session = ArtifactSandboxSession(**session_config)
        session.open()
        return session

    def _create_new_pod(
            self,
            pod_name: str,
            workdir: str,
            pod_manifest: dict,
            security_policy: SecurityPolicy
    ):
        """
        Create a new pod with the specified configuration.

        Args:
            pod_name: Name for the new pod
            workdir: Working directory
            pod_manifest: Pod manifest configuration
            security_policy: Security policy for code validation

        Returns:
            SandboxSession: Session for the newly created pod

        Raises:
            Exception: If pod creation fails
        """
        session_config = self._build_session_config(
            workdir=workdir,
            security_policy=security_policy,
            pod_manifest=pod_manifest,
            keep_template=True,
            default_timeout=SandboxConfig.DEFAULT_TIMEOUT
        )

        logger.info(f"Security policy applied: {security_policy.severity_threshold.name} threshold")

        session = ArtifactSandboxSession(**session_config)
        session.open()
        logger.info(f"✓ New pod created: {pod_name}")
        return session

    @staticmethod
    def _build_session_config(
            workdir: str,
            security_policy: SecurityPolicy,
            **kwargs
    ) -> dict:
        """
        Build session configuration with common parameters.

        Args:
            workdir: Working directory
            security_policy: Security policy for code validation
            **kwargs: Additional configuration parameters

        Returns:
            dict: Session configuration
        """
        config = {
            "backend": SandboxBackend.KUBERNETES,
            "lang": "python",
            "kube_namespace": SandboxConfig.NAMESPACE,
            "verbose": SandboxConfig.VERBOSE,
            "workdir": workdir,
            "execution_timeout": SandboxConfig.EXECUTION_TIMEOUT,
            "session_timeout": SandboxConfig.SESSION_TIMEOUT,
            "security_policy": security_policy,
            "skip_environment_setup": SandboxConfig.SKIP_ENVIRONMENT_SETUP
        }
        config.update(kwargs)
        return config

    def _close_session(self, pod_name: str):
        """Close and remove a session from the pool."""
        if pod_name in self._sessions:
            try:
                self._sessions[pod_name].close()
            except Exception as e:
                logger.warning(f"Error closing session for {pod_name}: {e}")
            finally:
                del self._sessions[pod_name]

    def close_all(self):
        """Close all managed sessions. Useful for cleanup."""
        for pod_name in self._sessions.keys():
            self._close_session(pod_name)
        logger.info("All sessions closed")


class CodeExecutorInput(BaseModel):
    code: str = Field(
        description=f"""
        Python code to execute in an isolated environment.

        IMPORTANT CONSTRAINTS:
        - Code MUST be Python only
        - ONLY use pre-installed libraries or Python standard library modules
        - External libraries NOT in the pre-installed list are NOT available and will cause import errors
        - Code that attempts to import unavailable libraries will FAIL

        Pre-installed libraries: {', '.join(COMMON_SANDBOX_LIBRARIES)}

        Standard library modules (e.g., os, sys, json, datetime, pathlib, etc.) are also available.
        """.strip()
    )
    export_files: Optional[List[str]] = Field(
        default=None,
        description="List of file paths to export after code execution. Files will be stored using file_repository."
    )


class CodeExecutorTool(CodeMieTool):
    """
    Tool for executing Python code in a secure, isolated environment.
    Provides safe code execution with resource limits and complete isolation.

    Features:
    - Infinite Loop Protection: Automatic timeout after execution_timeout seconds
    - Resource-Intensive Operation Control: CPU and memory limits via pod manifest
    - Session Lifetime Management: Sessions expire after session_timeout seconds
    - Security Policy: Code validation before execution using production-grade policy

    Security:
    - Production-grade security policy optimized for shared multi-tenant environments
    - Blocks dangerous system operations, file access, network calls, and code evaluation
    - Pre-execution code validation with detailed violation reporting
    """

    name: str = CODE_EXECUTOR_TOOL.name
    description: str = CODE_EXECUTOR_TOOL.description
    args_schema: Type[BaseModel] = CodeExecutorInput
    file_repository: Optional[Any] = None
    user_id: Optional[str] = ""
    security_policy: SecurityPolicy = None
    _custom_pod_manifest: Optional[dict] = None

    def __init__(
            self,
            file_repository: Optional[Any] = None,
            user_id: Optional[str] = "",
    ):
        """
        Initialize the CodeExecutorTool.

        Configuration is managed via SandboxConfig class:
        - NAMESPACE: Kubernetes namespace
        - EXECUTION_TIMEOUT: Code execution timeout
        - SESSION_TIMEOUT: Session lifetime
        - DEFAULT_TIMEOUT: Default operation timeout

        Args:
            file_repository: Repository for storing files generated by code execution
            user_id: User ID for file ownership attribution
        """
        super().__init__()
        self.file_repository = file_repository
        self.user_id = user_id
        self.security_policy = get_codemie_security_policy()
        logger.info("Security policy initialized")

    def _get_user_workdir(self) -> str:
        """
        Get user-specific working directory to ensure isolation between users.

        Uses sanitized user ID to create isolated workdir paths, preventing
        directory traversal attacks.

        Returns:
            str: User-specific workdir path
        """
        if self.user_id:
            safe_user_id = self.user_id.replace('/', '_').replace('\\', '_')
            return f"{SandboxConfig.WORKDIR_BASE}/{safe_user_id}"
        return SandboxConfig.WORKDIR_BASE

    @staticmethod
    def _get_available_pod_name() -> Optional[str]:
        """
        Get an available pod name randomly from the pool to distribute load.

        Pod reuse is handled by llm-sandbox's container_id parameter. Random
        selection provides basic load distribution across the pod pool.

        Returns:
            str: Random pod name from the pool, or None if pool is empty
        """
        return random.choice(SandboxConfig.POD_POOL) if SandboxConfig.POD_POOL else None  # NOSONAR

    @staticmethod
    def _create_default_pod_manifest(pod_name: str) -> dict:
        """
        Create a default pod manifest with appropriate resource limits and security settings.

        Resource-Intensive Operation Control:
        - Memory and CPU limits configured via SandboxConfig
        - Prevents resource exhaustion in multi-tenant environment

        Security Features:
        - Strict security policies to prevent system command execution
        - No privilege escalation allowed
        - All capabilities dropped
        - Seccomp profile to restrict system calls
        - No host namespace access

        Pod is shared between users with isolation at the workdir level.
        Each pod has a single container. The pool manages multiple pods for load distribution.

        Args:
            pod_name: Fixed pod name from the pool for reuse

        Returns:
            dict: Pod manifest configuration with resource limits and security settings
        """
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": SandboxConfig.NAMESPACE,
                "labels": {
                    "app": "codemie-executor",
                    "component": "code-executor"
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "python-executor",
                        "image": SandboxConfig.DOCKER_IMAGE,
                        "tty": True,
                        "stdin": True,
                        "securityContext": {
                            "runAsUser": SandboxConfig.RUN_AS_USER,
                            "runAsGroup": SandboxConfig.RUN_AS_GROUP,
                            "runAsNonRoot": True,
                            "allowPrivilegeEscalation": False,
                            "capabilities": {"drop": ["ALL"]},
                            "privileged": False,
                            "readOnlyRootFilesystem": True,
                            "seccompProfile": {"type": "RuntimeDefault"}
                        },
                        "volumeMounts": [
                            {"name": "tmp", "mountPath": "/tmp"}, #NOSONAR
                            {"name": "workdir", "mountPath": "/home/codemie"}
                        ],
                        "resources": {
                            "limits": {
                                "memory": SandboxConfig.MEMORY_LIMIT,
                                "cpu": SandboxConfig.CPU_LIMIT
                            },
                            "requests": {
                                "memory": SandboxConfig.MEMORY_REQUEST,
                                "cpu": SandboxConfig.CPU_REQUEST
                            }
                        }
                    }
                ],
                "volumes": [
                    {"name": "tmp", "emptyDir": {}},
                    {"name": "workdir", "emptyDir": {}}
                ],
                "securityContext": {
                    "runAsUser": SandboxConfig.RUN_AS_USER,
                    "runAsGroup": SandboxConfig.RUN_AS_GROUP,
                    "fsGroup": SandboxConfig.FS_GROUP,
                    "runAsNonRoot": True,
                    "seccompProfile": {"type": "RuntimeDefault"},
                    "supplementalGroups": [],
                    "fsGroupChangePolicy": "OnRootMismatch"
                },
                "hostNetwork": False,
                "hostPID": False,
                "hostIPC": False,
                "restartPolicy": "Never",
                "automountServiceAccountToken": False
            }
        }

    def execute(self, code: str, export_files: Optional[List[str]] = None) -> str:
        """
        Execute Python code in a secure, isolated environment.

        This method orchestrates the code execution workflow:
        1. Acquires a sandbox session (reuses existing or creates new)
        2. Validates code against security policy
        3. Executes code with timeout protection
        4. Processes and formats results
        5. Exports files if requested

        Args:
            code: The Python code to execute
            export_files: List of file paths to export after execution

        Returns:
            Execution result including stdout, stderr, and exit code.
            If export_files is provided and file_repository is available,
            includes URLs for exported files.

        Raises:
            ToolException: If execution fails, security validation fails,
                          or session acquisition fails
        """
        try:
            user_workdir = self._get_user_workdir()
            session, session_time = self._acquire_session(user_workdir)

            self._validate_code_security(session, code)

            result, exec_time = self._execute_code(session, code)
            self._log_execution_timing(session_time, exec_time)

            result_text = self._format_execution_result(result)
            export_files = self._export_files_from_execution(session, export_files, user_workdir)
            if export_files:
                result_text += ", ".join(export_files)

            return result_text

        except ImportError as e:
            raise ToolException(
                "Required library is not installed. "
                "Please install it with: pip install 'llm-sandbox[k8s]'"
            ) from e
        except ToolException:
            raise
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}", exc_info=True)
            raise ToolException(f"Error executing code: {str(e)}") from e

    def _acquire_session(self, user_workdir: str) -> Tuple[SandboxSession, float]:
        """
        Acquire a sandbox session for code execution.

        Args:
            user_workdir: User-specific working directory

        Returns:
            tuple: (session, elapsed_time_seconds)

        Raises:
            ToolException: If session acquisition fails
        """
        start_time = time.time()

        pod_name = self._get_available_pod_name()
        if not pod_name:
            raise ToolException("No pods available in the pool")

        logger.info(f"Using pod: {pod_name} with workdir: {user_workdir}")

        session_manager = SandboxSessionManager()
        pod_manifest = self._custom_pod_manifest or self._create_default_pod_manifest(pod_name)

        session = session_manager.get_session(
            pod_name=pod_name,
            workdir=user_workdir,
            pod_manifest=pod_manifest,
            security_policy=self.security_policy
        )

        elapsed = time.time() - start_time
        logger.info(f"✓ Session ready in {elapsed:.2f}s")

        return session, elapsed

    @staticmethod
    def _validate_code_security(session, code: str) -> None:
        """
        Validate code against security policy before execution.

        Args:
            session: Active sandbox session
            code: Python code to validate

        Raises:
            ToolException: If code fails security validation
        """
        logger.info("Performing security validation...")
        is_safe, violations = session.is_safe(code)

        if not is_safe:
            violation_details = [
                f"  • [{v.severity.name}] {v.description}"
                for v in violations
            ]
            error_msg = (
                    f"Code failed security validation ({len(violations)} violation(s) detected):\n"
                    + "\n".join(violation_details) +
                    "\n\nPlease review your code and remove any restricted operations."
            )
            logger.warning(f"Security violations detected: {len(violations)}")
            raise ToolException(error_msg)

        logger.info("✓ Security validation passed")

    @staticmethod
    def _execute_code(session, code: str) -> Tuple[Any, float]:
        """
        Execute code in the sandbox with timeout protection.

        Args:
            session: Active sandbox session
            code: Python code to execute

        Returns:
            tuple: (execution_result, elapsed_time_seconds)

        Raises:
            ToolException: If execution times out
        """
        start_time = time.time()
        logger.info(f"Executing user code (timeout: {SandboxConfig.EXECUTION_TIMEOUT}s)...")

        try:
            result = session.run(code, timeout=SandboxConfig.EXECUTION_TIMEOUT)
        except SandboxTimeoutError as e:
            error_msg = (
                f"Code execution timed out after {SandboxConfig.EXECUTION_TIMEOUT} seconds. "
                "This may indicate an infinite loop or a resource-intensive operation. "
                "Please review your code and consider optimizing it."
            )
            logger.error(error_msg)
            raise ToolException(error_msg) from e

        elapsed = time.time() - start_time
        logger.info(f"✓ Code execution completed in {elapsed:.2f}s")

        return result, elapsed

    @staticmethod
    def _log_execution_timing(session_time: float, exec_time: float) -> None:
        """
        Log execution timing information.

        Args:
            session_time: Time spent acquiring session
            exec_time: Time spent executing code
        """
        total_time = session_time + exec_time
        logger.info(
            f"Total execution time: session={session_time:.2f}s, "
            f"exec={exec_time:.2f}s, total={total_time:.2f}s"
        )

    def _format_execution_result(self, result: Any) -> str:
        """
        Format execution result into a human-readable string.

        Filters out internal setup messages from stdout to provide cleaner output.

        Args:
            result: Execution result object with stdout, stderr, and exit_code

        Returns:
            str: Formatted result string

        Raises:
            ToolException: If execution failed (non-zero exit code)
        """
        output_parts = []

        # Filter stdout to remove internal setup messages
        if result.stdout:
            filtered_stdout = self._filter_stdout(result.stdout)
            if filtered_stdout:
                output_parts.append(f"{filtered_stdout}")

        if result.stderr:
            output_parts.append(f"STDERR:\n{result.stderr}")

        if result.exit_code != 0:
            logger.warning(f"Code execution failed with exit code {result.exit_code}")
            raise ToolException(f"Code execution failed.\n\n{chr(10).join(output_parts)}")

        return chr(10).join(output_parts) if output_parts else \
            "Code executed successfully with no output."

    @staticmethod
    def _filter_stdout(stdout: str) -> str:
        """
        Filter out internal setup messages from stdout.

        Args:
            stdout: Raw stdout output

        Returns:
            str: Filtered stdout with internal messages removed
        """
        # Filter out setup/initialization messages
        lines = stdout.split('\n')
        filtered_lines = [
            line for line in lines
            if 'Python plot detection setup complete' not in line
        ]
        return '\n'.join(filtered_lines).strip()

    def _export_files_from_execution(self, session, file_paths: Optional[List[str]], workdir: str) -> List[str]:
        """
        Export files from the execution environment and store them using file_repository.

        Args:
            session: The active execution session
            file_paths: List of paths to export from the execution environment
            workdir: The user-specific working directory

        Returns:
            List of URLs for the stored files
        """
        if not self.file_repository:
            logger.warning("Cannot export files: file_repository not available")
            return []

        urls = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, src_path in enumerate(file_paths, 1):
                try:
                    filename = os.path.basename(src_path) or f"file_{i}"
                    temp_file_path = os.path.join(temp_dir, filename)

                    # Copy file from execution environment to host using user-specific workdir
                    session.copy_from_runtime(f"{workdir}/{src_path}", temp_file_path)

                    # Determine MIME type and read file content
                    extension = Path(src_path).suffix.lower().lstrip('.')
                    mime_type = self._determine_mime_type(extension)

                    with open(temp_file_path, 'rb') as f:
                        content = f.read()

                    # Store file in repository
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    stored_file = self.file_repository.write_file(
                        name=unique_filename,
                        mime_type=mime_type,
                        content=content,
                        owner=self.user_id
                    )

                    url = f"File '{filename}': sandbox:/v1/files/{stored_file.to_encoded_url()}"
                    urls.append(url)

                except Exception as e:
                    logger.error(f"Failed to export file {src_path}: {e}")

        return urls

    @staticmethod
    def _determine_mime_type(extension: str) -> str:
        """
        Determine the MIME type based on the file extension using Python's mimetypes module.

        Args:
            extension: The file extension (without leading dot)

        Returns:
            The MIME type string, defaults to 'application/octet-stream' if unknown
        """
        # Add dot prefix if not present for mimetypes.guess_type
        filename = f"file.{extension}" if not extension.startswith('.') else f"file{extension}"
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
