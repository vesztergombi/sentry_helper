

sentry_module = """import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration
from {} import {} as configuration

if configuration.sentry_enabled:
    sentry_sdk.init(
        configuration.sentry_integration_url,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
        release=configuration.version,
        attach_stacktrace=True
    )

"""

variable_tf_appendage = """
variable "sentry_enabled" { 
    default = false
}
variable "sentry_integration_url" {
    default = ""
}

"""

requirements_txt_appendage = """sentry-sdk>=1.5.12,<2
"""

import_sentry = """import src.sentry
"""

sentry_main_tf = ['--sentryEnabled ${var.sentry_enabled} \\\n',
                  '--sentryIntegrationUrl ${var.sentry_integration_url} \\\n']

serverless_custom = ["  sentryEnabled: ${opt:sentryEnabled, ''}\n",
                     "  sentryIntegrationUrl: ${opt:sentryIntegrationUrl, ''}\n"]


def configuration_patch(indent, get_env):
    return [f'{indent}self.version: str = {get_env}("VERSION", "0.0.0")\n',
            f'{indent}self.sentry_enabled: str = {get_env}("SENTRY_ENABLED", False)\n',
            f'{indent}self.sentry_integration_url: str = {get_env}("SENTRY_INTEGRATION_URL", "")\n']


def serverless_env(prefix):
    return [f"    {prefix}_SENTRY_ENABLED: ${{self:custom.sentryEnabled}}\n",
            f"    {prefix}_SENTRY_INTEGRATION_URL: ${{self:custom.sentryIntegrationUrl}}\n",
            f"    {prefix}_VERSION: ${{opt:ver, '0.0.0'}}\n"]
