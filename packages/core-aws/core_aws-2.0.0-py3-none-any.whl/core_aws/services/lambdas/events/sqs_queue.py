# -*- coding: utf-8 -*-

"""
AWS Lambda SQS queue event record.

This module provides a wrapper for SQS queue records received by AWS Lambda
functions, including access to message body, attributes, and receipt handles.
"""

from typing import Any
from typing import Dict

from .base import EventRecord
from .base import EventSource


class SqsRecord(EventRecord):
    """
    Represents a record from AWS SQS queue in a Lambda event.

    Provides access to SQS message body, attributes, receipt handle, and
    metadata from messages pulled from SQS queues. The receipt handle can
    be used to delete the message after processing.

    Example:
        .. code-block:: python

            # Lambda handler receiving SQS event
            def lambda_handler(event, context):
                for raw_record in event['Records']:
                    record = EventRecord.from_dict(raw_record)

                    if isinstance(record, SqsRecord):
                        # Access message content
                        print(f"Message: {record.message}")
                        print(f"Message ID: {record.message_id}")

                        # Access SQS metadata
                        print(f"Queue ARN: {record.queue_arn}")
                        print(f"Receipt Handle: {record.receipt_handle}")

                        # Access message attributes
                        if record.message_attributes:
                            for key, value in record.message_attributes.items():
                                print(f"Attribute {key}: {value}")

                        # Access system attributes
                        sent_timestamp = record.attributes.get("SentTimestamp")
                        print(f"Sent at: {sent_timestamp}")

            # Process JSON from SQS
            import json
            record = SqsRecord.from_dict(sqs_event_record)
            data = json.loads(record.message)
            process_message(data)
        ..
    """

    _source = EventSource.SQS_QUEUE

    # noinspection PyPep8Naming
    def __init__(
        self,
        eventSource: str,
        eventSourceARN: str,
        awsRegion: str,
        messageId: str,
        receiptHandle: str,
        body: str,
        md5OfBody: str,
        attributes: Dict[str, Any],
        md5OfMessageAttributes: str,
        messageAttributes: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """
        Initialize an SQS queue event record.

        :param eventSource: Source identifier (always "aws:sqs" for SQS).
        :param eventSourceARN: ARN of the SQS queue.
        :param awsRegion: AWS region where the queue exists.
        :param messageId: Unique message identifier.
        :param receiptHandle: Receipt handle for deleting the message.
        :param body: Message body content (often JSON-encoded).
        :param md5OfBody: MD5 hash of the message body.

        :param attributes:
            System attributes containing message metadata. Common attributes:

            .. code-block:: python

                {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1702071427000",
                    "SenderId": "AIDAIT2UOQQY3AUEKVGXU",
                    "ApproximateFirstReceiveTimestamp": "1702071427000"
                }
            ..

        :param md5OfMessageAttributes: MD5 hash of message attributes.

        :param messageAttributes:
            Custom message attributes. Structure:

            .. code-block:: python

                {
                    "attribute_name": {
                        "stringValue": "value",
                        "dataType": "String"
                    }
                }
            ..

        :param kwargs: Additional fields (ignored, for forward compatibility).
        """

        self._event_source = eventSource
        self._event_source_arn = eventSourceARN
        self._aws_region = awsRegion

        self._message_id = messageId
        self._receipt_handle = receiptHandle
        self._body = body

        self._attributes = attributes
        self._messageAttributes = messageAttributes

        self._md5_of_body = md5OfBody
        self._md5OfMessageAttributes = md5OfMessageAttributes

    @property
    def message_id(self) -> str:
        """
        Get the unique message ID for this SQS message.

        :return:
            SQS message ID (UUID format).
            Example: "19dd0b57-b21e-4ac1-bd88-01bbb068cb78"
        """
        return self._message_id

    @property
    def message(self) -> str:
        """
        Get the message body from the SQS message.

        :return:
            Message body. Often JSON-encoded string that needs further parsing.

        Example:
            .. code-block:: python

                record = SqsRecord(...)
                message = record.message  # '{"order_id": 123, "status": "pending"}'

                # Parse JSON if needed
                import json
                data = json.loads(record.message)
                print(data['order_id'])  # 123
            ..
        """
        return self._body

    @property
    def receipt_handle(self) -> str:
        """
        Get the receipt handle for this SQS message.

        The receipt handle is required to delete the message from the queue
        after processing. Each time a message is received, a new receipt
        handle is provided.

        :return:
            Receipt handle string (opaque token).
            Example: "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a..."

        Example:
            .. code-block:: python

                from boto3 import client

                sqs = client('sqs')
                record = SqsRecord(...)

                # Delete message after processing
                sqs.delete_message(
                    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789012/my-queue',
                    ReceiptHandle=record.receipt_handle
                )
            ..
        """
        return self._receipt_handle

    @property
    def queue_arn(self) -> str:
        """
        Get the ARN of the SQS queue that this message came from.

        :return:
            SQS queue ARN.
            Example: "arn:aws:sqs:us-east-1:123456789012:my-queue"
        """
        return self._event_source_arn

    @property
    def attributes(self) -> Dict[str, Any]:
        """
        Get the system attributes for this SQS message.

        System attributes contain metadata about the message such as
        timestamps, sender information, and receive count.

        :return:
            Dictionary of system attributes:

            .. code-block:: python

                {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1702071427000",
                    "SenderId": "AIDAIT2UOQQY3AUEKVGXU",
                    "ApproximateFirstReceiveTimestamp": "1702071427000"
                }
            ..

        Example:
            .. code-block:: python

                record = SqsRecord(...)

                # Check how many times message was received
                receive_count = int(record.attributes.get("ApproximateReceiveCount", "0"))
                if receive_count > 3:
                    print("Message has been received multiple times")

                # Get sent timestamp
                sent_ts = record.attributes.get("SentTimestamp")
                print(f"Sent at: {sent_ts}")
            ..
        """
        return self._attributes

    @property
    def message_attributes(self) -> Dict[str, Any]:
        """
        Get the custom message attributes for this SQS message.

        Message attributes are custom metadata set by the message producer.

        :return:
            Dictionary of message attributes with structure:

            .. code-block:: python

                {
                    "attribute_name": {
                        "stringValue": "value",
                        "dataType": "String"
                    }
                }
            ..

            Returns empty dict if no attributes present.

        Example:
            .. code-block:: python

                record = SqsRecord(...)
                attrs = record.message_attributes

                # Check for priority attribute
                if "priority" in attrs:
                    priority = attrs["priority"]["stringValue"]
                    print(f"Priority: {priority}")

                # Extract all string attributes
                for name, attr in attrs.items():
                    if attr["dataType"] == "String":
                        print(f"{name}: {attr['stringValue']}")
            ..
        """
        return self._messageAttributes

    @property
    def md5_of_body(self) -> str:
        """
        Get the MD5 hash of the message body.

        Can be used to verify message integrity.

        :return:
            MD5 hash string.
            Example: "098f6bcd4621d373cade4e832627b4f6"
        """
        return self._md5_of_body
