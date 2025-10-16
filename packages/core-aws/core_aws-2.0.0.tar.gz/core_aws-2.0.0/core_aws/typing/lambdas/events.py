# -*- coding: utf-8 -*-

"""
AWS Lambda event type definitions.

This module provides TypedDict definitions for Lambda events from various AWS services:
- SQS (Simple Queue Service)
- SNS (Simple Notification Service)
- Kinesis Data Streams

These types match the actual event structures that AWS Lambda functions receive.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TypedDict


# SQS Event Types
class SQSMessageAttributes(TypedDict):
    """SQS message attributes from the queue."""

    ApproximateReceiveCount: str
    """Number of times a message has been received but not deleted."""

    SentTimestamp: str
    """Time when the message was sent (epoch milliseconds)."""

    SenderId: str
    """AWS account ID or IAM role ID of the sender."""

    ApproximateFirstReceiveTimestamp: str
    """Time when the message was first received (epoch milliseconds)."""


class SQSRecord(TypedDict):
    """A single SQS message record in a Lambda event."""

    messageId: str
    """Unique identifier for the message."""

    receiptHandle: str
    """Token for deleting the message from the queue."""

    body: str
    """Message body (usually JSON string)."""

    attributes: SQSMessageAttributes
    """SQS message attributes."""

    messageAttributes: Dict[str, Any]
    """Custom message attributes."""

    md5OfMessageAttributes: Optional[str]
    """MD5 hash of the message attributes."""

    md5OfBody: str
    """MD5 hash of the message body."""

    eventSource: str
    """Event source identifier (always 'aws:sqs')."""

    eventSourceARN: str
    """ARN of the source SQS queue."""

    awsRegion: str
    """AWS region where the queue is located."""


class SQSEvent(TypedDict):
    """Lambda event from SQS queue trigger."""

    Records: List[SQSRecord]
    """List of SQS message records (batch)."""


# SNS Event Types
class SNSMessage(TypedDict):
    """SNS message details within a Lambda event."""

    Type: str
    """Message type (usually 'Notification')."""

    MessageId: str
    """Unique identifier for the message."""

    TopicArn: str
    """ARN of the SNS topic."""

    Subject: Optional[str]
    """Optional message subject."""

    Message: str
    """Message body (usually JSON string)."""

    Timestamp: str
    """ISO 8601 timestamp when the message was published."""

    SignatureVersion: str
    """Version of the signature algorithm."""

    Signature: str
    """Message signature for verification."""

    SigningCertUrl: str
    """URL to the signing certificate."""

    UnsubscribeUrl: str
    """URL to unsubscribe from the topic."""

    MessageAttributes: Dict[str, Any]
    """Custom message attributes."""


class SNSRecord(TypedDict):
    """A single SNS notification record in a Lambda event."""

    EventSource: str
    """Event source identifier (always 'aws:sns')."""

    EventVersion: str
    """Event format version."""

    EventSubscriptionArn: str
    """ARN of the subscription that triggered the Lambda."""

    Sns: SNSMessage
    """SNS message details."""


class SNSEvent(TypedDict):
    """Lambda event from SNS topic trigger."""

    Records: List[SNSRecord]
    """List of SNS notification records."""


class KinesisData(TypedDict):
    """Kinesis stream record data."""

    kinesisSchemaVersion: str
    """Schema version of the Kinesis data structure."""

    partitionKey: str
    """Partition key for the record."""

    sequenceNumber: str
    """Unique sequence number for the record in the shard."""

    data: str
    """Base64-encoded data blob."""

    approximateArrivalTimestamp: float
    """Approximate time when the record was added to the stream (Unix timestamp)."""


class KinesisRecord(TypedDict):
    """A single Kinesis stream record in a Lambda event."""

    kinesis: KinesisData
    """Kinesis stream data."""

    eventSource: str
    """Event source identifier (always 'aws:kinesis')."""

    eventVersion: str
    """Event format version."""

    eventID: str
    """Unique event identifier."""

    eventName: str
    """Event name (usually 'aws:kinesis:record')."""

    invokeIdentityArn: str
    """ARN of the IAM role used to invoke the Lambda function."""

    awsRegion: str
    """AWS region where the stream is located."""

    eventSourceARN: str
    """ARN of the Kinesis stream."""


class KinesisEvent(TypedDict):
    """Lambda event from Kinesis Data Streams trigger."""

    Records: List[KinesisRecord]
    """List of Kinesis stream records."""


__all__ = [
    # SQS types...
    "SQSEvent",
    "SQSRecord",
    "SQSMessageAttributes",
    # SNS types...
    "SNSEvent",
    "SNSRecord",
    "SNSMessage",
    # Kinesis types...
    "KinesisEvent",
    "KinesisRecord",
    "KinesisData",
]
