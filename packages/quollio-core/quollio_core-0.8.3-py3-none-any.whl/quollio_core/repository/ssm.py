import logging
import os
from typing import Tuple

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_parameter_by_assume_role(key: str, region: str = "ap-northeast-1") -> Tuple[str, Exception]:
    tenant_id = os.getenv("TENANT_ID")
    if not _is_str_valid(tenant_id):
        return ("", Exception("TENANT_ID is not set in get_parameter_by_assume_role."))
    qdc_account_id = os.getenv("QDC_ACCOUNT_ID")
    if not _is_valid_aws_account_id(qdc_account_id):
        return ("", Exception("QDC_ACCOUNT_ID is not set in get_parameter_by_assume_role."))
    qdc_region = os.getenv("QDC_REGION")
    if not _is_str_valid(qdc_region):
        return ("", Exception("QDC_REGION is not set in get_parameter_by_assume_role."))

    sts_assume_role_arn = "arn:aws:iam::{account_id}:role/qdc-{tenant_id}-cross-account-access".format(
        account_id=qdc_account_id, tenant_id=tenant_id
    )

    session = boto3.Session(region_name=region)
    sts = session.client("sts", endpoint_url="https://sts.{region}.amazonaws.com".format(region=qdc_region))
    assumed_role_object = sts.assume_role(
        RoleArn=sts_assume_role_arn,
        RoleSessionName="AssumeRoleSession",
    )
    credentials = assumed_role_object["Credentials"]

    try:
        ssm = session.client(
            "ssm",
            endpoint_url="https://ssm.{region}.amazonaws.com".format(region=qdc_region),
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )
        res = ssm.get_parameter(Name=key, WithDecryption=True)
        return (res["Parameter"]["Value"], None)
    except ClientError as e:
        logger.error(
            "Failed to run ssm.get_parameter().\
             Please check the value stored in parameter store is correct. error: {err}".format(
                err=e
            )
        )
        return ("", e)


def _is_valid_aws_account_id(s: str) -> bool:
    return s is not None and len(s) == 12 and s.isdigit()


def _is_str_valid(s: str) -> bool:
    return s is not None and s != ""
