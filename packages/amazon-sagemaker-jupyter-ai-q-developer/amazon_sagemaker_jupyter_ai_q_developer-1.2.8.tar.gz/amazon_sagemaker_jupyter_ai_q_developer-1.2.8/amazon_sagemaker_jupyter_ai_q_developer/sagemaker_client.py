import json
import os
from pathlib import Path
from typing import Dict

import boto3
import botocore
import botocore.session

from amazon_sagemaker_jupyter_ai_q_developer.constants import USE_DUALSTACK_ENDPOINT

SAGEMAKER_INTERNAL_METADATA_FILE_PATH = "/opt/.sagemakerinternal/internal-metadata.json"
LOOSELEAF_STAGE_MAPPING = {"devo": "beta", "loadtest": "gamma"}


class BaseAsyncBotoClient:
    cfg: any
    partition: str
    region_name: str
    sess: boto3.Session

    def __init__(self, partition: str, region_name: str):
        self.cfg = botocore.client.Config(
            connect_timeout=5,
            read_timeout=15,
            retries={"max_attempts": 2},
            use_dualstack_endpoint=USE_DUALSTACK_ENDPOINT,
        )
        self.partition = partition
        self.region_name = region_name

        os.environ["AMAZON_Q_DATA_PATH"] = os.path.join(
            Path(__file__).parent.parent, "service_models"
        )
        self.sess = boto3.Session()


class SageMakerAsyncBoto3Client(BaseAsyncBotoClient):
    def get_stage(self):
        try:
            with open(SAGEMAKER_INTERNAL_METADATA_FILE_PATH, "r") as file:
                data = json.load(file)
                return data.get("Stage")
        except Exception:
            return "prod"

    def _create_sagemaker_client(self):
        # based on the Studio domain stage, we want to choose the sagemaker endpoint
        # rest of the services will use prod stages for non prod stages
        create_client_args = {
            "service_name": "sagemaker",
            "config": self.cfg,
            "region_name": self.region_name,
        }

        stage = self.get_stage()
        if stage is not None and stage != "" and stage.lower() != "prod":
            endpoint_stage = LOOSELEAF_STAGE_MAPPING.get(stage.lower())
            create_client_args["endpoint_url"] = (
                f"https://sagemaker.{endpoint_stage}.{self.region_name}.ml-platform.aws.a2z.com"
            )

        return self.sess.client(**create_client_args)

    def describe_domain(self, domain_id: str) -> Dict:
        if domain_id is None:
            return {}
        else:
            return self._create_sagemaker_client().describe_domain(DomainId=domain_id)


def get_region_name():
    # Get region config in following order:
    # 1. AWS_REGION env var
    # 2. Region from AWS config (for example, through `aws configure`)
    # 3. AWS_DEFAULT_REGION env var
    # 4. If none of above are set, use us-east-1
    session = botocore.session.Session()
    region_config_chain = [
        os.environ.get("AWS_REGION"),
        session.get_config_variable("region"),
        os.environ.get("AWS_DEFAULT_REGION"),
        "us-east-1",
    ]
    for region_config in region_config_chain:
        if region_config is not None:
            return region_config
    return "us-east-1"


def get_partition():
    return boto3.Session().get_partition_for_region(get_region_name())


def get_sagemaker_client():
    return SageMakerAsyncBoto3Client(get_partition(), get_region_name())
