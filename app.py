import os
import streamlit as st
from mem0 import MemoryClient
from openai import OpenAI
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
import base64

# ====================== SECRETS ======================
MEM0_API_KEY = st.secrets.get("MEM0_API_KEY")
XAI_API_KEY = st.secrets.get("XAI_API_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = st.secrets.get("ELEVENLABS_API_KEY")

memory = MemoryClient(api_key=MEM0_API_KEY)

grok_client = OpenAI(base_url="https://api.x.ai/v1", api_key=XAI_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

if ELEVENLABS_API_KEY:
    eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

user_id = "ernesto"

core_facts = [
    "Ernesto lives at 1567 Triton Ln, Beaumont, CA 92223 near Yucaipa, California.",
    "Ernesto is building Oracle Nexus - a multi-persona AI system with long-term memory."
]

st.set_page_config(page_title="Oracle Nexus", page_icon="🔮", layout="wide")

st.title("🔮 Oracle Nexus")
st.caption("Your personal multi-persona AI with long-term memory + High Quality Voice")

st.sidebar.header("Configuration")

# Persona List
persona_options = {
    "1": ("Oracle", "oracle"),
    "2": ("Stuff", "stuff"),
    "3": ("Doctor", "doctor"),
    "4": ("Language Tutor", "language_tutor"),
    "5": ("Personal Chef", "personal_chef"),
    "6": ("Things to Do", "things_to_do"),
    "7": ("Financial Advisor", "financial_advisor"),
    "8": ("Travel", "travel"),
    "9": ("Shopping List", "shopping_list"),
    "10": ("News", "news"),
    "11": ("Projects", "projects"),
    "12": ("Work Productivity", "work_productivity"),
    "13": ("Midnight Oracle", "midnight_oracle")
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
    options=["Grok", "ChatGPT (GPT-4o)", "Gemini 2.5 Flash"],
    index=0
)

voice_style = st.sidebar.selectbox(
    "Voice Style (Top 25 Popular)",
    options=[
        "Aaron (Grok-like Tech Male)",
        "Adam (Warm Deep Male)",
        "Natasha Valley Girl (Energetic Female)",
        "Brian (Friendly Upbeat Male)",
        "Drew (Calm Mystical Male)",
        "Dave (Powerful Serious Male)",
        "Harry (Clear Versatile Male)",
        "Bella (Natural Female)",
        "Ellie (Friendly Female)",
        "Josh (Modern Energetic Male)",
        "Ryan British (Polite Male)",
        "Michael (Storyteller Male)",
        "Cassidy (Natural Female)",
        "Yearham (Epic Deep Male)",
        "Gretchen (Social Media Female)",
        "Brittney (Energetic Female)",
        "Daniel (Professional Male)",
        "Arnold (Elegant Male)",
        "James (Classic British Male)",
        "Anthony (Warm Modern Male)",
        "Liam (Viral Explainer Male)",
        "Henry (Documentary Male)",
        "Mark (Friendly Storyteller)",
        "Snap (Quirky Fun Male)",
        "Christopher (Calm British Male)"
    ],
    index=0
)

use_voice = st.sidebar.checkbox("🔊 Enable Natural Voice Output", value=True)

st.sidebar.info(f"Active: {persona_name} | LLM: {llm_choice}")

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

    core_mem = memory.search(query=prompt, filters={"user_id": user_id, "agent_id": "core"}, limit=12)
    persona_mem = memory.search(query=prompt, filters={"user_id": user_id, "agent_id": agent_id}, limit=12)

    context = ""
    if core_mem and "results" in core_mem and core_mem["results"]:
        context += "\nShared knowledge:\n" + "\n".join([f"• {m.get('memory')}" for m in core_mem["results"]])
    if persona_mem and "results" in persona_mem and persona_mem["results"]:
        context += "\nPersona memories:\n" + "\n".join([f"• {m.get('memory')}" for m in persona_mem["results"]])

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

            elif llm_choice == "ChatGPT (GPT-4o)":
                if not OPENAI_API_KEY:
                    reply = "OpenAI API key not configured."
                else:
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    reply = response.choices[0].message.content

            else:  # Gemini
                if not GOOGLE_API_KEY:
                    reply = "Gemini is not configured."
                else:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(system_prompt + "\n\nUser: " + prompt)
                    reply = response.text

            st.markdown(reply)

            # ElevenLabs Voice - Best Quality Model (v2)
            if use_voice and ELEVENLABS_API_KEY:
                try:
                    voice_map = {
                        "Aaron (Grok-like Tech Male)": "Aaron",
                        "Adam (Warm Deep Male)": "Adam",
                        "Natasha Valley Girl (Energetic Female)": "Natasha",
                        "Brian (Friendly Upbeat Male)": "Brian",
                        "Drew (Calm Mystical Male)": "Drew",
                        "Dave (Powerful Serious Male)": "Dave",
                        "Harry (Clear Versatile Male)": "Harry",
                        "Bella (Natural Female)": "Bella",
                        "Ellie (Friendly Female)": "Ellie",
                        "Josh (Modern Energetic Male)": "Josh",
                        "Ryan British (Polite Male)": "Ryan",
                        "Michael (Storyteller Male)": "Michael",
                        "Cassidy (Natural Female)": "Cassidy",
                        "Yearham (Epic Deep Male)": "Yearham",
                        "Gretchen (Social Media Female)": "Gretchen",
                        "Brittney (Energetic Female)": "Brittney",
                        "Daniel (Professional Male)": "Daniel",
                        "Arnold (Elegant Male)": "Arnold",
                        "James (Classic British Male)": "James",
                        "Anthony (Warm Modern Male)": "Anthony",
                        "Liam (Viral Explainer Male)": "Liam",
                        "Henry (Documentary Male)": "Henry",
                        "Mark (Friendly Storyteller)": "Mark",
                        "Snap (Quirky Fun Male)": "Snap",
                        "Christopher (Calm British Male)": "Christopher"
                    }
                    voice_id = voice_map.get(voice_style, "Adam")

                    audio = eleven_client.text_to_speech.convert(
                        text=reply[:2000],
                        voice_id=voice_id,
                        model_id="eleven_multilingual_v2",   # Best quality on Starter plan
                        output_format="mp3_44100_128"
                    )
                    audio_bytes = b"".join(audio)
                    audio_base64 = base64.b64encode(audio_bytes).decode()
                    st.audio(f"data:audio/mp3;base64,{audio_base64}", format="audio/mp3", autoplay=True)
                except Exception as e:
                    st.warning(f"Voice output failed: {str(e)[:100]}...")

    st.session_state.messages.append({"role": "assistant", "content": reply})

    memory.add(f"User: {prompt}\nOracle: {reply}", user_id=user_id, agent_id="core")
    memory.add(f"User: {prompt}\nOracle: {reply}", user_id=user_id, agent_id=agent_id)