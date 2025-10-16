# -*- coding: utf-8 -*-

"""
AWS Lambda type definitions.

This module provides type definitions for AWS Lambda contexts and events.
"""

from .context import ClientContext, LambdaContext

from .events import (
    KinesisData,
    KinesisEvent,
    KinesisRecord,
    SNSEvent,
    SNSMessage,
    SNSRecord,
    SQSEvent,
    SQSMessageAttributes,
    SQSRecord,
)

__all__ = [
    # Context types...
    "ClientContext",
    "LambdaContext",
    # Event types - SQS...
    "SQSEvent",
    "SQSRecord",
    "SQSMessageAttributes",
    # Event types - SNS...
    "SNSEvent",
    "SNSRecord",
    "SNSMessage",
    # Event types - Kinesis...
    "KinesisEvent",
    "KinesisRecord",
    "KinesisData",
]
