"""
Constants for brickstore integration.
"""
# Token should be updated every 30 mins by serving scheduler.
# Implement more frequent refresh for safety.
TOKEN_REFRESH_DURATION_SECONDS = 5 * 60
TOKEN_REFRESH_JITTER_MAX_SECONDS = 10
TOKEN_REFRESH_BASE_RETRY_DELAY_SECONDS = 2
# Max retry attempts == 9, meaning at most 10 attempts with total retry time 1024 seconds (17 minutes).
TOKEN_REFRESH_MAX_RETRIES = 9

# Mount folder for served model secrets.
SECRET_MOUNT_LOCATION = "/var/credentials-secret"

# HTTP gateway oauth token
BRICKSTORE_OAUTH_TOKEN_FILE_NAME = "brickstore-feature-lookup"
BRICKSTORE_OAUTH_TOKEN_FILE_PATH = (
    SECRET_MOUNT_LOCATION + "/" + BRICKSTORE_OAUTH_TOKEN_FILE_NAME
)

# PgSQL oauth token
LAKEBASE_OAUTH_TOKEN_FILE_NAME = "lakebase-sql-feature-lookup"
LAKEBASE_OAUTH_TOKEN_FILE_PATH = (
    SECRET_MOUNT_LOCATION + "/" + LAKEBASE_OAUTH_TOKEN_FILE_NAME
)

# User for Lakebase PgSql. This is PG role created for the service principal.
# It can also be overridden by the user by setting the environment variable.
LAKEBASE_USER = "LAKEBASE_USER"
# Password for Lakebase PgSql. If specified, this will override the oauth token.
LAKEBASE_PASSWORD = "LAKEBASE_PASSWORD"
# If set to true, postgres connection is allowed.
# Note that the actual eligibility is determined by the features used.
FEATURE_SERVING_HP = "FEATURE_SERVING_HP"
