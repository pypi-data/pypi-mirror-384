# -*- coding: utf-8 -*-

"""
Sample AWS Lambda event payloads for testing.

This module provides realistic example events for:
- SQS (Simple Queue Service)
- SNS (Simple Notification Service)
- Kinesis Data Streams

These samples match the actual event structures that AWS Lambda
functions receive when triggered by these services.
"""

from core_aws.typing.lambdas.events import KinesisEvent
from core_aws.typing.lambdas.events import SNSEvent
from core_aws.typing.lambdas.events import SQSEvent


# Example of an event payload received on Lambda coming
# from SQS queue...
SQS_EVENT: SQSEvent = {
    "Records": [
        {
            "messageId": "ae76a2d9-2064-40df-8dff-6aa9c3d10005",
            "receiptHandle": "AQEBP2si5WM8TgtuepI7mN+YJqIwm8Fermi7mEELXoLBFMFiEel9j+",
            "body": '{"value": 1}',
            "attributes": {
                "ApproximateReceiveCount": "2",
                "SentTimestamp": "1699540922291",
                "SenderId": "AROATQUBASLD2M2Y6MM3A:******",
                "ApproximateFirstReceiveTimestamp": "1699540982292"
            },
            "messageAttributes": {},
            "md5OfMessageAttributes": None,
            "md5OfBody": "1ff00094a5ba112cb7dd128e783d6803",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:******:SampleQueue",
            "awsRegion": "us-east-1"
        },
        {
            "messageId": "fd45b65d-b44f-4e91-b8bd-778f8ddb1601",
            "receiptHandle": "AQEB6Cnrp7qHg1fNCT12vt6N8hg85s6HQJcc2KOZ50qG6LJQZ+",
            "body": '{"value":2}',
            "attributes": {
                "ApproximateReceiveCount": "2",
                "SentTimestamp": "1699540928208",
                "SenderId": "AROATQUBASLD2M2Y6MM3A:******",
                "ApproximateFirstReceiveTimestamp": "1699540988209",
            },
            "messageAttributes": {},
            "md5OfMessageAttributes": None,
            "md5OfBody": "5d872de403edb944a7b10450eda2f46a",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:******:SampleQueue",
            "awsRegion": "us-east-1",
        },
    ]
}


# Example of an event payload received on Lambda coming
# from SNS topic...
SNS_EVENT: SNSEvent = {
    "Records": [
        {
            "EventSource": "aws:sns",
            "EventVersion": "1.0",
            "EventSubscriptionArn": "arn:aws:sns:us-east-1:******:SampleTopic:b7cfd752-05a9-4155-a1eb-6c9552a50d5b",
            "Sns": {
                "Type": "Notification",
                "MessageId": "33089596-71cb-5270-926e-c8516313cfc8",
                "TopicArn": "arn:aws:sns:us-east-1:******:SampleTopic",
                "Subject": None,
                "Message": '{"value": 1}',
                "Timestamp": "2023-11-09T17:02:16.286Z",
                "SignatureVersion": "1",
                "Signature": "QKgmQUcfzypgriomDr7NuUzQV==",
                "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-******.pem",
                "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:******:SampleTopic:b7cfd752-05a9-4155-a1eb-6c9552a50d5b",
                "MessageAttributes": {},
            },
        },
    ]
}


# Example of an event payload received on Lambda coming
# from Kinesis Data Stream...
KINESIS_EVENT: KinesisEvent = {
    "Records": [
        {
            "kinesis": {
                "kinesisSchemaVersion": "1.0",
                "partitionKey": "binlog",
                "sequenceNumber": "49647175778160097793486557372840800878012000746547970050",
                "data": "eyJldmVudF90aW1lc3RhbXAiOiAxNzAxNDY4MjkwLCAiZXZlbnRfdHlwZSI6ICJJTlNFUlQiLCAiZ3RpZCI6IG51bGwsICJzZXJ2aWNlIjogImJpbmxvZy1wcm9jZXNzb3IiLCAic291cmNlIjogImJpbmxvZy4wMDAwMDEiLCAicG9zaXRpb24iOiAxOTA0LCAicHJpbWFyeV9rZXkiOiAicGVyc29uX2lkIiwgInNjaGVtYV9uYW1lIjogInNvdXJjZSIsICJ0YWJsZV9uYW1lIjogInBlcnNvbiIsICJhdHRycyI6IHsicGVyc29uX2lkIjogMSwgImZpcnN0X25hbWUiOiAiSm9obiIsICJsYXN0X25hbWUiOiAiRG9lIiwgImRhdGVfb2ZfYmlydGgiOiAiMTk5MC0wMS0xNSIsICJlbWFpbCI6ICJqb2huLmRvZUBlbWFpbC5jb20iLCAiYWRkcmVzcyI6ICIxMjMgTWFpbiBTdCIsICJjcmVhdGVkX29uIjogIjIwMjMtMTItMDFUMjI6MDQ6NTAiLCAidXBkYXRlZF9vbiI6ICIyMDIzLTEyLTAxVDIyOjA0OjUwIn19",
                "approximateArrivalTimestamp": 1702071427.66
            },
            "eventSource": "aws:kinesis",
            "eventVersion": "1.0",
            "eventID": "shardId-000000000000:49647175778160097793486557372840800878012000746547970050",
            "eventName": "aws:kinesis:record",
            "invokeIdentityArn": "arn:aws:iam::******:role/service-role/test-role",
            "awsRegion": "us-east-1",
            "eventSourceARN": "arn:aws:kinesis:us-east-1:******:stream/test",
        },
    ]
}


__all__ = [
    "SQS_EVENT",
    "SNS_EVENT",
    "KINESIS_EVENT",
]
