from google.cloud import storage
from google.cloud.storage import Bucket

url = "storage.googleapis.com"

# minio = Minio(url, access_key, secret_key, secure=True)

# Doesn't work yet, placeholder ...
def check_connectivity_to_bucket(bucket_name: str) -> bool:
    client = storage.Client()
    bucket: Bucket = client.get_bucket(bucket_name)
    return bucket.exists() and bucket.get_iam_policy().bindings == []
