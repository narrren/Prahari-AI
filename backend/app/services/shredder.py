
import asyncio
import boto3
import time
from botocore.exceptions import ClientError

# Mock Boto3 for demo if no credentials
try:
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:4566")
    table = dynamodb.Table('PrahariPermits')
except:
    table = None

async def run_data_shredder():
    """
    DPDP COMPLIANCE JOB:
    Runs daily to delete PII from DynamoDB for expired permits.
    Leaves only the Blockchain Hash (Immutable Proof) behind.
    """
    if not table:
        print("SHREDDER: DynamoDB not connected. Skipping PII Purge.")
        return

    print("SHREDDER: Initiating PII Purge Sequence...")
    
    try:
        # Scan for expired items
        # In prod, use Global Secondary Index (GSI) for query by date
        response = table.scan()
        items = response.get('Items', [])
        
        current_time = time.time()
        deleted_count = 0
        
        for item in items:
            expiry = float(item.get('expiry_timestamp', 0))
            if expiry < current_time:
                # Shred PII fields
                table.update_item(
                    Key={'permit_id': item['permit_id']},
                    UpdateExpression="REMOVE name, passport_number, dob, address SET pii_status = :s",
                    ExpressionAttributeValues={':s': 'SHREDDED_COMPLIANT'},
                    ReturnValues="UPDATED_NEW"
                )
                deleted_count += 1
                
        print(f"SHREDDER: Purge Complete. {deleted_count} Records Anonymized.")
        
    except ClientError as e:
        print(f"SHREDDER ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(run_data_shredder())
