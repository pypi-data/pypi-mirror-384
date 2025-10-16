import json
import logging
import os
import random
import threading
import time

from databricks.feature_store.utils.lakebase_constants import (
    TOKEN_REFRESH_BASE_RETRY_DELAY_SECONDS,
    TOKEN_REFRESH_DURATION_SECONDS,
    TOKEN_REFRESH_JITTER_MAX_SECONDS,
    TOKEN_REFRESH_MAX_RETRIES,
)
from databricks.feature_store.utils.logging_utils import get_logger

_logger = get_logger(__name__, log_level=logging.INFO)


class OAuthTokenManager:
    def __init__(self, oauth_token_file_path: str, password_override: str = None):
        self._oauth_token = None
        self._password = password_override
        self._oauth_token_file_path = oauth_token_file_path
        self.refresh_oauth_token()

        self._run_token_refresh_thread = True
        self._token_refresh_thread = threading.Thread(
            target=self._refresh_oauth_token_loop
        )
        # Enable daemon thread to ensure the thread exits when the main thread exits.
        self._token_refresh_thread.daemon = True

    def start_token_refresh_thread(self):
        self._token_refresh_thread.start()

    def refresh_oauth_token(self, retry_count=0):
        """
        Periodically refresh from mounted secret file. Upstream validation ensures this path
        should exist.
        """
        if self._password:
            # If password is provided by endpoint deployer and is NOT expected to be
            # rotated, use it instead of oauth token.
            return
        should_retry = False

        if not os.path.exists(self._oauth_token_file_path):
            # File doesn't exist yet, trigger retry logic
            if retry_count >= TOKEN_REFRESH_MAX_RETRIES:
                raise Exception("OAuth token file not found and max retries exceeded.")
            should_retry = True
        else:
            with open(self._oauth_token_file_path, "r") as f:
                try:
                    oauth_dict = json.load(f)
                    ret_val = oauth_dict["OAUTH_TOKEN"][0]["oauthTokenValue"]
                    self._oauth_token = ret_val
                except Exception:
                    # Remediation for potential race condition in which the read occurs
                    # simultaneously with the secret mount update, resulting in a malformed
                    # token
                    if retry_count >= TOKEN_REFRESH_MAX_RETRIES:
                        raise Exception(
                            "Invalid online store credential configuration."
                        )
                    should_retry = True
        if should_retry:
            # Exponential backoff with jitter
            jitter = random.randint(0, TOKEN_REFRESH_JITTER_MAX_SECONDS)
            time.sleep(
                TOKEN_REFRESH_BASE_RETRY_DELAY_SECONDS * (2**retry_count) + jitter
            )
            if retry_count > 3:
                _logger.warning(
                    f"Retrying to read oauth token for the {retry_count - 1} time."
                )
            self.refresh_oauth_token(retry_count + 1)

    def _refresh_oauth_token_loop(self):
        """
        Periodically refresh from mounted secret file. Upstream validation ensures this path
        should exist.
        """
        while self._run_token_refresh_thread:
            # Adding a jitter to avoid all threads refreshing at the same time.
            jitter = random.randint(0, TOKEN_REFRESH_JITTER_MAX_SECONDS)
            time.sleep(TOKEN_REFRESH_DURATION_SECONDS + jitter)
            self.refresh_oauth_token()

    def get_oauth_token_or_password(self):
        if self._password:
            # Password is provided to override the oauth token.
            return self._password
        if not self._oauth_token:
            self.refresh_oauth_token()
        return self._oauth_token
