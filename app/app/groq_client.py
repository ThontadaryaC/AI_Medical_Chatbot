import os


def get_text_model():
    """Return the text model name to use for Groq text tasks.

    Can be overridden via GROQ_TEXT_MODEL or the legacy SUPERATE_TEXT_MODEL env var.
    Use a currently supported Groq model name such as llama-3.3-70b-versatile.
    """
    return (
        os.getenv("GROQ_TEXT_MODEL")
        or os.getenv("SUPERATE_TEXT_MODEL")
        or "llama-3.3-70b-versatile"
    )


def get_vision_model():
    """Return the vision model name to use for Groq vision tasks.

    Can be overridden via GROQ_VISION_MODEL or the legacy SUPERATE_VISION_MODEL env var.
    Use a currently supported Groq vision model such as llama-3.2-11b-vision-preview.
    """
    return (
        os.getenv("GROQ_VISION_MODEL")
        or os.getenv("SUPERATE_VISION_MODEL")
        or "llama-3.2-11b-vision-preview"
    )


def create_chat_completion(client, model, messages, **kwargs):
    """Wrapper around Groq's chat completion call using native SDK.

    Keeps call sites consistent and centralizes Groq-specific calls.
    """
    return client.chat.completions.create(model=model, messages=messages, **kwargs)
