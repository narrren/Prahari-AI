import boto3
import time
import os

# Configuration for LocalStack
AWS_REGION = "us-east-1"
ENDPOINT_URL = "http://localhost:4566"

# Initialize DynamoDB client
dynamodb = boto3.client(
    'dynamodb',
    region_name=AWS_REGION,
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

def create_table(table_name, key_schema, attribute_definitions, provisioning):
    try:
        print(f"DTO: Creating table {table_name}...")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            ProvisionedThroughput=provisioning
        )
        print(f"Success: Table {table_name} status: {table['TableDescription']['TableStatus']}")
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print(f"Info: Table {table_name} already exists.")
        else:
            print(f"Error creating {table_name}: {e}")

def setup_infrastructure():
    print("Initializing Prahari-AI Database Schema on LocalStack...")

    # 1. Tourists Table (Profile & DID mapping)
    # PK: did (String)
    create_table(
        table_name='Prahari_Tourists',
        key_schema=[
            {'AttributeName': 'did', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'did', 'AttributeType': 'S'}
        ],
        provisioning={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    # 2. Telemetry Table (Real-time tracking data)
    # PK: device_id (String), SK: timestamp (Number)
    # TTL: Enabled for auto-archiving (simulated)
    create_table(
        table_name='Prahari_Telemetry',
        key_schema=[
            {'AttributeName': 'device_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        attribute_definitions=[
            {'AttributeName': 'device_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'N'}
        ],
        provisioning={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 50}
    )

    # 3. Alerts Table (Incidents, SOS, Anomalies)
    # PK: alert_id (String)
    # GSI: device_id-index (to query all alerts for a user)
    create_table(
        table_name='Prahari_Alerts',
        key_schema=[
            {'AttributeName': 'alert_id', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'alert_id', 'AttributeType': 'S'}
        ],
        provisioning={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    # 4. GeoFences Table (Zone Definitions)
    # PK: zone_id (String)
    create_table(
        table_name='Prahari_GeoFences',
        key_schema=[
            {'AttributeName': 'zone_id', 'KeyType': 'HASH'}
        ],
        attribute_definitions=[
            {'AttributeName': 'zone_id', 'AttributeType': 'S'}
        ],
        provisioning={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    print("Database Schema Setup Complete.")

if __name__ == "__main__":
    setup_infrastructure()
