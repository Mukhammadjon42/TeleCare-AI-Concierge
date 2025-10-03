"""
TeleCare AI Concierge v3 - Ready for Hackathon Demo
---------------------------------------------------
Demo Instructions:
1. Pick a customer (Maria, Ahmed, Jana).
2. Toggle profile flags (usage spike, billing anomaly, travel) as needed.
3. Chat example messages:
   - "My internet is slow" -> triggers speed boost suggestion
   - "Why is my bill higher?" -> triggers billing investigation
   - "I’m traveling to Spain" -> triggers roaming pack suggestion
4. Use Quick Actions (Enable boost, Transfer to human) to simulate task completion.
5. Optional: Record voice / use TTS for smart-home demo.
6. After Transfer to human, check tickets.json for saved tickets.
"""


import streamlit as st
import time
import random
from datetime import datetime, timedelta
import json
import os

# Optional imports for OpenAI, speech, and tts
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False
try:
    import speech_recognition as sr
    SPEECH_RECOG_AVAILABLE = True
except Exception:
    SPEECH_RECOG_AVAILABLE = False
try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False




st.set_page_config(
    page_title="TeleCare AI Concierge (Prototype v2)", layout="wide")

# -----------------------------
# Helper functions (no external libs required for baseline)
# -----------------------------


def simple_sentiment(text: str) -> str:
    if not text or text.strip() == "":
        return "neutral"
    text_l = text.lower()
    anger_keywords = ["angry", "furious", "mad", "hate", "unacceptable",
                      "screw", "ripoff", "rip-off", "complain", "complaint", "outrage"]
    negative_keywords = ["bad", "slow", "slowly", "down", "disconnect", "disconnected", "issue",
                         "problem", "terrible", "poor", "can't", "cannot", "unable", "overpriced", "expensive"]
    positive_keywords = ["thanks", "thank you", "great", "awesome",
                         "love", "good", "nice", "perfect", "thanks!", "cheers"]
    exclamations = text.count("!")
    uppercase_ratio = sum(1 for c in text if c.isupper()) / max(1, len(text))
    if exclamations >= 2 or uppercase_ratio > 0.35 or any(k in text_l for k in anger_keywords):
        return "angry"
    if any(k in text_l for k in negative_keywords):
        return "negative"
    if any(k in text_l for k in positive_keywords):
        return "positive"
    return "neutral"


def generate_ai_reply_local(user_msg: str, sentiment: str, customer_profile: dict) -> str:
    if sentiment == "angry":
        tone = "direct"
    elif sentiment == "negative":
        tone = "empathetic"
    elif sentiment == "positive":
        tone = "upbeat"
    else:
        tone = "friendly"
    name = customer_profile.get("name", "Customer")
    plan = customer_profile.get("plan", "Standard")
    next_bill = customer_profile.get("next_bill", "unknown")
    suggestions = []
    if customer_profile.get("usage_spike"):
        suggestions.append(
            "We've detected higher-than-usual evening usage — we can enable a free temporary speed boost from 19:00–22:00 tonight.")
    if customer_profile.get("upcoming_trip"):
        suggestions.append(
            f"You're traveling to {customer_profile['upcoming_trip']} soon. Would you like us to enable a roaming pack with 5GB for the trip?")
    if customer_profile.get("billing_anomaly"):
        suggestions.append(
            "We noticed an unusual charge in your last invoice — we've created a ticket and can proactively investigate it now.")
    if tone == "direct":
        reply = f"Hi {name}. I understand this is frustrating — here's what I will do immediately: "
        if suggestions:
            reply += " ".join(suggestions)
        else:
            reply += "I'll run a quick diagnostics now and escalate to a specialist if needed."
    elif tone == "empathetic":
        reply = f"Sorry to hear that, {name}. That's not the experience we want. "
        if suggestions:
            reply += " ".join(suggestions)
        else:
            reply += "Let me check your connection and billing details and get back with a clear next step."
    elif tone == "upbeat":
        reply = f"Great news, {name}! We're on it. "
        if suggestions:
            reply += " ".join(suggestions)
        else:
            reply += f"Your {plan} plan looks healthy. Next bill: {next_bill}."
    else:
        reply = f"Hello {name}, thanks for reaching out. "
        if suggestions:
            reply += " ".join(suggestions)
        else:
            reply += "How can I help you today?"
    return reply


