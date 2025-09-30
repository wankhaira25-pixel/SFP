import streamlit as st
import pandas as pd
import google.generativeai as genai
import re
import time # For simulation delay

persona_instructions = """You are Echo, an elite personal assistant designed to analyze and clone the user's communication profile. 
Your ultimate goal is to generate responses that are indistinguishable from the user's own replies.

**Primary Directive: Clone the User's Profile**
1.  **Tone & Sentiment:** (e.g., sarcastic, enthusiastic, brief, verbose).
2.  **Punctuation & Emojis:** Use their exact patterns (e.g., if they use "!", use "!!").
3.  **Core Vocabulary:** Identify and reuse the user's favorite words and slang.
4.  **Response Length:** Match the length of the user's previous inputs.

**Secondary Directive: Respond as the User**
Based on the current chat history, analyze the user's style, and then generate a reply to the *most recent* user message, exactly as they would.
"""
# --- 1. CONFIGURATION & DATABASE PLACEHOLDER ---
# WARNING: Do NOT hardcode your API key. Use st.secrets.
GOOGLE_API_KEY = "AIzaSyCLzKVjpyw_FXfdleQb26b5dxKfKMJcKQg"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Placeholder for database functions (Simulated Memory)
# In a real app, you would replace these with SQL/Postgres/etc. connection logic.
def load_user_data(username):
    # Simulate loading data from a persistent store (e.g., SQLite/Postgres)
    if username == "user1":
        return {
            "style_profile": "User exhibits a slightly sarcastic, brief tone, with an affinity for the 😅 emoji.",
            "messages": [], # Messages are usually loaded/saved separately
            "password": "password"
        }
    return None

def save_user_data(username, profile):
    # Simulate saving data to the persistent store
    st.session_state.user_style_profile = profile
    # print(f"--- FAKE DB: Profile saved for {username} ---")
    pass

# --- 2. SESSION STATE MANAGEMENT ---

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "user_style_profile" not in st.session_state:
        # Default profile for new users
        st.session_state.user_style_profile = "User currently exhibits a friendly, neutral, and curious tone."
    if "training_active" not in st.session_state:
        st.session_state.training_active = False

# --- 3. GEMINI HELPER FUNCTIONS ---

def get_gemini_response(prompt, current_profile, system_instructions):
    """Generates a response using the current style profile and instructions."""
    history = st.session_state.messages
    
    # 1. Build Context
    conversation_context = ""
    for message in history[-10:]:
        role = "User" if message["role"] == "user" else "Assistant"
        conversation_context += f"{role}: {message['content']}\n"

    # 2. Build Full Prompt
    full_prompt = (
        f"{system_instructions}\n\n"
        f"--- USER STYLE PROFILE (Clone this style) ---\n"
        f"{current_profile}\n"
        f"--- CONVERSATION HISTORY (for immediate context) ---\n"
        f"{conversation_context}"
        f"--- END CONTEXT ---\n"
        f"Respond to the user's latest input:\n"
        f"User: {prompt}\n"
        f"Assistant:"
    )
    
    response = model.generate_content(full_prompt).text
    return response

def update_style_profile(new_message):
    """Uses the model to refine the style profile based on new input."""
    current_profile = st.session_state.user_style_profile
    
    # This prompt tells the model to analyze the new input and update the profile
    profile_update_prompt = f"""
    Analyze the following user message: "{new_message}"
    
    The user's current style profile is: "{current_profile}"
    
    Based on this new message, provide a **single-sentence updated profile** focusing on tone, length, punctuation, and specific slang/emojis.
    Do NOT include any conversational text. Just the single, updated profile sentence.
    """
    
    # Use a simpler model or temperature setting for concise analysis
    updated_profile = model.generate_content(profile_update_prompt).text.strip()
    st.session_state.user_style_profile = updated_profile
    save_user_data(st.session_state.username, updated_profile)
    # st.session_state.messages.append({"role": "system", "content": f"Profile Updated: {updated_profile}"})


# --- 4. GAME & TRAINING LOGIC ---

SCENARIO_PROMPT = "Your boss just texted you: 'Are you available for a quick 5-minute call at 4:30 PM today?'"
SCENARIO_INSTRUCTIONS = """
Your task is to provide the **reply that the user (you) would send** to the following external message. 
Analyze your stored style profile and the scenario, and generate the response. 
The user's response should be polite, but fully match their cloned style (brief, verbose, emoji-heavy, etc.).
"""

def start_training():
    st.session_state.training_active = True
    st.session_state.messages.append({"role": "system", "content": 
        f"***--- TRAINING MODE ACTIVATED ---***\n"
        f"Your task: Auto-reply to the following scenario in your own voice. Type your reply below."})
    st.session_state.messages.append({"role": "scenario", "content": SCENARIO_PROMPT})

