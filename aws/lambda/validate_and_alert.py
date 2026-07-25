"""validate_and_alert.py

Triggered by the same S3 ObjectCreated event that feeds Snowpipe. Validates
the file name convention and, on a bad file, posts an alert. Reads any needed
credential from AWS Secrets Manager instead of hardcoding it.

Deploy: zip this file, create a Lambda (Python 3.12), add an S3 trigger on the
oncolake-landing bucket, and give the role secretsmanager:GetSecretValue +
sns:Publish.
"""
import json
import re
import os
import boto3

FILENAME_RE = re.compile(r"^lab_results_\d{8}_[a-z0-9]+\.csv$")
ALERT_TOPIC_ARN = os.environ.get("ALERT_TOPIC_ARN", "")
SECRET_NAME = os.environ.get("SECRET_NAME", "oncolake/jdbc-source")

_sm = boto3.client("secretsmanager")
_sns = boto3.client("sns")


def get_secret(name):
    resp = _sm.get_secret_value(SecretId=name)
    return json.loads(resp["SecretString"])


def alert(message):
    if ALERT_TOPIC_ARN:
        _sns.publish(TopicArn=ALERT_TOPIC_ARN, Subject="OncoLake load issue", Message=message)
    print("ALERT:", message)


def handler(event, context):
    for record in event.get("Records", []):
        key = record["s3"]["object"]["key"]
        fname = key.split("/")[-1]
        if not FILENAME_RE.match(fname):
            alert(f"Rejected file with bad name: {key}. "
                  f"Expected lab_results_YYYYMMDD_<id>.csv")
            continue
        print(f"Accepted {key}; Snowpipe will auto-ingest it.")

    return {"statusCode": 200, "body": "validated"}
