import logging
import os
from importlib.metadata import version

from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.serializers.log_serializer import LogSerializer
from sagemaker_jupyterlab_extension_common.util.app_metadata import (
    get_aws_account_id,
    get_domain_id,
    get_space_name,
    get_user_profile_name,
)

from amazon_sagemaker_jupyter_ai_q_developer.constants import (
    LOG_FILE_NAME,
    LOG_FILE_PATH,
    LOGGER_NAME,
    METRICS_NAMESPACE,
)


def init_api_operation_logger(server_log):
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    log_file_location = os.path.join(LOG_FILE_PATH, LOG_FILE_NAME)

    try:
        os.makedirs(LOG_FILE_PATH, exist_ok=True)
        log_file_location = os.path.join(LOG_FILE_PATH, LOG_FILE_NAME)
        file_handler = logging.FileHandler(log_file_location)
        logger.addHandler(file_handler)
        server_log.info(
            f"Q Dev Chat API Logger Initialized and logs in - {log_file_location},{LOGGER_NAME}"
        )
    except Exception as ex:
        server_log.info(
            f"Unable to create log file directory - {LOG_FILE_PATH}, {ex}, using StreamHandler"
        )
        logger.addHandler(logging.StreamHandler())
    logger.propagate = False


def get_new_metrics_context(operation: str, environment: str):
    context = MetricsContext().empty()
    context.namespace = METRICS_NAMESPACE
    context.should_use_default_dimensions = False
    context.put_dimensions({"Operation": operation})
    context.set_property("AccountId", get_aws_account_id())
    context.put_dimensions({"Environment": environment})
    context.put_dimensions(
        {"QChatExtensionVersion": version("amazon_sagemaker_jupyter_ai_q_developer")}
    )
    context.put_dimensions(
        {"CommonExtensionVersion": version("sagemaker-jupyterlab-extension-common")}
    )
    context.set_property("DomainId", get_domain_id())
    context.set_property("SpaceName", get_space_name())
    context.set_property("UserProfileName", get_user_profile_name())
    return context


def flush_metrics(ctx):
    logger = logging.getLogger(LOGGER_NAME)
    for serialized_content in LogSerializer.serialize(ctx):
        if serialized_content:
            logger.info(serialized_content)
