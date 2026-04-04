import os
import streamlit as st
from mem0 import MemoryClient
from openai import OpenAI
import google.generativeai as genai
from edge_tts import Communicate
import asyncio
import base64
import tempfile

# Load secrets
MEM0_API_KEY = st.secrets.get("MEM0_API_KEY")
XAI_API_KEY = st.secrets.get("XAI_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

memory = MemoryClient(api_key=MEM0_API_KEY)
grok_client = OpenAI(base_url="https://api.x.ai/v1", api_key=XAI_API_KEY)

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

user_id = "ernesto"

core_facts = [
    "Ernesto lives at 1567 Triton Ln, Beaumont, CA 92223 near Yucaipa, California.",
    "Ernesto is building Oracle Nexus - a multi-persona AI system with long-term memory."
]

st.set_page_config(page_title="Oracle Nexus", page_icon="🔮", layout="wide")

st.title("🔮 Oracle Nexus")
st.caption("Your personal multi-persona AI with long-term memory + Voice")

st.sidebar.header("Settings")

# Your 14 Personas
persona_options = {
    "1": ("Oracle", "oracle"),
    "2": ("Doctor", "doctor"),
    "3": ("Language Tutor", "language_tutor"),
    "4": ("Personal Chef", "personal_chef"),
    "5": ("Stuff", "stuff"),
    "6": ("Daily Planner", "daily_planner"),
    "7": ("Financial Advisor", "financial_advisor"),
    "8": ("Journal / Reflection", "journal"),
    "9": ("Travel Planner", "travel_planner"),
    "10": ("Shopping Assistant", "shopping_assistant"),
    "11": ("News Curator", "news_curator"),
    "12": ("Project Manager", "project_manager"),
    "13": ("Work Productivity", "work_productivity"),
    "14": ("Midnight Oracle", "midnight_oracle")
}

selected = st.sidebar.radio(
    "Choose Persona",
    options=list(persona_options.keys()),
    format_func=lambda x: f"{x}. {persona_options[x][0]}"
)

agent_id = persona_options[selected][1]
persona_name = persona_options[selected][0]

llm_choice = st.sidebar.selectbox(
    "Choose LLM",
    options=["Grok", "Gemini 2.5 Flash"],
    index=0
)

voice_style = st.sidebar.selectbox(
    "Voice Style",
    options=["Ara (Upbeat Female)", "Eve (Soothing Female)", "Leo (British Male)", 
             "Rex (Calm Male)", "Sal (Smooth Male)", "Sergei (Strong Russian Accent)"],
    index=0
)

use_voice = st.sidebar.checkbox("🔊 Enable Voice Output", value=True)

st.sidebar.info(f"Active: {persona_name} | LLM: {llm_choice} | Voice: {voice_style}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    for fact in core_facts:
        memory.add(fact, user_id=user_id, agent_id="core")
        memory.add(fact, user_id=user_id, agent_id=agent_id)

    core_mem = memory.search(query=prompt, filters={"user_id": user_id, "agent_id": "core"})
    persona_mem = memory.search(query=prompt, filters={"user_id": user_id, "agent_id": agent_id})

    context = ""
    if core_mem and "results" in core_mem and core_mem["results"]:
        context += "\nShared knowledge:\n" + "\n".join([f"• {m.get('memory')}" for m in core_mem["results"][:8]])
    if persona_mem and "results" in persona_mem and persona_mem["results"]:
        context += "\nPersona memories:\n" + "\n".join([f"• {m.get('memory')}" for m in persona_mem["results"][:10]])

    system_prompt = f"""You are {persona_name} Oracle.

You have excellent long-term memory about Ernesto.

{context}
Answer naturally and refer to memories when relevant."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if llm_choice == "Grok":
                response = grok_client.chat.completions.create(
                    model="grok-4-1-fast-reasoning",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                reply = response.choices[0].message.content
            else:
                if not GOOGLE_API_KEY:
                    reply = "Gemini is not configured."
                else:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(system_prompt + "\n\nUser: " + prompt)
                    reply = response.text

            st.markdown(reply)

            # Voice Output with Edge-TTS
            if use_voice:
                try:
                    voice_map = {
                        "Ara (Upbeat Female)": "en-US-AriaNeural",
                        "Eve (Soothing Female)": "en-US-JennyNeural",
                        "Leo (British Male)": "en-GB-RyanNeural",
                        "Rex (Calm Male)": "en-US-GuyNeural",
                        "Sal (Smooth Male)": "en-US-ChristopherNeural",
                        "Sergei (Strong Russian Accent)": "ru-RU-DmitryNeural"
                    }
                    voice_name = voice_map.get(voice_style, "en-US-GuyNeural")
                    
                    communicate = Communicate(reply, voice_name)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        await communicate.save(tmp.name)
                        with open(tmp.name, "rb") as f:
                            audio_bytes = f.read()
                        audio_base64 = base64.b64encode(audio_bytes).decode()
                        st.audio(f"data:audio/mp3;base64,{audio_base64}", format="audio/mp3", autoplay=True)
                except Exception as e:
                    st.warning(f"Voice output failed: {str(e)}")

    st.session_state.messages.append({"role": "assistant", "content": reply})

    memory.add(f"User: {prompt}\nOracle: {reply}", user_id=user_id, agent_id="core")
    memory.add(f"User: {prompt}\nOracle: {reply}", user_id=user_id, agent_id=agent_id)