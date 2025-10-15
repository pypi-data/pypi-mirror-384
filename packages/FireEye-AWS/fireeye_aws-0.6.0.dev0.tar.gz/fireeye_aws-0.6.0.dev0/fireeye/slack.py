import os

import urllib3

from fireeye.logger import logger

requests = urllib3.PoolManager()
webhook_url = os.getenv("SLACK_URL", False)


def create_payload(info: dict, txt="Hi, it's FireEye here!"):
    account_id = info.get("acc_id", "none")
    resource_arn = info.get("arn", "none")
    resource_name = info.get("res_name", "none")

    message = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "AWS Alert from FireEye",
                    "emoji": "true",
                },
            },
            {"type": "divider"},
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "text",
                                "text": f"Account ID: {account_id}",
                                "style": {"bold": "true"},
                            },
                            {"type": "text", "text": "\n"},
                            {
                                "type": "text",
                                "text": f"Resource ARN: {resource_arn}",
                                "style": {"bold": "true"},
                            },
                            {"type": "text", "text": "\n"},
                            {
                                "type": "text",
                                "text": f"Resource Name: {resource_name}",
                                "style": {"bold": "true"},
                            },
                        ],
                    }
                ],
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"```{txt}```"}},
        ]
    }


class SlackApp:
    def __init__(self, url=False):
        self.url = url

    def send(self, payload: str):
        resp = None
        try:
            resp = requests.request("POST", self.url or webhook_url, data=payload)
        except Exception as e:
            logger.info(e)

        if resp.status != 200:
            return
        logger.info("Notification sent successfully!")
