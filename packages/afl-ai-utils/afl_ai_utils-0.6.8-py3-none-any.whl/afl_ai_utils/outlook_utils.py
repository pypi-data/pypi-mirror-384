import json
import base64
import logging
import os
import requests
from tqdm import tqdm
from dateutil.parser import parse
from datetime import datetime, timezone, timedelta
import pytz

logging.basicConfig(format='[%(asctime)s]:[%(levelname)s]:[%(filename)s %(lineno)d]:[%(funcName)s]:%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_resource_access_token(client_id=None, client_secret=None, tenant_id=None, resource=None):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"

    # Token request parameters
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "resource": resource
    }

    # Request access token
    token_response = requests.post(token_url, data=token_data)

    # Check if token request was successful
    if token_response.status_code == 200:
        # Extract access token from response
        access_token = token_response.json()["access_token"]
        return access_token
    else:
        print("Error:", token_response.text)


def get_access_token(client_id, client_secret, refresh_token, scopes="offline_access%20Mail.ReadWrite%20Mail.send"):
    url = "https://login.microsoftonline.com/d6454b9f-4ca2-4392-b62f-20e21e54335a/oauth2/v2.0/token"

    payload = f'client_id={client_id}&scope={scopes}&grant_type=refresh_token&client_secret={client_secret}&redirect_uri=https%3A%2F%2Flocalhost&refresh_token={refresh_token}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'buid=0.AXIAn0tF1qJMkkO2LyDiHlQzWv8X8zrAVMtPqebAWud5G3tyAAA.AQABAAEAAAAmoFfGtYxvRrNriQdPKIZ-kZ5EkppMdTFRuYfniN_3y8-Xd4UdnOxoj73wJ1eZZCaKAT8JgDNpeqo0oFp59_urEfHRgAmxblfrvqZtteL87F0uVuBqo0iR-vyvN064OsAgAA; esctx=PAQABAAEAAAAmoFfGtYxvRrNriQdPKIZ-P8XcBu5-Z0yzoAJsYjHRoOrKnytCJJQZgtooKwI6-pwI0SH2MDCLXDXZbbdMx66FO30bZMF3OHeT5bL1TAdiQ4VV253aXWPOxep_3bDQ51hSp_8t3O5-_onUpGnU8RcuxnipsDXB1JojtTrJv8z5wQjGcGTbcAT1ttYODVqDMgIgAA; esctx-FbQVuPalhqg=AQABAAEAAAAmoFfGtYxvRrNriQdPKIZ-3CuntieqvcMk6UUaMPDkg0albmtVMGDKcYBLElzQlZY5BuS8kjO13PYFuvM631jlMLKFAtIxhAhe-6ffmXxJ7FIvp6zkgdlCdjY3zoSgYxAmMXLDc8II0tV8QHkyO8MN_C-kClYgVW8qHbel_H_FjCAA; fpc=Am86eFjVZTxGmw3t5Z7iqnHZjOJlAQAAAAuHAt0OAAAAlaghQQEAAABQhwLdDgAAAP8yaQoCAAAA5IgC3Q4AAAA; stsservicecookie=estsfd; x-ms-gateway-slice=estsfd'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    result = json.loads(response.text)
    return result['access_token']


def read_mail(access_token=None, from_email=None, top=1):
    subject = r"Arvind Fashions Limited: Storewise Inventory Report - ODIN"
    endpoint = f'https://graph.microsoft.com/v1.0/me/messages'
    params = {"$search": f'"from:{from_email}"', "top": top}

    r = requests.get(endpoint, headers={'Authorization': 'Bearer ' + access_token}, params=params)
    r.raise_for_status()  # Raise an exception if request fails

    if r.ok:
        print('Retrieved emails successfully')
        result_json = r.json()["value"]
        # import pdb; pdb.set_trace();
        if top < 10:
            received_date = parse(result_json[0]['receivedDateTime'])
            return received_date, result_json[0]['body']['content']
        else:
            received_date = parse(result_json[0]['receivedDateTime'])
            return received_date, result_json

        # for data in result_json:
        #     print(data['receivedDateTime'])
        #     print(data['subject'])
        #     print(data['bodyPreview'])
        #     # print(data['body']['content'])
        #     print(data['hasAttachments'])