def finish_training_and_analyze(user_reply):
    st.session_state.training_active = False
    
    # 1. Save the user's reply to history
    st.session_state.messages.append({"role": "user", "content": f"(My Reply): {user_reply}"})

    # 2. Ask Echo to grade the reply and update its profile
    analysis_prompt = f"""
    The user's style profile is: {st.session_state.user_style_profile}.
    The user's reply to the scenario '{SCENARIO_PROMPT}' was: '{user_reply}'
    
    1. Provide a funny, encouraging, and highly specific analysis of how well this reply matches the profile. 
    2. Then, output the single-sentence **updated profile** as a structured tag: [NEW_PROFILE: <Updated Profile Sentence>]. 
    """
    
    analysis_response = model.generate_content(analysis_prompt).text

    # 3. Parse the analysis and update profile
    profile_match = re.search(r'\[NEW_PROFILE: (.*?)\]', analysis_response, re.DOTALL)
    
    if profile_match:
        new_profile = profile_match.group(1).strip()
        update_style_profile(new_profile) # Save to session state and simulated DB
        analysis_response = analysis_response.replace(profile_match.group(0), "").strip()
        
    st.session_state.messages.append({"role": "assistant", "content": 
        f"***--- TRAINING ANALYSIS ---***\n" + analysis_response})


# --- 5. AUTHENTICATION LOGIC ---

def login_user():
    username = st.session_state.login_username
    password = st.session_state.login_password
    
    user_data = load_user_data(username)
    
    if user_data and user_data['password'] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
        # Load profile from "database"
        st.session_state.user_style_profile = user_data['style_profile']
        st.success(f"Welcome back, {username}! Your style profile has been loaded.")
        time.sleep(1)
        st.rerun()
    else:
        st.error("Invalid username or password.")

def logout_user():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.messages = []
    st.session_state.user_style_profile = "User currently exhibits a friendly, neutral, and curious tone."
    st.success("Logged out successfully.")
    time.sleep(1)
    st.rerun()

# --- INITIALIZATION ---
initialize_session_state()

# --- SIDEBAR & AUTHENTICATION (Must run before main content) ---
with st.sidebar:
    st.title("Echo Clone System")
    
    if not st.session_state.logged_in:
        st.subheader("Account Sign-in")
        st.text_input("Username (e.g., user1)", key="login_username")
        st.text_input("Password (e.g., password)", type="password", key="login_password")
        st.button("Login", on_click=login_user)
        st.info("Use 'user1' and 'password' to test the memory feature.")
    else:
        st.success(f"Logged in as: {st.session_state.username}")
        st.markdown(f"**Current Style Profile:** {st.session_state.user_style_profile}")
        st.button("Logout", on_click=logout_user)
        
        st.markdown("---")
        st.subheader("Training & Features")

        if st.session_state.training_active:
            st.button("End Training Session", on_click=lambda: st.session_state.training_active == False)
        else:
            st.button("Start Auto-Reply Training", on_click=start_training)

        st.markdown("---")
        st.subheader("Other Settings")
        st.radio("Tone Setting", ["Friendly", "Formal", "Funny"], index=0)
        # You can integrate these sidebar controls into the persona_instructions

# --- MAIN APP LOGIC ---

def main():
    st.title("Echo: The Auto-Reply Clone 🤖")

    if not st.session_state.logged_in:
        st.info("Please sign in on the sidebar to load your personal style profile.")
        return

    # 1. Display chat messages
    for message in st.session_state.messages:
        # Custom role display for training scenario
        role = "Scenario" if message["role"] == "scenario" else message["role"]
        
        with st.chat_message(role):
            st.write(message["content"])

    # 2. Display Training Status
    if st.session_state.training_active:
        st.warning(f"AUTO-REPLY TRAINING ACTIVE. Your reply to the scenario is the next input.")


# Execute the main function
if __name__ == "__main__":
    main()

# --- USER INPUT HANDLING ---
if st.session_state.logged_in:
    
    input_label = "Your Reply to Scenario:" if st.session_state.training_active else "Chat with Echo:"
    
    if prompt := st.chat_input(input_label):

        if st.session_state.training_active:
            # --- TRAINING MODE INPUT ---
            finish_training_and_analyze(prompt)
            st.rerun()
            
        else:
            # --- NORMAL CHAT MODE INPUT ---
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)

            # 1. Update Profile (Long-term memory integration)
            update_style_profile(prompt)
            
            # 2. Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # 3. Get Gemini response with current profile
            response = get_gemini_response(prompt, st.session_state.user_style_profile, persona_instructions)

            # 4. Display assistant response
            with st.chat_message("assistant"):
                st.write(response)

            # 5. Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": response})