def generate_ai_reply_openai(user_msg: str, sentiment: str, customer_profile: dict) -> str:
    # Compose a system prompt with profile & sentiment and ask OpenAI for a reply
    system_prompt = (
        "You are TeleCare AI Concierge. You must respond helpfully and adapt tone to sentiment. "
        "Do not invent personal data. Use the customer's profile and diagnostics provided."
    )
    profile_text = json.dumps(customer_profile)
    user_prompt = f"Customer message: {user_msg}\nSentiment: {sentiment}\nProfile: {profile_text}\nRespond concisely, suggest actions, and include escalation if necessary."
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY", "")
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini" if "gpt-4o-mini" in openai.Model.list() else "gpt-4o",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            max_tokens=250,
            temperature=0.2
        )
        text = response.choices[0].message.content.strip()
        return text
    except Exception as e:
        return f"(OpenAI error: {e}) Fallback to local reply:\\n" + generate_ai_reply_local(user_msg, sentiment, customer_profile)


def simulate_diagnostics(customer_profile: dict) -> dict:
    time.sleep(0.7)
    status = {}
    if customer_profile.get("usage_spike"):
        status["wifi_load"] = "high"
        status["suggested_action"] = "enable_temporary_boost"
    else:
        status["wifi_load"] = random.choice(["normal", "low", "normal"])
        status["suggested_action"] = "none"
    if customer_profile.get("billing_anomaly"):
        status["billing_check"] = "anomaly_found"
    else:
        status["billing_check"] = "ok"
    return status


def save_ticket(ticket: dict) -> str:
    tickets_file = "tickets.json"
    if os.path.exists(tickets_file):
        with open(tickets_file, "r", encoding="utf-8") as f:
            try:
                tickets = json.load(f)
            except Exception:
                tickets = []
    else:
        tickets = []
    tickets.append(ticket)
    with open(tickets_file, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2)
    return ticket["ticket_id"]


def create_ticket_from_context(messages, customer_profile, diagnostics, sentiment):
    ticket = {
        "ticket_id": f"T{int(time.time())}",
        "created_at": datetime.utcnow().isoformat(),
        "customer_id": customer_profile.get("id"),
        "customer_name": customer_profile.get("name"),
        "sentiment": sentiment,
        "diagnostics": diagnostics,
        "conversation": messages[-6:],  # last few messages
        "status": "open"
    }
    return ticket


def speak_text_tts(text: str):
    if not TTS_AVAILABLE:
        return
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.warning(f"TTS error: {e}")


# -----------------------------
# Mock customer profiles (would come from DB in real product)
# -----------------------------
MOCK_CUSTOMERS = {
    "maria": {
        "id": "C001", "name": "Maria", "plan": "Family Home 200 Mbps", "next_bill": "$48.90 on 2025-10-15",
        "usage_spike": True, "upcoming_trip": None, "billing_anomaly": False,
        "notes": "Two kids doing remote learning in the evening."
    },
    "ahmed": {
        "id": "C002", "name": "Ahmed", "plan": "Solo Streamer 100 Mbps", "next_bill": "$29.99 on 2025-10-20",
        "usage_spike": False, "upcoming_trip": "Spain (2025-10-18)", "billing_anomaly": False,
        "notes": "Frequent traveler, likes sports content."
    },
    "jana": {
        "id": "C003", "name": "Jana", "plan": "Basic 50 Mbps", "next_bill": "$22.00 on 2025-10-12",
        "usage_spike": False, "upcoming_trip": None, "billing_anomaly": True,
        "notes": "Recent bill higher than expected."
    }
}

