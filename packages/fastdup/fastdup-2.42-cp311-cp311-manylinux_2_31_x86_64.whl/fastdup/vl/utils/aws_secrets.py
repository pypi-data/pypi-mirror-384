import json

from fastdup.vl.common.settings import Settings

if not Settings.IS_FASTDUP:
    import boto3
    from botocore.exceptions import ClientError

def get_secret(secret_name: str, secret_key: str):
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        aws_access_key_id=Settings.AWS_ACCESS_KEY,
        aws_secret_access_key=Settings.AWS_SECRET_KEY,
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    secret_dict: dict = json.loads(secret)
    return secret_dict[secret_key]
