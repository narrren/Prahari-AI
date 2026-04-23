import boto3
from app.core.config import settings

from botocore.config import Config

def get_db_resource():
    config = Config(connect_timeout=0.5, read_timeout=0.5, retries={'max_attempts': 0})
    return boto3.resource(
        'dynamodb',
        region_name=settings.AWS_REGION,
        endpoint_url=settings.DYNAMODB_ENDPOINT,
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
        config=config
    )

def get_table(table_name: str):
    dynamodb = get_db_resource()
    return dynamodb.Table(table_name)

