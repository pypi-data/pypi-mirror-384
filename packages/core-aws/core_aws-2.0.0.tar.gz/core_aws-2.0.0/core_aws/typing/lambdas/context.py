# -*- coding: utf-8 -*-

import time
from dataclasses import dataclass
from dataclasses import field
from typing import Any, Dict
from typing import Optional

from core_aws.typing.cognito.identity import CognitoIdentity
from core_aws.typing.mobile.client import MobileClient


@dataclass(frozen=True)
class ClientContext:
    """
    Client context that's provided to Lambda by the
    client application.
    """

    client: MobileClient
    """Client context that's provided to Lambda by the client application."""

    custom: Dict[str, Any]
    """Custom values set by the mobile client application."""

    env: Dict[str, Any]
    """Environment information provided by the AWS SDK."""


@dataclass
class LambdaContext:
    """
    Provides methods and properties that provide information
    about the invocation, function, and
    execution environment.
    """

    function_name: str
    """The name of the Lambda function."""

    function_version: str
    """The version of the function."""

    invoked_function_arn: str
    """
    The Amazon Resource Name (ARN) that's used to invoke the function.
    Indicates if the invoker specified a version number or alias.
    """

    memory_limit_in_mb: int
    """The amount of memory that's allocated for the function."""

    aws_request_id: str
    """The identifier of the invocation request."""

    log_group_name: str
    """The log group for the function."""

    log_stream_name: str
    """The log stream for the function instance."""

    timeout_seconds: int = 900
    """The function timeout in seconds (default: 900s / 15 minutes)."""

    identity: Optional[CognitoIdentity] = None
    """Information about the Amazon Cognito identity that authorized the request (mobile apps)."""

    client_context: Optional[ClientContext] = None
    """Client context that's provided to Lambda by the client application (mobile apps)."""

    _start_time_ms: int = field(
        default_factory=lambda: int(time.time() * 1000),
        init=False,
        repr=False
    )
    """Internal: Track execution start time for timeout calculation."""

    _timeout_ms: int = field(init=False, repr=False)
    """Internal: Calculated timeout in milliseconds."""

    def __post_init__(self) -> None:
        """Initialize calculated fields after dataclass initialization."""
        self._timeout_ms = self.timeout_seconds * 1000

    def get_remaining_time_in_millis(self) -> int:
        """
        Returns the number of milliseconds left before the execution times out.
        :return: Remaining time in milliseconds. Returns 0 if timeout has been exceeded.
        """

        current_time_ms = int(time.time() * 1000)
        elapsed_ms = current_time_ms - self._start_time_ms
        remaining_ms = self._timeout_ms - elapsed_ms
        return max(0, remaining_ms)
