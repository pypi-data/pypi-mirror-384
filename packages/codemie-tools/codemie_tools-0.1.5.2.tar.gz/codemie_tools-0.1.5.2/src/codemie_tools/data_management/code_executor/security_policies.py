"""
Security policy for code execution in shared sandbox environments.

This module provides a production-grade security policy based on llm-sandbox best practices
for multi-tenant environments where pods are shared between users.
"""

import logging

from llm_sandbox.security import (
    SecurityPolicy,
    SecurityPattern,
    RestrictedModule,
    SecurityIssueSeverity
)

logger = logging.getLogger(__name__)


def get_codemie_security_policy() -> SecurityPolicy:
    """
    Get the CodeMie security policy optimized for shared multi-tenant environments.

    This policy blocks:
    - System operations (os, subprocess, sys manipulation)
    - File system operations (shutil, pathlib, glob, tempfile)
    - Network operations (socket, urllib, requests, httpx)
    - Process/thread manipulation (threading, multiprocessing)
    - Code evaluation/compilation (eval, exec, compile)
    - Inspection/introspection modules (inspect, importlib)

    Optimized for shared pod environments with balanced security.
    """
    policy = SecurityPolicy(
        severity_threshold=SecurityIssueSeverity.LOW,
        restricted_modules=[
            # System operations - HIGH severity
            RestrictedModule(
                name="os",
                description="Operating system interface - blocked in multi-tenant environment",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="subprocess",
                description="Process execution - blocked for security",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="sys",
                description="System-specific parameters - restricted for isolation",
                severity=SecurityIssueSeverity.HIGH
            ),

            # File system operations - HIGH severity
            RestrictedModule(
                name="shutil",
                description="High-level file operations - blocked in shared environment",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="pathlib",
                description="Object-oriented filesystem paths - restricted",
                severity=SecurityIssueSeverity.MEDIUM
            ),
            RestrictedModule(
                name="glob",
                description="Unix style pathname pattern expansion - restricted",
                severity=SecurityIssueSeverity.MEDIUM
            ),
            RestrictedModule(
                name="tempfile",
                description="Temporary file creation - use with caution",
                severity=SecurityIssueSeverity.MEDIUM
            ),

            # Network operations - HIGH severity
            RestrictedModule(
                name="socket",
                description="Network socket operations - blocked",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="urllib",
                description="URL handling - blocked for security",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="requests",
                description="HTTP library - blocked",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="httpx",
                description="HTTP client - blocked",
                severity=SecurityIssueSeverity.HIGH
            ),

            # Code execution - HIGH severity
            RestrictedModule(
                name="eval",
                description="Dynamic code evaluation - extremely dangerous",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="exec",
                description="Dynamic code execution - extremely dangerous",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="compile",
                description="Code compilation - blocked",
                severity=SecurityIssueSeverity.HIGH
            ),

            # Process/Thread manipulation - HIGH severity
            RestrictedModule(
                name="threading",
                description="Thread-based parallelism - restricted in shared environment",
                severity=SecurityIssueSeverity.HIGH
            ),
            RestrictedModule(
                name="multiprocessing",
                description="Process-based parallelism - blocked",
                severity=SecurityIssueSeverity.HIGH
            ),

            # Code inspection - MEDIUM severity
            RestrictedModule(
                name="inspect",
                description="Code introspection - restricted",
                severity=SecurityIssueSeverity.MEDIUM
            ),
            RestrictedModule(
                name="importlib",
                description="Dynamic import system - restricted",
                severity=SecurityIssueSeverity.MEDIUM
            ),
        ]
    )

    # Add dangerous patterns
    _add_dangerous_patterns(policy)

    return policy


def _add_dangerous_patterns(policy: SecurityPolicy) -> None:
    """
    Add patterns for detecting dangerous code constructs.

    Args:
        policy: Security policy to enhance
    """
    # System command execution patterns
    policy.add_pattern(SecurityPattern(
        pattern=r"os\.system\s*\(",
        description="System command execution - blocked for security",
        severity=SecurityIssueSeverity.HIGH
    ))

    policy.add_pattern(SecurityPattern(
        pattern=r"subprocess\.(run|call|Popen|check_output)",
        description="Process execution - blocked for security",
        severity=SecurityIssueSeverity.HIGH
    ))

    # File system manipulation
    # Disabled for now, to allow to write files and export
    # policy.add_pattern(SecurityPattern(
    #     pattern=r"open\s*\([^,]*,\s*['\"]w['\"]",
    #     description="File write operation - restricted in shared environment",
    #     severity=SecurityIssueSeverity.HIGH
    # ))

    policy.add_pattern(SecurityPattern(
        pattern=r"os\.(remove|rmdir|unlink|mkdir|makedirs)",
        description="File system modification - restricted",
        severity=SecurityIssueSeverity.HIGH
    ))

    # Network access
    policy.add_pattern(SecurityPattern(
        pattern=r"socket\.socket\s*\(",
        description="Network socket creation - blocked",
        severity=SecurityIssueSeverity.HIGH
    ))

    policy.add_pattern(SecurityPattern(
        pattern=r"requests\.(get|post|put|delete)",
        description="HTTP request - blocked for security",
        severity=SecurityIssueSeverity.HIGH
    ))

    # Code evaluation
    policy.add_pattern(SecurityPattern(
        pattern=r"\beval\s*\(",
        description="Dynamic code evaluation - extremely dangerous",
        severity=SecurityIssueSeverity.HIGH
    ))

    policy.add_pattern(SecurityPattern(
        pattern=r"\bexec\s*\(",
        description="Dynamic code execution - extremely dangerous",
        severity=SecurityIssueSeverity.HIGH
    ))

    # Environment manipulation
    policy.add_pattern(SecurityPattern(
        pattern=r"os\.environ\[",
        description="Environment variable modification - restricted",
        severity=SecurityIssueSeverity.HIGH
    ))

    # Dangerous builtins
    policy.add_pattern(SecurityPattern(
        pattern=r"__builtins__",
        description="Access to builtins - potential security risk",
        severity=SecurityIssueSeverity.HIGH
    ))