def download_attachment(access_token=None, email_date=None, from_email=None, filename=None, email_object=None,
                        subject=None, top=10):
    endpoint = f'https://graph.microsoft.com/v1.0/me/messages'
    received_date = None
    if email_object is None:
        params = {"$search": f'"from:{from_email}"', "top": top}

        r = requests.get(endpoint, headers={'Authorization': 'Bearer ' + access_token}, params=params)
        r.raise_for_status()  # Raise an exception if request fails

        if r.ok:
            result_json = r.json()["value"]
            first_received_date = parse(result_json[0]['receivedDateTime'])
            received_date = first_received_date
            for data in result_json:

                received_date = parse(data['receivedDateTime'])
                print(f"Retrieved emails successfully for date={received_date} with subject {data['subject']} and passed subject={subject}")
                if received_date.date() == email_date and data['hasAttachments']:
                    # getting message id
                    message_id = data["id"]
                    email_sub = data['subject'].replace("Re:", "")

                    # import pdb; pdb.set_trace();
                    if subject and subject.lower().strip() == email_sub.lower().strip():
                        endpoint_attachment = endpoint + "/" + message_id + "/attachments/"
                        r = requests.get(endpoint_attachment, headers={'Authorization': 'Bearer ' + access_token})
                        r.raise_for_status()  # Raise an exception if request fails
                        # Getting the last attachment id
                        attachment_id = r.json().get('value')[-1].get('id')
                        endpoint_attachment_file = endpoint_attachment + "/" + attachment_id + "/$value"

                        res = requests.get(url=endpoint_attachment_file,
                                           headers={'Authorization': 'Bearer ' + access_token}, stream=True)
                        res.raise_for_status()  # Raise an exception if request fails

                        file_size = len(r.content)
                        with open(f"{filename}", 'wb') as f, tqdm(unit='iB', unit_scale=True, unit_divisor=1024,
                                                                  total=file_size,
                                                                  desc=f"Downloading {filename}") as pbar:
                            for data in res.iter_content(chunk_size=1024):
                                pbar.update(len(data))
                                f.write(data)

                        return received_date, True
                    elif subject is None or subject=="":
                        endpoint_attachment = endpoint + "/" + message_id + "/attachments/"
                        r = requests.get(endpoint_attachment, headers={'Authorization': 'Bearer ' + access_token})
                        r.raise_for_status()  # Raise an exception if request fails
                        # Getting the last attachment id
                        attachment_id = r.json().get('value')[-1].get('id')
                        endpoint_attachment_file = endpoint_attachment + "/" + attachment_id + "/$value"

                        res = requests.get(url=endpoint_attachment_file,
                                           headers={'Authorization': 'Bearer ' + access_token}, stream=True)
                        res.raise_for_status()  # Raise an exception if request fails

                        file_size = len(r.content)
                        with open(f"{filename}", 'wb') as f, tqdm(unit='iB', unit_scale=True, unit_divisor=1024,
                                                                  total=file_size,
                                                                  desc=f"Downloading {filename}") as pbar:
                            for data in res.iter_content(chunk_size=1024):
                                pbar.update(len(data))
                                f.write(data)

                        return received_date, True

            return first_received_date, False
    if email_object:
        received_date = parse(email_object['receivedDateTime'])
        if received_date.date() == email_date and email_object['hasAttachments']:
            # getting message id
            message_id = email_object["id"]

            endpoint_attachment = endpoint + "/" + message_id + "/attachments/"
            r = requests.get(endpoint_attachment, headers={'Authorization': 'Bearer ' + access_token})
            r.raise_for_status()  # Raise an exception if request fails
            # Getting the last attachment id
            attachment_id = r.json().get('value')[-1].get('id')

            endpoint_attachment_file = endpoint_attachment + "/" + attachment_id + "/$value"

            res = requests.get(url=endpoint_attachment_file,
                               headers={'Authorization': 'Bearer ' + access_token}, stream=True)
            res.raise_for_status()  # Raise an exception if request fails

            file_size = len(r.content)
            with open(f"{filename}", 'wb') as f, tqdm(unit='iB', unit_scale=True, unit_divisor=1024,
                                                      total=file_size,
                                                      desc=f"Downloading {filename}") as pbar:
                for data in res.iter_content(chunk_size=1024):
                    pbar.update(len(data))
                    f.write(data)
            return received_date, True

    return received_date, False


