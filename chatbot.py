import re
import sqlite3
import streamlit as st
import requests

# Config
DB_PATH = "/home/santhoshtk/Desktop/Singapore_Airlines_Customer_Support_Chatbot/Data/singapore_airlines_bookings.db"
NEBIUS_API_KEY = ""
NEBIUS_MODEL = "meta-llama/Llama-3.3-70B-Instruct-LoRa:singapore-airline-support-bSbK"
NEBIUS_URL = "https://api.studio.nebius.com/v1/chat/completions"

# ---------------- System Prompt ----------------
SYSTEM_TEMPLATE = """You are a customer-support assistant for Singapore Airlines.
Your tone should be human-like with empathy, not robotic.

Purpose:
- Understand any customer message about flights, bookings, cancellations, check-in, baggage, or refunds.
- Respond naturally, politely, and concisely.
- Stay strictly on airline topics. 
- If the message is unrelated to air travel, reply: “I can only help with airline-related questions such as flight status, bookings, or baggage.”
- Do not engage in off-topic chat, math, jokes, or personal questions.

Behavior and policy:
1. Be factual and professional. 
2. Never invent or assume data not confirmed by the system or database.
3. If required data (flight number, date, booking reference) is missing, ask for it instead of guessing.
4. Do not confirm a refund, booking, or payment unless an API or database result explicitly confirms it.
5. Never output full credit-card numbers, phone numbers, or email addresses.
6. Be brief (1–3 sentences) and in a helpful airline-agent tone.

Context handling:
- Use any context provided in the “Context:” section to keep the conversation coherent.
- If the context is empty or irrelevant, continue normally.

Output format:
Return only a plain, natural sentence to the customer—no code or JSON.
"""

# ---------------- DB Helpers ----------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def fetch_booking(booking_id):
    conn = get_conn()
    cur = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id.upper(),))
    row = cur.fetchone()
    conn.close()
    return row

def build_context_from_row(row):
    if not row:
        return ""
    return (
        f"Context: Booking ID {row[0]}; Passenger {row[1]}; Flight {row[2]}; Seat {row[3]}; "
        f"Class {row[4]}; From {row[5]} to {row[6]}; Departure {row[7]}; Arrival {row[8]}; "
        f"Status {row[9]}; Baggage {row[10]}."
    )

# ---------------- LLM Call ----------------
def call_nebius(messages):
    if not NEBIUS_API_KEY:
        return "Error: NEBIUS_API_KEY not set."
    payload = {
        "model": NEBIUS_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "top_p": 0.95,
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {NEBIUS_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        r = requests.post(NEBIUS_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"LLM call failed: {e}"

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Singapore Airlines MCP", layout="centered")
st.title("✈️ Singapore Airlines Customer Assistant (Nebius LLM)")

mode = st.radio("Select Mode", ["General", "Specific"], horizontal=True)

booking_row = None
booking_context = ""
valid_booking = False

# --- Specific Mode ---
if mode == "Specific":
    st.info("Enter your 6-digit booking reference (example: A1B2C3)")
    booking_id = st.text_input("Booking Reference (6 chars)").strip().upper()

    if booking_id:
        if not re.fullmatch(r"[A-Z0-9]{6}", booking_id):
            st.error("Invalid format. Use a 6-character alphanumeric code (A-Z,0-9).")
        else:
            row = fetch_booking(booking_id)
            if row:
                booking_row = row
                booking_context = build_context_from_row(row)
                valid_booking = True
                st.success("✅ Booking loaded successfully.")
                st.text(booking_context)
            else:
                st.warning("No booking found for this reference.")

# --- Chat Section ---
st.markdown("---")

if mode == "Specific" and not valid_booking:
    st.warning("Please enter a valid 6-digit booking reference to start chatting.")
    st.stop()

user_message = st.text_area(
    "Customer Message",
    placeholder="Type your message here...",
    disabled=(mode == "Specific" and not valid_booking),
)

if st.button("Send", disabled=(mode == "Specific" and not valid_booking)):
    if not user_message.strip():
        st.warning("Please enter a message.")
    else:
        # Prepare messages for Nebius
        messages = [{"role": "system", "content": SYSTEM_TEMPLATE}]
        if mode == "Specific" and booking_context:
            messages.append({"role": "system", "content": booking_context})
        messages.append({"role": "user", "content": user_message.strip()})

        with st.spinner("Contacting Singapore Airlines Assistant..."):
            reply = call_nebius(messages)

        st.markdown("**Assistant Reply:**")
        st.write(reply)

        with st.expander("🔍 Debug / Logs"):
            st.json({
                "mode": mode,
                "valid_booking": valid_booking,
                "booking_context": booking_context,
                "messages_sent_to_nebius": messages,
                "llm_reply": reply
            })
