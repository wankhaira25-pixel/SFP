import streamlit as st
import google.generativeai as genai
import random 

# --- Configuration ---

# The API Key is hardcoded in the original, but best practice is to use st.secrets!
# NOTE: Using st.secrets is highly recommended for security.
# GOOGLE_API_KEY = "AIzaSyCLzKVjpyw_FXfdleQb26b5dxKfKMJcKQg" 

# Best practice for Streamlit Secrets
try:
    # Use st.secrets if you've configured them
    GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
except (KeyError, AttributeError):
    # Fallback if st.secrets is not used, or if you prefer environment variable
    # NOTE: Replace with your actual key if not using st.secrets
    GOOGLE_API_KEY = "AIzaSyCLzKVjpyw_FXfdleQb26b5dxKfKMJcKQg" # REMOVE/REPLACE THIS LINE IN PRODUCTION

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash') 
except Exception as e:
    # The app will stop here if the key is invalid or an error occurs
    st.error(f"Error configuring Gemini API: {e}. Please check your API key.")
    st.stop()


# --- GM Persona and Game Instructions ---

# Moved instructions to a global constant for clarity
GAME_MASTER_INSTRUCTIONS = """
You are a witty, fair, and immersive Dungeon Master (DM) for a Dungeons & Dragons 5th Edition (5e) campaign.
The game is called 'The Quest for the Lost Artifact'.

**Your Core Roles:**
1.  **Narrate the World:** Describe the settings, non-player characters (NPCs), and the consequences of the players' actions.
2.  **Manage the Story:** Guide the overarching plot. Present challenges, puzzles, and encounters.
3.  **Handle Game Mechanics:**
    * When a player wants to attempt an action with an uncertain outcome (e.g., attacking, persuading, searching), you must ask them for a **d20 roll** plus any relevant modifier (e.g., 'Roll a DC 15 Persuasion check.').
    * The player will then tell you the result of their roll (e.g., 'I rolled a 17!').
    * You will then determine if they succeed or fail based on the Difficulty Class (DC) you set and describe the outcome.
4.  **Manage Player Characters (PCs):** There are up to 4 players, including the human user.
    * **User (The Player):** The human interacting with you.
    * **AI Player 1 (Kaelen):** A stoic, half-elf Rogue, specialized in stealth. Kaelen often suggests the sneaky route.
    * **AI Player 2 (Bartholomew):** A boisterous, human Paladin, always advocating for the most honorable and direct approach.
    * **AI Player 3 (Lyra):** A quirky, gnome Wizard, who is very curious and prone to casting unnecessary spells.

**When the user gives an instruction or asks a question:**
* Respond as the DM, addressing the user's action and then, if appropriate, having the AI Players react or offer their own suggestions *in the third person* (e.g., "Kaelen whispers, 'Maybe we should check the shadows first.'").
* If the user asks to start a new game or if the session is just beginning, set the scene.
* **Keep the narrative flowing and be descriptive!**

**Start the game now. Set the initial scene and introduce the party.**
"""

# --- Streamlit Session State & Functions ---

def initialize_session_state():
    """Initializes the required variables in Streamlit's session state."""
    # Initialize all necessary keys if they are not present
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    if "show_intro" not in st.session_state:
        st.session_state.show_intro = True 
    if "show_rules" not in st.session_state:
        st.session_state.show_rules = False
    # Flag to indicate that a dice roll was made and the AI needs to respond to it.
    if "trigger_ai_response" not in st.session_state:
         st.session_state.trigger_ai_response = False
    # Flag to prevent duplicate appending of the AI's *response* to the history.
    if "response_ready" not in st.session_state:
         st.session_state.response_ready = None


