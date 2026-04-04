import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from mem0 import MemoryClient
from openai import OpenAI

load_dotenv()

memory = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))
client = OpenAI(base_url="https://api.x.ai/v1", api_key=os.getenv("XAI_API_KEY"))

user_id = "ernesto"

# Force correct current date
CURRENT_DATE = "April 4, 2026"

# Core facts
core_facts = [
    "Ernesto lives at 1567 Triton Ln, Beaumont, CA 92223 near Yucaipa, California.",
    "Ernesto is building Oracle Nexus - a multi-persona AI system with long-term memory.",
    f"Today is {CURRENT_DATE}."
]

st.set_page_config(page_title="Oracle Nexus", page_icon="🔮", layout="wide")

st.title("🔮 Oracle Nexus")
st.caption(f"Your personal multi-persona AI with long-term memory • Today is {CURRENT_DATE}")

# Sidebar
st.sidebar.header("Select Persona")

persona_options = {
    "1": ("Oracle", "oracle", "Main everyday assistant"),
    "2": ("Doctor", "doctor", "Symptoms, medications, appointments"),
    "3": ("Language Tutor", "language_tutor", "Russian + other languages"),
    "4": ("Personal Chef", "personal_chef", "Turkish, Mexican, New Orleans recipes"),
    "5": ("Stuff", "stuff", "Random thoughts, brain dumps"),
    "6": ("Daily Planner", "daily_planner", "Scheduling, time blocking"),
    "7": ("Financial Advisor", "financial_advisor", "Budget, expenses, money decisions"),
    "8": ("Journal / Reflection", "journal", "Journaling, mood, self-reflection"),
    "9": ("Travel Planner", "travel_planner", "Trips, itineraries"),
    "10": ("Shopping Assistant", "shopping_assistant", "Product research, shopping"),
    "11": ("News Curator", "news_curator", "Personalized news summaries"),
    "12": ("Project Manager", "project_manager", "Managing specific projects"),
    "13": ("Work Productivity", "work_productivity", "Meetings, emails, work tasks"),
    "14": ("Midnight Oracle", "midnight_oracle", "X-rated / adult conversations")
}

selected = st.sidebar.radio(
    "Choose Persona",
    options=list(persona_options.keys()),
    format_func=lambda x: f"{x}. {persona_options[x][0]}"
)

agent_id = persona_options[selected][1]
persona_name = persona_options[selected][0]

st.sidebar.info(f"Active: {persona_name}")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Load core facts
    for fact in core_facts:
        memory.add(fact, user_id=user_id, agent_id="core")
        memory.add(fact, user_id=user_id, agent_id=agent_id)

    # Retrieve memories
    core_mem = memory.search(query=prompt, filters={"user_id": user_id, "agent_id": "core"})
    persona_mem = memory.search(query=prompt, filters={"user_id": user_id, "agent_id": agent_id})

    context = ""
    if core_mem and "results" in core_mem and core_mem["results"]:
        context += "\nShared knowledge:\n" + "\n".join([f"• {m.get('memory')}" for m in core_mem["results"][:8]])
    if persona_mem and "results" in persona_mem and persona_mem["results"]:
        context += "\nPersona memories:\n" + "\n".join([f"• {m.get('memory')}" for m in persona_mem["results"][:10]])

    system_prompt = f"""You are {persona_name} Oracle.

Current date is {CURRENT_DATE}. Always use this exact date when asked about today or current time.

You have excellent long-term memory about Ernesto.

{context}

Answer naturally and refer to memories when relevant. Never say the date is in 2024."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model="grok-4-1-fast-reasoning",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            reply = response.choices[0].message.content
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Save to memory
    memory.add(f"User: {prompt}\nOracle: {reply}", user_id=user_id, agent_id="core")
    memory.add(f"User: {prompt}\nOracle: {reply}", user_id=user_id, agent_id=agent_id)