
import boto3
import json
import time
import os
from decimal import Decimal
from app.core.shared_state import LATEST_POSITIONS
from app.core.config import settings

def create_snapshot():
    """
    Backs up the entire In-MEMORY state to S3 (Simulated by LocalStack).
    Standard Disaster Recovery (DR) practice.
    """
    if not LATEST_POSITIONS:
        return

    try:
        # 1. Config S3 Client (LocalStack)
        s3 = boto3.client(
            's3',
            endpoint_url=settings.DYNAMODB_ENDPOINT, # Reuse localstack endpoint
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test"
        )
        
        BUCKET_NAME = "prahari-dr-snapshots"
        
        # Ensure bucket exists
        try:
            s3.create_bucket(Bucket=BUCKET_NAME)
        except:
            pass # Exists
            
        # 2. Serialize State
        # Convert Decimals if any remain (though State usually keeps floats now)
        # Just to be safe
        dumped_state = {}
        for k, v in LATEST_POSITIONS.items():
            dumped_state[k] = v

        filename = f"snapshot_{int(time.time())}.json"
        
        # 3. Upload
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=json.dumps(dumped_state, default=str)
        )
        
        print(f"SNAPSHOT: Saved state to s3://{BUCKET_NAME}/{filename}")
        
    except Exception as e:
        print(f"Snapshot Failed: {e}")
