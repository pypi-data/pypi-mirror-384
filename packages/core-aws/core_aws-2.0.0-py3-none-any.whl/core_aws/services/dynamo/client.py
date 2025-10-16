# -*- coding: utf-8 -*-

"""
AWS DynamoDB client wrapper.

This module provides a high-level interface for interacting with AWS DynamoDB,
including item operations like get_item and update_item with automatic error handling.
"""

from typing import Any, Dict

from core_aws.services.base import AwsClient, AwsClientException


class DynamoDbClient(AwsClient):
    """
    Client for AWS DynamoDB.

    This client provides methods for interacting with DynamoDB tables,
    including retrieving and updating items. Supports both single-item
    operations and conditional updates with automatic error handling.

    Example:
        .. code-block:: python

            # Initialize client
            dynamodb = DynamoDbClient(region="us-east-1")

            # Get item by primary key
            response = dynamodb.get_item(
                table="Users",
                key={"userId": {"S": "user123"}}
            )
            if "Item" in response:
                print(f"User: {response['Item']}")

            # Update item with conditional expression
            dynamodb.update_item(
                table="Users",
                key={"userId": {"S": "user123"}},
                update_expression="SET #name = :name, lastLogin = :timestamp",
                expression_attribute_values={
                    ":name": {"S": "John Doe"},
                    ":timestamp": {"N": "1609459200"}
                },
                ExpressionAttributeNames={"#name": "name"}
            )
        ..
    """

    client: "mypy_boto3_dynamodb.client.DynamoDBClient"  # type: ignore[name-defined]

    def __init__(self, region: str, **kwargs: Any) -> None:
        """
        Initialize the DynamoDB client.

        :param region: AWS region name (e.g., 'us-east-1', 'eu-west-1').
        :param kwargs: Additional arguments passed to boto3.client().
        """
        super().__init__("dynamodb", region_name=region, **kwargs)

    def get_item(
        self,
        table: str,
        key: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Retrieve an item from a DynamoDB table by primary key. Returns
        all attributes for the item with the specified primary key. If no
        matching item exists, the response will not contain an "Item" field.
        Uses eventually consistent reads by default.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/get_item.html

        :param table: Name of the DynamoDB table.

        :param key:
            Primary key of the item to retrieve. Must include partition key
            and sort key (if table has one). Format:

            .. code-block:: python

                # Table with partition key only
                {"userId": {"S": "user123"}}

                # Table with partition + sort key
                {"userId": {"S": "user123"}, "timestamp": {"N": "1609459200"}}
            ..

        :param kwargs:
            Additional boto3 parameters:

            - **ConsistentRead** (bool):
                Use strongly consistent read instead of eventually consistent.
                Default: False.

            - **ProjectionExpression** (str):
                Comma-separated list of attributes to retrieve.
                Example: "username, email, lastLogin"

            - **ExpressionAttributeNames** (dict):
                Substitution tokens for attribute names in expressions.
                Example: {"#n": "name"} (use when attribute is reserved word)

            - **ReturnConsumedCapacity** (str):
                Return capacity info: "INDEXES", "TOTAL", or "NONE".

        :return:
            Dictionary containing item data (if found) and metadata:

            .. code-block:: python

                {
                    "Item": {  # Present only if item exists
                        "userId": {"S": "user123"},
                        "username": {"S": "john_doe"},
                        "email": {"S": "john@example.com"},
                        "loginCount": {"N": "42"},
                        "tags": {"SS": ["premium", "verified"]},
                        "metadata": {
                            "M": {
                                "created": {"N": "1609459200"},
                                "updated": {"N": "1640995200"}
                            }
                        },
                        "active": {"BOOL": True}
                    },
                    "ConsumedCapacity": {  # If ReturnConsumedCapacity specified
                        "TableName": "Users",
                        "CapacityUnits": 0.5
                    }
                }
            ..

        :raises AwsClientException: If the operation fails.

        Example:
            .. code-block:: python

                dynamodb = DynamoDbClient(region="us-east-1")

                # Get item by partition key
                response = dynamodb.get_item(
                    table="Users",
                    key={"userId": {"S": "user123"}}
                )

                if "Item" in response:
                    user = response["Item"]
                    print(f"Username: {user['username']['S']}")
                else:
                    print("User not found")

                # Get item with consistent read
                response = dynamodb.get_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    ConsistentRead=True
                )

                # Get specific attributes only
                response = dynamodb.get_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    ProjectionExpression="username, email, lastLogin"
                )

                # Get item from table with partition + sort key
                response = dynamodb.get_item(
                    table="OrderHistory",
                    key={
                        "userId": {"S": "user123"},
                        "orderId": {"S": "order-456"}
                    }
                )

                # Use attribute name substitution (when attribute is reserved word)
                response = dynamodb.get_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    ProjectionExpression="#n, email",
                    ExpressionAttributeNames={"#n": "name"}
                )
            ..
        """

        try:
            return self.client.get_item(TableName=table, Key=key, **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error

    def update_item(
        self,
        table: str,
        key: Dict[str, Any],
        expression_attribute_values: Dict[str, Any],
        update_expression: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Update an existing item's attributes in a DynamoDB table.

        Modifies an existing item or creates a new item if it doesn't exist.
        Supports SET, REMOVE, ADD, and DELETE operations on attributes.
        Can perform conditional updates and return old/new attribute values.

        Reference:
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb/client/update_item.html

        :param table: Name of the DynamoDB table.

        :param key:
            Primary key of the item to update (partition key + sort key if applicable).
            Example: {"userId": {"S": "user123"}}

        :param expression_attribute_values:
            Values to substitute in the update expression. Must be prefixed with colon (:).
            Example: {":name": {"S": "John"}, ":count": {"N": "1"}}

        :param update_expression:
            Expression defining how to update the item. Supports:
              - SET: Set attribute value
              - REMOVE: Remove attribute
              - ADD: Increment number or add to set
              - DELETE: Remove from set

            Example: "SET #name = :name, loginCount = loginCount + :count"

        :param kwargs:
            Additional boto3 parameters:

            - **ConditionExpression** (str):
                Condition that must be true for update to proceed.
                Example: "attribute_exists(userId)" or "version = :oldVersion"

            - **ExpressionAttributeNames** (dict):
                Substitution tokens for attribute names (use for reserved words).
                Example: {"#name": "name", "#status": "status"}

            - **ReturnValues** (str):
                What values to return: "NONE" (default), "ALL_OLD", "UPDATED_OLD",
                "ALL_NEW", "UPDATED_NEW".

            - **ReturnConsumedCapacity** (str):
                Return capacity info: "INDEXES", "TOTAL", or "NONE".

            - **ReturnItemCollectionMetrics** (str):
                Return collection metrics: "SIZE" or "NONE".

        :return:
            Dictionary containing updated attributes (based on ReturnValues):

            .. code-block:: python

                {
                    "Attributes": {  # Present based on ReturnValues
                        "userId": {"S": "user123"},
                        "username": {"S": "john_doe"},
                        "loginCount": {"N": "43"},
                        "lastLogin": {"N": "1640995200"}
                    },
                    "ConsumedCapacity": {  # If ReturnConsumedCapacity specified
                        "TableName": "Users",
                        "CapacityUnits": 1.0
                    }
                }
            ..

        :raises AwsClientException: If the operation fails or condition is not met.

        Example:
            .. code-block:: python

                dynamodb = DynamoDbClient(region="us-east-1")

                # Simple SET operation
                dynamodb.update_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    update_expression="SET lastLogin = :timestamp",
                    expression_attribute_values={
                        ":timestamp": {"N": "1640995200"}
                    }
                )

                # Multiple operations with attribute name substitution
                dynamodb.update_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    update_expression="SET #name = :name, email = :email, loginCount = loginCount + :inc",
                    expression_attribute_values={
                        ":name": {"S": "John Doe"},
                        ":email": {"S": "john@example.com"},
                        ":inc": {"N": "1"}
                    },
                    ExpressionAttributeNames={
                        "#name": "name"  # 'name' is a reserved word
                    }
                )

                # Conditional update with return values
                response = dynamodb.update_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    update_expression="SET accountBalance = accountBalance - :amount",
                    expression_attribute_values={
                        ":amount": {"N": "50"},
                        ":min": {"N": "0"}
                    },
                    ConditionExpression="accountBalance >= :min",
                    ReturnValues="ALL_NEW"
                )
                print(f"New balance: {response['Attributes']['accountBalance']['N']}")

                # REMOVE operation
                dynamodb.update_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    update_expression="REMOVE temporaryToken",
                    expression_attribute_values={}
                )

                # ADD to set
                dynamodb.update_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    update_expression="ADD tags :newTag",
                    expression_attribute_values={
                        ":newTag": {"SS": ["premium"]}
                    }
                )

                # Complex update with multiple clauses
                dynamodb.update_item(
                    table="Users",
                    key={"userId": {"S": "user123"}},
                    update_expression="SET #status = :active, updatedAt = :now REMOVE oldField ADD loginCount :one",
                    expression_attribute_values={
                        ":active": {"S": "ACTIVE"},
                        ":now": {"N": "1640995200"},
                        ":one": {"N": "1"}
                    },
                    ExpressionAttributeNames={
                        "#status": "status"
                    },
                    ReturnValues="UPDATED_NEW"
                )
            ..
        """

        try:
            return self.client.update_item(
                TableName=table,
                Key=key,
                ExpressionAttributeValues=expression_attribute_values,
                UpdateExpression=update_expression,
                **kwargs)

        except Exception as error:
            raise AwsClientException(error) from error
