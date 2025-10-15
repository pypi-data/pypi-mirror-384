import json
import os
from pathlib import Path

import boto3
from amazon_sagemaker_jupyter_ai_q_developer.exceptions import ServerExtensionException
from amazon_sagemaker_jupyter_ai_q_developer.file_cache_manager import FileCacheManager
from botocore.config import Config

# service_models is at root, relative path ../../service_models
SESSION_FOLDER = f"{Path(__file__).parent.parent}/service_models"
REQUEST_OPT_OUT_HEADER_NAME = "x-amzn-codewhisperer-optout"


class BaseClient:
    @staticmethod
    def get_client(service_name, endpoint_url, api_version, region_name, signature_version=None):
        session = boto3.Session()
        if signature_version is None:
            config = Config(connect_timeout=10)
        else:
            config = Config(connect_timeout=10, signature_version=signature_version)
        session._loader.search_paths.extend([SESSION_FOLDER])
        return session.client(
            service_name=service_name,
            endpoint_url=endpoint_url,
            region_name=region_name,
            config=config,
            api_version=api_version,
        )

    @staticmethod
    def add_header(opt_out, request, **kwargs):
        request.headers.add_header(REQUEST_OPT_OUT_HEADER_NAME, f"{opt_out}")
        request.headers.add_header("Authorization", f"Bearer {BaseClient._get_bearer_token()}")
        request.headers.add_header("Content-Type", "application/json")
        request.headers.add_header("Content-Encoding", "amz-1.0")

    @staticmethod
    def _get_bearer_token():
        return BaseClient._extractor(
            "~/.aws/sso/idc_access_token.json", lambda d: d["idc_access_token"]
        )

    @staticmethod
    def _extractor(file_path=None, value_extractor=None):
        content = json.loads(
            FileCacheManager().get_cached_file_content(os.path.expanduser(file_path))
        )
        val = value_extractor(content)
        if val is None or not val.strip():
            raise ServerExtensionException(f"No value found in {file_path}.")
        return value_extractor(content)
