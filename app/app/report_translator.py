from PIL import Image
import pytesseract
import openai
import base64
from deep_translator import GoogleTranslator
import os
from dotenv import load_dotenv
import pytesseract
import pdfplumber
import io
from ai_client import get_client
from groq_client import get_text_model, get_vision_model, create_chat_completion

load_dotenv()

# ✅ Set the correct path to Tesseract executable (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Use model names as before — these may be provider-specific. When a GROQ
# key is provided, the client will be created via `ai_client.get_client()` and
# the provider's base URL should be set via `GROQ_BASE_URL` if needed.
MODEL_NAME = get_text_model()
VISION_MODEL = get_vision_model()

# 🔍 Function to extract text from an image or PDF using LLM vision or pdfplumber
def extract_text(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        # Extract text from PDF
        try:
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"
    else:
        # Assume it's an image
        try:
            # Encode image to base64 in memory
            image = Image.open(file_path)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

            prompt = "Extract all the text from this medical report image. Provide only the extracted text without any additional comments or formatting."

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]

            client = get_client()
            if client is None:
                # No LLM client configured; fall back to local OCR
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                return text.strip()

            response = client.chat.completions.create(
                model=VISION_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=1024
            )

            extracted_text = response.choices[0].message.content.strip()
            return extracted_text
        except Exception as e:
            # Fallback to Tesseract
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()

# 🌐 Function to simplify and translate text to a specified language using LLM for simplification and GoogleTranslator for translation
def translate_text(text, dest_lang="hi", dest_lang_name="Hindi"):
    try:
        client = get_client()
        if client is None:
            # No LLM provider configured — skip simplification and just translate
            if dest_lang != "en":
                translator = GoogleTranslator(source='auto', target=dest_lang)
                final_text = translator.translate(text)
            else:
                final_text = text
            return final_text

        # First, simplify the medical report in simple words using LLM
        simplify_prompt = f"Simplify the following medical report text into simple, easy-to-understand words. Explain any medical terms in plain language. Provide only the simplified text:\n\n{text}"
        simplify_messages = [{"role": "user", "content": simplify_prompt}]
        simplify_response = create_chat_completion(
            client,
            MODEL_NAME,
            simplify_messages,
            temperature=0.5,
            max_tokens=1024,
        )
        simplified = simplify_response.choices[0].message.content.strip()

        # Then, translate to the target language using GoogleTranslator for reliability
        if dest_lang != "en":
            translator = GoogleTranslator(source='en', target=dest_lang)
            final_text = translator.translate(simplified)
        else:
            final_text = simplified

        return final_text
    except Exception as e:
        # Fallback: directly translate the original text using GoogleTranslator
        try:
            if dest_lang != "en":
                translator = GoogleTranslator(source='auto', target=dest_lang)
                final_text = translator.translate(text)
            else:
                final_text = text
            return final_text
        except Exception as fallback_e:
            # Last resort: return original text
            return text