# -----------------------------
# UI layout
# -----------------------------
st.title("TeleCare AI Concierge — Prototype v2")
st.write("Demo of an emotion-aware AI concierge for telecom customer service. (Prototype: local logic + optional OpenAI integration)")

left, right = st.columns([2, 1])

with right:
    st.header("Customer Selector & Profile")
    cust_key = st.selectbox("Choose mock customer",
                            list(MOCK_CUSTOMERS.keys()), index=0)
    profile = MOCK_CUSTOMERS[cust_key]
    st.markdown(
        f"**Name:** {profile['name']}  \n**Plan:** {profile['plan']}  \n**Next bill:** {profile['next_bill']}")
    st.markdown("**Profile notes:**")
    st.write(profile["notes"])
    st.markdown("---")
    st.write("Simulated profile flags:")
    st.write({
        "usage_spike": profile["usage_spike"],
        "upcoming_trip": profile["upcoming_trip"],
        "billing_anomaly": profile["billing_anomaly"]
    })
    st.markdown("---")
    st.write("Demo controls:")
    if st.button("Toggle usage spike"):
        profile["usage_spike"] = not profile["usage_spike"]
        st.experimental_rerun()
    if st.button("Toggle billing anomaly"):
        profile["billing_anomaly"] = not profile["billing_anomaly"]
        st.experimental_rerun()
    st.markdown("---")
    st.write("Integration options:")
    st.write(f"OpenAI available in environment: {OPENAI_AVAILABLE}")
    st.write(f"SpeechRecognition available locally: {SPEECH_RECOG_AVAILABLE}")
    st.write(f"pyttsx3 (TTS) available locally: {TTS_AVAILABLE}")
    st.markdown("---")
    st.write("Developer notes: set env var OPENAI_API_KEY to enable LLM replies.")

