import os

import boto3


class AWS:
    def __init__(self):
        self.access_key_id = ""
        self.secret_key = ""
        self.region = ""

    def _get_creds(self):
        access_key_id = os.getenv("AWS_ACCESS_KEY_ID", None)
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", None)
        region = os.getenv("AWS_DEFAULT_REGION", None)

        self.access_key_id = access_key_id
        self.secret_key = secret_key
        self.region = region

    def aws_session(self):
        self._get_creds()
        session = boto3.Session(
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )

        return session
