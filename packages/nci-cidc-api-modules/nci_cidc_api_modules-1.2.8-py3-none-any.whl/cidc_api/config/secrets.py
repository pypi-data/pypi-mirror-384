from os import environ
from google.cloud import secretmanager


def get_secrets_manager(is_testing=False):
    """
    Get a secrets manager based on whether the app is running in test mode
    """
    if is_testing:
        from unittest.mock import MagicMock

        # If we're testing, we shouldn't need access to secrets in Secret Manager
        return MagicMock()

    return GoogleSecretManager()


class GoogleSecretManager:
    """
    Get secrets (e.g., API keys, db passwords) from Google Secret Manager
    (defaults to latest version).
    """

    def __init__(self, version_id="latest"):
        """
        Initialize a GoogleSecretManager with a connection to Google Secret Manager.
        """
        self.version_id = version_id
        self.client = secretmanager.SecretManagerServiceClient()

    @property
    def project_id(self):
        # This env variable is automatically set in GAE.
        # Be sure to set it locally if not running in GAE.
        return environ.get("GOOGLE_CLOUD_PROJECT")

    def get(self, secret_id):
        """
        Try to find a secret in Google Secret Manager.
        Raises a google.api_core.exceptions.NotFound exception
        if the secret_id/version_id doesn't exist.
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{self.version_id}"
        response = self.client.access_secret_version(name=name)
        secret = response.payload.data.decode("UTF-8")

        return secret