with left:
    st.header("Chat with TeleCare Concierge")
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "text": "Welcome to TeleCare. I am the AI Concierge. How can I help?"}
        ]
    # Display messages
    for m in st.session_state.messages:
        if m["role"] == "user":
            st.markdown(f"**You:** {m['text']}")
        elif m["role"] == "assistant":
            st.markdown(f"**Concierge:** {m['text']}")
        elif m["role"] == "system_info":
            st.markdown(f"*System:* {m['text']}")

    # Voice input option (local only)
    use_voice = st.checkbox(
        "Enable microphone voice input (local only)", value=False)
    if use_voice:
        if not SPEECH_RECOG_AVAILABLE:
            st.warning(
                "SpeechRecognition not installed or unavailable. Install `speechrecognition` and `pyaudio` (or use file upload).")
        else:
            st.write(
                "Press 'Record (5s)' then speak. The captured audio will be transcribed locally.")
            if st.button("Record (5s)"):
                try:
                    r = sr.Recognizer()
                    with sr.Microphone() as source:
                        st.write("Recording... speak now.")
                        audio = r.record(source, duration=5)
                        st.write("Transcribing...")
                        text = r.recognize_google(audio)
                        st.session_state.messages.append(
                            {"role": "user", "text": text, "time": datetime.utcnow().isoformat()})
                        st.experimental_rerun()
                except Exception as e:
                    st.warning(f"Microphone/recognition error: {e}")

    # File upload fallback for voice
    audio_file = st.file_uploader("Or upload a WAV file for transcription (optional)", type=[
                                  "wav", "mp3"], key="audio_up")
    if audio_file is not None and SPEECH_RECOG_AVAILABLE:
        if st.button("Transcribe uploaded audio"):
            try:
                r = sr.Recognizer()
                with sr.AudioFile(audio_file) as source:
                    audio = r.record(source)
                    text = r.recognize_google(audio)
                    st.session_state.messages.append(
                        {"role": "user", "text": text, "time": datetime.utcnow().isoformat()})
                    st.experimental_rerun()
            except Exception as e:
                st.warning(f"Transcription error: {e}")

    user_input = st.text_input(
        "Type your message and press Enter", key="input_text_v2")
    send_pressed = st.button("Send")
    if send_pressed or (user_input and st.session_state.get('last_input') != user_input):
        msg = (user_input or "").strip()
        st.session_state['last_input'] = msg
        if msg == "":
            st.warning("Please type a message.")
        else:
            st.session_state.messages.append(
                {"role": "user", "text": msg, "time": datetime.utcnow().isoformat()})
            sentiment = simple_sentiment(msg)
            diagnostics = simulate_diagnostics(profile)
            # Choose reply generator
            use_openai = os.getenv(
                "OPENAI_API_KEY", "") != "" and OPENAI_AVAILABLE
            if use_openai:
                reply = generate_ai_reply_openai(msg, sentiment, profile)
            else:
                reply = generate_ai_reply_local(msg, sentiment, profile)
            if diagnostics.get("suggested_action") == "enable_temporary_boost":
                reply += " (Quick action available: [Enable temporary boost])"
            if diagnostics.get("billing_check") == "anomaly_found":
                reply += " We've flagged a billing anomaly and prepared an investigation ticket."
            st.session_state.messages.append({"role": "assistant", "text": reply, "time": datetime.utcnow(
            ).isoformat(), "meta": {"sentiment": sentiment, "diagnostics": diagnostics}})
            # Optional TTS: speak reply if available and user enabled
            if TTS_AVAILABLE:
                speak_enabled = st.session_state.get("tts_enabled", False)
                if speak_enabled:
                    speak_text_tts(reply)
            st.rerun()

    # Quick-action buttons and escalation
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Enable temporary boost (demo)"):
            # simulate action
            st.session_state.messages.append(
                {"role": "system_info", "text": "Temporary speed boost enabled from 19:00–22:00 tonight."})
            st.experimental_rerun()
    with col2:
        if st.button("Open billing investigation (demo)"):
            st.session_state.messages.append(
                {"role": "system_info", "text": "Billing investigation ticket created. Ticket ID will be shown on transfer."})
            st.experimental_rerun()
    with col3:
        if st.button("Transfer to human (create ticket)"):
            diagnostics = simulate_diagnostics(profile)
            sentiment = "unknown"
            # try to get last sentiment if available
            for m in reversed(st.session_state.messages):
                if m.get("meta") and m["meta"].get("sentiment"):
                    sentiment = m["meta"]["sentiment"]
                    break
            ticket = create_ticket_from_context(
                st.session_state.messages, profile, diagnostics, sentiment)
            ticket_id = save_ticket(ticket)
            st.success(f"Ticket created: {ticket_id} — saved to tickets.json")
            st.experimental_rerun()

    # TTS toggle
    tts_col = st.checkbox(
        "Enable local TTS playback of assistant replies (pyttsx3)", value=False)
    st.session_state['tts_enabled'] = tts_col

    st.markdown("---")
    st.subheader("Conversation Log (raw)")
    st.write(st.session_state.messages)

st.markdown("---")
st.subheader("How to extend this prototype")
st.markdown("""
- **LLM integration**: Set environment variable `OPENAI_API_KEY` and install `openai` to enable richer replies. The code shows how to pass profile + sentiment as context.  
- **Voice I/O**: For local demos, install `speechrecognition` + `pyaudio` and `pyttsx3` for TTS. File-upload transcription also supported.  
- **Escalation**: 'Transfer to human' creates `tickets.json` with context — replace with a real ticketing API in production.  
- **Telemetry**: Connect real modem logs and CDRs to trigger genuine proactive actions.
""")
st.markdown("**Run locally:** `streamlit run telecare_app_v2.py`")