def get_gemini_response(prompt, system_instruction):
    """
    Calls the Gemini API with the full conversation history and system instruction.
    Converts the Streamlit history format to the Gemini API Content format.
    """
    
    # 1. Convert Streamlit's history format to Gemini's API format
    history = []
    for m in st.session_state.messages:
        # The API expects 'user' or 'model' roles.
        role = "user" if m["role"] == "user" else "model"
        
        # The API expects the content inside a list of 'parts'.
        history.append({
            "role": role,
            "parts": [{"text": m["content"]}]
        })
    
    # 2. Use a configuration object to hold the system instruction for the AI's persona
    config = genai.types.GenerateContentConfig(
        system_instruction=system_instruction
    )
        
    # 3. Start a new chat session with the converted history and system instruction config
    # The last message is the one to which the model should respond, which is passed separately.
    # Note: We pass all history *except* the very last message (the prompt) to `history`
    # and pass the prompt text to `send_message`.
    
    # Check if there is history to pass
    if len(history) > 1:
        history_for_chat = history[:-1] # All messages except the last one (the current prompt)
        latest_prompt_part = history[-1]['parts']
        # The latest prompt text is the last message's content
        latest_prompt_text = latest_prompt_part[0]['text']
        
        chat = model.start_chat(history=history_for_chat)
        response = chat.send_message(latest_prompt_text, config=config)
    else:
        # If it's the very first message, start a chat without history
        chat = model.start_chat(history=[])
        response = chat.send_message(prompt, config=config)
    
    return response.text

# --- Dice Rolling Functionality ---

def roll_dice_and_inject(dice_sides):
    """Simulates a dice roll and injects the result into the chat as a user message."""
    
    # Check if the last message was already a dice roll to prevent multiple rolls in one click
    if st.session_state.messages and 'I rolled a d' in st.session_state.messages[-1]["content"]:
        st.warning("Please wait for the DM's response before rolling again.")
        return

    roll = random.randint(1, dice_sides)
    # The message is formatted to clearly communicate the roll to the GM/AI
    user_roll_message = f"I rolled a d{dice_sides} and got a **{roll}**! (My current modifier is +0, so the total is {roll}). DM, what happens next?"
    
    # Inject the roll result as the user's message
    st.session_state.messages.append({"role": "user", "content": user_roll_message})
    
    # Set a flag to trigger the AI response in the next run
    st.session_state.trigger_ai_response = True
    
    # Rerun the app to process the new message and get the AI's response
    # FIX: Replaced st.experimental_rerun() with st.rerun()
    st.rerun()

# --- Streamlit UI ---

