from dotenv import load_dotenv
import os
import logging
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)


def get_client():
    """Return a Groq client using GROQ_API_KEY.

    Returns a `groq.Groq` client instance or None if no key is configured.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        logger.info("GROQ_API_KEY detected — using Groq native client")
        try:
            return Groq(api_key=groq_key)
        except Exception as e:
            logger.exception("Failed to create Groq client: %s", e)
            return None

    logger.warning("No GROQ_API_KEY configured")
    return None
