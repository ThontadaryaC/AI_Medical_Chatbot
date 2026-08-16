import streamlit as st
from pathlib import Path
import base64
import os
import sys
import logging
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import tempfile

# MUST be the first Streamlit command!
st.set_page_config(page_title="AI Medical ChatBot", layout="wide")

# Add current directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from tts_manager import speak_text_async, cleanup_tts
    TTS_AVAILABLE = True
except ImportError as e:
    logging.error(f"TTS not available: {e}")
    TTS_AVAILABLE = False
    # Create dummy functions for fallback
    def speak_text_async(text):
        logging.warning(f"TTS not available, would speak: {text[:50]}...")
        return False
    def cleanup_tts():
        pass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Chat history management functions
def save_chat(chat_id, title, messages):
    """Save a chat to JSON file"""
    chat_data = {
        "id": chat_id,
        "title": title,
        "messages": messages,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    filename = f"chats/{chat_id}.json"
    # Ensure chats directory exists before writing
    chats_dir = Path("chats")
    try:
        chats_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.exception("Failed to create chats directory: %s", e)

    with open(filename, 'w') as f:
        json.dump(chat_data, f, indent=2)

def load_chat(chat_id):
    """Load a chat from JSON file"""
    filename = f"chats/{chat_id}.json"
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return None

def delete_chat(chat_id):
    """Delete a chat file"""
    filename = f"chats/{chat_id}.json"
    if os.path.exists(filename):
        os.remove(filename)

def list_chats():
    """List all saved chats"""
    if not os.path.exists("chats"):
        return []
    chats = []
    for file in os.listdir("chats"):
        if file.endswith(".json"):
            chat_id = file[:-5]  # Remove .json
            chat_data = load_chat(chat_id)
            if chat_data:
                chats.append(chat_data)
    # Sort by updated_at descending
    chats.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return chats

def generate_chat_title(messages):
    """Generate a title from the first user message"""
    for msg in messages:
        if msg["role"] == "user":
            title = msg["content"][:50].strip()
            if len(msg["content"]) > 50:
                title += "..."
            return title
    return "New Chat"

def load_bg_image(image_path):
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct absolute path to the assets folder
    full_path = os.path.join(current_dir, "..", image_path)
    # If the expected path doesn't exist, try common workspace assets locations
    alt_path = os.path.join(current_dir, "..", "..", "assets", "assets", os.path.basename(image_path))
    if not os.path.exists(full_path) and os.path.exists(alt_path):
        full_path = alt_path

    if not os.path.exists(full_path):
        logging.warning(f"Background image not found at {full_path} or fallback locations.")
        return ""

    with open(full_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return encoded


def apply_theme(theme):
    if theme == "Light":
        bg_image = load_bg_image("assets/light_bg.png")
        text_color = "#000000"
        chat_user_bg = "#DCF8C6"
        chat_bot_bg = "#F1F0F0"
        button_color = "#4CAF50"
        button_text_color = "#ffffff"
        tab_bg_color = "transparent"
        tab_text_color = "red"
    else:
        bg_image = load_bg_image("assets/dark_bg.png")
        text_color = "#FFFFFF"
        chat_user_bg = "#2b7a78"
        chat_bot_bg = "#3a3a3a"
        button_color = "#1E88E5"
        button_text_color = "#ffffff"
        tab_bg_color = "transparent"
        tab_text_color = "red"

    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{bg_image}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        color: {text_color};
    }}

    /* Global text color override for all markdown and text elements */
    .stMarkdown {{
        color: {text_color} !important;
    }}
    .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: {text_color} !important;
    }}
    .stText {{
        color: {text_color} !important;
    }}
    label {{
        color: {text_color} !important;
    }}

    /* Tabs background and text color */
    .stTabs [role="tablist"] button[role="tab"] {{
        background-color: {tab_bg_color} !important;
        color: {tab_text_color} !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        margin: 0 0.25rem !important;
        border-radius: 0.25rem !important;
    }}

    .stTabs [role="tablist"] button[role="tab"][aria-selected="true"] {{
        background-color: transparent !important;
        color: {tab_text_color} !important;
        border-bottom: none !important;
        font-weight: bold;
    }}

    .stTabs [role="tablist"] button[role="tab"]:hover {{
        background-color: transparent !important;
        color: {tab_text_color} !important;
    }}

    /* Chat Messages Styling - Enhanced for full visibility */
    .stChatMessage {{
        background-color: transparent;
    }}
    .stChatMessage * {{
        color: {text_color} !important;
    }}
    .stChatMessage [data-testid="chatAvatarIcon-user"] {{
        background-color: {button_color};
    }}
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {{
        background-color: {button_color};
    }}

    /* Ensure text is visible in both themes - Expanded */
    .stChatMessage .stMarkdown p {{
        color: {text_color} !important;
        font-size: 16px;
        line-height: 1.5;
    }}

    /* Input and form elements styling for visibility */
    .stChatInput {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: {text_color} !important;
    }}
    .stChatInput input {{
        color: {text_color} !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
    }}
    .stTextInput > div > div > input {{
        color: {text_color} !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
    }}
    .stTextArea > div > textarea {{
        color: {text_color} !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
    }}
    .stSelectbox > div > div {{
        color: {text_color} !important;
    }}
    .stFileUploader label {{
        color: {text_color} !important;
    }}
    .stFileUploader > div > div {{
        color: {text_color} !important;
    }}

    /* Streamlit Button Styling */
    button[data-baseweb="button"] {{
        background-color: {button_color} !important;
        color: {button_text_color} !important;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
    }}

    /* Fix label padding */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }}

    /* Sidebar styling */
    .css-1d391kg {{
        background-color: rgba(0, 0, 0, 0.1) !important;
        color: {text_color} !important;
    }}
    .css-1d391kg * {{
        color: {text_color} !important;
    }}

    /* Ensure all tab content text is visible */
    section[data-testid="stHorizontalBlock"] * {{
        color: {text_color} !important;
    }}

    /* Chat select buttons styling */
    .stButton button[key^="select_"] {{
        background: none !important;
        border: none !important;
        color: {text_color} !important;
        text-align: left !important;
        padding: 0 !important;
        font-size: inherit !important;
        width: 100% !important;
        cursor: pointer !important;
    }}
    .stButton button[key^="select_"]:hover {{
        background: rgba(255,255,255,0.1) !important;
    }}

    /* Chat delete buttons styling */
    .stButton button[key^="delete_"] {{
        background: none !important;
        border: none !important;
        color: #ff6b6b !important;
        padding: 0 !important;
        font-size: 16px !important;
        cursor: pointer !important;
    }}
    .stButton button[key^="delete_"]:hover {{
        background: rgba(255, 0, 0, 0.1) !important;
    }}
    </style>"""
    st.markdown(css, unsafe_allow_html=True)



# Initialize theme in session state if not exists
if "theme" not in st.session_state:
    st.session_state.theme = "Light"

# Create a single toggle button for theme
st.sidebar.header("🌓 Theme Toggle")
if st.sidebar.button(f"Switch to {'Dark' if st.session_state.theme == 'Light' else 'Light'} Mode"):
    st.session_state.theme = "Dark" if st.session_state.theme == "Light" else "Light"
    st.rerun()

# Translator Section in Sidebar
st.sidebar.header("🌐 Language Translator")
st.sidebar.markdown("---")

# Initialize language preference in session state
if "language_preference" not in st.session_state:
    st.session_state.language_preference = "hi"  # Default to Hindi

# Language selection dropdown
language_options = [
    ("English", "en"),
    ("Hindi", "hi"),
    ("Kannada", "kn"),
    ("Telugu", "te"),
    ("Tamil", "ta"),
    ("Marathi", "mr"),
]

selected_lang = st.sidebar.selectbox(
    "Select Language:",
    language_options,
    format_func=lambda x: x[0],
    index=1,  # Default to Hindi (index 1)
    key="language_selector"
)

# Update session state when language changes
if selected_lang[1] != st.session_state.language_preference:
    st.session_state.language_preference = selected_lang[1]
st.sidebar.success(f"Language set to {selected_lang[0]}")

# Chat History Section in Sidebar
st.sidebar.header("💬 Chat History")
st.sidebar.markdown("---")

# Initialize current chat ID if not exists
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# New Chat button
if st.sidebar.button("➕ New Chat", type="primary"):
    # Save current chat if it exists and has messages
    if st.session_state.current_chat_id and len(st.session_state.chat_history) > 1:
        title = generate_chat_title(st.session_state.chat_history)
        save_chat(st.session_state.current_chat_id, title, st.session_state.chat_history)

    # Create new chat
    new_chat_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_chat_id
    st.session_state.chat_history = [
        {"role": "system", "content": "You are an intelligent AI medical assistant. Answer accurately and clearly. If the user asks about analyzing medical images, translating reports, or finding hospitals, guide them to use the Image Analysis, Report Reader, or Hospital Locator tabs respectively. For other medical queries, provide direct answers without mentioning other features."}
    ]
    st.rerun()

# List saved chats
saved_chats = list_chats()
if saved_chats:
    st.sidebar.subheader("Recent Chats")
    for chat in saved_chats:
        # Create a flex container for each chat item
        chat_html = f"""
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; border-radius: 0.25rem; margin-bottom: 0.25rem;">
            <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                📝 {chat['title']}
            </div>
        </div>
        """
        st.sidebar.markdown(chat_html, unsafe_allow_html=True)

        # Use columns for buttons but make them invisible and position them absolutely
        col1, col2 = st.sidebar.columns([1, 0.1])
        with col1:
            if st.sidebar.button(chat['title'], key=f"select_{chat['id']}", help="Select this chat"):
                # Save current chat first
                if st.session_state.current_chat_id and len(st.session_state.chat_history) > 1:
                    title = generate_chat_title(st.session_state.chat_history)
                    save_chat(st.session_state.current_chat_id, title, st.session_state.chat_history)

                # Load selected chat
                st.session_state.current_chat_id = chat['id']
                st.session_state.chat_history = chat['messages']
                st.rerun()
        with col2:
            if st.sidebar.button("🗑️", key=f"delete_{chat['id']}", help="Delete this chat"):
                delete_chat(chat['id'])
                # If deleting current chat, reset to new chat
                if st.session_state.current_chat_id == chat['id']:
                    st.session_state.current_chat_id = None
                    st.session_state.chat_history = [
                        {"role": "system", "content": "You are an intelligent AI medical assistant. Answer accurately and clearly. If the user asks about analyzing medical images, translating reports, or finding hospitals, guide them to use the Image Analysis, Report Reader, or Hospital Locator tabs respectively. For other medical queries, provide direct answers without mentioning other features."}
                    ]
                st.rerun()
else:
    st.sidebar.info("No saved chats yet. Start a conversation!")

# Apply the theme
apply_theme(st.session_state.theme)

# Logo and title
st.markdown(
    """
    <div style='display: flex; align-items: center; justify-content: center;'>
        <img src='https://cdn-icons-png.flaticon.com/512/3774/3774299.png' width='60'>
        <h1 style='padding-left: 20px;'>AI_Medical_ChatBot</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Tabs for different functionalities
