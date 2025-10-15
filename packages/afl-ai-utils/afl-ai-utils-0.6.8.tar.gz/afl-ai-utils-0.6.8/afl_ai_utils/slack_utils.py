from random import randint
import logging
import time
import json
import os

from afl_ai_utils.consts import min_wait_time, max_wait_time

import requests

logging.basicConfig(format='%(name)s - %(levelname)s -%(asctime)s- %(message)s', level=logging.INFO)


def send_slack_alert(info_alert_slack_webhook_url: str, red_alert_slack_webhook_url: str, slack_red_alert_userids: str,
                     payload: dict, is_red_alert: bool):
    """Send a Slack message to a channel via a webhook.

    Args:
        info_alert_slack_webhook_url(str): Infor slack channel url
        red_alert_slack_webhook_url(str): red alert channel url
        slack_red_alert_userids (list): userid's to mention in slack for red alert notification
        payload (dict): Dictionary containing Slack message, i.e. {"text": "This is a test"}
        is_red_alert (bool): Full Slack webhook URL for your chosen channel.

    Returns:
        HTTP response code, i.e. <Response [503]>
    """

    channel_url = info_alert_slack_webhook_url
    payload["text"] = os.getcwd() + " " + payload["text"]
    if is_red_alert:
        message = ""
        for message_line in payload["text"].split("\n"):
            if message_line.strip():
                message += "`" + message_line + "`"
                message += "\n"
        payload["text"] = message
        for slack_red_alert_userid in slack_red_alert_userids.split(","):
            payload["text"] += slack_red_alert_userid
            payload["text"] += " "
        channel_url = red_alert_slack_webhook_url
        logging.error(payload["text"])

    else:
        payload["text"] = "```" + payload["text"] + "```"
        logging.info(payload["text"])

    response_code = 500
    retry_count = 0

    while response_code != 200 and retry_count < 2:
        response = requests.post(channel_url, json.dumps(payload),
                                 headers={'Content-Type': 'application/json'})
        response_code = response.status_code
        time.sleep(randint(min_wait_time, max_wait_time))
        retry_count += 1
