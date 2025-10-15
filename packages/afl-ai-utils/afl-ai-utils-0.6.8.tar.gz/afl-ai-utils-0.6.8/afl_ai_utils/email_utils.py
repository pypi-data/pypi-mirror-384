import pdb

import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
import msal
import base64
import requests

class Email():

    def __init__(self, email, password):
        self.email = email
        self.password = password

        tenant_id = os.getenv('ANALYTICS_ALERT_TENENT_ID')
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        client_id = os.getenv('ANALYTICS_ALERT_CLIENT_ID')
        client_secret = os.getenv('ANALYTICS_ALERT_APP_SEC')
        scope = ['https://graph.microsoft.com/.default']

        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=authority,
            client_credential=client_secret
        )
        self.access_token = app.acquire_token_for_client(scopes=scope)

    def sendmail(self, subject: str, msg_body: str, data_frame: pd.DataFrame, from_email: str, to: str, cc: str,
                 bcc: str, attachment_file: str):
        # emaillist = recipients+cc_recipients
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to
        msg['Cc'] = cc
        rcpt = cc.split(",") + bcc.split(",") + [to]
        html = ""
        if msg_body and data_frame and len(msg_body) > 1 and len(data_frame) > 0:
            html = """\
            <html>
                {0}
              <head></head>
              <body>
                {1}
              </body>
            </html>
            """.format(msg_body, data_frame.to_html())
        else:

            html = """\
            <html>
              <head></head>
              <body>
                {0}
              </body>
            </html>
            """.format(msg_body)

        if html and len(html) > 1:
            part1 = MIMEText(html, 'html')
            msg.attach(part1)

        if attachment_file and len(attachment_file) > 1:
            attachment = attachment_file
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(attachment, "rb").read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename=attachment)
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(self.email, self.password)
        server.sendmail(msg['From'], rcpt, msg.as_string())

    def send_outlook_email(self, subject: str, msg_body: str, data_frame: pd.DataFrame, from_email: str, to: str,
                           cc: str,
                           bcc: str, attachment_file):
        msg = MIMEMultipart()
        msg['Subject'] = subject
        html = ""
        if msg_body and data_frame is not None and len(msg_body) > 1 and len(data_frame) > 0:
            html = """\
            <html>
                {0}
              <head></head>
              <body>
                {1}
              </body>
            </html>
            """.format(msg_body, data_frame.to_html())
        else:

            html = """\
            <html>
              <head></head>
              <body>
                {0}
              </body>
            </html>
            """.format(msg_body)

        if html and len(html) > 1:
            part1 = MIMEText(html, 'html')
            msg.attach(part1)

        if attachment_file and len(attachment_file) > 1:
            if isinstance(attachment_file, list):
                for file in attachment_file:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(open(file, "rb").read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file)}')
                    msg.attach(part)
            else:
                part = MIMEBase('application', "octet-stream")
                part.set_payload(open(attachment_file, "rb").read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=attachment_file)
                msg.attach(part)

        msg['Body'] = msg_body
        msg['From'] = from_email
        msg['To'] = to
        msg['Cc'] = cc

        with smtplib.SMTP('smtp.office365.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.email, self.password)
            server.send_message(msg)


    def replay_to_all_for_particular_mail(self, mail_read_from, message_id, email_body):
        token = self.access_token['access_token']
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Step 1: Create reply draft
        reply_url = f"https://graph.microsoft.com/v1.0/users/{mail_read_from}/messages/{message_id}/createReplyAll"
        draft_response = requests.post(reply_url, headers=headers)
        draft_data = draft_response.json()
        draft_id = draft_data['id']

        # Step 2: Update the draft with your content
        update_url = f"https://graph.microsoft.com/v1.0/users/{mail_read_from}/messages/{draft_id}"
        update_payload = {
            "body": {
                "contentType": "Text",
                "content": email_body
            }
        }
        requests.patch(update_url, headers=headers, json=update_payload)

        # Step 3: Send the reply
        send_url = f"https://graph.microsoft.com/v1.0/users/{mail_read_from}/messages/{draft_id}/send"
        send_response = requests.post(send_url, headers=headers)

        if send_response.status_code == 202:
            print("✅ Reply sent successfully.")
        else:
            raise Exception(f"❌ Failed to send reply: {send_response.status_code} - {send_response.text}")

    def reply_to_all_or_start_new_thread(self, mail_read_from, mail_subject, to, cc, email_body, attachment_files=None):
        token = self.access_token['access_token']
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            # Step 1: Search for existing email in Sent Items using subject
            find_email_api = f"https://graph.microsoft.com/v1.0/users/{mail_read_from}/mailFolders/sentitems/messages?$filter=contains(subject, '{mail_subject}')"
            response = requests.get(url=find_email_api, headers=headers)

            if response.status_code == 200 and response.json().get('value'):
                message = response.json()
                message_id = message['value'][0]['id']

                # Step 2: Create draft reply to all
                reply_url = f"https://graph.microsoft.com/v1.0/users/{mail_read_from}/messages/{message_id}/createReplyAll"
                draft_response = requests.post(reply_url, headers=headers)
                draft_data = draft_response.json()
                draft_id = draft_data['id']

                # Step 3: Update body only (attachments need separate call)
                #email_body = f"<b>Gentle Reminder</b><br><br>{email_body}"
                update_url = f"https://graph.microsoft.com/v1.0/users/{mail_read_from}/messages/{draft_id}"

                update_payload = {
                    "body": {
                        "contentType": "HTML",
                        "content": email_body
                    }
                }

                patch_response = requests.patch(update_url, headers=headers, json=update_payload)
                if patch_response.status_code not in (200, 202):
                    raise Exception(f"PATCH failed: {patch_response.status_code} - {patch_response.text}")

                # Step 4: Attach files
                if attachment_files:
                    for file_path in attachment_files:
                        with open(file_path, 'rb') as f:
                            content_bytes = base64.b64encode(f.read()).decode('utf-8')
                            attachment_payload = {
                                "@odata.type": "#microsoft.graph.fileAttachment",
                                "name": os.path.basename(file_path),
                                "contentType": "application/octet-stream",
                                "contentBytes": content_bytes
                            }

                            attach_url = f"https://graph.microsoft.com/v1.0/users/{mail_read_from}/messages/{draft_id}/attachments"
                            attach_response = requests.post(attach_url, headers=headers, json=attachment_payload)

                            if attach_response.status_code not in (200, 201, 202):
                                print(
                                    f"❌ Failed to attach file: {file_path} | {attach_response.status_code} - {attach_response.text}")
                            else:
                                print(f"📎 Attached file: {file_path}")

                # Step 5: Send the email
                send_url = f"https://graph.microsoft.com/v1.0/users/{mail_read_from}/messages/{draft_id}/send"
                send_response = requests.post(send_url, headers=headers)

                if send_response.status_code == 202:
                    print("✅ Reply sent in existing thread.")
                else:
                    raise Exception(
                        f"❌ Failed to send threaded reply: {send_response.status_code} - {send_response.text}")

            else:
                raise Exception("Could not find existing thread")

        except Exception as e:
            print(f"⚠️ Could not find thread. Sending fresh email. Reason: {str(e)}")

            # Fallback: Send a new email thread
            self.send_outlook_email(
                subject=mail_subject,
                msg_body=email_body,
                data_frame=None,
                from_email=mail_read_from,
                to=to,
                cc=cc,
                bcc=None,
                attachment_file=attachment_files
            )
            print("✅ New email thread started.")
    # def send_outlook_email(self, subject: str, msg_body: str, from_email: str, to: list, cc: list, attachment_file: str):
    #
    #     ## FILE TO SEND AND ITS PATH
    #     filename = 'test.csv'
    #     SourcePathName = os.getcwd() + "/" + filename
    #
    #     msg = MIMEMultipart()
    #     msg['From'] = os.getenv("FROM")
    #     msg['To'] = os.getenv("TO")
    #     msg['Subject'] = "Test file subject"
    #     body = 'Hi, \n, PFA \n regards, Abhay\n'
    #     msg.attach(MIMEText(body, 'plain'))
    #
    #     ## ATTACHMENT PART OF THE CODE IS HERE
    #     attachment = open(SourcePathName, 'rb')
    #     part = MIMEBase('application', "octet-stream")
    #     part.set_payload((attachment).read())
    #     encoders.encode_base64(part)
    #     part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    #     msg.attach(part)
    #
    #     server = smtplib.SMTP('smtp.office365.com', 587)  ### put your relevant SMTP here
    #     server.ehlo()
    #     server.starttls()
    #     server.ehlo()
    #     print(os.getenv("FROM"), os.getenv("PASSWORD"))
    #     server.login(os.getenv("FROM"), os.getenv("PASSWORD"))  ### if applicable
    #     server.send_message(msg)
    #     server.quit()
    #     print("Send email ", msg)

# e = Email()
# e.sendmail(subject=subject, data_frame=df, from_email=from_email, to=to, cc=cc, bcc=bcc, attachment_file=attachment_file, msg_body=body)
