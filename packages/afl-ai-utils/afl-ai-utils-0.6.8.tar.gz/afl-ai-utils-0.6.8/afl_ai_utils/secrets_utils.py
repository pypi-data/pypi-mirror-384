import os

from dotenv import load_dotenv
from google.cloud import secretmanager
import time

def load_da_secrets():
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/162221169123/secrets/da-secrets/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    payload = response.payload.data.decode("UTF-8")
    with open(os.getcwd()+'/.env', 'w', encoding='utf-8') as f:
        f.write(payload)
    load_dotenv()

def load_de_secrets():
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/162221169123/secrets/de-secrets/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    payload = response.payload.data.decode("UTF-8")
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(payload)
    load_dotenv()
