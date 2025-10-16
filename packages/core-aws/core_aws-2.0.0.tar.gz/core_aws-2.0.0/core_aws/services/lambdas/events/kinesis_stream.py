# -*- coding: utf-8 -*-

"""
AWS Lambda Kinesis Data Stream event record.

This module provides a wrapper for Kinesis Data Stream records received by
AWS Lambda functions, handling automatic base64 decoding of the data payload.
"""

import base64
from typing import Any
from typing import Dict

from .base import EventRecord
from .base import EventSource


class KinesisRecord(EventRecord):
    """
    Represents a record from AWS Kinesis Data Stream in
    a Lambda event. Automatically decodes base64-encoded Kinesis
    data and provides access to record metadata including
    sequence number, partition key, and event details.

    Example:
        .. code-block:: python

            # Lambda handler receiving Kinesis stream event
            def lambda_handler(event, context):
                for raw_record in event['Records']:
                    record = EventRecord.from_dict(raw_record)

                    if isinstance(record, KinesisRecord):
                        # Access decoded message
                        print(f"Message: {record.message}")

                        # Access Kinesis metadata
                        print(f"Sequence: {record.sequence_number}")
                        print(f"Partition Key: {record.partition_key}")
                        print(f"Shard ID: {record._kinesis['kinesisSchemaVersion']}")

            # Process JSON from Kinesis
            import json
            record = KinesisRecord.from_dict(kinesis_event_record)
            data = json.loads(record.message)
            process_event(data)
        ..
    """

    _source = EventSource.KINESIS_DATA_STREAM

    # noinspection PyPep8Naming
    def __init__(
        self,
        kinesis: Dict[str, Any],
        eventSource: str,
        eventVersion: str,
        eventID: str,
        eventName: str,
        invokeIdentityArn: str,
        awsRegion: str,
        eventSourceARN: str,
        **kwargs: Any
    ) -> None:
        """
        Initialize a Kinesis Data Stream event record.

        :param kinesis:
            Kinesis-specific data containing the record payload and metadata.
            Structure:

            .. code-block:: python

                {
                    "kinesisSchemaVersion": "1.0",
                    "partitionKey": "user-123",
                    "sequenceNumber": "49647175778160097793486557372840800878012000746547970050",
                    "data": "eyJldmVudCI6ICJsb2dpbiJ9",  # base64-encoded
                    "approximateArrivalTimestamp": 1702071427.66
                }
            ..

        :param eventSource: Source identifier (always "aws:kinesis" for Kinesis).
        :param eventVersion: Event format version.
        :param eventID: Unique event identifier (shard ID:sequence number).
        :param eventName: Event name (typically "aws:kinesis:record").
        :param invokeIdentityArn: ARN of the identity invoking the Lambda.
        :param awsRegion: AWS region where the stream exists.
        :param eventSourceARN: ARN of the Kinesis stream.
        :param kwargs: Additional fields (ignored, for forward compatibility).
        """

        self._aws_region = awsRegion
        self._invoke_identity_arn = invokeIdentityArn
        self._kinesis = kinesis

        self._event_name = eventName
        self._event_source = eventSource
        self._event_source_arn = eventSourceARN
        self._event_version = eventVersion
        self._event_id = eventID

    @property
    def message_id(self) -> str:
        """
        Get the unique event ID for this Kinesis record.

        :return:
            Event ID in format: "shardId-{timestamp}-{sequenceNumber}".
            Example: "shardId-000000000001:49590338271490256608559692538361571095921575989136588898"
        """
        return self._event_id

    @property
    def message(self) -> str:
        """
        Get the decoded message data from the Kinesis record. Automatically
        decodes the base64-encoded data field and returns it
        as a UTF-8 string.

        :return:
            Decoded message content. Often JSON-encoded string that needs further parsing.

        Example:
            .. code-block:: python

                record = KinesisRecord(...)
                message = record.message  # '{"event": "login", "user_id": 123}'

                # Parse JSON if needed
                import json
                data = json.loads(record.message)
                print(data['event'])  # "login"
            ..
        """
        return base64.b64decode(self._kinesis["data"]).decode()

    @property
    def sequence_number(self) -> str:
        """
        Get the sequence number for this Kinesis record.

        :return:
            Sequence number string. Used for ordering and checkpointing.
            Example: "49647175778160097793486557372840800878012000746547970050"
        """
        return self._kinesis["sequenceNumber"]

    @property
    def partition_key(self) -> str:
        """
        Get the partition key for this Kinesis record.

        :return:
            Partition key that determined which shard received this record.
            Example: "user-123"
        """
        return self._kinesis["partitionKey"]

    @property
    def approximate_arrival_timestamp(self) -> float:
        """
        Get the approximate arrival timestamp for this record.

        :return:
            Unix timestamp (seconds since epoch) when record arrived in the stream.
            Example: 1702071427.66
        """
        return self._kinesis["approximateArrivalTimestamp"]
