import boto3
from django.conf import settings

_secrets_manager_client = None


def get_secrets_manager_client():
    global _secrets_manager_client
    if _secrets_manager_client:
        return _secrets_manager_client

    _secrets_manager_client = boto3.Session(
        aws_access_key_id=settings.ENV.secrets_manager.access_key,
        aws_secret_access_key=settings.ENV.secrets_manager.secret_key,
        region_name=settings.ENV.secrets_manager.region_name,
    ).client("secretsmanager")
    return _secrets_manager_client


def get_secret_value(secret_name: str) -> str:
    response = get_secrets_manager_client().get_secret_value(SecretId=secret_name)
    return response["SecretString"]


def set_secret_value(secret_name: str, secret_value: str) -> dict:
    client = get_secrets_manager_client()
    try:
        client.describe_secret(SecretId=secret_name)
        response = client.put_secret_value(
            SecretId=secret_name, SecretString=secret_value
        )
    except client.exceptions.ResourceNotFoundException:
        response = client.create_secret(Name=secret_name, SecretString=secret_value)

    return response
