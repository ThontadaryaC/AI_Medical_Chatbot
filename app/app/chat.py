import os
from dotenv import load_dotenv
from report_translator import translate_text
from ai_client import get_client
from groq_client import get_text_model

load_dotenv()

# Use Groq's native text model
MODEL_NAME = get_text_model()


def chat_with_bot(messages, target_lang=None):
    try:
        client = get_client()
        if client is None:
            return ("❌ Error: No API key configured. Set GROQ_API_KEY.", None)

        # Send message to Groq API
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=512,
        )

        reply = response.choices[0].message.content.strip()

        # Optional translation
        translated_reply = None
        if target_lang:
            translated_reply = translate_text(reply, target_lang)

        return reply, translated_reply

    except Exception as e:
        return f"❌ Error: {str(e)}", None
