# amazon_sagemaker_jupyter_ai_q_developer

A JupyterLab extension.

This extension is composed of a Python package named `amazon_sagemaker_jupyter_ai_q_developer`
for the server extension and a NPM package named `amazon_sagemaker_jupyter_ai_q_developer`
for the frontend extension.

## Requirements
* JupyterLab >= 4 < 4.2
* jupyter-ai >= 2.26.0 < 3
* jupyter-ai-magics >= 2.26.0 <3
* sagemaker-jupyterlab-extension-common >= 0.1.26 < 1
* boto3

## Installing the extension
To install the extension within local Jupyter environment, a Docker image/container or in SageMaker Studio, run:
```
pip install amazon_sagemaker_jupyter_ai_q_developer-<version>-py3-none-any.whl`
```

## Uninstalling the extension
To uninstall this extension, run:
```
pip uninstall amazon_sagemaker_jupyter_ai_q_developer`
```

### Troubleshooting
If you are seeing the frontend extension, but it is not working, check that the server extension is enabled:

```
jupyter serverextension list
```

If the server extension is installed and enabled, but you are not seeing the frontend extension, check the frontend extension is installed:
```
jupyter labextension list
```
