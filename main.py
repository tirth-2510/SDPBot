import ast
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from pymongo import MongoClient
# import os
# from dotenv import load_dotenv

# load_dotenv()
# groq_api_key = os.getenv("GROQ_API_KEY")
# mongo_uri = os.getenv("MONGODB_URI")

groq_api_key = st.secrets["GROQ_API_KEY"]
mongo_uri = st.secrets["MONGODB_URI"]

# <------------------------- MongoDB Connection ------------------------->
mongoClient = MongoClient(mongo_uri)
db=mongoClient["sdp_chatbot"]
collection=db["foodItems"]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# <------------------------- Functions ------------------------->
def appendInChatHistory(role: str, content: str):
    st.session_state.chat_history.append({"role": role, "content": content})

def get_groq_client():
    return ChatGroq(
        # model="llama-3.1-8b-instant",
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.5,
        api_key=groq_api_key,
    )

def get_mongo_query(user_query: str):
    system_prompt = f"""
        You are a highly intelligent AI assistant, specialized in generating personalized diet plans by converting user queries into MongoDB aggregation pipeline queries.
        Objective: Based on the user's question and personal details, generate an aggregation query to retrieve the most relevant diet plan records from a MongoDB collection.
        Instructions:
        Only return the aggregation query in valid MongoDB syntax.
        Do not return any explanation, additional text, or commentary.
        Always limit results to top 5 where applicable.
        Use double quotes (") for all fields and operators (e.g., "$match", "$gte").
        Always format the query strictly as a JSON list of stages for direct pipeline usage.

        SCHEMA:
        'food': (string) food name in english, 
        'hindiName': (string) food name in hindi, 
        'foodType': (string) Food type [V: Vegetarian, NV: Non-vegetarian, E: Eggetarian, Ve: Vegan], 
        'type': (string) Type of food 
            [
            F: Fruits, 
            N: Nuts / Paans,
            NS: Oilseeds / Nut Seeds,
            NB: Nut Butters,
            DY: Dairy, 
            DK: Milk / Buttermilk / Chaach,
            DP: Paneer / Tofu,
            Y: Yogurt / Curd,
            DB: Cheese / Butter / Ghee,
            DD: Milk Additives,
            D: Other Drinks (non-dairy, no milk),
            DM: Beverages / Smoothies / Shakes with Animal Milk,
            DMK: Keto Drinks with Milk,
            DS: Vegan Beverages / Smoothies with Nut Milk,
            DSK: Keto Drink Smoothies,
            DJ: Juices,
            DC: Caffeinated Beverages (Tea / Coffee),
            DO: Soda / Soft Drinks,
            DZ: Drinks with Zero Calories,
            WC: Breakfast Cereals / International Cereals (e.g., Corn Flakes),
            WM: International Snack with Milk (e.g., Poha with Curd),
            M: Meal (typically International Plans),
            R: Raita,
            S: Side Salad,
            SA: Complete Salad / Full Salad (International),
            C: Curries,
            A: All Dry Vegetables,
            SO: Soups,
            B: Chapati / Roti / Rice / Pulao / Biryani / Breads,
            WP: Stuffed Chapati / Paranthas / Naan,
            BN: Vermicelli,
            BO: Noodles,
            BS: Pasta / Spaghetti,
            BB: Breads,
            HS: Healthy Snacks,
            WN: Namkeen Snacks,
            PA: Papad,
            PO: Popcorn,
            CP: Chips (all kinds),
            W: Other Snacks,
            CH: Chocolates,
            WI: Ice Cream / Kulfi,
            WD: Indian Sweets / Desserts (Kheer / Barfi) / Dessert Snacks,
            WT: Candies,
            CR: Cakes / Rolls,
            WG: Granola Bars,
            HN: Sugary Items (Honey / Jams / Chikki / Sugary Snacks),
            WB: Biscuits / Cookies,
            RS: Rusks / Waffy,
            WA: Cakes / Pastry / Donut / Jars / Brownie / Muffin / Cupcake,
            WU: Burger,
            WZ: Pizza,
            WE: Tacos / Burritos,
            WW: Rolls / Wraps,
            WH: Hotdogs,
            SK: Ketchups,
            SE: Dips / Spreads,
            XD: Cooking Sauces,
            SD: Chutney / Pickles / Seasoning,
            XO: Oils / Fat,
            XS: Sugar / Jaggery,
            XM: Spices,
            Z: Supplements,
            FI: Functional Item,
            IS: Immunity Boosters (Ghee / Decoction / Oil Pulling),
            XP: Instant Mix / Premix,
            FF: Frozen Foods,
            WR: Ready to Eat,
            RW: Raw Items (Masalas / Tea Leaves / Coffee Powder),
            HC: Raw Pulses and Cereals,
            HA: Raw Chicken / Fish / Other Animal Foods,
            PW: Post Workout Snacks,
            WS: Drinks Smoothie,
            X: Miscellaneous Add-ons,
            Q: Barbeque,
            G: Pancakes / Waffles / Tart,
            K: Cheela,
            ],
        'possibleSlots': (Int) Usual slots to consume the food 
            [
            -1: Alternative Choice,
            0: When you wake up,
            1: Before Breakfast,
            2: Breakfast,
            3: Mid-Morning Snack,
            4: Lunch,
            5: Post-Lunch,
            6: Evening Snack,
            7: Dinner,
            8: Post-Dinner
            ], 
        'calories': (float) Calories, 
        'carbs': (float) Carbohydrates, 
        'fat': (float) Fat, 
        'protein': (float) Protein, 
        'fiber': (float) Fiber, 
        'weight_loss_score': (int) Weight loss score, 
        'best_slot_in_weight_loss': (int) Best slot for weight loss, 
        'community': (string) Community
            [
            U: All States,
            P: North India,
            S: South India,
            M: Maharashtra,
            G: Gujarat,
            B: Bengali,
            ], 
        'avoidIn': (string) Avoid in Condition
        'recommendedIn': (string) Recommended in Condition, 
        'recipe': (string) Recipe of the food, 
        'steps': (string) Steps to prepare the food, 
        'recipeHindi': (string) Recipe of the food in hindi, 
        'stepsHindi': (string) Steps to prepare the food in hindi, 
        'video': (string) Video URL, 
        'portion': (float) Portion, 
        'portion_unit': (string) Portion unit, 
        'country': (string) Country
            [
            IND: India,
            IR: Iran,
            AUS: Australia,
            UK: United Kingdom,
            USA: United States of America,
            CAN: Canada,
            EGY: Egypt,
            MAL: Malaysia,
            UAE: United Arab Emirates   
            ], 
        'diabetes_score': (int) Diabetes score, 
        'best_slot_in_diabetes': (int) Best slot for diabetes, 
        'bp_score': (int) Blood pressure score, 
        'best_slot_in_bp': (int) Best slot for blood pressure, 
        'cholestrol_score': (int) Cholestrol score, 
        'best_slot_in_cholestrol': (int) Best slot for cholestrol, 
        'pcos_score': (int) PCOS score, 
        'best_slot_in_pcos': (int) Best slot for PCOS, 
        'muscle_building_score': (int) Muscle building score, 
        'best_slot_in_morning_workout': (int) Best slot for morning workout, 
        'best_slot_in_evening_workout': (int) Best slot for evening workout

        Score rules = 
            9: "Excellent food choice",
            6: "Good food choice",
            3: "Average food choice",
            1: "Below average choice",
            -1: "Not recommended",
            
        If Score is -1 and Slot is also -1 than the food items is not recommended

        Conditions for avoidIn and recommendedIn fields:
            A: Acidity,
            AN: Anemia",
            AI: Anti-inflammatory,
            B: Blood Pressure,
            C: Cholesterol,
            CR: Calcium-Rich,
            D: Diabetes,
            PD: Pre-Diabetes,
            GD: Gestational Diabetes,
            E: Egestion / Constipation,
            FL: Fatty Liver,
            HP: High Protein,
            IR: Iron-Rich,
            LP: Low Protein,
            P: PCOS,
            T: Hypothyroid,
            S: Sleep Disorder,
            UA: Uric Acid,
            VB: Vitamin B12,
            VD: Vitamin D,
            W: Wind / Flatulence / Bloating,
            PT1: Pregnancy Trimester 1,
            PT2: Pregnancy Trimester 2,
            PT3: Pregnancy Trimester 3,
            L1: Postpartum 0-45 Days,
            L2: Lactation 0-6 Months,
            L3: Lactation 7-12 Months,
            N: Nuts,
            F: Fish,
            E: Eggs,
            ML: Milk / Lactose,
            SO: Soya,
            SF: Seafood,
            G: Gluten,

        Example:
        Q: Create a vegetarian Indian diet plan for weight loss
        [
            {{
                "$match": {{
                    "foodType": "V",
                    "country": "IND",
                    "weight_loss_score": {{ "$gte": 6 }},
                    "best_slot_in_weight_loss": {{ "$ne": -1 }}
                }}
            }},
            {{
                "$group": {{
                    "_id": "$best_slot_in_weight_loss",
                    "foods": {{
                        "$push": {{
                            "food": "$food",
                            "portion": "$portion",
                            "portion_unit": "$portion_unit",
                            "calories": "$calories",
                            "protein": "$protein"
                        }}
                    }}
                }}
            }},
            {{
                "$project": {{
                    "_id": 0,
                    "slot": "$_id",
                    "foods": {{ "$slice": ["$foods", 1] }}
                }}
            }},
            {{
                "$sort": {{ "slot": 1 }}
            }}
        ]

        Q: Generate a high-protein muscle building plan for a non-vegetarian Indian person
        [
            {{
                "$match": {{
                    "foodType": {{ "$in": ["NV", "E"] }},
                    "country": "IND",
                    "muscle_building_score": {{ "$gte": 6 }},
                    "best_slot_in_morning_workout": {{ "$ne": -1 }}
                }}
            }},
            {{
                "$group": {{
                    "_id": "$best_slot_in_morning_workout",
                    "foods": {{
                        "$push": {{
                            "food": "$food",
                            "portion": "$portion",
                            "portion_unit": "$portion_unit",
                            "protein": "$protein",
                            "calories": "$calories"
                        }}
                    }}
                }}
            }},
            {{
                "$project": {{
                    "_id": 0,
                    "slot": "$_id",
                    "foods": {{ "$slice": ["$foods", 1] }}
                }}
            }},
            {{
                "$sort": {{ "slot": 1 }}
            }}
        ]

        Q: I am diabetic, can you generate a weight loss plan also i would prefer a snack item in the evening
        [
            {{
                "$match": {{
                    "weight_loss_score": {{ "$gte": 6 }},
                    "diabetes_score": {{ "$gte": 6 }},
                    "best_slot_in_weight_loss": {{ "$ne": -1 }}
                }}
            }},
            {{
                "$addFields": {{
                    "preferred_snack": {{
                        "$cond": [
                            {{ "$eq": ["$best_slot_in_weight_loss", 6] }},
                            true,
                            false
                        ]
                    }}
                }}
            }},
            {{
                "$group": {{
                    "_id": "$best_slot_in_weight_loss",
                    "foods": {{
                        "$push": {{
                            "food": "$food",
                            "portion": "$portion",
                            "portion_unit": "$portion_unit",
                            "calories": "$calories",
                            "protein": "$protein",
                            "type": "$type",
                            "preferred_snack": "$preferred_snack"
                        }}
                    }}
                }}
            }},
            {{
                "$project": {{
                    "_id": 0,
                    "slot": "$_id",
                    "foods": {{
                        "$slice": [
                            {{
                                "$filter": {{
                                    "input": "$foods",
                                    "as": "item",
                                    "cond": {{
                                        "$or": [
                                            {{ "$eq": ["$$item.preferred_snack", true] }},
                                            {{ "$ne": ["$_id", 6] }}
                                        ]
                                    }}
                                }}
                            }},
                            1
                        ]
                    }}
                }}
            }},
            {{
                "$sort": {{ "slot": 1 }}
            }}
        ]

        As an expert you must use them whenever required.
        Note: You have to just return the query nothing else, group by slots Only. Don't return any additional text with the query.
        Please follow this strictly, if you can't generate a query, return None.
        Query:
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_query),
    ]
    llm = get_groq_client()
    return llm.invoke(messages)

def getMongoResponse(query: list):
    return collection.aggregate(query)
 
def textualizeDocs(doc: dict):
    SlotDict = {
        -1: "Its an Alternative Option not preferred first",
        0: "When you wake up",
        1: "Before Breakfast",
        2: "Breakfast",
        3: "Mid Morning Snack",
        4: "Lunch",
        5: "Post Lunch",
        6: "Evening Snack",
        7: "Dinner",
        8: "Post Dinner",
    }
    
    output = f"""{SlotDict[doc.get("slot", "")]}"""+"\n"
    foods = doc.get("foods", [])
    for food in foods:
        output += "  "+food.get("food", "Unknown")+"\n"
        portion = food.get("portion", "N/A")
        unit = food.get("portion_unit", "")
        calories = food.get("calories")
        carbs = food.get("carbs")
        fat = food.get("fat")
        protein = food.get("protein")
        fiber = food.get("fiber")
        output += "  "+f"Portion: {portion} {unit}\n"
        if calories is not None:
            output += "  "+f"Calories: {calories}\n"
        if carbs is not None:
            output += "  "+f"Carbs: {carbs}\n"
        if fat is not None:
            output += "  "+f"Fat: {fat}\n"
        if protein is not None:
            output += "  "+f"Protein: {protein}\n"
        if fiber is not None:
            output += "  "+f"Fiber: {fiber}\n"
        output+="\n"
    return output
    
def generateDietPlan(user_input: str):
    aggr_query = get_mongo_query(user_input)
    aggregation_query = ast.literal_eval(aggr_query.content)
    # st.code(aggregation_query)
    mongo_documents = getMongoResponse(aggregation_query)
    context = ""
    for document in mongo_documents:
        text = textualizeDocs(document)
        context += text+"\n"
    system = f"""You are a Nutrition Assistant. Your task is to generate a personalized daily diet plan 
    based on the user's health conditions, dietary preferences, and nutritional goals. Consider only the context present between [START CONTENT] and [END CONTENT]
    RULES:
    - Do not exceed 250 words.
    - Use only the following MongoDB documents to construct the meal plan:
    [START CONTENT]
    {context}
    [END CONTENT]
    - Only list meals with items, quantities, and their individual macros.
    - Do not include totals after each meal section.
    - You may include a single total for daily macros intake at the end.
    - Do not add disclaimers, introductions, or explanations. Only return the meal plan.
    - Response Format: 
        Slot: 
        - Food item: macros
        - Food item: macros
        ...
        
        Slot: 
        - Food item: macros
        - Food item: macros
        ... 
        
        
        Total Macros:
        - macros: total, macros: total, macros: total
        
    """

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=user_input),
    ]
    llm = get_groq_client()
    response = llm.stream(messages)
    return response
            
# <------------------------- Streamlit UI ------------------------->
st.set_page_config(page_title="SDP Chatbot", layout="wide")
st.title("🤖 SDP Diet Plan Generator")

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
    appendInChatHistory("user", user_input)
    with st.chat_message("assistant"):
        response_stream = generateDietPlan(user_input)
        assistant_output = ""
        placeholder = st.empty()
        for token in response_stream:
            if token.content is None:
                continue
            assistant_output += token.content
            placeholder.markdown(assistant_output)
        appendInChatHistory("assistant", assistant_output)