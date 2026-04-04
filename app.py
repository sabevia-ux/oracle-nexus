# ... (keep everything the same until the voice section)

            st.markdown(reply)

            # ElevenLabs Voice Output - Improved error handling
            if use_voice and ELEVENLABS_API_KEY:
                try:
                    voice_map = {
                        "Friendly Female": "EXAVITQu4vr4xnSDxMaL",
                        "Upbeat Female": "21m00Tcm4TlvDq8ikWAM",
                        "Calm Male": "TxGEqnHWrfWFTfGW9XjX",
                        "Deep Male": "AZnzlk1XvdvUeBnXmlld",
                        "British Male": "en-GB-RyanNeural",
                        "Russian Male": "pNInz6obpgDQGcFmaJgB"
                    }
                    voice_id = voice_map.get(voice_style, "EXAVITQu4vr4xnSDxMaL")

                    audio = eleven_client.generate(
                        text=reply[:2000],   # Limit length to avoid credit overuse
                        voice_id=voice_id,
                        model="eleven_monolingual_v1"
                    )
                    audio_bytes = b"".join(audio)
                    audio_base64 = base64.b64encode(audio_bytes).decode()
                    st.audio(f"data:audio/mp3;base64,{audio_base64}", format="audio/mp3", autoplay=True)
                    st.success("🔊 Voice played successfully")
                except Exception as e:
                    error_msg = str(e)
                    if "credit" in error_msg.lower() or "quota" in error_msg.lower():
                        st.error("❌ Out of ElevenLabs credits. Please check your plan or wait for renewal.")
                    elif "voice" in error_msg.lower():
                        st.error("❌ Voice not found. Try a different voice style.")
                    else:
                        st.warning(f"Voice output failed: {error_msg[:100]}...")
            else:
                if use_voice and not ELEVENLABS_API_KEY:
                    st.warning("ElevenLabs API key not found in secrets.")

    st.session_state.messages.append({"role": "assistant", "content": reply})

    memory.add(f"User: {prompt}\nOracle: {reply}", user_id=user_id, agent_id="core")
    memory.add(f"User: {prompt}\nOracle: {reply}", user_id=user_id, agent_id=agent_id)