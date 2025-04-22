import streamlit as st
import google.generativeai as genai
from bs4 import BeautifulSoup
import pandas as pd


# **Security Note:** It's best practice to manage API keys securely, not directly in the code.
# Consider using Streamlit Secrets or environment variables.
genai.configure(api_key="AIzaSyAwD8E-BJXs9d4jDMQ_23rZ1ukk7y0HpVk")

# Model setup - Consider initializing this outside the main flow if it's a one-time setup
@st.cache_resource
def load_gemini_model():
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 65536,
        "response_mime_type": "text/plain",
    }
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-04-17",
        generation_config=generation_config,
        system_instruction="""You are the Mood Chef: Mood-Based Recipe Recommendation System with Dynamic Cooking Constraints.

Generates recipes based on ingredients available (will be given as a list) and mood of the user.
Step 1: Find recipes based on ingredients.
Step 2: Rank them based on metrics like : Prep Time, Cook Time, Cleaning Time, # of ingredients

Note: If the user is in good mood and is excited to eat something new, choose a dish with higher Prep Time, Cook Time, Cleaning Time, # of ingredients and vice versa.

The output should be structured in the following format: Only the table which is displayed in html

List the recipes based on the ranking along with the table of  Prep Time, Cook Time, Cleaning Time, # of ingredients

Then ask what I want to cook

"""
    )

model = load_gemini_model()

# Initialize chat session in Streamlit's session state
if "chat_session" not in st.session_state:
    st.session_state["chat_session"] = model.start_chat(history=[])

chat_session = st.session_state["chat_session"]

st.title("🍲 Mood Chef")

with st.form("mood_form"):
    mood = st.slider("How happy are you feeling today? (1 = meh, 10 = super excited)", 1, 10)
    ingredients = st.text_area("What ingredients do you have?", placeholder="e.g. eggs, tomatoes, onion, pasta...")
    submitted = st.form_submit_button("Get Recipe Suggestions")

if submitted and ingredients:
    with st.spinner("Cooking up ideas..."):
        response = chat_session.send_message(f"{ingredients}\nHappiness Score (Out of 10): {mood}")
        st.session_state["suggestions"] = response.text
    st.subheader("🍽️ Recipe Suggestions")
    # Parse HTML to DataFrame
    soup = BeautifulSoup(st.session_state["suggestions"], "html.parser")
    table = soup.find("table")
    if table:
        # Extract headers
        headers = [th.get_text(strip=True) for th in table.find_all("th")]

        # Extract rows
        rows = []
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(cells)

        df = pd.DataFrame(rows, columns=headers)
        st.dataframe(df)
    else:
        st.markdown(st.session_state["suggestions"], unsafe_allow_html=True)

    

recipe_name = st.text_input("Enter the name of the recipe you'd like to cook:")

if recipe_name:
    with st.spinner("Fetching the full recipe..."):
        recipe_response = chat_session.send_message(recipe_name)
        st.session_state["full_recipe"] = recipe_response.text
    st.subheader("📋 Full Recipe")
    st.markdown(f"```\n{st.session_state['full_recipe']}\n```")
