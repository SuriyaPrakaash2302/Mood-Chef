import streamlit as st
import google.generativeai as genai
from bs4 import BeautifulSoup
import pandas as pd
import json
import re

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
        system_instruction="""DONT USE MARKDOWN IN OUTPUTS EVERRRRRRRRRRRR  DO NOT INCLUDE BACKTICKS IN THE RESPONSE

        Prompt:

You are Mood Chef, an intelligent recipe recommendation system that tailors recipe suggestions based on the user’s mood and available ingredients.

Instructions:

Step 1 – Recipe Generation:
Based on the list of ingredients provided by the user, generate a list of possible recipes.

Step 2 – Recipe Ranking (Mood-Based):
Adjust the ranking of the recipes depending on the user’s mood:

If the user is in a good mood and feeling excited to cook, prioritize:

Higher Prep Time

Higher Cook Time

Higher Cleaning Time

Greater # of ingredients

If the user is in a tired, lazy, or low-energy mood, prioritize:

Lower Prep Time

Lower Cook Time

Lower Cleaning Time

Fewer # of ingredients

Step 3 – Display Results:
Output only a ranked HTML table of recipes based on the criteria above.
Each row must include:

Recipe Name

Prep Time (min)

Cook Time (min)

Cleaning Time (min)

# of Ingredients

Step 4 – Follow-up:
After displaying the table, ask the user:
“Which one would you like to cook?”



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

        # Parse HTML to DataFrame and store it
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if table:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            rows = []
            for tr in table.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if cells:
                    rows.append(cells)
            st.session_state["recipe_df"] = pd.DataFrame(rows, columns=headers)
        else:
            st.session_state["recipe_df"] = None

# Display section — shown whether or not a new form is submitted
if "suggestions" in st.session_state:
    st.subheader("🍽️ Recipe Suggestions")
    if st.session_state.get("recipe_df") is not None:
        df = st.session_state["recipe_df"]

        st.html(f"""
        <style>
        .cookbook-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px auto;
            font-family: 'Georgia', serif;
            background-color: #fffdf7;
            border: 2px solid #f4d9a4;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
            color: black;
        }}
        .cookbook-table th, .cookbook-table td {{
            padding: 0.75rem 1rem;
            text-align: center;
            border-bottom: 1px solid #ddd;
            color: black;
        }}
        .cookbook-table th {{
            background-color: #fef3dc;
            color: black;
            font-size: 1.1rem;
        }}
        .cookbook-table tr:nth-child(even) {{
            background-color: #f9f4ea;
            color: black;
        }}
        .cookbook-table tr:hover {{
            background-color: #fff5e1;
        }}
        </style>

        <table class="cookbook-table">
            <thead>
                <tr>
                    {''.join(f'<th>{col}</th>' for col in df.columns)}
                </tr>
            </thead>
            <tbody>
                {''.join(
                    '<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
                    for row in df.values.tolist()
                )}
            </tbody>
        </table>
        """)



recipe_options = []
if "recipe_df" in st.session_state and st.session_state["recipe_df"] is not None:
    # Assume the first column contains the recipe names
    recipe_options = st.session_state["recipe_df"].iloc[:, 0].tolist()

st.subheader("👩‍🍳 Pick Your Recipe")
selected_recipe = st.selectbox("Choose a recipe from the suggestions:", options=[""] + recipe_options)
custom_recipe_name = st.text_input("Or enter your own recipe name:")

final_recipe_name = custom_recipe_name.strip() if custom_recipe_name.strip() else selected_recipe.strip()

if final_recipe_name:
    with st.spinner("Fetching the full recipe..."):
        recipe_response = chat_session.send_message("""Make the output in json format without markdown. DO NOT INCLUDE BACKTICKS IN THE RESPONSE, it is very important that there is no markdown in the output DOnt use suffix json. I need only the dictionary. Get me the recipe for""" + final_recipe_name+ 
                                                    """  as a json with headers. fOLLOW THE HEADERS NAME I GIVE BELOW
                                                     **Recipe Title**

                                                    *(optional description)*

                                                        **Yields:** ...
                                                    **Prep time:** ...
                                                    **Cook time:** ...

                                                    **Ingredients:**


                                                    **Instructions:**

                                                    rememMBER no markdown

                                                    eXAMPLE:

                                                    {'Recipe Title': 'Basic Boiled Potatoes with Salt', 'Yields': '1-2 servings', 'Prep time': '10-15 minutes', 'Cook time': '15-25 minutes', 'Ingredients': ['1-2 medium potatoes', 'Water', 'Salt, to taste'], 'Instructions': ['Wash the potatoes thoroughly.', 'Peel the potatoes if desired, or leave the skin on.', 'Cut larger potatoes into halves or quarters for more even cooking. Smaller potatoes can be boiled whole.', 'Place the potatoes in a pot and cover them with cold water.', 'Add a generous pinch of salt to the water.', 'Bring the water to a boil over high heat.', 'Reduce the heat to medium and simmer the potatoes until they are tender when pierced with a fork.', 'Drain the potatoes thoroughly.', 'Serve hot, adding more salt if desired.']} """)
        st.session_state["full_recipe"] = recipe_response.text
    st.subheader("📋 Full Recipe")

    # Sample recipe_json - replace this with your actual JSON dictionary
    #print(recipe_response.text)
    #json_match = re.search(r'\{.*\}', recipe_response.text, re.DOTALL)
    print(recipe_response.text)
    recipe_json = json.loads(recipe_response.text)
    print(recipe_json)

    # HTML display
    st.html(f"""
    <style>
    .recipe-card {{
        background-color: #fffdf7;
        padding: 2rem;
        border: 2px solid #f4d9a4;
        border-radius: 15px;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.1);
        font-family: 'Georgia', serif;
        max-width: 800px;
        margin: auto;
        line-height: 1.6;
        color: #3e3e3e;
    }}

    .recipe-title {{
        font-size: 2.2rem;
        font-weight: bold;
        color: #b35c1e;
        text-align: center;
        margin-bottom: 0.5rem;
    }}

    .description {{
        font-style: italic;
        text-align: center;
        color: #666;
        margin-bottom: 1.5rem;
    }}

    .details {{
        text-align: center;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }}

    .section-title {{
        font-size: 1.4rem;
        margin-top: 1.5rem;
        color: #774400;
        border-bottom: 1px solid #ddd;
        padding-bottom: 0.3rem;
    }}

    ul, ol {{
        padding-left: 1.5rem;
    }}
    </style>

    <div class="recipe-card">
        <div class="recipe-title">{recipe_json['Recipe Title']}</div>
        <div class="description">{recipe_json.get('Optional Description', '')}</div>
        <div class="details">
            <strong>Yields:</strong> {recipe_json.get('Yields', 'N/A')} &nbsp; | &nbsp;
            <strong>Prep Time:</strong> {recipe_json.get('Prep time', 'N/A')} &nbsp; | &nbsp;
            <strong>Cook Time:</strong> {recipe_json.get('Cook time', 'N/A')}
        </div>

        <div class="section-title">🧂 Ingredients</div>
        <ul>
            {''.join(f"<li>{item}</li>" for item in recipe_json.get('Ingredients', []))}
        </ul>

        <div class="section-title">👨‍🍳 Instructions</div>
        <ol>
            {''.join(f"<li>{step}</li>" for step in recipe_json.get('Instructions', []))}
        </ol>
    </div>
    """)

    # Render in Streamlit
    #st.markdown(html, unsafe_allow_html=True)

