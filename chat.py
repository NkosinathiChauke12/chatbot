import random
import json
import torch
import datetime
import os
import google.generativeai as genai
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize

# Set device for PyTorch
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load intents
with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

# Load trained model
FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "NSFAS CHATBOT"
NSFAS_KEYWORDS = ["nsfas", "funding", "bursary", "loan", "allowance", "scholarship", "application", "university", "college", "financial aid"]
analytics_log = []

# Google Gemini setup
genai.configure(api_key="AIzaSyD1JaVxrlkMty1R0Zn2sjxC5w9I86woYjs") 
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 100,
    "response_mime_type": "text/plain",
}
gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def GenerateResponse(input_text):
    response = gemini_model.generate_content([
        "You are an NSFAS chatbot. Answer in exactly two sentences.",
        f"Question: {input_text}",
        "Answer: ",
    ])
    return response.text.strip()

def translate_to_english(text):
    response = gemini_model.generate_content([
        "Translate this to English, but keep any NSFAS terms unchanged:",
        text
    ])
    return response.text.strip()

def detect_language(text):
    response = gemini_model.generate_content(["Identify the language of this text. Just return the name of this language", text])
    return response.text.strip().lower()

def is_nsfas_related(question):
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in NSFAS_KEYWORDS)

def log_interaction(user_input, response, used_gemini):
    analytics_log.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "user_input": user_input,
        "response": response,
        "used_gemini": used_gemini
    })

def verify_document(filepath):
    if filepath.endswith('.pdf'):
        return {"status": "Received PDF", "verified": False}

# Check for intent response
def get_first_intent_response(user_input):
    for intent in intents['intents']:
        for pattern in intent["patterns"]:
            if pattern.lower() in user_input.lower():
                return random.choice(intent["responses"])
    return None

# Get chatbot response: intent first, Gemini fallback
def get_chatbot_response(sentence):
    intent_response = get_first_intent_response(sentence)
    if intent_response:
        return intent_response
    else:
        return GenerateResponse(sentence)

# Main chatbot logic
def chat():
    user_name = input("Before we start, may I have your name? ")
    user_email = input("Please enter your email address: ")
    print(f"Hello {user_name}, how can I assist you with NSFAS today?")
    print("Type 'quit' to exit.")

    while True:
        user_input = input(f"{user_name}: ")
        if user_input.lower() == "quit":
            break

        intern_keywords = ["speak to", "talk to", "connect me", "chat with", "reach out"]
        target_keywords = ["intern", "official", "nsfas staff", "nsfas agent", "representative"]

        if (any(word in user_input.lower() for word in intern_keywords) and
            any(role in user_input.lower() for role in target_keywords)):

            ticket_number = f"TKT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            ticket_data = {
                "ticket_number": ticket_number,
                "student_name": user_name,
                "email": user_email,
                "question": user_input,
                "timestamp": datetime.datetime.now().isoformat()
            }

            with open("pending_tickets.json", "a") as f:
                json.dump(ticket_data, f)
                f.write("\n")

            print(f"NSFAS Chatbot: Your request has been submitted. Ticket Number: {ticket_number}")
            print("NSFAS Chatbot: An NSFAS representative will contact you via email soon.")
            log_interaction(user_input, f"Ticket created: {ticket_number}", used_gemini=False)
            continue

        detected_input = detect_language(user_input)
        if detected_input != "english":
            translated_input = translate_to_english(user_input)
        else:
            translated_input = user_input

        if not is_nsfas_related(translated_input):
            print("NSFAS Chatbot: Sorry, I can only answer NSFAS-related questions.")
            log_interaction(user_input, "Unrelated to NSFAS", used_gemini=False)
            continue

        bot_response = get_chatbot_response(translated_input)
        print(f"NSFAS Chatbot: {bot_response}")
        log_interaction(user_input, bot_response, used_gemini=("NSFAS CHATBOT (GEMINI):" in bot_response))

    with open("analytics_log.json", "w") as f:
        json.dump(analytics_log, f, indent=4)
    print("Session ended. Thank you!")

if __name__ == "__main__":
    chat()