import asyncio
import datetime
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import requests
from sagemaker_jupyterlab_extension_common.util.environment import (
    Environment,
)

from amazon_sagemaker_jupyter_ai_q_developer.constants import (
    Q_DEVELOPER_SETTINGS_ENDPOINT,
)
from amazon_sagemaker_jupyter_ai_q_developer.exceptions import ServerExtensionException
from amazon_sagemaker_jupyter_ai_q_developer.file_cache_manager import FileCacheManager

logging.basicConfig(format="%(levelname)s: %(message)s")


def get_settings_property_value(settings_data, key, secondary_default):
    default_value = (
        settings_data.get("schema", {})
        .get("properties", {})
        .get(key, {})
        .get("default", secondary_default)
    )
    value = settings_data.get("settings", {}).get(key, default_value)
    return value


def get_q_dev_settings():
    return requests.get(Q_DEVELOPER_SETTINGS_ENDPOINT)


async def get_settings_async(metrics):
    settings = {
        "share_content_with_aws": False,
        "suggestions_with_code_references": False,
        "telemetry_enabled": False,
        "log_level": "ERROR",
    }
    get_settings_start_time = datetime.datetime.now()
    try:
        # Q_DEVELOPER_SETTINGS_ENDPOINT is in parity with base url from SMD so in local development
        # it won't be able to fetch settings and also locally headers have to be manually appended for this to work
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(executor, get_q_dev_settings)
        settings_data = response.json()

        settings["share_content_with_aws"] = get_settings_property_value(
            settings_data, "shareCodeWhispererContentWithAWS", False
        )
        settings["suggestions_with_code_references"] = get_settings_property_value(
            settings_data, "suggestionsWithCodeReferences", False
        )
        settings["telemetry_enabled"] = get_settings_property_value(
            settings_data, "codeWhispererTelemetry", False
        )
        settings["log_level"] = get_settings_property_value(
            settings_data, "codeWhispererLogLevel", "ERROR"
        )
    except Exception as e:
        logging.warning(f"Can not read Q Developer settings, using default values. Error: {e}")
    finally:
        elapsed = datetime.datetime.now() - get_settings_start_time
        metrics.put_metric("SettingsLatency", int(elapsed.total_seconds() * 1000), "Milliseconds")
    return settings


def get_q_dev_profile_arn(environment: Environment):
    if environment == Environment.STUDIO_IAM or environment == Environment.MD_IAM:
        return "dummy_profile_arn"  # Not needed as of now for Free tier
    return extractor("~/.aws/amazon_q/q_dev_profile.json", lambda d: d["q_dev_profile_arn"])


def get_q_customization_arn(environment: Environment):
    if environment in [Environment.STUDIO_SSO, Environment.MD_IDC]:
        return extractor("~/.aws/amazon_q/customization_arn.json", lambda d: d["customization_arn"])
    return None


def get_smus_q_enabled(environment: Environment):
    """To check q_enabled flag value for default space only"""
    if environment == Environment.MD_IAM and not is_smus_default_space():
        return True  # Enable Q Free Tier access for non-default IDE space
    return extractor("~/.aws/amazon_q/settings.json", lambda d: d["q_enabled"])


def extractor(file_path=None, value_extractor=None):
    content = json.loads(FileCacheManager().get_cached_file_content(os.path.expanduser(file_path)))
    val = value_extractor(content)

    if isinstance(val, bool):
        return value_extractor(content)
    if val is None or not val.strip():
        raise ServerExtensionException(f"No value found in {file_path}.")
    return value_extractor(content)


def is_smus_environment(environment: Environment):
    return environment in [
        Environment.MD_IAM,
        Environment.MD_IDC,
        Environment.MD_SAML,
    ]


def get_ide_category(environment: Environment):
    if is_smus_environment(environment):
        return "JUPYTER_MD"
    else:
        return "JUPYTER_SM"


def getQTelemetryInteractionType(interactionType):
    if interactionType == "copy":
        return "COPY_SNIPPET"
    elif interactionType == "insert-above":
        return "INSERT_AT_CURSOR"
    elif interactionType == "insert-below":
        return "INSERT_AT_CURSOR"
    elif interactionType == "replace":
        return "INSERT_AT_CURSOR"
    elif interactionType == "upvote":
        return "UPVOTE"
    elif interactionType == "downvote":
        return "DOWNVOTE"
    else:
        return "UNKNOWN"


def get_telemetry_event(
    telemetry_event_type,
    conversation_id,
    request_id,
    metrics,
    q_dev_profile_arn,
    telemetry_event=None,
):
    t_event = {
        telemetry_event_type: {
            "conversationId": conversation_id,
            "messageId": request_id,
        },
    }

    if telemetry_event_type == "chatInteractWithMessageEvent" and telemetry_event:
        interactionType = getQTelemetryInteractionType(telemetry_event["type"])
        t_event[telemetry_event_type]["interactionType"] = interactionType
        metrics.put_dimensions({"InteractionType": interactionType})

        code = telemetry_event.get("code", {})
        charCount = code.get("charCount", None)
        if charCount is not None:
            t_event[telemetry_event_type]["acceptedCharacterCount"] = charCount
            metrics.put_metric("CharCount", int(charCount))

        lineCount = code.get("lineCount", None)
        if lineCount is not None:
            t_event[telemetry_event_type]["acceptedLineCount"] = lineCount
            metrics.put_metric("LineCount", int(lineCount))

    metrics.set_property("QDevProfileArn", q_dev_profile_arn)
    return t_event


def is_smus_default_space():
    amazon_q_directory = "/home/sagemaker-user/.aws/amazon_q"
    amazon_q_settings_file = os.path.join(amazon_q_directory, "settings.json")
    try:
        if os.path.exists(amazon_q_directory) and os.path.exists(amazon_q_settings_file):
            return True
    except Exception as e:
        logging.error(f"Error checking default space: {e}")
    return False
