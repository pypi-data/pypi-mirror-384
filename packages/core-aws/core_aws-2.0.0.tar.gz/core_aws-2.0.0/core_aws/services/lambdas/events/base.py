# -*- coding: utf-8 -*-

"""
AWS Lambda event record base classes and utilities.

This module provides base classes for handling AWS Lambda event records from
various sources (Kinesis, SQS, SNS). It implements a factory pattern that
automatically instantiates the correct record type based on the event source.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from enum import Enum
from typing import Any
from typing import Dict
from typing import Type

from core_mixins import Self


class EventSource(str, Enum):
    """
    AWS event source identifiers for Lambda function triggers.

    These values correspond to the "eventSource" or "EventSource" field
    in Lambda event records.
    """

    KINESIS_DATA_STREAM = "aws:kinesis"
    SNS_TOPIC = "aws:sns"
    SQS_QUEUE = "aws:sqs"


class EventRecord(ABC):
    """
    Abstract base class for AWS Lambda event records.

    This class provides a factory pattern for creating specific record types
    (SqsRecord, SnsRecord, KinesisRecord) based on the event source. Subclasses
    are automatically registered when defined with a `_source` attribute.

    The factory pattern allows automatic deserialization of Lambda event records:

    Example:
        .. code-block:: python

            # Lambda handler receiving SQS event
            def lambda_handler(event, context):
                for raw_record in event['Records']:
                    # Factory automatically creates SqsRecord instance
                    record = EventRecord.from_dict(raw_record)

                    # Access common interface
                    print(f"Message ID: {record.message_id}")
                    print(f"Body: {record.message}")

                    # Type-specific access
                    if isinstance(record, SqsRecord):
                        print(f"Receipt Handle: {record._receipt_handle}")

            # Or handle unknown event sources gracefully
            record = EventRecord.from_dict(raw_record)
            if isinstance(record, dict):
                # Unknown source - got raw dict back
                print(f"Unknown event source: {record.get('eventSource')}")
            else:
                # Known source - got EventRecord subclass
                process_message(record.message)
        ..

    Subclass Implementation:
        To create a new event record type:

        .. code-block:: python

            class CustomRecord(EventRecord):
                _source = EventSource.SQS_QUEUE  # Register with factory

                def __init__(self, messageId: str, body: str, **kwargs):
                    self._message_id = messageId
                    self._body = body

                @property
                def message_id(self) -> str:
                    return self._message_id

                @property
                def message(self) -> str:
                    return self._body
        ..
    """

    _subclasses: Dict[str, Type[Self]] = {}
    _source: EventSource

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Register subclass in the factory registry.

        Automatically called when a subclass is defined. Registers the subclass
        with its associated event source for use in the factory pattern.

        :param kwargs: Additional keyword arguments passed to parent __init_subclass__.
        """

        super().__init_subclass__(**kwargs)
        cls._subclasses[cls._source] = cls  # type: ignore[assignment]

    @property
    @abstractmethod
    def message_id(self) -> str:
        """
        Get the unique identifier for this message/record.
        :return: Message ID string (format varies by event source).

        Example:
          - SQS: "19dd0b57-b21e-4ac1-bd88-01bbb068cb78"
          - SNS: "95df01b4-ee98-5cb9-9903-4c221d41eb5e"
          - Kinesis: Sequence number
        """

    @property
    @abstractmethod
    def message(self) -> str:
        """
        Get the message payload/body.
        :return: Message content as string (may be JSON-encoded).

        Example:
          - SQS: Body field content
          - SNS: Message field content
          - Kinesis: Base64-decoded data
        """

    @classmethod
    def from_dict(
        cls,
        message: Dict[str, Any],
    ) -> Self | Dict[str, Any]:
        """
        Factory method to create appropriate EventRecord subclass
        from raw event data. Inspects the "eventSource" or "EventSource" field
        to determine the correct record type, then instantiates and returns
        it. If the event source is not recognized, returns the raw
        dictionary unchanged.

        :param message:
            Raw event record dictionary from Lambda event. Must contain
            "eventSource" or "EventSource" field.

        :return:
            - EventRecord subclass instance if source is recognized
            - Raw dict if event source is unknown/unsupported

        Example:
            .. code-block:: python

                # SQS event record
                sqs_record = {
                    "eventSource": "aws:sqs",
                    "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
                    "body": '{"order_id": 123}',
                    "receiptHandle": "AQEBwJ...",
                    # ... other fields
                }

                record = EventRecord.from_dict(sqs_record)
                # Returns: SqsRecord instance
                print(record.message_id)  # "19dd0b57-b21e-4ac1-bd88-01bbb068cb78"
                print(record.message)     # '{"order_id": 123}'

                # Unknown event source
                unknown_record = {
                    "eventSource": "aws:unknown",
                    "data": "something"
                }

                record = EventRecord.from_dict(unknown_record)
                # Returns: Dict (unchanged)
                print(record)  # {"eventSource": "aws:unknown", "data": "something"}

                # Batch processing in Lambda
                def lambda_handler(event, context):
                    for raw_record in event['Records']:
                        record = EventRecord.from_dict(raw_record)

                        if isinstance(record, dict):
                            # Unrecognized source
                            logger.warning(f"Unknown source: {record.get('eventSource')}")
                            continue

                        # Process recognized record types
                        process_message(record.message_id, record.message)
            ..
        """

        # Try to get event source from either field name variation
        event_source = message.get("eventSource", "") or message.get("EventSource", "")
        cls_ = cls._subclasses.get(event_source)
        if not cls_:
            return message

        return cls_(**message)
