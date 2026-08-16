import base64
import os
from dotenv import load_dotenv
from report_translator import translate_text
from ai_client import get_client
from groq_client import get_vision_model, create_chat_completion

load_dotenv()

def analyze_medical_image(image_path, image_type, target_lang=None):
    try:
        # Encode image to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Use Groq Superate-2 (configurable via SUPERATE_VISION_MODEL)
        vision_model = get_vision_model()

        # Create prompt based on image type
        if image_type == "X-ray":
            prompt = "You are a radiologist analyzing an X-ray image. Identify any fractures, dislocations, or abnormalities in bones and joints. Describe the affected areas precisely, assess severity, and provide medical insights. Note: This is not a diagnosis - consult a healthcare professional."
        elif image_type == "CT Scan":
            prompt = "You are a radiologist analyzing a CT scan image. Identify any abnormalities in organs, tissues, or structures. Describe findings in detail, assess potential conditions, and provide medical insights. Note: This is not a diagnosis - consult a healthcare professional."
        elif image_type == "MRI Scan":
            prompt = "You are a radiologist analyzing an MRI scan image. Identify any abnormalities in soft tissues, brain, spine, or joints. Describe findings in detail, assess potential conditions, and provide medical insights. Note: This is not a diagnosis - consult a healthcare professional."
        elif image_type == "Skin Rash":
            prompt = "You are a dermatologist analyzing a skin condition image. Describe the rash appearance, distribution, and characteristics. Suggest possible causes and provide general treatment recommendations. Note: This is not a diagnosis - consult a healthcare professional."
        else:
            prompt = "Describe this medical image in detail and provide any relevant medical observations."

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
            return "❌ Error: No API key configured. Set GROQ_API_KEY."

        response = create_chat_completion(
            client,
            vision_model,
            messages,
            temperature=0.7,
            max_tokens=512,
        )

        reply = response.choices[0].message.content.strip()

        # Optional translation
        if target_lang:
            reply = translate_text(reply, target_lang)

        return reply

    except Exception as e:
        return f"❌ Error analyzing image: {str(e)}"
