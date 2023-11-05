import json
from os import environ
from urllib.parse import urlparse

import boto3

from wwara.database import coordinations
from wwara.plan import EXCEPTIONS
from wwara.qa import test

S3 = boto3.client("s3")
SNS = boto3.client("sns")

BUCKET = "wwara"
KEY = "DataBaseExtract.zip"
TOPIC_ARN = environ.get("TOPIC_ARN")
VERSION_DEPTH = int(environ.get("VERSION_DEPTH", 1)) + 1


def lambda_handler(event=None, context=None):
    print(json.dumps(event, default=str))
    if "Records" in event:
        # From S3
        event_detail = event["Records"][0]["s3"]
    elif "detail" in event:
        # From S3 through EventBridge
        event_detail = event["detail"]
    else:
        raise
    bucket = event_detail["bucket"]["name"]
    key = event_detail["object"]["key"]
    print(json.dumps({"bucket": bucket, "key": key}))

    latest_object = S3.get_object(Bucket=bucket, Key=key)
    latest = set(coordinations(file_obj=latest_object["Body"]))

    versions = S3.list_object_versions(Bucket=bucket, Prefix=key, MaxKeys=VERSION_DEPTH)
    version_id = versions["Versions"][-1]["VersionId"]
    print(json.dumps({"Previous-VersionId": version_id}))

    previous_object = S3.get_object(Bucket=bucket, Key=key, VersionId=version_id)
    previous = set(coordinations(file_obj=previous_object["Body"]))

    changed = False
    for subject, channels in (
        ("WWARA Removed", previous - latest),
        ("WWARA Added", latest - previous),
    ):
        if channels:
            changed = True
            messages = []
            for channel in sorted(channels):
                error, comments = test(channel)
                if error and channel not in EXCEPTIONS:
                    comments.insert(0, "ERROR!")
                if comments:
                    comments = " ".join(comments)
                    messages.append(f"{channel} {comments}")
                else:
                    messages.append(str(channel))
            message = "\n".join(messages)
            print(json.dumps({"Subject": subject, "Message": message}))
            if TOPIC_ARN:
                SNS.publish(
                    TopicArn=TOPIC_ARN,
                    Subject=subject,
                    Message=message,
                )
    if not changed:
        print("no changes")


if __name__ == "__main__":
    event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {
                    "bucket": {"name": BUCKET},
                    "object": {"key": KEY},
                },
            }
        ]
    }
    event = {"detail": {"bucket": {"name": BUCKET}, "object": {"key": KEY}}}
    lambda_handler(event=event, context=None)
