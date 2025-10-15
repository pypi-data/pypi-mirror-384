from sagemaker_jupyterlab_extension_common.dual_stack_utils import is_dual_stack_enabled

LOG_FILE_NAME = "q-dev-chat.api.log"
LOGGER_NAME = "q-dev-chat-api-operations"
LOG_FILE_PATH = "/var/log/studio/q_dev_chat"
LOG_FILE_NAME = "q_dev_chat_api.log"
METRICS_NAMESPACE = "QDevChat"
# /jupyterlab/default part of the Q_DEVELOPER_SETTINGS_ENDPOINT should be the same as --ServerApp.base_url
# it is defined within the Sagemaker Distribution image so we have to keep parity
# see this for more info https://github.com/aws/sagemaker-distribution/blob/main/template/v1/dirs/usr/local/bin/start-jupyter-server
Q_DEVELOPER_SETTINGS_ID = "amazon-q-developer-jupyterlab-ext:completer"
Q_DEVELOPER_SETTINGS_ENDPOINT = (
    f"http://localhost:8888/jupyterlab/default/lab/api/settings/{Q_DEVELOPER_SETTINGS_ID}"
)
USE_DUALSTACK_ENDPOINT = is_dual_stack_enabled()

# Origin for SMUS environment requests
MD_IDE = "MD_IDE"
