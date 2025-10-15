import datetime

from fireeye.aws import AWS
from fireeye.logger import logger, dark_green, end


def print_logs(api_response: dict):
    for resp in api_response["response"]:
        logger.info(f"{dark_green}{resp[2].get('value')}{end}")
        logger.info(f"{resp[1].get('value')}")


def time_diff():
    this_time = datetime.datetime.now()
    step_size = 3
    past_time = int((this_time - datetime.timedelta(days=step_size)).timestamp())

    return past_time, int(this_time.timestamp())


def parse_arn(arn: str):  # Filter resource name from un-qualified lambda arn
    logger.info("Parsing ARN")
    try:
        if arn.split(":")[2] == "lambda":
            lambda_name = arn.split(":")[-1]

            return lambda_name
    except:
        logger.info("Failed to parse ARN")

    return arn


class CloudWatch(AWS):
    def __init__(self, arn):
        super().__init__()

        self.resource_name = f"{parse_arn(arn)}"  # Lambda name
        self.lambda_arn = arn  # optional
        self.log_stream_count = 3  # default set to fetch latest 3 streams
        self.aws_session = super().aws_session()
        self.start_time, self.end_time = time_diff()
        self.query = ""

    def get_ctx_info(self):
        sts_client = self.aws_session.client("sts")
        get_caller_id = sts_client.get_caller_identity()
        acc_id = get_caller_id.get("Account")
        user_iam = get_caller_id.get("Arn").split(":")[-1]
        arn = self.lambda_arn or False
        res_name = self.resource_name

        ctx_info = {
            "acc_id": acc_id,
            "default_region": self.aws_session.region_name,
            "iam_user": user_iam,
            "resource_arn": arn,
            "res_name": res_name,
        }

        return ctx_info

    def _create_query(self, to_trace):
        query = f'fields @timestamp, @message, @logStream | filter @message like "{to_trace}"'

        self.query = query

    def lambda_logs(self, to_trace):
        lambda_client = self.aws_session.client("logs")
        self.resource_name = f"/aws/lambda/{self.resource_name}"

        self._create_query(to_trace)

        query_id = lambda_client.start_query(
            logGroupName=self.resource_name,
            startTime=self.start_time,
            endTime=self.end_time,
            queryString=self.query,
            limit=self.log_stream_count,
        )

        logger.info(f"Query String :: {self.query}")
        logger.info(
            f"Time Range :: {datetime.datetime.fromtimestamp(self.start_time)} to {datetime.datetime.fromtimestamp(self.end_time)}"
        )
        logger.info(f"Log Group :: {self.resource_name}\n")

        query_results = lambda_client.get_query_results(
            queryId=query_id.get("queryId", False)
        )

        return {"response": query_results.get("results", None)}
