"""
StudyBuddy Chatbot - Flask backend

Serves the chat UI and forwards messages to the Gemini API,
using the persona and rules defined in chatbot_config.py.
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import google.generativeai as genai

from chatbot_config import SYSTEM_PROMPT

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to your .env file before starting the app."
    )

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-3.1-flash-lite"

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYSTEM_PROMPT,
)

app = Flask(__name__)


@app.route("/")
def home():
    """Render the chat UI."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Receive a user message plus prior turns, return the model's reply."""
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    raw_history = data.get("history") or []

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    # Convert the client-side history into the format the Gemini SDK expects.
    gemini_history = []
    for turn in raw_history:
        role = turn.get("role")
        text = turn.get("text")
        if role in ("user", "model") and text:
            gemini_history.append({"role": role, "parts": [text]})

    try:
        chat_session = model.start_chat(history=gemini_history)
        response = chat_session.send_message(user_message)
        reply_text = response.text
    except Exception as exc:  # keep the API resilient to upstream errors
        return (
            jsonify(
                {
                    "error": "StudyBuddy couldn't process that message. Please try again.",
                    "details": str(exc),
                }
            ),
            500,
        )

    return jsonify({"reply": reply_text})


if __name__ == "__main__":
    app.run(debug=True)