def draft_attachment(files):
    if not os.path.exists(files):
        logger.info('File is not found')
        return

    with open(files, 'rb') as upload:
        media_content = base64.b64encode(upload.read())

    data_body = {
        '@odata.type': '#microsoft.graph.fileAttachment',
        'contentBytes': media_content.decode('utf-8'),
        'name': os.path.basename(files),
    }
    return data_body


def get_message_id(access_token: str, from_email: str, subject: str, email_date: datetime):
    # API endpoint
    url = f"https://graph.microsoft.com/v1.0/me/mailfolders/inbox/messages"
    params = {
        "$filter": f"from/emailAddress/address eq '{from_email}' and subject eq '{subject}'",
        "$top": 4
    }

    # Send the GET request
    response = requests.get(url, params=params, headers={"Authorization": f"Bearer {access_token}"})

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()
        # Print the message ID
        if 'value' in data and len(data['value']) > 0:
            all_sent_emails = data['value']
            for sent_email in all_sent_emails:
                message_id = sent_email['id']
                sent_time = parse(sent_email['sentDateTime']) + timedelta(minutes=330)
                subject = sent_email['subject']
                print(f"Message ID: {message_id} - {sent_time} - {subject}")
                if sent_time.date() == email_date.date():
                    return message_id

        # Print the entire response for further inspection
        # print(data)
    else:
        # Print the error response if the request was not successful
        print(f"Error: {response.status_code}")

    return -1


def reply_to_mail(message_id: str, access_token: str, reply_body: str):
    # Replace with your access token and message ID

    # Reply body
    reply_body = {
        "comment": reply_body
    }

    # API endpoint
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/replyAll"
    # url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/reply"

    # Send the POST request
    response = requests.post(url, json=reply_body,
                             headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"})

    print("Replied to all with \n", reply_body)


def send_mail(to_emails: str, subject: [str, None], files: [str, None], mail_text: str, access_token: str):
    html_content = f"""
    <html>
    <body>
        {mail_text}
    </body>
    </html>
    """

    # to_recipients = [
    #                 {
    #                     'emailAddress': {
    #                         'address': senders_email
    #                     }
    #                 }
    #             ]

    to_recipients = []

    for to in to_emails.split(","):
        to_recipients.append({"emailAddress": {"address": to}})

    if files is not None:
        request_body = {
            'message': {
                # recipient list
                'toRecipients': to_emails,
                # email subject
                'subject': subject,
                'importance': 'normal',

                # include attachments
                'attachments': [
                    draft_attachment(files)

                ]
            }
        }
    else:
        request_body = {
            'message': {
                # recipient list
                'toRecipients': to_recipients,
                # email subject
                'subject': subject,
                "body": {
                    "contentType": "html",
                    "content": html_content
                },
                'importance': 'normal',

            }
        }

    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    GRAPH_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    endpoint = GRAPH_ENDPOINT + '/me/sendMail'

    try:
        response = requests.post(endpoint, headers=headers, json=request_body)
        response.raise_for_status()  # Raise an exception if request fails

        if response.status_code == 202:
            logger.info(f"Email sent to: {to_emails}")
        else:
            logger.exception(f"Email not sent to: {to_emails}")

    except requests.exceptions.RequestException as e:
        logger.exception("An error occurred while sending the email")
