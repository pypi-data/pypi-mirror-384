from msal import ConfidentialClientApplication
import requests
import pandas as pd
from io import BytesIO
import os



class MicrosoftUtils():
    def __init__(self, client_id, client_secret, tenant_id, access_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token=access_token
    def read_ms_sheet(self, url):

        # OneDrive link

        # Send a GET request to download the file
        response = requests.get(url, headers={'Authorization': 'Bearer ' + self.access_token})

        # Check if the request was successful
        if response.status_code == 200:
            # Read the content of the response as bytes
            content = response.content
            # Convert bytes to a pandas DataFrame
            df = pd.read_excel(BytesIO(content))
            # Display the first few rows of the DataFrame
            df = pd.read_excel(response.content)

            # Display the DataFrame
            print(df)
            print(df.head())
        else:
            print("Failed to download the file.",response.content)
