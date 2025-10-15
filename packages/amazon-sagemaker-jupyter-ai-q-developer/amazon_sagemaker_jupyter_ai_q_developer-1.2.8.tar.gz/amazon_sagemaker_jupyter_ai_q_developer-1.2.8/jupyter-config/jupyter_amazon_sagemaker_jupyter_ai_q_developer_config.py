from sagemaker_jupyterlab_extension_common.identity import SagemakerIdentityProvider

# https://jupyter-server.readthedocs.io/en/latest/operators/configuring-extensions.html

c.AiExtension.default_language_model = "amazon-q:Q-Developer"  # noqa: F821
c.AiExtension.default_embeddings_model = "codesage:codesage-small"  # noqa: F821
c.ServerApp.identity_provider_class = SagemakerIdentityProvider  # noqa: F821
c.AiExtension.help_message_template = """ 
Hi there! I'm Amazon Q, your programming assistant in JupyterLab. You can ask me a question using the text box below. You can also use these commands:
{slash_commands_list}

For more information, see the [Amazon Q documentation](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/what-is.html).
""".strip()  # noqa: F821
