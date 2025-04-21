import streamlit as st
import google.generativeai as genai

# Configure the API key
genai.configure(api_key="AIzaSyAwD8E-BJXs9d4jDMQ_23rZ1ukk7y0HpVk")  # Replace with your actual API key

# Model setup
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 65536,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-preview-04-17",
    generation_config=generation_config,
    system_instruction="""You are the Mood Chef: Mood-Based Recipe Recommendation System with Dynamic Cooking Constraints.

Generates recipes based on ingredients available (will be given as a list) and mood of the user.  
Step 1: Find recipes based on ingredients. 
Step 2: Rank them based on metrics like : Prep Time, Cook Time, Cleaning Time, # of ingredients

Note: If the user is in good mood and is excited to eat something new, choose a dish with higher Prep Time, Cook Time, Cleaning Time, # of ingredients and vice versa.

The output should be structured in the following format:

List the recipes based on the ranking along with the table of  Prep Time, Cook Time, Cleaning Time, # of ingredients

Then ask what I want to cook

Then give recipe in this format:

Recipe Name  
Cuisine  
Servings  
Prep Time  
Ingredients  
Instructions"""
)

chat_session = model.start_chat(history=[])

# Streamlit UI
st.title("🍲 Mood Chef")

with st.form("mood_form"):
    mood = st.slider("How happy are you feeling today? (1 = meh, 10 = super excited)", 1, 10)
    ingredients = st.text_area("What ingredients do you have?", placeholder="e.g. eggs, tomatoes, onion, pasta...")
    submitted = st.form_submit_button("Get Recipe Suggestions")

if submitted and ingredients:
    with st.spinner("Cooking up ideas..."):
        response = chat_session.send_message(f"{ingredients}\nHappiness Score (Out of 10): {mood}")
        suggestions = response.text
    st.subheader("🍽️ Recipe Suggestions")
    st.markdown(f"```\n{suggestions}\n```")

    recipe_name = st.text_input("Enter the name of the recipe you'd like to cook:")

    if recipe_name:
        with st.spinner("Fetching the full recipe..."):
            recipe_response = chat_session.send_message(recipe_name)
        st.subheader("📋 Full Recipe")
        st.markdown(f"```\n{recipe_response.text}\n```")
