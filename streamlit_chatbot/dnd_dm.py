import streamlit as st
import google.generativeai as genai
import os
import random

# --- 1. Configuration & API Key Setup ---
# *** IMPORTANT: REPLACE THIS PLACEHOLDER WITH YOUR ACTUAL GEMINI API KEY ***
# RECOMMENDATION: Use st.secrets or environment variables for security.
GOOGLE_API_KEY = "AIzaSyBtMGPg3oUK0K0akIwlZW2sGzTleED4vRw" 

if not GOOGLE_API_KEY:
    st.error("Gemini API Key not found. Please set the 'GOOGLE_API_KEY' variable.")
    st.stop()

# --- 2. System Instruction (The Dungeon Master Persona) ---
DND_SYSTEM_INSTRUCTION = """
You are a Dungeon Master (DM) for a solo Dungeons & Dragons 5th Edition text-based adventure. 
Your primary goal is to provide an immersive, dynamic, and challenging role-playing experience.

### DM Rules & Behavior:
1.  **Do Not Break Character:** You are the DM and the world. Never mention that you are an AI or a language model.
2.  **Immersive Descriptions:** Describe scenes, NPCs, and events using vivid sensory details (sight, sound, smell, feel).
3.  **NPCs & Monsters:** Control all Non-Player Characters and monsters. You determine their actions, dialogue, and motivations.
4.  **Skill Checks & Rolls:**
    * When the player is required to roll for an action in the adventure, they will state the result in the chat (e.g., "I rolled a 15 + 2 for a total of 17"). You then determine the outcome.
5.  **Combat & Pacing:** Manage the combat rounds, track enemy stats, and keep the story moving.

### Game Start Sequence (CRITICAL - FOLLOW THESE STEPS EXACTLY):
1.  **Welcome & Character Status:** Your absolute first response must be a friendly welcome, acknowledging that the player has entered their basic character details in the sidebar.
2.  **Ability Score Roll (Step 1):** You must then explain the six D&D Ability Scores (Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma) and instruct the player to use the **4d6 Drop Lowest** method to generate their six scores. Instruct the player to enter their six results, one by one, in the chat.
3.  **Party Introduction (Step 2):** After the player has successfully provided six ability scores, your next response must be to introduce three pre-rolled, Level 1, AI-controlled party members, including their Name, Race, Class, and their six ability scores (you must generate these stats for them).
4.  **Scene Setup (Step 3):** After the party introduction, you must immediately ask the player: **"With your full party assembled, do you wish to describe the first scene/location yourself, or shall I roll on the Random Encounters table to start the adventure?"** The adventure begins only after the player answers this question.
"""

# Configure Gemini API
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Set the system instruction when creating the model object
    model = genai.GenerativeModel(
        'gemini-2.5-pro',
        system_instruction=DND_SYSTEM_INSTRUCTION
    ) 
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

# --- 3. Sidebar Dice Rolling Logic ---

def roll_dice(num_dice, sides, drop_lowest=0):
    """Simulates rolling multiple dice and summing the result, optionally dropping the lowest."""
    rolls = [random.randint(1, sides) for _ in range(num_dice)]
    rolls.sort()
    
    # Drop the lowest 'drop_lowest' number of rolls
    final_rolls = rolls[drop_lowest:]
    
    total = sum(final_rolls)
    
    if drop_lowest > 0:
        return total, f"Rolls: {rolls} (Dropped lowest: {rolls[:drop_lowest]}). Sum: {total}"
    else:
        return total, f"Rolls: {rolls}. Sum: {total}"

def handle_dice_click(num_dice, sides, drop_lowest=0):
    """Handles dice button clicks and stores result in session state."""
    total, details = roll_dice(num_dice, sides, drop_lowest)
    st.session_state.last_roll = f"**d{sides} Roll:** {total}"
    if drop_lowest > 0:
        st.session_state.last_roll = f"**{num_dice}d{sides} Drop Lowest:** {total}"
    st.session_state.roll_details = details

# --- 4. Streamlit Session State and Chat Management ---

