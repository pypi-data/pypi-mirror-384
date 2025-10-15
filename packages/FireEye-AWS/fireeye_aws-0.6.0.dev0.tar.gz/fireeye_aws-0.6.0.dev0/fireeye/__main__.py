import argparse

from fireeye.aws_lambda import CloudWatch, print_logs
from fireeye.exceptions import CloudWatchLogException
from fireeye.logger import logger

parser = argparse.ArgumentParser()
parser.add_argument(
    "--trace", help="Match a string/character", dest="to_trace", default="duration"
)
parser.add_argument("--arn", help="AWS Resource ARN", dest="arn", default=False)
parser.add_argument(
    "--resource-name", help="AWS Lambda Name", dest="res_name", default=False
)

# parser.add_argument(
#     "--slack-url",
#     help="Slack App incoming webhook URL",
#     dest="slack_webhook",
#     default=False,
# )

args = parser.parse_args()
if (args.arn or args.res_name) is False:
    exit(parser.print_help())


def main():
    try:
        # pdb.set_trace()
        lambda_logs = CloudWatch(args.arn or args.res_name)
        ctx_info = lambda_logs.get_ctx_info()

        logger.info(
            f"Account ID: {ctx_info.get("acc_id")}, Region: {ctx_info.get("default_region")}, "
            f"IAM User: {ctx_info.get("iam_user")}"
        )

        logs = lambda_logs.lambda_logs(args.to_trace)

        print_logs(logs)

        if not logs["response"]:
            raise CloudWatchLogException("Invalid Response")

        # if args.slack_webhook:
        # slack_app = SlackApp(url=args.slack_webhook)
        # payload = slack_message.create_payload(ctx_info, logs)
        #
        # slack_app.send(payload)
        # pass
    except Exception as e:
        logger.info(e, exc_info=True)


# main()
