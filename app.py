import streamlit as st
import httpx
URI = st.secrets["URI"]

st.set_page_config(page_title="SDP Chatbot", layout="wide")
st.title("🤖 Smart Diet Planner Chatbot")

def saveFields():
    st.session_state.user_data = {
        "id": id,
        "name": name,
        "age": age,
        "community": [c.strip() for c in community.split(",")] if community else [],
        "foodtype": foodtype,
        "condition": condition,
        "allergies": [a.strip() for a in allergies.split(",")] if allergies else []
    }
    st.session_state.user_saved = True

def editFields():
    st.session_state.user_saved = False

# Sidebar for knowledge base selection
with st.sidebar:
    st.header("API Request Settings")

    kb = st.selectbox("Knowledge Base", ["ConditionVDB", "NutritionVDB", "GeneralVDB"])

    if kb == "ConditionVDB":
        chunk_category = st.selectbox("Chunk Category", ["cholesterol", "diabetes", "hypertension", "weightloss"])
        section = st.selectbox("Section", ["Cholestrol", "Diabetes", "Hypertension", "Weightloss"])
    elif kb == "NutritionVDB":
        chunk_category = st.selectbox("Chunk Category", [
            "biotin", "calcium", "choline", "chromium", "copper", "folate", "iodine", "iron",
            "magnesium", "manganese", "omega3", "selenium", "vitamin-a", "vitamin-b12",
            "vitamin-c", "vitamin-d3", "vitamin-e", "vitamin-k", "zinc"
        ])
        section = st.selectbox("Section", ["Biotin", "Calcium", "Choline", "Chromium", "Copper", "Folate", "Iodine", "Iron", "Magnesium", "Manganese", "Omega3", "Selenium", "Vitamin-a", "Vitamin-b12", "Vitamin-c", "Vitamin-d3", "Vitamin-e", "Vitamin-k", "Zinc"])
    elif kb == "GeneralVDB":
        chunk_category = st.selectbox("Chunk Category", [
            "craving", "diet", "fast", "hydration", "motivation", "oil_intake"
        ])
        section = st.selectbox("Section", ["Craving", "Plateau", "Motivation", "Fasting", "Micronutrients", "Exercise", "Hydration"])

    st.divider()
    st.header("User Data")

    # Initialize session state
    if "user_saved" not in st.session_state:
        st.session_state.user_saved = False
    if "user_data" not in st.session_state:
        st.session_state.user_data = {}

    # Get disabled state
    disabled = st.session_state.user_saved

    # Load saved data if any
    user_data = st.session_state.user_data
    id = user_data.get("id", "")
    name = user_data.get("name", "")
    age = user_data.get("age", "")
    community = ",".join(user_data.get("community", []))
    foodtype = user_data.get("foodtype", [])
    condition = user_data.get("condition", [])
    allergies = ",".join(user_data.get("allergies", []))

    # Fields
    id = st.text_input("Id", value=id, placeholder="User ID", disabled=disabled)
    name = st.text_input("Name", value=name, placeholder="User Name", disabled=disabled)
    age = st.number_input("Age", min_value=0, max_value=120, step=1, disabled=disabled)
    community = st.text_input("State", value=community, placeholder="Community (Separate by \",\")", disabled=disabled)
    foodtype = st.multiselect("Food Type", ["Non Vegetarian", "Vegetarian", "Vegan", "Eggetarian"], default=foodtype, disabled=disabled)
    condition = st.multiselect("Condition", ["Diabetes", "Cholesterol", "Hypertension", "Hypothyroid", "Blood Pressure", "PCOS"], default=condition, disabled=disabled)
    allergies = st.text_input("Allergies", value=allergies, placeholder="Allergies (Separate by \",\")", disabled=disabled)
    
    if st.button("Save" if not disabled else "Edit", on_click=saveFields if not disabled else editFields, icon="✔️" if not disabled else "✏️"):
        if not disabled: 
            st.success("User data saved successfully!")
        else:
            st.success("User data edited successfully!")
            
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def appendChatHistory(user_query: str, assistant_response: str):
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

def get_response(request_body):
    with httpx.stream("POST", URI, json=request_body, timeout=60.0) as response:
        for chunk in response.iter_text():  # yields decoded strings
            yield chunk

# Display previous messages
if st.session_state.chat_history:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Question...")

# If new user input
if user_input:
    st.chat_message("user").markdown(user_input)
    request_body = {
        "id": id,
        "knowledge_base": kb,
        "section": section,
        "chunk_category": chunk_category,
        "query": user_input
    }
    if kb == "ConditionVDB" or kb == "NutritionVDB":
        request_body["user_data"] = {
            "name": name,
            "age": age,
            "community": [c.strip() for c in community.split(",")] if community else [],
            "foodType": foodtype,
            "conditions": condition,
            "allergies": [a.strip() for a in allergies.split(",")] if allergies else []
        }
    with st.chat_message("assistant"): 
        response_stream = get_response(request_body)
        assistant_output = ""
        placeholder = st.empty()
        for token in response_stream:
            assistant_output += token
            placeholder.markdown(assistant_output)
        appendChatHistory(user_input, assistant_output)
        