def main():
    """The main function to run the Streamlit application."""
    st.set_page_config(page_title="D&D Game Master Bot", layout="centered")
    st.title("🧙‍♂️ D&D Game Master Bot")
    st.caption("The AI DM for your grand adventure! Get started below.")

    initialize_session_state()

    # --- Sidebar Content ---
    with st.sidebar:
        st.header("The Party")
        st.markdown(f"**DM:** AI (Gemini)")
        st.markdown(f"**Player:** You (The User)")
        st.markdown(f"**AI Players:** Kaelen (Rogue), Bartholomew (Paladin), Lyra (Wizard)")
        
        st.divider()
        st.header("🎲 Dice Roller")
        st.write("Click a die to roll it. The result will be added to the chat!")
        
        # Dice Buttons Layout
        dice_cols = st.columns(3)
        dice_buttons = {
            "d4": dice_cols[0], "d6": dice_cols[1], "d8": dice_cols[2],
            "d10": dice_cols[0], "d12": dice_cols[1], "d20": dice_cols[2],
        }

        # Create the dice buttons
        for dice_name, col in dice_buttons.items():
            sides = int(dice_name[1:])
            # Use 'col.button' to place buttons in columns
            if col.button(f"{dice_name} (Roll)", key=f"roll_{sides}"):
                roll_dice_and_inject(sides) # This function calls st.rerun()
                # Execution stops here and restarts at the top of main()

        st.divider()
        if st.button("❓ Show Game Rules", key="toggle_rules"):
            st.session_state.show_rules = not st.session_state.show_rules
        
        if st.session_state.show_rules:
            st.subheader("Game Rules (Brief)")
            st.markdown("""
            * **Rolls:** When the DM asks for a check (e.g., 'DC 15 Persuasion'), use the dice roller to get your result.
            * **Modifiers:** For simplicity, assume a **+0 modifier** to your rolls initially. Tell the DM the total.
            * **Actions:** Describe what you want to do (e.g., 'I search the chest', 'I use my sword'). The DM handles the rest!
            """)

        st.divider()
        if st.button("Reset Game", help="Start a new quest and clear all messages."):
            st.session_state.messages = []
            st.session_state.game_started = False
            st.session_state.show_intro = True
            st.session_state.trigger_ai_response = False
            st.session_state.response_ready = None
            # FIX: Replaced st.experimental_rerun() with st.rerun()
            st.rerun()


    # --- Introduction Pop-up Logic ---
    intro_placeholder = st.empty()
    
    if st.session_state.show_intro:
        with intro_placeholder.container():
            st.header("Welcome to the Quest! 📜")
            st.info("""
            **You are about to embark on an epic Dungeons & Dragons adventure!**
            
            The AI, powered by Gemini, will serve as your Dungeon Master (DM) and control three AI party members.
            
            **How to Play:**
            1.  Click **"Begin Adventure"** to start the story.
            2.  When the DM asks for a roll (like a d20), use the **"Dice Roller"** in the sidebar.
            3.  Type your actions in the chat box below!
            """)
            if st.button("⚔️ Begin Adventure"):
                st.session_state.show_intro = False
                # Use st.rerun() to immediately hide the intro and proceed
                st.rerun()
            return # Stops drawing the rest of the page until the button is clicked.

    # --- Chat Display and Logic ---

    # Display chat messages from history
    for message in st.session_state.messages:
        avatar = "🎲" if message["role"] == "user" else "🧙‍♂️"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            
    # If a response was generated in the last run (due to a dice roll), display it now
    if st.session_state.response_ready is not None:
        with st.chat_message("assistant", avatar="🧙‍♂️"):
            st.markdown(st.session_state.response_ready)
        
        # Add the AI's response to the history
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.response_ready})
        
        # Clear the flag
        st.session_state.response_ready = None
        # Rerun to clear the spinner and finalize the state
        st.rerun()
        return

    # Determine the prompt source (dice roll or manual input)
    prompt = None
    
    # 1. Handle Dice Roll Prompt
    if st.session_state.trigger_ai_response:
        # The prompt is the last message (the injected dice roll)
        prompt = st.session_state.messages[-1]["content"]
        # Reset the flag immediately
        st.session_state.trigger_ai_response = False
    
    # 2. Handle Manual Chat Input Prompt
    else:
        # Get input from the standard chat box
        prompt = st.chat_input("What do you do? (e.g., 'I look around the room' or 'I attack the goblin')")
    
    
    if prompt:
        
        # If the prompt came from the chat_input, we must add it to the history and display it
        # If it came from the dice roll (trigger_ai_response was true), it's already in the history.
        if not st.session_state.trigger_ai_response: 
            st.chat_message("user", avatar="🎲").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

        # Get Gemini response with 'spinner'
        with st.chat_message("assistant", avatar="🧙‍♂️"):
            with st.spinner("The DM is thinking..."):
                
                is_first_response = not st.session_state.game_started
                
                response = get_gemini_response(prompt, GAME_MASTER_INSTRUCTIONS)
                
                if is_first_response:
                    st.session_state.game_started = True 
        
        # Store the response in session state *instead of* displaying it immediately.
        # This is the robust way to ensure all messages are displayed in the correct order
        # and prevents the final response from being "double-drawn" on the first pass.
        st.session_state.response_ready = response
        
        # RERUN to finalize the display and state
        st.rerun()

# --- Execution ---
if __name__ == "__main__":
    main()