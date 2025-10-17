"""Build-time constants generated during packaging.

This file is auto-generated during the build process.
DO NOT EDIT MANUALLY.
"""

# Sentry DSN embedded at build time (empty string if not provided)
SENTRY_DSN = 'https://2818a6d165c64eccc94cfd51ce05d6aa@o4506813296738304.ingest.us.sentry.io/4510045952409600'

# PostHog configuration embedded at build time (empty strings if not provided)
POSTHOG_API_KEY = ''
POSTHOG_PROJECT_ID = '191396'

# Logfire configuration embedded at build time (only for dev builds)
LOGFIRE_ENABLED = 'true'
LOGFIRE_TOKEN = 'pylf_v1_us_KZ5NM1pP3NwgJkbBJt6Ftdzk8mMhmrXcGJHQQgDJ1LfK'

# Build metadata
BUILD_TIME_ENV = "production" if SENTRY_DSN else "development"
IS_DEV_BUILD = True
