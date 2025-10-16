# -*- coding: utf-8 -*-

"""
AWS Lambda SQS message processing decorators.

This module provides decorators for processing SQS messages in Lambda functions
with automatic error handling and batch failure reporting using AWS Lambda's
partial batch response feature.

Type Aliases:
  - MessageHandler: Function that processes individual SQS messages/records.
  - LambdaHandler: Standard AWS Lambda handler function signature.
  - BatchResponse: Lambda response format for batch item failures.
  - DecoratedHandler: Lambda handler that returns batch failure information.
"""

from __future__ import annotations

from functools import wraps
from logging import Logger
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from core_aws.services.lambdas.events.base import EventRecord
from core_aws.typing import LambdaContext

# Type aliases for cleaner decorator signatures...
BatchResponse = Dict[str, List[Dict[str, str]]]
DecoratedHandler = Callable[[Dict[str, Any], LambdaContext], BatchResponse]
MessageHandler = Callable[[Union[EventRecord, Dict[str, Any]]], Any]
LambdaHandler = Callable[[Dict[str, Any], LambdaContext], Any]


def process_sqs_batch(
    message_handler: MessageHandler,
    logger: Logger,
    post_process_fcn: Optional[Callable[[], None]] = None,
) -> Callable[[LambdaHandler], DecoratedHandler]:
    """
    Process SQS messages with partial batch failure reporting (RECOMMENDED). This
    decorator implements AWS Lambda's partial batch response feature for SQS, which
    is the **recommended and safer approach** compared to manual message
    deletion. Failed messages are automatically returned to the queue
    for retry, while successful messages are deleted by Lambda.

    **IMPORTANT**: You must enable "Report batch item failures" in your Lambda
    trigger configuration for this decorator to work properly.

    References:
      - https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html#services-sqs-batchfailurereporting
      - https://repost.aws/knowledge-center/lambda-sqs-report-batch-item-failures

    :param message_handler:
        Function that processes each individual message (MessageHandler).
        Receives an EventRecord instance or Dict containing the message data.
        Should raise an exception if processing fails to mark the message
        for retry.

    :param logger:
        Logger instance for tracking message processing and errors.

    :param post_process_fcn:
        Optional cleanup function called after all messages are processed,
        regardless of success or failure (e.g., closing database connections,
        releasing resources). Receives no arguments and returns None.

    :return:
        Decorator function that transforms a LambdaHandler into a
        DecoratedHandler that returns batch failure information.

    Example:
        .. code-block:: python

            import logging
            from core_aws.services.lambdas.decorators import process_sqs_batch
            from core_aws.services.lambdas.events import SqsRecord

            logger = logging.getLogger(__name__)

            def process_message(record):
                \"\"\"Process individual SQS message.\"\"\"
                # Access message content
                message_data = json.loads(record.message)

                # Process the data
                result = do_something(message_data)

                # Raise exception on failure to mark message as failed
                if not result:
                    raise ValueError("Processing failed")

            def cleanup():
                \"\"\"Optional cleanup after batch processing.\"\"\"
                db_connection.close()

            @process_sqs_batch(
                message_handler=process_message,
                logger=logger,
                post_process_fcn=cleanup
            )
            def lambda_handler(event, context):
                \"\"\"
                Lambda handler - executed before processing messages.
                Body is optional - use for initialization if needed.
                \"\"\"
                logger.info("Lambda invoked")
                # Optional: initialization code here

            # Lambda returns:
            # {
            #     "batchItemFailures": [
            #         {"itemIdentifier": "failed-message-id-1"},
            #         {"itemIdentifier": "failed-message-id-2"}
            #     ]
            # }
        ..

    Benefits:
      1. **No manual deletion**: Lambda handles message deletion automatically
      2. **Safer**: Failed messages stay in queue for retry
      3. **Simpler**: No need to manage SQS client or queue URLs
      4. **AWS recommended**: Official pattern for SQS + Lambda
      5. **Better visibility**: CloudWatch metrics show batch failures

    Configuration:
      Enable "Report batch item failures" in Lambda trigger:
      1. Go to Lambda console > Your function > Configuration > Triggers
      2. Edit SQS trigger
      3. Expand "Additional settings"
      4. Enable "Report batch item failures"
      5. Save changes
    """

    def decorator(handler: LambdaHandler) -> DecoratedHandler:
        @wraps(handler)
        def execute(event: Dict[str, Any], context: LambdaContext) -> BatchResponse:
            logger.info("Starting the execution of handler function...")
            handler(event, context)

            logger.info("Processing the incoming event and the records within it...")
            batch_item_failures: List[Dict[str, str]] = []

            for raw_record in event.get("Records", []):
                record = EventRecord.from_dict(raw_record)

                if isinstance(record, EventRecord):
                    message_id = record.message_id

                else:
                    # Fallback for unknown event sources...
                    message_id = raw_record.get("messageId", "unknown")

                try:
                    logger.info(f"Processing message [{message_id}]...")
                    message_handler(record)
                    logger.info(f"Message [{message_id}] processed successfully!")

                except Exception as error:
                    # Add to failures, Lambda will not delete these messages...
                    batch_item_failures.append({"itemIdentifier": message_id})

                    logger.error({
                        "MessageId": message_id,
                        "error_type": type(error).__name__,
                        "error": str(error),
                    })

            if post_process_fcn:
                logger.info("Processing post process function...")
                post_process_fcn()

            logger.info(
                f"Execution Done! Successful: {len(event.get('Records', [])) - len(batch_item_failures)}, "
                f"Failed: {len(batch_item_failures)}."
            )

            return {"batchItemFailures": batch_item_failures}

        return execute

    return decorator
