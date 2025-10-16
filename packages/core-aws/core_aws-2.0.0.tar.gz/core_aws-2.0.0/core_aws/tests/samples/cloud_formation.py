# -*- coding: utf-8 -*-

from datetime import datetime


describe_stacks = {
    "Stacks": [
        {
            "StackId": "the_stack_id",
            "StackName": "the_stack_name",
            "ChangeSetId": "string",
            "Description": "string",
            "Parameters": [
                {
                    "ParameterKey": "string",
                    "ParameterValue": "string",
                    "UsePreviousValue": True,
                    "ResolvedValue": "string",
                },
            ],
            "CreationTime": datetime(2015, 1, 1),
            "DeletionTime": datetime(2015, 1, 1),
            "LastUpdatedTime": datetime(2015, 1, 1),
            "RollbackConfiguration": {
                "RollbackTriggers": [
                    {
                        "Arn": "string",
                        "Type": "string"
                    },
                ],
                "MonitoringTimeInMinutes": 123
            },
            "StackStatus": "CREATE_IN_PROGRESS",
            "StackStatusReason": "string",
            "DisableRollback": True,
            "NotificationARNs": [
                "string",
            ],
            "TimeoutInMinutes": 123,
            "Capabilities": [
                "CAPABILITY_IAM",
            ],
            "Outputs": [
                {
                    "OutputKey": "SomeKey",
                    "OutputValue": "SomeValue",
                    "Description": "SomeDescription",
                    "ExportName": "SomeExportName",
                },
            ],
            "RoleARN": "string",
            "Tags": [
                {
                    "Key": "string",
                    "Value": "string",
                },
            ],
            "EnableTerminationProtection": True,
            "ParentId": "string",
            "RootId": "string",
            "DriftInformation": {
                "StackDriftStatus": "DRIFTED",
                "LastCheckTimestamp": datetime(2015, 1, 1),
            },
            "RetainExceptOnCreate": True,
            "DeletionMode": "STANDARD",
            "DetailedStatus": "CONFIGURATION_COMPLETE",
        },
    ],
    "NextToken": "string",
}