tabs = ["Chat", "Image Analysis", "Report Reader", "Hospital Locator"]
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

tab_objects = st.tabs(tabs)

with tab_objects[0]:
    from chat import chat_with_bot

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "system", "content": "You are an intelligent AI medical assistant. Answer accurately and clearly. If the user asks about analyzing medical images, translating reports, or finding hospitals, guide them to use the Image Analysis, Report Reader, or Hospital Locator tabs respectively. For other medical queries, provide direct answers without mentioning other features."}
        ]

    # Simple chat interface - Display messages first
    if st.session_state.chat_history and len(st.session_state.chat_history) > 1:
        st.markdown("### 💬 Chat with AI Assistant")

        # Display chat messages with TTS buttons
        for idx, message in enumerate(st.session_state.chat_history[1:]):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    col1, col2 = st.columns([4,1])
    with col1:
        user_input = st.chat_input("Type your message here...", key="chat_input")
        if user_input:
            cleaned_input = user_input.strip()
            st.session_state.chat_history.append({"role": "user", "content": cleaned_input})
    
             # Immediately rerun to show user message
            st.rerun()

# After rerun, continue here if assistant needs to reply
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            reply, _ = chat_with_bot(st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

            # Auto-save the chat after assistant reply
            if st.session_state.current_chat_id:
                title = generate_chat_title(st.session_state.chat_history)
                save_chat(st.session_state.current_chat_id, title, st.session_state.chat_history)

            st.rerun()

    with col2:
        if TTS_AVAILABLE:
            if st.button("🔊 Speak"):
                last_assistant_msg = next((msg for msg in reversed(st.session_state.chat_history) if msg["role"] == "assistant"), None)
                if last_assistant_msg:
                    if speak_text_async(last_assistant_msg["content"]):
                        st.success("🔊 Speaking...")
                    else:
                        st.error("❌ TTS not available. Please check your audio settings.")
                else:
                    st.warning("No assistant message to speak.")
        else:
            st.button("🔊 Speak", disabled=True)
            st.info("🔊 TTS not available - Audio system not detected")

with tab_objects[1]:
    from image_analysis import analyze_medical_image

    st.subheader("🖼️ Medical Image Analysis")

    uploaded_image = st.file_uploader("Upload a medical image (X-ray, tumor, skin rash)", type=["png", "jpg", "jpeg"])

    if uploaded_image:
        # Save temporarily
        temp_path = "temp_image.jpg"
        with open(temp_path, "wb") as f:
            f.write(uploaded_image.getbuffer())

        # Select image type
        image_type = st.selectbox("Select image type", ["X-ray", "CT Scan", "MRI Scan", "Skin Rash"])

        if st.button("Analyze Image"):
            with st.spinner("Analyzing image..."):
                result = analyze_medical_image(temp_path, image_type)
            st.success("Analysis Result:")
            st.write(result)

        # Display the image
        st.image(uploaded_image, caption="Uploaded Image")

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

with tab_objects[2]:
    from report_translator import extract_text, translate_text
    st.subheader("📄 Upload Medical Report Image")

    uploaded_file = st.file_uploader("Choose an image or PDF file", type=["png", "jpg", "jpeg", "pdf"])

    # Use the global language preference from sidebar
    current_lang = st.session_state.get("language_preference", "hi")
    lang_name = next(name for name, code in language_options if code == current_lang)

    st.info(f"🌐 Translation will be in: **{lang_name}** (Change in sidebar)")

    if uploaded_file:
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_file_path = temp_file.name

        try:
            with st.spinner("🔍 Extracting text from image..."):
                extracted = extract_text(temp_file_path)
                st.text_area("📝 Extracted Text:", extracted, height=200)

            if st.button("🌐 Translate"):
                translated = translate_text(extracted, dest_lang=current_lang, dest_lang_name=lang_name)
                st.success("✅ Translated Report:")
                st.text_area("🌍 Translation:", translated, height=200)
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

with tab_objects[3]:
    from hospital_locator import find_nearest_hospitals

    st.subheader("🗺️ Find Nearest Hospitals")

    # Location input options
    col1, col2 = st.columns([3, 1])
    with col1:
        location_input = st.text_input("Enter your City or Area (e.g., Mumbai, Bangalore):", key="location_input")
    with col2:
        use_current_location = st.checkbox("📍 Use Current Location", key="use_current_location")

    # Hospital type selection
    hospital_types = {
        "All Hospitals": "hospital",
        "Emergency": "emergency",
        "General Hospital": "general+hospital",
        "Specialized": "specialized+hospital",
        "24/7 Hospital": "24+hour+hospital"
    }

    selected_hospital_type = st.selectbox(
        "Hospital Type:",
        options=list(hospital_types.keys()),
        index=0,
        key="hospital_type"
    )

    # Search radius
    radius_options = {
        "1 km": 1000,
        "2 km": 2000,
        "5 km": 5000,
        "10 km": 10000,
        "25 km": 25000
    }

    selected_radius = st.selectbox(
        "Search Radius:",
        options=list(radius_options.keys()),
        index=2,  # Default to 5 km
        key="search_radius"
    )

    # Search button
    if st.button("🔍 Find Hospitals", type="primary"):
        if not location_input and not use_current_location:
            st.error("Please enter a location or enable current location detection.")
        else:
            hospitals, center = find_nearest_hospitals(
                location_input=location_input,
                use_current_location=use_current_location,
                radius=radius_options[selected_radius],
                hospital_type=hospital_types[selected_hospital_type]
            )

            # Note: Google Maps link is displayed directly in find_nearest_hospitals function
            # Users can click to open Google Maps for hospital search
            st.success("✅ Click the Google Maps button above to find hospitals!")

    # Note: Hospital locator now uses Google Maps link - no API key required!
    st.info("✅ Hospital locator uses Google Maps link - no API key needed!")