# Initialize chat history, chat session, and dice results
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
if "last_roll" not in st.session_state:
    st.session_state.last_roll = "—"
if "roll_details" not in st.session_state:
    st.session_state.roll_details = "Click a dice button to roll."


# --- 5. Main App Layout ---
st.set_page_config(page_title="Gemini D&D DM Chatbot", layout="wide")
st.title("🧙‍♂️ Gemini Dungeon Master (D&D 5e)")

# Pop-up Rule/Disclaimer
st.info("⚔️ **Roll-Playing Rules:** When the DM asks for a check, type your **total result** (e.g., 'I got an 18'). For generating ability scores, use the **4d6 Drop Lowest** button in the sidebar and type your final result into the chat.")

# Sidebar for controls
with st.sidebar:
    st.title("Game Controls")
    st.markdown("---")

    # --- Dice Roller Panel ---
    st.subheader("🎲 Dice Roller")
    st.metric("Last Roll Result", st.session_state.last_roll)
    with st.expander("Roll Details"):
        st.caption(st.session_state.roll_details)

    # Dice buttons in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.button("d4", on_click=handle_dice_click, args=(1, 4))
        st.button("d8", on_click=handle_dice_click, args=(1, 8))
        st.button("d12", on_click=handle_dice_click, args=(1, 12))
        
    with col2:
        st.button("d6", on_click=handle_dice_click, args=(1, 6))
        st.button("d10", on_click=handle_dice_click, args=(1, 10))
        st.button("d20", on_click=handle_dice_click, args=(1, 20))

    st.markdown("---")
    # Special button for ability scores (4d6 drop lowest)
    st.subheader("Ability Score Roll")
    st.button("4d6 Drop Lowest", on_click=handle_dice_click, args=(4, 6, 1), type="secondary")
    st.markdown("---")

    # --- Character Creation Panel (Player Input) ---
    st.subheader("👤 Create Your Level 1 Character")
    st.text_input("Name", "Alistair", key='character_name')
    st.text_input("Race", "Half-Elf", key='character_race')
    st.text_input("Class", "Rogue", key='character_class')
    st.text_area("Physical & Other Details (Age, Height, Scars, Skin Color, etc.)", "6ft tall, green eyes, wears a tattered cloak.", key='character_details')
    st.markdown("---")

    # Character Stats Tracker (For Player to Manually Track)
    st.subheader("📈 Player Stats Tracker")
    st.text_input("HP / AC", "10 / 14", key='player_stats')
    st.markdown("---")
    
    # Clear Chat History
    if st.button("Start New Adventure / Clear Chat", type="primary"):
        st.session_state.messages = []
        # Re-initialize the chat session to reset the AI's memory
        st.session_state.chat_session = model.start_chat(history=[])
        st.rerun() 

# Display existing chat messages
for message in st.session_state.messages:
    # Map Streamlit roles to appropriate avatars
    avatar = "👤" if message["role"] == "user" else "🔮"
    with st.chat_message(message["role"], avatar=avatar):
        # Display the stored clean content
        st.markdown(message["content"])

# --- 6. Chat Input and Game Logic ---
if prompt := st.chat_input("Enter your character's roll, action, or response..."):
    
    # 1. Display user message immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        
    # 2. Add user message to session history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 3. Get Gemini (DM) response
    with st.chat_message("assistant", avatar="🔮"):
        # Create a placeholder to stream the response into
        placeholder = st.empty()
        full_response = ""
        
        with st.spinner("The DM is consulting the scrolls..."):
            try:
                # Use the Streamlit chat session to send the message and stream the response
                response = st.session_state.chat_session.send_message(
                    prompt, 
                    stream=True
                )
                
                # Stream the response content to the screen and collect the full text
                for chunk in response:
                    if chunk.text: # Ensure chunk.text exists before appending
                         # Collect the text from all chunks
                        full_response += chunk.text
                        # Update the placeholder with the text so far (for streaming effect)
                        placeholder.markdown(full_response)
                
                # 4. Add DM response (the clean text) to session history
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"A critical quest failure (API error) occurred: {e}")
                # Remove the user message added if the API call failed
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()