import os
import os.path
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import requests
import json


# If modifying these scopes, delete the file token.json.

def get_drive_token(client_id, client_secret, refresh_token):
    url = "https://login.microsoftonline.com/d6454b9f-4ca2-4392-b62f-20e21e54335a/oauth2/v2.0/token"

    payload = f'client_id={client_id}&scope=offline_access%20Mail.ReadWrite%20Mail.send&grant_type=refresh_token&client_secret={client_secret}&redirect_uri=https%3A%2F%2Flocalhost&refresh_token={refresh_token}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'buid=0.AXIAn0tF1qJMkkO2LyDiHlQzWv8X8zrAVMtPqebAWud5G3tyAAA.AQABAAEAAAAmoFfGtYxvRrNriQdPKIZ-kZ5EkppMdTFRuYfniN_3y8-Xd4UdnOxoj73wJ1eZZCaKAT8JgDNpeqo0oFp59_urEfHRgAmxblfrvqZtteL87F0uVuBqo0iR-vyvN064OsAgAA; esctx=PAQABAAEAAAAmoFfGtYxvRrNriQdPKIZ-P8XcBu5-Z0yzoAJsYjHRoOrKnytCJJQZgtooKwI6-pwI0SH2MDCLXDXZbbdMx66FO30bZMF3OHeT5bL1TAdiQ4VV253aXWPOxep_3bDQ51hSp_8t3O5-_onUpGnU8RcuxnipsDXB1JojtTrJv8z5wQjGcGTbcAT1ttYODVqDMgIgAA; esctx-FbQVuPalhqg=AQABAAEAAAAmoFfGtYxvRrNriQdPKIZ-3CuntieqvcMk6UUaMPDkg0albmtVMGDKcYBLElzQlZY5BuS8kjO13PYFuvM631jlMLKFAtIxhAhe-6ffmXxJ7FIvp6zkgdlCdjY3zoSgYxAmMXLDc8II0tV8QHkyO8MN_C-kClYgVW8qHbel_H_FjCAA; fpc=Am86eFjVZTxGmw3t5Z7iqnHZjOJlAQAAAAuHAt0OAAAAlaghQQEAAABQhwLdDgAAAP8yaQoCAAAA5IgC3Q4AAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    result = json.loads(response.text)
    return result['access_token']


def get_files_id_name(credential_json_file, token_json_file):
    """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
    SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly", 'https://www.googleapis.com/auth/drive']
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_json_file):
        creds = Credentials.from_authorized_user_file(token_json_file, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_json_file, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_json_file, "w") as token:
            token.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)

    # Call the Drive v3 API
    results = (
        service.files()
        .list(pageSize=10, fields="nextPageToken, files(id, name)")
        .execute()
    )
    items = results.get("files", [])

    if not items:
        print("No files found.")
        return
    file_id_name = {}
    for item in items:
        file_id_name[item['id']] = item['name']
    return file_id_name


def download_drive_file(file_id, file_name, credential_json_file, token_json_file):
    """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
    SCOPES = ['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/drive',
              "https://www.googleapis.com/auth/bigquery"]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_json_file):
        creds = Credentials.from_authorized_user_file(token_json_file, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_json_file, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_json_file, "w") as token:
            token.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)

    file_id = file_id

    request = service.files().get_media(fileId=file_id)
    file = io.FileIO(file_name, mode='wb')
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}.")
    return True
