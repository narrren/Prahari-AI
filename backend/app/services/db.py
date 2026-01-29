import boto3
from app.core.config import settings

def get_db_resource():
    return boto3.resource(
        'dynamodb',
        region_name=settings.AWS_REGION,
        endpoint_url=settings.DYNAMODB_ENDPOINT,
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY
    )

def get_table(table_name: str):
    dynamodb = get_db_resource()
    return dynamodb.Table(table_name)

