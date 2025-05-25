import datetime
import os
import json
import google.generativeai as genai
from chat import get_chatbot_response # Import trained chatbot response
import random
from difflib import SequenceMatcher


class intentMatcher:
    def __init__(self):
        with open('intents.json', 'r') as json_data:
         self.intents = json.load(json_data)['intents']
    def get_best_intent_response(self, user_input):
        user_input = user_input.lower()
        
        #check answer that matches the question in the intents
        for intent in self.intents:
            for pattern in intent["patterns"]:
                if pattern.lower() == user_input:
                    return random.choice(intent["response"])
        best_match = None
        highest_score = 0
        
        for intent in self.intents:
            for pattern in intent["pattern"]:
                score = SequenceMatcher(None, user_input, pattern.lower()).ratio()
                if score > highest_score:
                    highest_score = score
                    best_match = intent  
                    
        #return best response that hight a score higher than 0.6
        if best_match and highest_score > 0.6:
            return random.choice(best_match["reponses"])
        return None  
# Configure Google Gemini AI
genai.configure(api_key="AIzaSyD1JaVxrlkMty1R0Zn2sjxC5w9I86woYjs")

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 100,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)


# Load intents.json
with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

# NSFAS Keywords
NSFAS_KEYWORDS = ["nsfas", "funding", "bursary", "loan", "allowance", "scholarship", "application", "university", "college", "financial aid"]

# Analytics log list
analytics_log = []



def is_nsfas_related(question):
    """Check if the question is related to NSFAS"""
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in NSFAS_KEYWORDS)

def get_first_intent_response(user_input):
    """Find the intent that matches user input and return the first response"""
    for intent in intents['intents']:
        for pattern in intent["patterns"]:
            if pattern.lower() in user_input.lower():
                return intent["responses"][0]
    return None

def GenerateResponse(input_text):
    """Use Google Gemini AI for NSFAS-related responses (limited to two sentences)"""
    response = model.generate_content([
        "You are an NSFAS chatbot. Answer in exactly two sentences.",
        f"Question: {input_text}",
        "Answer: ",
    ])
    return response.text.strip()
 #to help students understand output in their mother toungue
def translate_to_english(text):
    """Translate non-English input to English (preserving NSFAS terms)"""
    response = model.generate_content([
        "Translate this to English, but keep any NSFAS terms unchanged:",
        text
    ])
    return response.text.strip()

def log_interaction(user_input, response, used_gemini):
    """Log each user interaction"""
    analytics_log.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "user_input": user_input,
        "response": response,
        "used_gemini": used_gemini
    })
def detect_language(text): #define language detector using gemini
    """Detect the language of the input text"""
    response = model.generate_content(["Identity the language of this text. Just return the name of this language", text])
    return response.text.strip().lower()
def verify_document(filepath):
    """document verification"""
    if filepath.endswith('.pdf'):
     return {"status": "Received PDF", "verified": False}
 
def chat():
    """Main chatbot function"""
    user_name = input("Before we start, may I have your name? ")
    user_email = input("Please enter your email address: ")
    print(f"Hello {user_name}, how can I assist you with NSFAS today?")
    print("Type 'quit' to exit.")
    
    while True:
        user_input = input(f"{user_name}: ")
        if user_input.lower() == "quit":
            break

        # Check if the user wants to speak to an intern/official
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
            
            # Save ticket to a JSON file (append mode)
            with open("pending_tickets.json", "a") as f:
                json.dump(ticket_data, f)
                f.write("\n")  # Add newline for multiple entries
                
            print(f"NSFAS Chatbot: Your request has been submitted. Ticket Number: {ticket_number}")
            print("NSFAS Chatbot: An NSFAS representative will contact you via email soon.")
            log_interaction(user_input, f"Ticket created: {ticket_number}", used_gemini=False)
            continue  # This is now correctly inside the if block

        # Rest of your chatbot logic...
        detected_input = detect_language(user_input)
        if detected_input != "english":
            translated_input = translate_to_english(user_input)
        else:
            translated_input = user_input

        if not is_nsfas_related(translated_input):
            print("NSFAS Chatbot: Sorry, I can only answer NSFAS-related questions.")
            log_interaction(user_input, "Unrelated to NSFAS", used_gemini=False)
            continue

        intent_response = get_first_intent_response(translated_input)
        if intent_response:
            print(f"NSFAS Chatbot: {intent_response}")
            log_interaction(user_input, intent_response, used_gemini=False)
            continue

        bot_response = get_chatbot_response(translated_input)
        if bot_response != "I do not understand...":
            print(f"NSFAS Chatbot: {bot_response}")
            log_interaction(user_input, bot_response, used_gemini=False)
        else:
            print("NSFAS Chatbot: Give me few seconds, let me get more info...")
            gemini_response = GenerateResponse(translated_input)
            print(f"NSFAS CHATBOT(GEMINI): {gemini_response}")
            log_interaction(user_input, gemini_response, used_gemini=True)

    # Save analytics log on exit
    with open("analytics_log.json", "w") as f:
        json.dump(analytics_log, f, indent=4)
    print("Session ended. Thank you!")
if __name__ == "__main__":
    chat()