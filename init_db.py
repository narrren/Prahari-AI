import boto3
import os

# Config
ENDPOINT = "http://localhost:4566"
REGION = "us-east-1"
ACCESS_KEY = "test"
SECRET_KEY = "test"

def init_db():
    print(f"Initializing DynamoDB Tables at {ENDPOINT}...")
    
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=REGION,
        endpoint_url=ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )

    # 1. TELEMETRY TABLE
    try:
        table = dynamodb.create_table(
            TableName='Prahari_Telemetry',
            KeySchema=[
                {'AttributeName': 'device_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'device_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("✅ Table Created: Prahari_Telemetry")
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("ℹ️ Table Exists: Prahari_Telemetry")
        else:
            print(f"❌ Error creating Prahari_Telemetry: {e}")

    # 2. PERMITS TABLE
    try:
        table = dynamodb.create_table(
            TableName='PrahariPermits',
            KeySchema=[
                {'AttributeName': 'permit_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'permit_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("✅ Table Created: PrahariPermits")
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("ℹ️ Table Exists: PrahariPermits")
        else:
            print(f"❌ Error creating PrahariPermits: {e}")

if __name__ == "__main__":
    init_db()
