"""Observability setup for Logfire."""

import os

from shotgun.logging_config import get_early_logger
from shotgun.utils.env_utils import is_falsy, is_truthy

# Use early logger to prevent automatic StreamHandler creation
logger = get_early_logger(__name__)


def setup_logfire_observability() -> bool:
    """Set up Logfire observability if enabled.

    Returns:
        True if Logfire was successfully set up, False otherwise
    """
    # Try to get Logfire configuration from build constants first, fall back to env vars
    logfire_enabled = None
    logfire_token = None

    try:
        from shotgun.build_constants import LOGFIRE_ENABLED, LOGFIRE_TOKEN

        # Use build constants if they're not empty
        if LOGFIRE_ENABLED:
            logfire_enabled = LOGFIRE_ENABLED
        if LOGFIRE_TOKEN:
            logfire_token = LOGFIRE_TOKEN
    except ImportError:
        # No build constants available
        pass

    # Fall back to environment variables if not set from build constants
    if not logfire_enabled:
        logfire_enabled = os.getenv("LOGFIRE_ENABLED", "false")
    if not logfire_token:
        logfire_token = os.getenv("LOGFIRE_TOKEN")

    # Allow environment variable to override and disable Logfire
    env_override = os.getenv("LOGFIRE_ENABLED")
    if env_override and is_falsy(env_override):
        logfire_enabled = env_override

    # Check if Logfire observability is enabled
    if not is_truthy(logfire_enabled):
        logger.debug("Logfire observability disabled via LOGFIRE_ENABLED")
        return False

    try:
        import logfire

        # Check for Logfire token
        if not logfire_token:
            logger.warning("LOGFIRE_TOKEN not set, Logfire observability disabled")
            return False

        # Configure Logfire
        # Always disable console output - we only want telemetry sent to the web service
        logfire.configure(
            token=logfire_token,
            console=False,  # Never output to console, only send to Logfire service
        )

        # Instrument Pydantic AI for better observability
        logfire.instrument_pydantic_ai()

        # Add LogfireLoggingHandler to root logger so logfire logs also go to file
        import logging

        root_logger = logging.getLogger()
        logfire_handler = logfire.LogfireLoggingHandler()
        root_logger.addHandler(logfire_handler)
        logger.debug("Added LogfireLoggingHandler to root logger for file integration")

        # Set user context using baggage for all logs and spans
        try:
            from opentelemetry import baggage, context

            from shotgun.agents.config import get_config_manager

            config_manager = get_config_manager()
            shotgun_instance_id = config_manager.get_shotgun_instance_id()

            # Set shotgun_instance_id as baggage in global context - this will be included in all logs/spans
            ctx = baggage.set_baggage("shotgun_instance_id", shotgun_instance_id)
            context.attach(ctx)
            logger.debug(
                "Logfire user context set with shotgun_instance_id: %s",
                shotgun_instance_id,
            )
        except Exception as e:
            logger.warning("Failed to set Logfire user context: %s", e)

        logger.debug("Logfire observability configured successfully")
        logger.debug("Token configured: %s", "Yes" if logfire_token else "No")
        return True

    except ImportError as e:
        logger.warning("Logfire not available: %s", e)
        return False
    except Exception as e:
        logger.warning("Failed to setup Logfire observability: %s", e)
        return False
