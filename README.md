# AI Medical ChatBot — Groq Superate-2 integration

This project uses Groq models for chat, image analysis, and report simplification.

- Text chat and report simplification use `GROQ_TEXT_MODEL` or the legacy `SUPERATE_TEXT_MODEL` override.
- Image analysis uses `GROQ_VISION_MODEL` or the legacy `SUPERATE_VISION_MODEL` override.
- The defaults are current supported Groq models that avoid the retired `mixtral-8x7b-32768` model.

Setup:

1. Add your Groq API key to the `.env` file as `GROQ_API_KEY`.
2. Optionally override the model names in `.env` if needed.

Example `.env`:

GROQ_API_KEY=YOUR_KEY_HERE
GROQ_TEXT_MODEL=llama-3.3-70b-versatile
GROQ_VISION_MODEL=llama-3.2-11b-vision-preview

The code uses `app/groq_client.py` as a small helper to centralize model names and chat completion calls.
