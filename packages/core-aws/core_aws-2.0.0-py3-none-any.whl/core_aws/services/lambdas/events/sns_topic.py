# -*- coding: utf-8 -*-

"""
AWS Lambda SNS topic event record.

This module provides a wrapper for SNS topic records received by AWS Lambda
functions, including access to message content, attributes, and metadata.
"""

from typing import Any
from typing import Dict
from typing import Optional

from .base import EventRecord
from .base import EventSource


class SnsRecord(EventRecord):
    """
    Represents a record from AWS SNS topic in a Lambda event.

    Provides access to SNS message content, attributes, subject, timestamp,
    and other metadata from notifications published to SNS topics.

    Example:
        .. code-block:: python

            # Lambda handler receiving SNS event
            def lambda_handler(event, context):
                for raw_record in event['Records']:
                    record = EventRecord.from_dict(raw_record)

                    if isinstance(record, SnsRecord):
                        # Access message content
                        print(f"Message: {record.message}")
                        print(f"Subject: {record.subject}")

                        # Access SNS metadata
                        print(f"Topic ARN: {record.topic_arn}")
                        print(f"Timestamp: {record.timestamp}")

                        # Access message attributes
                        if record.message_attributes:
                            for key, value in record.message_attributes.items():
                                print(f"Attribute {key}: {value}")

            # Process JSON from SNS
            import json
            record = SnsRecord.from_dict(sns_event_record)
            data = json.loads(record.message)
            process_notification(data)
        ..
    """

    _source = EventSource.SNS_TOPIC

    # noinspection PyPep8Naming
    def __init__(
        self,
        EventSource: str,
        EventSubscriptionArn: str,
        EventVersion: str,
        Sns: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """
        Initialize an SNS topic event record.

        :param EventSource: Source identifier (always "aws:sns" for SNS).
        :param EventSubscriptionArn: ARN of the SNS subscription that triggered this event.
        :param EventVersion: Event format version.

        :param Sns:
            SNS-specific data containing the message and metadata. Structure:

            .. code-block:: python

                {
                    "Type": "Notification",
                    "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                    "TopicArn": "arn:aws:sns:us-east-1:123456789012:my-topic",
                    "Subject": "Order Notification",
                    "Message": '{"order_id": 123, "status": "shipped"}',
                    "Timestamp": "2024-01-01T12:00:00.000Z",
                    "SignatureVersion": "1",
                    "Signature": "...",
                    "SigningCertUrl": "https://...",
                    "UnsubscribeUrl": "https://...",
                    "MessageAttributes": {
                        "priority": {
                            "Type": "String",
                            "Value": "high"
                        }
                    }
                }
            ..

        :param kwargs: Additional fields (ignored, for forward compatibility).
        """

        self._event_source = EventSource
        self._event_subscription_arn = EventSubscriptionArn
        self._event_version = EventVersion
        self._sns = Sns

    @property
    def message_id(self) -> str:
        """
        Get the unique message ID for this SNS notification.

        :return:
            SNS message ID (UUID format).
            Example: "95df01b4-ee98-5cb9-9903-4c221d41eb5e"
        """
        return self._sns["MessageId"]

    @property
    def message(self) -> str:
        """
        Get the message content from the SNS notification.

        :return:
            Message body. Often JSON-encoded string that needs further parsing.

        Example:
            .. code-block:: python

                record = SnsRecord(...)
                message = record.message  # '{"order_id": 123, "status": "shipped"}'

                # Parse JSON if needed
                import json
                data = json.loads(record.message)
                print(data['order_id'])  # 123
            ..
        """
        return self._sns["Message"]

    @property
    def topic_arn(self) -> str:
        """
        Get the ARN of the SNS topic that published this message.

        :return:
            SNS topic ARN.
            Example: "arn:aws:sns:us-east-1:123456789012:my-topic"
        """
        return self._sns["TopicArn"]

    @property
    def subject(self) -> Optional[str]:
        """
        Get the subject of the SNS notification (if provided).

        :return:
            Subject string or None if no subject was provided.
            Example: "Order Notification"
        """
        return self._sns.get("Subject")

    @property
    def timestamp(self) -> str:
        """
        Get the timestamp when the message was published.

        :return:
            ISO 8601 timestamp string.
            Example: "2024-01-01T12:00:00.000Z"
        """
        return self._sns["Timestamp"]

    @property
    def message_attributes(self) -> Dict[str, Any]:
        """
        Get the message attributes (custom metadata) from the SNS notification.

        :return:
            Dictionary of message attributes with structure:

            .. code-block:: python

                {
                    "attribute_name": {
                        "Type": "String" | "Number" | "Binary",
                        "Value": "attribute_value"
                    }
                }
            ..

            Returns empty dict if no attributes present.

        Example:
            .. code-block:: python

                record = SnsRecord(...)
                attrs = record.message_attributes

                if "priority" in attrs:
                    priority = attrs["priority"]["Value"]
                    print(f"Priority: {priority}")

                # Extract all string attributes
                for name, attr in attrs.items():
                    if attr["Type"] == "String":
                        print(f"{name}: {attr['Value']}")
            ..
        """
        return self._sns.get("MessageAttributes", {})
