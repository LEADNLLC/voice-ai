"""
⚡ VOICE — AI That Closes Deals ⚡
===================================
🧪 AI TESTING LAB - One-click agent testing
📅 FULL APPOINTMENT SYSTEM - Complete lifecycle tracking
📆 INTERACTIVE CALENDAR - Visual calendar with drag & drop
📱 AUTO SMS - Confirmation & reminder texts
💰 LIVE COST TRACKING - Real-time budget monitoring
🤖 12 OUTBOUND AGENTS - Sales team (NEPQ methodology)
📞 15 INBOUND AGENTS - Front desk receptionists  
🧠 AI ASSISTANT - Chat-based app control
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, sqlite3, os, requests, threading, time, webbrowser, re
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import base64

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - Set these in Railway dashboard as environment variables
# ═══════════════════════════════════════════════════════════════════════════════

# API Keys - Add these in Railway: Settings → Variables
VAPI_API_KEY = os.environ.get('VAPI_API_KEY', '')
VAPI_PHONE_ID = os.environ.get('VAPI_PHONE_ID', '')
TWILIO_SID = os.environ.get('TWILIO_SID', '')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', '')
TWILIO_PHONE = os.environ.get('TWILIO_PHONE', '')
TEST_PHONE = os.environ.get('TEST_PHONE', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8080/oauth/callback')
GOOGLE_CALENDAR_ID = os.environ.get('GOOGLE_CALENDAR_ID', 'primary')

COMPANY_NAME = os.environ.get('COMPANY_NAME', 'VOICE')
COMPANY_PHONE = os.environ.get('COMPANY_PHONE', '')

COST_PER_MINUTE_VAPI = 0.05
COST_PER_SMS = 0.0075
FB_DAILY_BUDGET = 50.00
MONTHLY_BUDGET_GOAL = 2000.00
DAILY_BUDGET_GOAL = 100.00
DB_PATH = os.environ.get('DB_PATH', os.path.expanduser("~/voice.db"))
PORT = int(os.environ.get('PORT', 8080))

# Session management
import hashlib
import secrets
import uuid
from http.cookies import SimpleCookie

active_cycles = {}
active_sessions = {}  # session_token -> user_id

# App Secret for session signing (generate once and store)
APP_SECRET = secrets.token_hex(32)

# ═══════════════════════════════════════════════════════════════════════════════
# NEPQ FRAMEWORK (OUTBOUND)
# ═══════════════════════════════════════════════════════════════════════════════

NEPQ_CORE = """JEREMY MINER NEPQ RULES:
1. OPENER: Pattern interrupt - sound confused "I'm not sure if you can help me..."
2. TONALITY: Curious, slow, pause often. NEVER salesy.
3. QUESTIONS: "What's going on?", "How long?", "What happens if you don't fix it?"
4. PHRASES: "I'm just curious...", "Does that make sense?", "Tell me more..."
5. NEVER: Sound scripted, be pushy, talk fast, pitch before pain."""

# ═══════════════════════════════════════════════════════════════════════════════
# INBOUND RECEPTIONIST FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════════════

RECEPTIONIST_CORE = """You are a warm, professional, and incredibly helpful front desk receptionist. You sound EXACTLY like a real human - friendly, caring, and naturally conversational.

CRITICAL VOICE RULES:
- Speak naturally with a warm, welcoming tone
- Use "..." to create natural pauses
- NEVER sound robotic or scripted
- Use filler words naturally: "absolutely", "of course", "sure thing", "no problem"
- Be empathetic and understanding
- Mirror the caller's energy - if they're stressed, be calming. If excited, match their enthusiasm.
- Smile while you talk - it comes through in your voice

GREETING:
"Thank you for calling {company_name}, this is {agent_name}, how can I help you today?"

CORE BEHAVIORS:
1. LISTEN FIRST - Let them fully explain why they're calling
2. ACKNOWLEDGE - "I completely understand" / "I can definitely help with that"
3. GATHER INFO - Get their name, phone, and what they need
4. BOOK OR TRANSFER - Either schedule an appointment or offer to help directly

APPOINTMENT BOOKING:
When they want to schedule:
- "I'd be happy to get you scheduled! Let me check what we have available..."
- "I have [DAY] at [TIME] or [DAY] at [TIME]... which works better for you?"
- "Perfect! And can I get your name and the best number to reach you?"
- "Great, you're all set for [DAY] at [TIME]. We'll send you a confirmation text. Is there anything else I can help with?"

COMMON SCENARIOS:
- Pricing questions: "Great question! The best thing would be to get you in for a free consultation so we can give you an accurate quote. Would you like me to schedule that?"
- Hours/Location: Provide info, then offer to book
- Complaints: "I'm so sorry to hear that. Let me get you to someone who can help right away..."
- General info: Answer helpfully, always offer to book an appointment

CLOSING:
- "Is there anything else I can help you with today?"
- "Thank you so much for calling {company_name}! Have a wonderful day!"

REMEMBER:
- You represent the company - be professional but warm
- Your goal is to help AND book appointments
- Never let them hang up without offering to schedule
- Always confirm details before ending the call"""

# ═══════════════════════════════════════════════════════════════════════════════
# 12 OUTBOUND AGENTS (SALES TEAM)
# ═══════════════════════════════════════════════════════════════════════════════

OUTBOUND_AGENTS = {
    "roofing": {"name": "Paige", "industry": "Roofing", "icon": "🏠", "color": "#ef4444", "bilingual": False,
        "first_message": "Hey... {name}?... ... this is Paige... I'm not even sure if you can help me with this or not...",
        "prompt": """You are Paige, an elite roofing appointment setter. Sound EXACTLY like a real human - warm, natural, unsure at first.

VOICE: Speak SLOWLY with natural pauses "...". Use fillers: "yeah", "so", "um", "gotcha". Never interrupt.

OPENER: "Hey... {name}?... this is Paige... I'm not even sure if you can help me with this or not..."
Then: "Yeah so... your info came across my desk about your roof... did you still need help or did someone take care of it?"

DISCOVERY (one question, then LISTEN):
- "What's going on with it exactly?"
- "How long has that been happening?"
- "Has anyone looked at it yet?"

CLOSE - ALWAYS DO THIS:
"I've got two times open... tomorrow at 10 or 2... which works better?"
Get: Day + Time + Address. NEVER end without booking."""},

    "solar": {"name": "Luna", "industry": "Solar", "icon": "☀️", "color": "#f59e0b", "bilingual": False,
        "first_message": "Hey {name}... this is Luna... I'm not sure if this is even something you'd be open to...",
        "prompt": f"You are Luna, elite solar setter.\n{NEPQ_CORE}\nOPENER: 'Hey {{name}}... this is Luna... not sure if this is something you'd be open to...' Ask about electric bill, why interested. ALWAYS CLOSE WITH 2 TIME OPTIONS."},

    "insurance": {"name": "Maya", "industry": "Insurance", "icon": "🛡️", "color": "#3b82f6", "bilingual": False,
        "first_message": "Hey {name}... this is Maya... I'm actually not sure if I can even help you...",
        "prompt": f"You are Maya, elite insurance specialist.\n{NEPQ_CORE}\nAsk about current coverage, concerns. ALWAYS CLOSE WITH 2 TIME OPTIONS."},

    "auto": {"name": "Marco", "industry": "Auto Sales", "icon": "🚗", "color": "#10b981", "bilingual": False,
        "first_message": "Hey {name}... this is Marco... I'm not even sure if we have what you're looking for...",
        "prompt": f"You are Marco, elite auto sales specialist.\n{NEPQ_CORE}\nAsk about current car, what they want. ALWAYS CLOSE WITH 2 TIME OPTIONS."},

    "realtor": {"name": "Sofia", "industry": "Real Estate", "icon": "🏡", "color": "#8b5cf6", "bilingual": False,
        "first_message": "Hey {name}... this is Sofia... I'm not sure if I can help you or not...",
        "prompt": f"You are Sofia, elite real estate setter.\n{NEPQ_CORE}\nAsk about areas, budget, timeline. ALWAYS CLOSE WITH 2 TIME OPTIONS."},

    "dental": {"name": "Carmen", "industry": "Dental", "icon": "🦷", "color": "#06b6d4", "bilingual": True,
        "first_message": "Hey {name}... this is Carmen from the dental clinic... do you have a quick second?",
        "prompt": f"You are Carmen, warm dental receptionist.\n{NEPQ_CORE}\nAsk about dental needs. ALWAYS CLOSE WITH 2 TIME OPTIONS.",
        "first_message_es": "Hola, habla Carmen de la clínica dental... ¿hablo con {name}?",
        "prompt_es": "Eres Carmen, recepcionista dental cálida. Hablas español natural. SIEMPRE CIERRA CON 2 OPCIONES DE HORARIO."},

    "hvac": {"name": "Jake", "industry": "HVAC", "icon": "❄️", "color": "#0ea5e9", "bilingual": False,
        "first_message": "Hey {name}... this is Jake... I'm not sure if you still need help with this...",
        "prompt": f"You are Jake, HVAC specialist.\n{NEPQ_CORE}\nAsk what the AC/heater is doing. ALWAYS CLOSE WITH 2 TIME OPTIONS."},

    "legal": {"name": "Victoria", "industry": "Legal Services", "icon": "⚖️", "color": "#6366f1", "bilingual": False,
        "first_message": "Hi {name}... this is Victoria... I'm reaching out about your inquiry...",
        "prompt": f"You are Victoria, professional legal intake.\n{NEPQ_CORE}\nAsk what happened, timeline. ALWAYS CLOSE WITH 2 TIME OPTIONS."},

    "fitness": {"name": "Alex", "industry": "Gym/Fitness", "icon": "💪", "color": "#ec4899", "bilingual": False,
        "first_message": "Hey {name}! This is Alex... you were checking out our gym right?",
        "prompt": f"You are Alex, energetic fitness consultant.\n{NEPQ_CORE}\nAsk about fitness goals. ALWAYS CLOSE WITH 2 TIME OPTIONS."},

    "cleaning": {"name": "Rosa", "industry": "Cleaning", "icon": "🧹", "color": "#84cc16", "bilingual": True,
        "first_message": "Hey {name}, this is Rosa from the cleaning service... do you have a quick moment?",
        "prompt": f"You are Rosa, friendly cleaning coordinator.\n{NEPQ_CORE}\nAsk about cleaning needs, frequency. ALWAYS CLOSE WITH 2 TIME OPTIONS.",
        "first_message_es": "Hola {name}, soy Rosa de servicios de limpieza... ¿tiene un momentito?",
        "prompt_es": "Eres Rosa, coordinadora de limpieza amable. SIEMPRE CIERRA CON 2 OPCIONES DE HORARIO."},

    "landscaping": {"name": "Miguel", "industry": "Landscaping", "icon": "🌳", "color": "#22c55e", "bilingual": False,
        "first_message": "Hey {name}, this is Miguel... you were asking about landscaping right?",
        "prompt": f"You are Miguel, landscaping specialist.\n{NEPQ_CORE}\nAsk what they want done. ALWAYS CLOSE WITH 2 TIME OPTIONS."},

    "tax": {"name": "Diana", "industry": "Tax Services", "icon": "📊", "color": "#f97316", "bilingual": False,
        "first_message": "Hi {name}... this is Diana... calling about your tax inquiry...",
        "prompt": f"You are Diana, professional tax consultant.\n{NEPQ_CORE}\nAsk about tax situation. ALWAYS CLOSE WITH 2 TIME OPTIONS."}
}

# ═══════════════════════════════════════════════════════════════════════════════
# 15 INBOUND AGENTS (FRONT DESK / RECEPTIONISTS)
# ═══════════════════════════════════════════════════════════════════════════════

INBOUND_AGENTS = {
    "inbound_medical": {
        "name": "Sarah", "industry": "Medical Office", "icon": "🏥", "color": "#ef4444", "bilingual": True,
        "company": "Wellness Medical Center",
        "first_message": "Thank you for calling Wellness Medical Center, this is Sarah, how can I help you today?",
        "prompt": """You are Sarah, the friendly and professional receptionist at Wellness Medical Center.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Wellness Medical Center").replace("{agent_name}", "Sarah") + """

SPECIFIC TO MEDICAL:
- For emergencies: "If this is an emergency, please hang up and call 911"
- For appointments: Offer same-day if urgent, otherwise next available
- For prescription refills: "I can send that request to your provider right away"
- For test results: "Let me transfer you to our nursing staff"
- Hours: Monday-Friday 8am-5pm, Saturday 9am-1pm
- Ask for: Name, DOB, reason for visit, insurance info""",
        "first_message_es": "Gracias por llamar a Wellness Medical Center, habla Sarah, ¿en qué puedo ayudarle hoy?",
        "prompt_es": "Eres Sarah, recepcionista amable del centro médico. Habla español naturalmente. Ayuda con citas y preguntas médicas."
    },

    "inbound_dental": {
        "name": "Emily", "industry": "Dental Office", "icon": "🦷", "color": "#06b6d4", "bilingual": True,
        "company": "Bright Smile Dental",
        "first_message": "Thank you for calling Bright Smile Dental, this is Emily, how may I help you?",
        "prompt": """You are Emily, the warm and caring receptionist at Bright Smile Dental.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Bright Smile Dental").replace("{agent_name}", "Emily") + """

SPECIFIC TO DENTAL:
- Emergency dental: "Are you in pain right now? Let me see if we can get you in today"
- New patients: "We'd love to have you! First visits include exam, x-rays, and cleaning"
- Insurance: "We accept most major insurance. What provider do you have?"
- Cosmetic: "We offer free consultations for cosmetic procedures"
- Hours: Monday-Thursday 8am-5pm, Friday 8am-2pm
- Appointment types: Cleaning, exam, filling, extraction, whitening, consultation""",
        "first_message_es": "Gracias por llamar a Bright Smile Dental, habla Emily, ¿cómo puedo ayudarle?",
        "prompt_es": "Eres Emily, recepcionista cálida de la clínica dental. Habla español naturalmente."
    },

    "inbound_legal": {
        "name": "Grace", "industry": "Law Firm", "icon": "⚖️", "color": "#6366f1", "bilingual": False,
        "company": "Johnson & Associates Law",
        "first_message": "Thank you for calling Johnson & Associates Law, this is Grace, how may I direct your call?",
        "prompt": """You are Grace, the professional and discreet receptionist at Johnson & Associates Law.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Johnson & Associates Law").replace("{agent_name}", "Grace") + """

SPECIFIC TO LEGAL:
- Be professional and maintain confidentiality
- For new cases: "I'd be happy to schedule a free consultation with one of our attorneys"
- Practice areas: Personal injury, family law, criminal defense, estate planning
- Urgent matters: "Let me see if an attorney is available to speak with you"
- Hours: Monday-Friday 9am-6pm
- Always get: Name, phone, brief description of legal matter"""
    },

    "inbound_realestate": {
        "name": "Jennifer", "industry": "Real Estate Agency", "icon": "🏡", "color": "#8b5cf6", "bilingual": False,
        "company": "Premier Realty Group",
        "first_message": "Thank you for calling Premier Realty Group, this is Jennifer, how can I help you today?",
        "prompt": """You are Jennifer, the enthusiastic and knowledgeable receptionist at Premier Realty Group.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Premier Realty Group").replace("{agent_name}", "Jennifer") + """

SPECIFIC TO REAL ESTATE:
- Buyers: "Are you looking to buy? I can connect you with one of our buyer specialists!"
- Sellers: "Thinking of selling? We offer free home valuations"
- Rentals: "We have a great rental department. What area are you looking in?"
- Open houses: Provide current listings and times
- Get: Name, phone, buying/selling/renting, area of interest, budget range"""
    },

    "inbound_automotive": {
        "name": "Mike", "industry": "Auto Dealership", "icon": "🚗", "color": "#10b981", "bilingual": False,
        "company": "City Auto Group",
        "first_message": "Thanks for calling City Auto Group, this is Mike, what can I do for you today?",
        "prompt": """You are Mike, the friendly and helpful receptionist at City Auto Group.

""" + RECEPTIONIST_CORE.replace("{company_name}", "City Auto Group").replace("{agent_name}", "Mike") + """

SPECIFIC TO AUTO:
- Sales: "Looking for a new ride? I can connect you with a sales specialist or schedule a test drive"
- Service: "Need service? I can get you scheduled - is it routine maintenance or something specific?"
- Parts: "I'll transfer you to our parts department"
- Hours: Sales 9am-8pm, Service 7am-6pm Monday-Saturday
- Get: Name, phone, new/used preference, trade-in, service needs"""
    },

    "inbound_salon": {
        "name": "Brittany", "industry": "Hair Salon/Spa", "icon": "💇", "color": "#ec4899", "bilingual": False,
        "company": "Luxe Salon & Spa",
        "first_message": "Thank you for calling Luxe Salon & Spa, this is Brittany, how can I pamper you today?",
        "prompt": """You are Brittany, the upbeat and friendly receptionist at Luxe Salon & Spa.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Luxe Salon & Spa").replace("{agent_name}", "Brittany") + """

SPECIFIC TO SALON/SPA:
- Services: Haircuts, color, highlights, blowouts, facials, massage, nails, waxing
- Stylist requests: "Do you have a preferred stylist, or would you like a recommendation?"
- New clients: "First time with us? We'd love to have you! Any particular service you're interested in?"
- Pricing: Give ranges, offer consultation for color services
- Hours: Tuesday-Saturday 9am-7pm
- Get: Name, phone, service type, stylist preference, any special requests"""
    },

    "inbound_restaurant": {
        "name": "Tony", "industry": "Restaurant", "icon": "🍽️", "color": "#f59e0b", "bilingual": True,
        "company": "Bella Italia Ristorante",
        "first_message": "Bella Italia, this is Tony, how can I help you?",
        "prompt": """You are Tony, the warm and welcoming host at Bella Italia Ristorante.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Bella Italia").replace("{agent_name}", "Tony") + """

SPECIFIC TO RESTAURANT:
- Reservations: "I'd be happy to book a table! What day and how many guests?"
- Wait times: "We're currently about [X] minutes for walk-ins"
- Private events: "We have a beautiful private dining room! Let me tell you about our event packages"
- Menu questions: Answer enthusiastically, recommend popular dishes
- Hours: Lunch 11am-3pm, Dinner 5pm-10pm, Closed Mondays
- Get: Name, phone, party size, date/time, special occasions""",
        "first_message_es": "Bella Italia, habla Tony, ¿en qué puedo ayudarle?",
        "prompt_es": "Eres Tony, el anfitrión cálido del restaurante italiano. Habla español naturalmente."
    },

    "inbound_hotel": {
        "name": "Amanda", "industry": "Hotel", "icon": "🏨", "color": "#0ea5e9", "bilingual": True,
        "company": "Grand Plaza Hotel",
        "first_message": "Thank you for calling Grand Plaza Hotel, this is Amanda, how may I assist you?",
        "prompt": """You are Amanda, the professional and helpful front desk agent at Grand Plaza Hotel.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Grand Plaza Hotel").replace("{agent_name}", "Amanda") + """

SPECIFIC TO HOTEL:
- Reservations: "I'd be happy to check availability! What dates are you looking at?"
- Room types: Standard, Deluxe, Suite, Presidential
- Amenities: Pool, fitness center, restaurant, room service, free WiFi, parking
- Check-in/out: 3pm check-in, 11am checkout
- Current guests: "Of course! Let me transfer you to that room"
- Get: Name, dates, room preference, number of guests, special requests""",
        "first_message_es": "Gracias por llamar al Grand Plaza Hotel, habla Amanda, ¿cómo puedo ayudarle?",
        "prompt_es": "Eres Amanda, agente de recepción profesional del hotel. Habla español naturalmente."
    },

    "inbound_gym": {
        "name": "Chris", "industry": "Fitness Center", "icon": "💪", "color": "#84cc16", "bilingual": False,
        "company": "PowerFit Gym",
        "first_message": "PowerFit Gym, this is Chris, ready to help you crush your goals!",
        "prompt": """You are Chris, the energetic and motivating receptionist at PowerFit Gym.

""" + RECEPTIONIST_CORE.replace("{company_name}", "PowerFit Gym").replace("{agent_name}", "Chris") + """

SPECIFIC TO GYM:
- Membership inquiries: "We have several membership options! Want to come in for a free tour and trial?"
- Personal training: "Our trainers are amazing! I can schedule a free fitness assessment"
- Class schedules: Yoga, spin, HIIT, CrossFit, boxing
- Hours: 5am-11pm weekdays, 7am-8pm weekends
- Get: Name, phone, fitness goals, any injuries/limitations, tour time"""
    },

    "inbound_insurance": {
        "name": "Patricia", "industry": "Insurance Agency", "icon": "🛡️", "color": "#3b82f6", "bilingual": False,
        "company": "Shield Insurance Group",
        "first_message": "Thank you for calling Shield Insurance Group, this is Patricia, how can I help protect you today?",
        "prompt": """You are Patricia, the knowledgeable and caring receptionist at Shield Insurance Group.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Shield Insurance Group").replace("{agent_name}", "Patricia") + """

SPECIFIC TO INSURANCE:
- Types: Auto, home, life, health, business, umbrella
- Quotes: "I can have an agent prepare a free quote! What type of coverage are you looking for?"
- Claims: "I'm sorry to hear that. Let me transfer you to our claims department right away"
- Policy questions: "Let me pull up your policy... can I get your policy number?"
- Hours: Monday-Friday 8am-6pm, Saturday 9am-1pm
- Get: Name, phone, type of insurance, current provider"""
    },

    "inbound_vet": {
        "name": "Kelly", "industry": "Veterinary Clinic", "icon": "🐾", "color": "#a855f7", "bilingual": False,
        "company": "Happy Paws Veterinary",
        "first_message": "Thank you for calling Happy Paws Veterinary, this is Kelly, how can I help you and your fur baby today?",
        "prompt": """You are Kelly, the warm and animal-loving receptionist at Happy Paws Veterinary.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Happy Paws Veterinary").replace("{agent_name}", "Kelly") + """

SPECIFIC TO VET:
- Emergencies: "Is your pet having an emergency? We have emergency hours until 10pm, or I can direct you to the 24-hour hospital"
- Appointments: Wellness exams, vaccinations, sick visits, dental, surgery
- New patients: "We'd love to meet your fur baby! First visits include a full wellness exam"
- Prescriptions/food: "I can have that ready for pickup!"
- Hours: Monday-Friday 8am-6pm, Saturday 8am-2pm, Emergency until 10pm
- Get: Pet name, species, owner name, phone, reason for visit"""
    },

    "inbound_school": {
        "name": "Linda", "industry": "School/Education", "icon": "🎓", "color": "#f97316", "bilingual": True,
        "company": "Bright Futures Academy",
        "first_message": "Thank you for calling Bright Futures Academy, this is Linda, how may I help you?",
        "prompt": """You are Linda, the helpful and professional receptionist at Bright Futures Academy.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Bright Futures Academy").replace("{agent_name}", "Linda") + """

SPECIFIC TO SCHOOL:
- Enrollment: "We'd love to have your child join us! Would you like to schedule a tour?"
- Current parents: "Let me look that up for you... what's your child's name?"
- Attendance: "I'll make a note of that absence"
- After-school: "Our after-school program runs until 6pm"
- Hours: Office 7:30am-4pm, School hours 8am-3pm
- Get: Child name, parent name, phone, grade level, reason for call""",
        "first_message_es": "Gracias por llamar a Bright Futures Academy, habla Linda, ¿cómo puedo ayudarle?",
        "prompt_es": "Eres Linda, recepcionista profesional de la escuela. Habla español naturalmente."
    },

    "inbound_contractor": {
        "name": "Dave", "industry": "General Contractor", "icon": "🔨", "color": "#78716c", "bilingual": False,
        "company": "BuildRight Construction",
        "first_message": "BuildRight Construction, this is Dave, how can I help you with your project?",
        "prompt": """You are Dave, the knowledgeable and friendly receptionist at BuildRight Construction.

""" + RECEPTIONIST_CORE.replace("{company_name}", "BuildRight Construction").replace("{agent_name}", "Dave") + """

SPECIFIC TO CONTRACTOR:
- Services: Remodels, additions, kitchens, bathrooms, decks, roofing, siding
- Estimates: "We offer free estimates! I can schedule someone to come take a look"
- Timeline questions: "Every project is different, but we can discuss that at the estimate"
- Licensed/Insured: "Yes, we're fully licensed and insured"
- Hours: Monday-Friday 7am-5pm, Saturday by appointment
- Get: Name, phone, address, type of project, timeline"""
    },

    "inbound_accounting": {
        "name": "Rachel", "industry": "Accounting Firm", "icon": "📊", "color": "#059669", "bilingual": False,
        "company": "Precision Accounting",
        "first_message": "Thank you for calling Precision Accounting, this is Rachel, how may I assist you?",
        "prompt": """You are Rachel, the professional and detail-oriented receptionist at Precision Accounting.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Precision Accounting").replace("{agent_name}", "Rachel") + """

SPECIFIC TO ACCOUNTING:
- Services: Tax prep, bookkeeping, payroll, business consulting, audit support
- Tax season: "We're booking tax appointments now! Individual or business return?"
- New clients: "We offer a free initial consultation to discuss your needs"
- Document drop-off: "You can drop documents off anytime during business hours"
- Hours: Monday-Friday 9am-5pm (extended hours Jan-April)
- Get: Name, phone, individual or business, type of service needed"""
    },

    "inbound_therapy": {
        "name": "Michelle", "industry": "Therapy/Counseling", "icon": "🧠", "color": "#7c3aed", "bilingual": False,
        "company": "Serenity Counseling Center",
        "first_message": "Thank you for calling Serenity Counseling Center, this is Michelle, how can I help you today?",
        "prompt": """You are Michelle, the compassionate and calming receptionist at Serenity Counseling Center.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Serenity Counseling Center").replace("{agent_name}", "Michelle") + """

SPECIFIC TO THERAPY:
- Be extra warm and non-judgmental - callers may be nervous
- "Taking this step to call is really brave. I'm here to help."
- Services: Individual therapy, couples counseling, family therapy, group sessions
- New patients: "I can schedule an initial consultation to find the right therapist for you"
- Insurance: "We accept most insurance. I can verify your benefits"
- Crisis: "If you're in crisis, I want to make sure you're safe. Are you having thoughts of harming yourself?"
- Hours: Monday-Friday 8am-8pm, Saturday 9am-3pm
- Get: Name, phone, type of therapy interested in, insurance"""
    }
}

# Combine all agents for easy lookup
AGENT_TEMPLATES = {**OUTBOUND_AGENTS, **INBOUND_AGENTS}
# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Enhanced leads table with full tracking
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY, 
        phone TEXT UNIQUE, 
        first_name TEXT, 
        last_name TEXT,
        email TEXT, 
        address TEXT, 
        city TEXT, 
        state TEXT, 
        zip TEXT,
        status TEXT DEFAULT 'new', 
        source TEXT DEFAULT 'manual',
        agent_type TEXT DEFAULT 'roofing', 
        pipeline_stage TEXT DEFAULT 'new_lead',
        
        -- Call tracking
        total_calls INTEGER DEFAULT 0,
        total_answered INTEGER DEFAULT 0,
        total_voicemail INTEGER DEFAULT 0,
        total_hungup INTEGER DEFAULT 0,
        total_no_answer INTEGER DEFAULT 0,
        last_call_date TIMESTAMP,
        last_call_outcome TEXT,
        
        -- Cycle tracking (3 calls per day, double-tap pattern)
        cycle_day INTEGER DEFAULT 1,
        cycle_attempt INTEGER DEFAULT 0,
        cycle_status TEXT DEFAULT 'pending',
        cycle_completed INTEGER DEFAULT 0,
        max_cycle_days INTEGER DEFAULT 7,
        
        -- Appointment tracking
        appointment_set INTEGER DEFAULT 0,
        appointment_id INTEGER,
        appointment_date TEXT,
        
        -- Ad/Source tracking
        ad_campaign TEXT, 
        ad_set TEXT, 
        ad_id TEXT, 
        ad_spend REAL DEFAULT 0,
        utm_source TEXT,
        utm_medium TEXT,
        utm_campaign TEXT,
        
        -- Outcome
        final_disposition TEXT,
        sale_amount REAL DEFAULT 0,
        
        notes TEXT, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY, lead_id INTEGER, phone TEXT, first_name TEXT, last_name TEXT,
        email TEXT, address TEXT, city TEXT, state TEXT, zip TEXT,
        appointment_date TEXT, appointment_time TEXT, appointment_datetime TIMESTAMP,
        duration_minutes INTEGER DEFAULT 60, agent_type TEXT, assigned_tech TEXT, tech_phone TEXT,
        status TEXT DEFAULT 'scheduled', source TEXT DEFAULT 'ai_call',
        pipeline_stage TEXT DEFAULT 'appointment_set',
        confirmation_sent INTEGER DEFAULT 0, confirmation_sent_at TIMESTAMP,
        reminder_sent INTEGER DEFAULT 0, reminder_sent_at TIMESTAMP,
        google_event_id TEXT, google_calendar_link TEXT,
        disposition TEXT, disposition_notes TEXT, sale_amount REAL DEFAULT 0,
        call_id TEXT, call_duration INTEGER DEFAULT 0, call_recording_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, completed_at TIMESTAMP
    )''')
    
    # Enhanced call log with outcomes
    c.execute('''CREATE TABLE IF NOT EXISTS call_log (
        id INTEGER PRIMARY KEY, 
        lead_id INTEGER,
        phone TEXT, 
        status TEXT, 
        outcome TEXT DEFAULT 'pending',
        duration INTEGER DEFAULT 0,
        call_id TEXT, 
        agent_type TEXT, 
        is_test_call INTEGER DEFAULT 0, 
        is_inbound INTEGER DEFAULT 0,
        is_live INTEGER DEFAULT 0, 
        test_phone TEXT,
        
        -- Call outcome details
        answered INTEGER DEFAULT 0,
        voicemail INTEGER DEFAULT 0,
        hungup INTEGER DEFAULT 0,
        no_answer INTEGER DEFAULT 0,
        busy INTEGER DEFAULT 0,
        failed INTEGER DEFAULT 0,
        appointment_booked INTEGER DEFAULT 0,
        
        -- Quality metrics
        ai_score INTEGER DEFAULT 0, 
        human_rating INTEGER DEFAULT 0,
        latency INTEGER DEFAULT 0, 
        call_quality INTEGER DEFAULT 0,
        
        -- Cycle info
        cycle_day INTEGER DEFAULT 1,
        cycle_attempt INTEGER DEFAULT 1,
        
        transcript TEXT, 
        recording_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sms_log (
        id INTEGER PRIMARY KEY, phone TEXT, lead_id INTEGER, message TEXT, direction TEXT DEFAULT 'outbound',
        message_type TEXT DEFAULT 'general', status TEXT DEFAULT 'pending', twilio_sid TEXT,
        error_message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS cost_log (
        id INTEGER PRIMARY KEY, cost_type TEXT, amount REAL,
        description TEXT, agent_type TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS assistant_chat (
        id INTEGER PRIMARY KEY, role TEXT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Facebook/Instagram Ads tracking
    c.execute('''CREATE TABLE IF NOT EXISTS ad_campaigns (
        id INTEGER PRIMARY KEY,
        platform TEXT DEFAULT 'facebook',
        campaign_id TEXT UNIQUE,
        campaign_name TEXT,
        status TEXT DEFAULT 'active',
        daily_budget REAL DEFAULT 0,
        total_spend REAL DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        leads INTEGER DEFAULT 0,
        appointments INTEGER DEFAULT 0,
        sales INTEGER DEFAULT 0,
        revenue REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS ad_daily_stats (
        id INTEGER PRIMARY KEY,
        campaign_id TEXT,
        date TEXT,
        spend REAL DEFAULT 0,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        leads INTEGER DEFAULT 0,
        appointments INTEGER DEFAULT 0,
        sales INTEGER DEFAULT 0,
        revenue REAL DEFAULT 0,
        cpl REAL DEFAULT 0,
        cpa REAL DEFAULT 0,
        roas REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Pipeline stages configuration
    c.execute('''CREATE TABLE IF NOT EXISTS pipeline_stages (
        id INTEGER PRIMARY KEY,
        stage_key TEXT UNIQUE,
        stage_name TEXT,
        stage_order INTEGER,
        stage_color TEXT DEFAULT '#6B7280',
        stage_icon TEXT DEFAULT '📋',
        is_active INTEGER DEFAULT 1
    )''')
    
    # App settings including test phone
    c.execute('''CREATE TABLE IF NOT EXISTS app_settings (
        id INTEGER PRIMARY KEY,
        setting_key TEXT UNIQUE,
        setting_value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # CSV Import history
    c.execute('''CREATE TABLE IF NOT EXISTS import_history (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        total_rows INTEGER DEFAULT 0,
        imported INTEGER DEFAULT 0,
        skipped INTEGER DEFAULT 0,
        errors INTEGER DEFAULT 0,
        source TEXT DEFAULT 'csv',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Insert default pipeline stages with icons
    default_stages = [
        ('new_lead', 'New Lead', 1, '#6B7280', '🆕'),
        ('contacted', 'Contacted', 2, '#3B82F6', '📞'),
        ('no_answer', 'No Answer', 3, '#F59E0B', '📵'),
        ('callback', 'Callback Scheduled', 4, '#8B5CF6', '🔄'),
        ('qualified', 'Qualified', 5, '#06B6D4', '✅'),
        ('appointment_set', 'Appointment Set', 6, '#00D1FF', '📅'),
        ('appointment_completed', 'Appt Completed', 7, '#10B981', '🎯'),
        ('proposal_sent', 'Proposal Sent', 8, '#EC4899', '📄'),
        ('negotiation', 'Negotiation', 9, '#F97316', '🤝'),
        ('sold', 'Sold', 10, '#22C55E', '💰'),
        ('lost', 'Lost/Dead', 11, '#EF4444', '❌'),
    ]
    for stage in default_stages:
        c.execute('INSERT OR IGNORE INTO pipeline_stages (stage_key, stage_name, stage_order, stage_color, stage_icon) VALUES (?, ?, ?, ?, ?)', stage)
    
    # Insert default settings
    c.execute('INSERT OR IGNORE INTO app_settings (setting_key, setting_value) VALUES (?, ?)', ('test_phone', TEST_PHONE))
    c.execute('INSERT OR IGNORE INTO app_settings (setting_key, setting_value) VALUES (?, ?)', ('mode', 'testing'))
    c.execute('INSERT OR IGNORE INTO app_settings (setting_key, setting_value) VALUES (?, ?)', ('calls_per_day', '3'))
    c.execute('INSERT OR IGNORE INTO app_settings (setting_key, setting_value) VALUES (?, ?)', ('max_cycle_days', '7'))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MULTI-TENANT & AUTH TABLES
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Enhanced Users table with auth
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        name TEXT,
        company TEXT,
        phone TEXT,
        role TEXT DEFAULT 'user',
        is_active INTEGER DEFAULT 1,
        email_verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        login_count INTEGER DEFAULT 0
    )''')
    
    # Sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        session_token TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # User Integrations (each user has their own API keys)
    c.execute('''CREATE TABLE IF NOT EXISTS user_integrations (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        integration_type TEXT NOT NULL,
        integration_name TEXT,
        api_key TEXT,
        api_secret TEXT,
        access_token TEXT,
        refresh_token TEXT,
        account_id TEXT,
        webhook_url TEXT,
        is_active INTEGER DEFAULT 1,
        is_connected INTEGER DEFAULT 0,
        last_sync TIMESTAMP,
        config_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, integration_type)
    )''')
    
    # Zapier Webhooks
    c.execute('''CREATE TABLE IF NOT EXISTS zapier_webhooks (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        webhook_name TEXT,
        webhook_url TEXT NOT NULL,
        trigger_event TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        last_triggered TIMESTAMP,
        trigger_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Facebook Ad Accounts
    c.execute('''CREATE TABLE IF NOT EXISTS fb_ad_accounts (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        account_id TEXT NOT NULL,
        account_name TEXT,
        access_token TEXT,
        is_active INTEGER DEFAULT 1,
        last_sync TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # API Keys for external access
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        key_name TEXT,
        api_key TEXT UNIQUE NOT NULL,
        permissions TEXT DEFAULT 'read',
        is_active INTEGER DEFAULT 1,
        last_used TIMESTAMP,
        use_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
    admin_salt = secrets.token_hex(16)
    admin_hash = hashlib.sha256(('admin123' + admin_salt).encode()).hexdigest()
    c.execute('''INSERT OR IGNORE INTO users (email, password_hash, salt, name, role, is_active, email_verified) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', 
              ('admin@voice.ai', admin_hash, admin_salt, 'Admin', 'admin', 1, 1))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def hash_password(password, salt=None):
    """Hash password with salt"""
    if not salt:
        salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt

def verify_password(password, password_hash, salt):
    """Verify password against hash"""
    return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash

def create_user(email, password, name="", company="", phone=""):
    """Create a new user account"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if email exists
    c.execute('SELECT id FROM users WHERE email = ?', (email.lower(),))
    if c.fetchone():
        conn.close()
        return {"error": "Email already exists"}
    
    password_hash, salt = hash_password(password)
    
    try:
        c.execute('''INSERT INTO users (email, password_hash, salt, name, company, phone) 
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (email.lower(), password_hash, salt, name, company, phone))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"success": True, "user_id": user_id}
    except Exception as e:
        conn.close()
        return {"error": str(e)}

def authenticate_user(email, password):
    """Authenticate user and create session"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM users WHERE email = ? AND is_active = 1', (email.lower(),))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return {"error": "Invalid email or password"}
    
    if not verify_password(password, user['password_hash'], user['salt']):
        conn.close()
        return {"error": "Invalid email or password"}
    
    # Create session
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=7)
    
    c.execute('''INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)''',
              (user['id'], session_token, expires_at))
    
    # Update last login
    c.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1 WHERE id = ?',
              (user['id'],))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "session_token": session_token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "company": user['company'],
            "role": user['role']
        }
    }

def validate_session(session_token):
    """Validate session token and return user"""
    if not session_token:
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT u.*, s.expires_at FROM sessions s 
                 JOIN users u ON s.user_id = u.id 
                 WHERE s.session_token = ? AND u.is_active = 1''', (session_token,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return None
    
    # Check if expired
    if result['expires_at']:
        expires = datetime.strptime(result['expires_at'], '%Y-%m-%d %H:%M:%S')
        if expires < datetime.now():
            return None
    
    return dict(result)

def logout_user(session_token):
    """Delete session"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
    conn.commit()
    conn.close()
    return {"success": True}

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT id, email, name, company, phone, role, created_at FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATIONS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

INTEGRATION_TYPES = {
    'vapi': {'name': 'VAPI', 'icon': '🤖', 'description': 'AI Voice Agents', 'fields': ['api_key', 'phone_id']},
    'twilio': {'name': 'Twilio', 'icon': '📱', 'description': 'SMS & Voice', 'fields': ['account_sid', 'auth_token', 'phone_number']},
    'google_calendar': {'name': 'Google Calendar', 'icon': '📅', 'description': 'Calendar Sync', 'fields': ['client_id', 'client_secret'], 'oauth': True},
    'outlook': {'name': 'Microsoft Outlook', 'icon': '📧', 'description': 'Calendar & Email', 'fields': ['client_id', 'client_secret'], 'oauth': True},
    'zapier': {'name': 'Zapier', 'icon': '⚡', 'description': 'Workflow Automation', 'fields': ['webhook_url']},
    'facebook_ads': {'name': 'Facebook Ads', 'icon': '📘', 'description': 'Ad Account & Leads', 'fields': ['access_token', 'account_id'], 'oauth': True},
    'instagram': {'name': 'Instagram', 'icon': '📸', 'description': 'IG Lead Forms', 'fields': ['access_token'], 'oauth': True},
    'openai': {'name': 'OpenAI', 'icon': '🧠', 'description': 'AI Assistant', 'fields': ['api_key']},
    'stripe': {'name': 'Stripe', 'icon': '💳', 'description': 'Payments', 'fields': ['api_key', 'webhook_secret']},
}

def get_user_integrations(user_id):
    """Get all integrations for a user"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM user_integrations WHERE user_id = ?', (user_id,))
    integrations = [dict(row) for row in c.fetchall()]
    conn.close()
    
    # Add integration metadata
    for i in integrations:
        meta = INTEGRATION_TYPES.get(i['integration_type'], {})
        i['icon'] = meta.get('icon', '🔌')
        i['display_name'] = meta.get('name', i['integration_type'])
        i['description'] = meta.get('description', '')
    
    return integrations

def get_integration(user_id, integration_type):
    """Get specific integration for user"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM user_integrations WHERE user_id = ? AND integration_type = ?', 
              (user_id, integration_type))
    result = c.fetchone()
    conn.close()
    return dict(result) if result else None

def save_integration(user_id, integration_type, data):
    """Save or update integration"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if exists
    c.execute('SELECT id FROM user_integrations WHERE user_id = ? AND integration_type = ?',
              (user_id, integration_type))
    existing = c.fetchone()
    
    config_json = json.dumps(data.get('config', {})) if data.get('config') else None
    
    if existing:
        c.execute('''UPDATE user_integrations SET 
                     api_key = ?, api_secret = ?, access_token = ?, refresh_token = ?,
                     account_id = ?, webhook_url = ?, is_active = ?, is_connected = ?,
                     config_json = ?, updated_at = CURRENT_TIMESTAMP
                     WHERE user_id = ? AND integration_type = ?''',
                  (data.get('api_key'), data.get('api_secret'), data.get('access_token'),
                   data.get('refresh_token'), data.get('account_id'), data.get('webhook_url'),
                   data.get('is_active', 1), data.get('is_connected', 0), config_json,
                   user_id, integration_type))
    else:
        c.execute('''INSERT INTO user_integrations 
                     (user_id, integration_type, integration_name, api_key, api_secret, 
                      access_token, refresh_token, account_id, webhook_url, is_active, config_json)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, integration_type, INTEGRATION_TYPES.get(integration_type, {}).get('name', integration_type),
                   data.get('api_key'), data.get('api_secret'), data.get('access_token'),
                   data.get('refresh_token'), data.get('account_id'), data.get('webhook_url'),
                   data.get('is_active', 1), config_json))
    
    conn.commit()
    conn.close()
    return {"success": True}

def test_integration(user_id, integration_type):
    """Test if integration is working"""
    integration = get_integration(user_id, integration_type)
    if not integration:
        return {"success": False, "error": "Integration not found"}
    
    try:
        if integration_type == 'vapi':
            response = requests.get('https://api.vapi.ai/assistant',
                headers={'Authorization': f'Bearer {integration["api_key"]}'}, timeout=10)
            return {"success": response.status_code == 200, "status": response.status_code}
        
        elif integration_type == 'twilio':
            # Test Twilio credentials
            from base64 import b64encode
            auth = b64encode(f'{integration["api_key"]}:{integration["api_secret"]}'.encode()).decode()
            response = requests.get(f'https://api.twilio.com/2010-04-01/Accounts/{integration["api_key"]}.json',
                headers={'Authorization': f'Basic {auth}'}, timeout=10)
            return {"success": response.status_code == 200}
        
        elif integration_type == 'openai':
            response = requests.get('https://api.openai.com/v1/models',
                headers={'Authorization': f'Bearer {integration["api_key"]}'}, timeout=10)
            return {"success": response.status_code == 200}
        
        else:
            return {"success": True, "message": "Connection saved (test not available)"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_integration(user_id, integration_type):
    """Delete an integration"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM user_integrations WHERE user_id = ? AND integration_type = ?',
              (user_id, integration_type))
    conn.commit()
    conn.close()
    return {"success": True}

def get_user_api_keys(user_id, integration_type):
    """Get API keys for a specific integration (for making API calls)"""
    integration = get_integration(user_id, integration_type)
    if not integration:
        return None
    return {
        'api_key': integration.get('api_key'),
        'api_secret': integration.get('api_secret'),
        'access_token': integration.get('access_token'),
        'account_id': integration.get('account_id')
    }

# Zapier webhook functions
def get_zapier_webhooks(user_id):
    """Get all Zapier webhooks for user"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM zapier_webhooks WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    webhooks = [dict(row) for row in c.fetchall()]
    conn.close()
    return webhooks

def create_zapier_webhook(user_id, webhook_name, webhook_url, trigger_event):
    """Create a Zapier webhook"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO zapier_webhooks (user_id, webhook_name, webhook_url, trigger_event)
                 VALUES (?, ?, ?, ?)''', (user_id, webhook_name, webhook_url, trigger_event))
    webhook_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": webhook_id}

def trigger_zapier_webhook(user_id, event, data):
    """Trigger all webhooks for an event"""
    webhooks = get_zapier_webhooks(user_id)
    results = []
    for wh in webhooks:
        if wh['trigger_event'] == event and wh['is_active']:
            try:
                response = requests.post(wh['webhook_url'], json=data, timeout=10)
                results.append({"webhook": wh['webhook_name'], "success": response.status_code == 200})
                # Update trigger count
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('UPDATE zapier_webhooks SET last_triggered = CURRENT_TIMESTAMP, trigger_count = trigger_count + 1 WHERE id = ?', (wh['id'],))
                conn.commit()
                conn.close()
            except:
                results.append({"webhook": wh['webhook_name'], "success": False})
    return results

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def format_phone(phone):
    if not phone: return ""
    phone = ''.join(c for c in str(phone) if c.isdigit())
    if len(phone) == 10: return f"+1{phone}"
    if len(phone) == 11 and phone.startswith('1'): return f"+{phone}"
    return f"+{phone}" if phone else ""

def format_phone_display(phone):
    digits = ''.join(c for c in str(phone) if c.isdigit())
    if len(digits) == 11 and digits.startswith('1'): digits = digits[1:]
    if len(digits) == 10: return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone

def log_cost(cost_type, amount, description="", agent_type=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO cost_log (cost_type, amount, description, agent_type) VALUES (?, ?, ?, ?)', 
              (cost_type, amount, description, agent_type))
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════════════════════
# SMS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def send_sms(phone, message, message_type="general"):
    phone = format_phone(phone)
    try:
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
            auth=(TWILIO_SID, TWILIO_TOKEN),
            data={"From": TWILIO_PHONE, "To": phone, "Body": message},
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO sms_log (phone, message, message_type, status, twilio_sid) VALUES (?, ?, ?, ?, ?)',
                      (phone, message, message_type, data.get('status', 'sent'), data.get('sid', '')))
            conn.commit()
            conn.close()
            log_cost('sms', COST_PER_SMS, f'{message_type} SMS to {phone}')
            return {"success": True}
        return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_appointment_confirmation(appt_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM appointments WHERE id = ?', (appt_id,))
    row = c.fetchone()
    appt = dict(row) if row else None
    conn.close()
    
    if not appt: return {"error": "Not found"}
    
    msg = f"""✅ Appointment Confirmed!

Hi {appt.get('first_name', 'there')}! Your appointment is set:

📅 {appt.get('appointment_date', 'TBD')}
⏰ {appt.get('appointment_time', 'TBD')}
📍 {appt.get('address', '')}

Reply CONFIRM or call {COMPANY_PHONE} if you need to reschedule.

- {COMPANY_NAME}"""

    result = send_sms(appt['phone'], msg, 'confirmation')
    
    if result.get('success'):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE appointments SET confirmation_sent = 1, confirmation_sent_at = CURRENT_TIMESTAMP WHERE id = ?', (appt_id,))
        conn.commit()
        conn.close()
    
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# CALL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def make_call(phone, name="there", agent_type="roofing", is_test=False, use_spanish=False):
    phone = format_phone(phone)
    agent = AGENT_TEMPLATES.get(agent_type, OUTBOUND_AGENTS["roofing"])
    is_inbound = agent_type.startswith("inbound_")
    
    if use_spanish and agent.get("bilingual") and "first_message_es" in agent:
        first_msg = agent["first_message_es"].replace("{name}", name)
        prompt = agent["prompt_es"].replace("{name}", name)
    else:
        first_msg = agent["first_message"].replace("{name}", name)
        prompt = agent["prompt"].replace("{name}", name)
    
    if "company" in agent:
        first_msg = first_msg.replace("{company}", agent["company"])
        prompt = prompt.replace("{company}", agent["company"])
    
    print(f"📞 Calling {phone} with {agent.get('name', 'Agent')}...")
    
    call_data = {
        "phoneNumberId": VAPI_PHONE_ID,
        "customer": {"number": phone},
        "assistant": {
            "firstMessage": first_msg,
            "model": {"provider": "openai", "model": "gpt-4o", "messages": [{"role": "system", "content": prompt}], "temperature": 0.8},
            "voice": {"provider": "vapi", "voiceId": "Paige"},
            "silenceTimeoutSeconds": 45,
            "responseDelaySeconds": 1.2,
            "backgroundSound": "office"
        }
    }
    
    try:
        response = requests.post("https://api.vapi.ai/call/phone",
            headers={"Authorization": f"Bearer {VAPI_API_KEY}", "Content-Type": "application/json"},
            json=call_data, timeout=15)
        
        if response.status_code in [200, 201]:
            result = response.json()
            call_id = result.get('id', '')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO call_log (phone, status, call_id, agent_type, is_test_call, is_inbound) VALUES (?, ?, ?, ?, ?, ?)',
                      (phone, 'initiated', call_id, agent_type, 1 if is_test else 0, 1 if is_inbound else 0))
            conn.commit()
            conn.close()
            log_cost('vapi', COST_PER_MINUTE_VAPI, f'Call to {phone}', agent_type)
            print(f"   ✅ Call initiated: {call_id}")
            return {"success": True, "call_id": call_id}
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return {"error": response.text, "success": False}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"error": str(e), "success": False}

def test_agent(agent_type, test_phone=None, use_spanish=False):
    return make_call(test_phone or TEST_PHONE, "there", agent_type, is_test=True, use_spanish=use_spanish)

# ═══════════════════════════════════════════════════════════════════════════════
# APPOINTMENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def create_appointment(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    phone = format_phone(data.get('phone', ''))
    
    c.execute('SELECT id FROM leads WHERE phone = ?', (phone,))
    lead_row = c.fetchone()
    lead_id = lead_row[0] if lead_row else None
    
    if not lead_id:
        c.execute('INSERT INTO leads (phone, first_name, last_name, address, agent_type, status) VALUES (?, ?, ?, ?, ?, ?)',
                  (phone, data.get('first_name', ''), data.get('last_name', ''), data.get('address', ''), data.get('agent_type', 'roofing'), 'booked'))
        lead_id = c.lastrowid
    
    c.execute('''INSERT INTO appointments (lead_id, phone, first_name, last_name, email, address, city, state, zip,
        appointment_date, appointment_time, duration_minutes, agent_type, assigned_tech, source, call_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        lead_id, phone, data.get('first_name', ''), data.get('last_name', ''), data.get('email', ''),
        data.get('address', ''), data.get('city', ''), data.get('state', ''), data.get('zip', ''),
        data.get('date', ''), data.get('time', ''), data.get('duration', 60),
        data.get('agent_type', 'roofing'), data.get('tech', ''), data.get('source', 'manual'), data.get('call_id', '')))
    
    appt_id = c.lastrowid
    conn.commit()
    conn.close()
    
    if data.get('send_confirmation', True):
        send_appointment_confirmation(appt_id)
    
    return {"success": True, "appointment_id": appt_id}

def update_appointment(appt_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updates = []
    params = []
    
    for field in ['first_name', 'last_name', 'phone', 'email', 'address', 'appointment_date', 'appointment_time', 
                  'status', 'assigned_tech', 'disposition', 'disposition_notes', 'sale_amount', 'duration_minutes']:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])
    
    if updates:
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(appt_id)
        c.execute(f'UPDATE appointments SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()
    
    conn.close()
    return {"success": True}

def get_appointments(filters=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = 'SELECT * FROM appointments'
    params = []
    
    if filters:
        conditions = []
        if filters.get('date'): conditions.append('appointment_date = ?'); params.append(filters['date'])
        if filters.get('status'): conditions.append('status = ?'); params.append(filters['status'])
        if filters.get('agent_type'): conditions.append('agent_type = ?'); params.append(filters['agent_type'])
        if filters.get('month'):
            conditions.append("strftime('%Y-%m', appointment_date) = ?")
            params.append(filters['month'])
        if conditions: query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY appointment_date, appointment_time'
    c.execute(query, params)
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def get_appointment_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    stats = {}
    
    c.execute('SELECT COUNT(*) FROM appointments'); stats['total'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date = ?', (today,)); stats['today'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM appointments WHERE status = "scheduled"'); stats['scheduled'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM appointments WHERE disposition IS NULL AND status = "scheduled"'); stats['pending_disposition'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM appointments WHERE disposition = "sold"'); stats['sold'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM appointments WHERE disposition = "no-show"'); stats['no_show'] = c.fetchone()[0]
    c.execute('SELECT COALESCE(SUM(sale_amount), 0) FROM appointments WHERE disposition = "sold"'); stats['revenue'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM appointments WHERE google_event_id IS NOT NULL'); stats['on_calendar'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM appointments WHERE disposition IS NOT NULL'); disposed = c.fetchone()[0]
    stats['close_rate'] = round((stats['sold'] / disposed * 100) if disposed > 0 else 0, 1)
    
    conn.close()
    return stats

def get_upcoming_appointments(days=7):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    end = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    c.execute('SELECT * FROM appointments WHERE appointment_date >= ? AND appointment_date <= ? ORDER BY appointment_date, appointment_time', (today, end))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def update_disposition(appt_id, disposition, notes="", sale_amount=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''UPDATE appointments SET disposition = ?, disposition_notes = ?, sale_amount = ?,
                 status = 'completed', completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?''', 
              (disposition, notes, sale_amount, appt_id))
    conn.commit()
    conn.close()
    return {"success": True}

def get_calendar_data(year, month):
    """Get appointment counts by day for calendar view"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    month_str = f"{year}-{str(month).zfill(2)}"
    c.execute('''SELECT appointment_date, COUNT(*) as count, 
                 GROUP_CONCAT(first_name || ' ' || COALESCE(appointment_time, '')) as details
                 FROM appointments 
                 WHERE strftime('%Y-%m', appointment_date) = ?
                 GROUP BY appointment_date''', (month_str,))
    
    data = {}
    for row in c.fetchall():
        data[row[0]] = {"count": row[1], "details": row[2]}
    
    conn.close()
    return data
# ═══════════════════════════════════════════════════════════════════════════════
# AI ASSISTANT - "ARIA"
# ═══════════════════════════════════════════════════════════════════════════════

ARIA_SYSTEM_PROMPT = """You are Aria, the AI assistant for VOICE - a sales automation platform. You help users manage their leads, appointments, calls, and agents through natural conversation.

You have access to these ACTIONS you can perform by including them in your response:

APPOINTMENTS:
- [ACTION:CREATE_APPOINTMENT:{"first_name":"John","phone":"7025551234","date":"2025-01-15","time":"10:00","agent_type":"roofing"}] - Create new appointment
- [ACTION:UPDATE_APPOINTMENT:{"id":5,"date":"2025-01-16","time":"14:00"}] - Reschedule appointment
- [ACTION:GET_APPOINTMENTS:{"date":"2025-01-15"}] - List appointments for a date
- [ACTION:GET_TODAY_APPOINTMENTS] - Show today's appointments

CALLS:
- [ACTION:TEST_AGENT:{"agent_type":"roofing"}] - Test call an outbound agent
- [ACTION:TEST_INBOUND:{"agent_type":"inbound_medical"}] - Test call an inbound agent
- [ACTION:CALL_LEAD:{"phone":"7025551234","name":"John","agent_type":"roofing"}] - Call a lead

LEADS:
- [ACTION:ADD_LEAD:{"phone":"7025551234","name":"John"}] - Add new lead
- [ACTION:START_CYCLE:{"phone":"7025551234","name":"John","agent_type":"roofing"}] - Start lead cycle

SMS:
- [ACTION:SEND_SMS:{"phone":"7025551234","message":"Hello!"}] - Send text message
- [ACTION:SEND_CONFIRMATION:{"appointment_id":5}] - Send appointment confirmation

STATS:
- [ACTION:GET_STATS] - Get dashboard statistics
- [ACTION:GET_COSTS] - Get cost breakdown
- [ACTION:GET_AGENT_STATS:{"agent_type":"roofing"}] - Get specific agent stats

You are helpful, friendly, and efficient. When users ask you to do something, include the appropriate ACTION in your response. You can include multiple actions if needed.

AVAILABLE OUTBOUND AGENTS (Sales Team):
- roofing (Paige), solar (Luna), insurance (Maya), auto (Marco), realtor (Sofia), dental (Carmen), hvac (Jake), legal (Victoria), fitness (Alex), cleaning (Rosa), landscaping (Miguel), tax (Diana)

AVAILABLE INBOUND AGENTS (Front Desk):
- inbound_medical (Sarah), inbound_dental (Emily), inbound_legal (Grace), inbound_realestate (Jennifer), inbound_automotive (Mike), inbound_salon (Brittany), inbound_restaurant (Tony), inbound_hotel (Amanda), inbound_gym (Chris), inbound_insurance (Patricia), inbound_vet (Kelly), inbound_school (Linda), inbound_contractor (Dave), inbound_accounting (Rachel), inbound_therapy (Michelle)

Always be conversational and confirm what you're doing. If you need more information, ask for it.
"""

def process_aria_actions(response_text):
    """Extract and execute actions from Aria's response"""
    results = []
    action_pattern = r'\[ACTION:(\w+)(?::({[^}]+}))?\]'
    
    for match in re.finditer(action_pattern, response_text):
        action = match.group(1)
        params = json.loads(match.group(2)) if match.group(2) else {}
        
        try:
            if action == "CREATE_APPOINTMENT":
                result = create_appointment(params)
                results.append(f"✅ Created appointment for {params.get('first_name', 'customer')}")
            
            elif action == "UPDATE_APPOINTMENT":
                result = update_appointment(params.get('id'), params)
                results.append(f"✅ Updated appointment #{params.get('id')}")
            
            elif action == "GET_APPOINTMENTS":
                appts = get_appointments(params)
                results.append(f"📅 Found {len(appts)} appointments")
            
            elif action == "GET_TODAY_APPOINTMENTS":
                appts = get_appointments({'date': datetime.now().strftime('%Y-%m-%d')})
                results.append(f"📅 {len(appts)} appointments today")
            
            elif action == "TEST_AGENT" or action == "TEST_INBOUND":
                result = test_agent(params.get('agent_type', 'roofing'))
                if result.get('success'):
                    results.append(f"📞 Test call initiated!")
                else:
                    results.append(f"❌ Call failed: {result.get('error', 'Unknown')[:50]}")
            
            elif action == "CALL_LEAD":
                result = make_call(params.get('phone'), params.get('name', 'there'), params.get('agent_type', 'roofing'))
                results.append(f"📞 Calling {params.get('name', 'lead')}...")
            
            elif action == "ADD_LEAD":
                lead_id = add_lead(params.get('phone'), params.get('name', ''))
                results.append(f"✅ Added lead #{lead_id}")
            
            elif action == "START_CYCLE":
                result = start_lead_cycle(params.get('phone'), params.get('name', 'there'), 'manual', 1, params.get('agent_type', 'roofing'))
                results.append(f"🔥 Started lead cycle")
            
            elif action == "SEND_SMS":
                result = send_sms(params.get('phone'), params.get('message'))
                results.append(f"📱 SMS sent" if result.get('success') else f"❌ SMS failed")
            
            elif action == "SEND_CONFIRMATION":
                result = send_appointment_confirmation(params.get('appointment_id'))
                results.append(f"📱 Confirmation sent" if result.get('success') else f"❌ Failed")
            
            elif action == "GET_STATS":
                stats = get_appointment_stats()
                results.append(f"📊 {stats['total']} total, {stats['today']} today, {stats['sold']} sold, ${stats['revenue']} revenue")
            
            elif action == "GET_COSTS":
                costs = get_live_costs()
                results.append(f"💰 Today: ${costs['today']['total']:.2f}, Month: ${costs['month']['total']:.2f}")
            
            elif action == "GET_AGENT_STATS":
                stats = get_agent_stats(params.get('agent_type', 'roofing'))
                results.append(f"🤖 {stats['total_calls']} calls, {stats['appointments']} appts, {stats['conversion_rate']}% conv")
        
        except Exception as e:
            results.append(f"❌ Error: {str(e)[:50]}")
    
    # Remove action tags from response for clean display
    clean_response = re.sub(action_pattern, '', response_text).strip()
    
    return clean_response, results

def chat_with_aria(user_message):
    """Chat with Aria AI assistant"""
    # Get chat history
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT role, content FROM assistant_chat ORDER BY id DESC LIMIT 10')
    history = [{"role": row[0], "content": row[1]} for row in reversed(c.fetchall())]
    
    # Save user message
    c.execute('INSERT INTO assistant_chat (role, content) VALUES (?, ?)', ('user', user_message))
    conn.commit()
    conn.close()
    
    # Build messages
    messages = [{"role": "system", "content": ARIA_SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    
    # Call OpenAI (or use built-in if no key)
    if OPENAI_API_KEY:
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": "gpt-4o-mini", "messages": messages, "max_tokens": 500},
                timeout=30
            )
            if response.status_code == 200:
                aria_response = response.json()['choices'][0]['message']['content']
            else:
                aria_response = "I'm having trouble connecting. Try again?"
        except:
            aria_response = "Connection error. Please try again."
    else:
        # Simple built-in responses without API
        aria_response = process_simple_command(user_message)
    
    # Process any actions in the response
    clean_response, action_results = process_aria_actions(aria_response)
    
    # Save Aria's response
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO assistant_chat (role, content) VALUES (?, ?)', ('assistant', clean_response))
    conn.commit()
    conn.close()
    
    return {
        "response": clean_response,
        "actions": action_results
    }

def process_simple_command(message):
    """Process commands without OpenAI"""
    msg = message.lower()
    
    # Google Calendar questions
    if 'google' in msg and 'calendar' in msg:
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
            return "Yes! Google Calendar integration is configured. Appointments you book will sync automatically. You can also go to /oauth/google to re-authorize if needed."
        else:
            return "Google Calendar is not connected yet. To enable it, you'll need to:\n\n1. Go to Google Cloud Console\n2. Create OAuth credentials\n3. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to the config at the top of voice_app.py\n4. Restart the app and go to /oauth/google to authorize\n\nWant me to explain any of these steps?"
    
    if 'calendar' in msg and ('connect' in msg or 'sync' in msg or 'link' in msg):
        return "To connect Google Calendar, set your GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the config, then visit http://localhost:8080/oauth/google to authorize. Once connected, all appointments will sync automatically!"
    
    if 'test' in msg and 'agent' in msg:
        for agent_type in list(OUTBOUND_AGENTS.keys()) + list(INBOUND_AGENTS.keys()):
            if agent_type.replace('_', ' ') in msg or agent_type.replace('inbound_', '') in msg:
                return f"Sure! Testing {AGENT_TEMPLATES[agent_type]['name']} now. [ACTION:TEST_AGENT:{{\"agent_type\":\"{agent_type}\"}}]"
        return "Which agent would you like to test? I have 12 outbound sales agents (roofing, solar, insurance, auto, real estate, dental, hvac, legal, fitness, cleaning, landscaping, tax) and 15 inbound receptionists."
    
    if 'appointment' in msg and ('today' in msg or 'schedule' in msg):
        return "Here are today's appointments: [ACTION:GET_TODAY_APPOINTMENTS]"
    
    if 'stat' in msg or 'dashboard' in msg:
        return "Let me get your stats: [ACTION:GET_STATS]"
    
    if 'cost' in msg or 'spending' in msg:
        return "Here's your cost breakdown: [ACTION:GET_COSTS]"
    
    if 'call' in msg:
        return "Who would you like me to call? Give me a name and phone number, and which agent to use."
    
    if 'book' in msg or 'schedule' in msg:
        return "I can book an appointment! What's the customer's name, phone, and when should we schedule it?"
    
    if 'help' in msg or 'what can' in msg:
        return """Hey! I'm Aria, your AI assistant. Here's what I can help with:

📅 **Appointments**: "Show today's appointments", "Book an appointment"
📞 **Calls**: "Test the roofing agent", "Test the medical receptionist"
📊 **Stats**: "Show me the dashboard stats", "What are today's costs?"
🔗 **Integrations**: "Is Google Calendar connected?"
🤖 **Agents**: "What agents do we have?"

Just ask naturally and I'll take care of it!"""
    
    return """Hey! I'm Aria, your VOICE AI assistant. 

I can help you:
• Test any of the 27 AI agents
• Book and manage appointments  
• Check stats and costs
• Answer questions about the system

Try asking: "Test the roofing agent" or "Is Google Calendar connected?"

What would you like to do?"""

def get_chat_history():
    """Get recent chat history"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT role, content, created_at FROM assistant_chat ORDER BY id DESC LIMIT 50')
    history = [{"role": row[0], "content": row[1], "time": row[2]} for row in reversed(c.fetchall())]
    conn.close()
    return history

def clear_chat_history():
    """Clear chat history"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM assistant_chat')
    conn.commit()
    conn.close()
    return {"success": True}

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS & OTHER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_leads():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM leads ORDER BY created_at DESC')
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def add_lead(phone, first_name="", agent_type="roofing"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    phone = format_phone(phone)
    try:
        c.execute('INSERT INTO leads (phone, first_name, agent_type) VALUES (?, ?, ?)', (phone, first_name, agent_type))
        lead_id = c.lastrowid
        conn.commit()
        return lead_id
    except sqlite3.IntegrityError:
        c.execute('SELECT id FROM leads WHERE phone = ?', (phone,))
        result = c.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def get_calls(limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM call_log ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def get_sms_logs(limit=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM sms_log ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows

def get_live_costs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM cost_log WHERE date(created_at) = ?", (today,))
    today_total = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM cost_log WHERE date(created_at) >= ?", (month_start,))
    month_total = c.fetchone()[0]
    c.execute("SELECT cost_type, COALESCE(SUM(amount), 0) FROM cost_log WHERE date(created_at) = ? GROUP BY cost_type", (today,))
    today_by_type = dict(c.fetchall())
    c.execute("SELECT COUNT(*) FROM call_log WHERE date(created_at) = ?", (today,))
    today_calls = c.fetchone()[0]
    
    conn.close()
    return {
        'today': {'total': round(today_total, 4), 'vapi': round(today_by_type.get('vapi', 0), 4), 
                  'sms': round(today_by_type.get('sms', 0), 4), 'calls': today_calls},
        'month': {'total': round(month_total, 2)},
        'budget': {'daily_goal': DAILY_BUDGET_GOAL, 'monthly_goal': MONTHLY_BUDGET_GOAL}
    }

def get_agent_stats(agent_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*), COALESCE(SUM(duration), 0) FROM call_log WHERE agent_type = ?', (agent_type,))
    data = c.fetchone()
    c.execute('SELECT COUNT(*) FROM call_log WHERE agent_type = ? AND is_test_call = 1', (agent_type,))
    test_calls = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM appointments WHERE agent_type = ?', (agent_type,))
    appts = c.fetchone()[0]
    conn.close()
    
    total_calls = data[0] or 0
    return {
        'agent_type': agent_type, 'total_calls': total_calls, 'test_calls': test_calls,
        'appointments': appts,
        'conversion_rate': round((appts / total_calls * 100) if total_calls > 0 else 0, 1),
        'cost': round((data[1] or 0) / 60 * COST_PER_MINUTE_VAPI, 2)
    }

def get_all_agent_stats():
    stats = []
    for k, v in AGENT_TEMPLATES.items():
        s = get_agent_stats(k)
        s.update({'name': v['name'], 'icon': v['icon'], 'color': v['color'], 'industry': v['industry']})
        stats.append(s)
    return stats

def get_analytics():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM leads'); total_leads = c.fetchone()[0] or 1
    c.execute('SELECT COUNT(*) FROM appointments'); total_appts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM appointments WHERE disposition = 'sold'"); sold = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(sale_amount), 0) FROM appointments WHERE disposition = 'sold'"); revenue = c.fetchone()[0]
    conn.close()
    return {'total_leads': total_leads, 'total_appts': total_appts, 'sold': sold, 'revenue': revenue or 0}

# Lead Cycle Functions
def update_lead_cycle(lead_id, day, attempt, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE leads SET cycle_day=?, cycle_attempt=?, cycle_status=? WHERE id=?', (day, attempt, status, lead_id))
    conn.commit()
    conn.close()

def run_cycle_attempt(lead_id, phone, name, day, attempt, agent_type):
    global active_cycles
    key = str(lead_id)
    agent = AGENT_TEMPLATES.get(agent_type, OUTBOUND_AGENTS["roofing"])
    active_cycles[key] = {'lead_id': lead_id, 'phone': phone, 'name': name, 'day': day, 
                          'attempt': attempt, 'status': '🚀 Starting...', 'agent': agent['name'], 'icon': agent['icon']}
    try:
        active_cycles[key]['status'] = '📱 SMS...'
        send_sms(phone, f"Hey {name}! 👋 Calling you now!")
        time.sleep(3)
        active_cycles[key]['status'] = '📞 Call #1...'
        make_call(phone, name, agent_type)
        time.sleep(45)
        active_cycles[key]['status'] = '📞 Call #2...'
        make_call(phone, name, agent_type)
        time.sleep(40)
        active_cycles[key]['status'] = '📱 Follow-up...'
        send_sms(phone, f"Hey {name}! Just tried calling. Text back! 📱")
        update_lead_cycle(lead_id, day, attempt, 'completed')
        active_cycles[key]['status'] = '✅ Done!'
    except Exception as e:
        active_cycles[key]['status'] = f'❌ Error'
    time.sleep(5)
    if key in active_cycles: del active_cycles[key]

def start_lead_cycle(phone, name, source="manual", is_homeowner=1, agent_type="roofing"):
    lead_id = add_lead(phone, first_name=name, agent_type=agent_type)
    if not lead_id: return {"error": "Failed"}
    update_lead_cycle(lead_id, 1, 1, 'in_progress')
    thread = threading.Thread(target=run_cycle_attempt, args=(lead_id, format_phone(phone), name, 1, 1, agent_type), daemon=True)
    thread.start()
    return {"success": True, "lead_id": lead_id}

def get_active_cycles():
    return list(active_cycles.values())

# ═══════════════════════════════════════════════════════════════════════════════
# SETTINGS & TEST PHONE
# ═══════════════════════════════════════════════════════════════════════════════

def get_settings():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT setting_key, setting_value FROM app_settings')
    settings = {row['setting_key']: row['setting_value'] for row in c.fetchall()}
    conn.close()
    return settings

def update_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO app_settings (setting_key, setting_value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)', (key, value))
    conn.commit()
    conn.close()
    return {"success": True}

def get_test_phone():
    settings = get_settings()
    return settings.get('test_phone', TEST_PHONE)

def set_test_phone(phone):
    return update_setting('test_phone', format_phone(phone))

def get_app_mode():
    settings = get_settings()
    return settings.get('mode', 'testing')

def set_app_mode(mode):
    return update_setting('mode', mode)

# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE STAGES
# ═══════════════════════════════════════════════════════════════════════════════

def get_pipeline_stages():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM pipeline_stages WHERE is_active = 1 ORDER BY stage_order')
    stages = [dict(row) for row in c.fetchall()]
    conn.close()
    return stages

def get_pipeline_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    stages = get_pipeline_stages()
    stats = {}
    for stage in stages:
        c.execute('SELECT COUNT(*) FROM leads WHERE pipeline_stage = ?', (stage['stage_key'],))
        lead_count = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM appointments WHERE pipeline_stage = ?', (stage['stage_key'],))
        appt_count = c.fetchone()[0]
        stats[stage['stage_key']] = {
            'name': stage['stage_name'],
            'color': stage['stage_color'],
            'icon': stage.get('stage_icon', '📋'),
            'leads': lead_count,
            'appointments': appt_count,
            'total': lead_count + appt_count
        }
    conn.close()
    return stats

# ═══════════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE LEAD TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

def get_lead_details(lead_id):
    """Get full lead details with all call history"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get lead
    c.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
    lead = dict(c.fetchone()) if c.fetchone() else None
    if not lead:
        conn.close()
        return None
    
    # Get all calls for this lead
    c.execute('SELECT * FROM call_log WHERE phone = ? ORDER BY created_at DESC', (lead['phone'],))
    calls = [dict(row) for row in c.fetchall()]
    
    # Get all SMS for this lead
    c.execute('SELECT * FROM sms_log WHERE phone = ? ORDER BY created_at DESC', (lead['phone'],))
    sms = [dict(row) for row in c.fetchall()]
    
    # Get appointment if exists
    c.execute('SELECT * FROM appointments WHERE lead_id = ? OR phone = ?', (lead_id, lead['phone']))
    appointment = dict(c.fetchone()) if c.fetchone() else None
    
    conn.close()
    
    return {
        'lead': lead,
        'calls': calls,
        'sms': sms,
        'appointment': appointment,
        'summary': {
            'total_calls': len(calls),
            'answered': sum(1 for c in calls if c.get('answered')),
            'no_answer': sum(1 for c in calls if c.get('no_answer')),
            'voicemail': sum(1 for c in calls if c.get('voicemail')),
            'hungup': sum(1 for c in calls if c.get('hungup')),
            'appointment_booked': any(c.get('appointment_booked') for c in calls)
        }
    }

def get_leads_with_status():
    """Get all leads with their current status and call summary"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT l.*, 
        (SELECT COUNT(*) FROM call_log WHERE phone = l.phone) as call_count,
        (SELECT COUNT(*) FROM call_log WHERE phone = l.phone AND answered = 1) as answered_count,
        (SELECT COUNT(*) FROM call_log WHERE phone = l.phone AND no_answer = 1) as no_answer_count,
        (SELECT outcome FROM call_log WHERE phone = l.phone ORDER BY created_at DESC LIMIT 1) as last_outcome
        FROM leads l ORDER BY l.created_at DESC''')
    
    leads = [dict(row) for row in c.fetchall()]
    conn.close()
    return leads

def update_lead_after_call(phone, outcome, appointment_booked=False, call_id=None):
    """Update lead status after a call"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get current lead stats
    c.execute('SELECT * FROM leads WHERE phone = ?', (format_phone(phone),))
    lead = c.fetchone()
    if not lead:
        conn.close()
        return
    
    # Update call counts based on outcome
    updates = {
        'total_calls': 'total_calls + 1',
        'last_call_date': 'CURRENT_TIMESTAMP',
        'last_call_outcome': f"'{outcome}'"
    }
    
    if outcome == 'answered':
        updates['total_answered'] = 'total_answered + 1'
        updates['pipeline_stage'] = "'contacted'"
    elif outcome == 'no_answer':
        updates['total_no_answer'] = 'total_no_answer + 1'
        updates['pipeline_stage'] = "'no_answer'"
    elif outcome == 'voicemail':
        updates['total_voicemail'] = 'total_voicemail + 1'
    elif outcome == 'hungup':
        updates['total_hungup'] = 'total_hungup + 1'
    
    if appointment_booked:
        updates['appointment_set'] = '1'
        updates['pipeline_stage'] = "'appointment_set'"
    
    set_clause = ', '.join([f"{k} = {v}" for k, v in updates.items()])
    c.execute(f'UPDATE leads SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE phone = ?', (format_phone(phone),))
    
    conn.commit()
    conn.close()

def import_leads_from_csv(csv_data, source='csv', agent_type='roofing', campaign=None):
    """Import leads from CSV data (list of dicts)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    imported = 0
    skipped = 0
    errors = 0
    
    for row in csv_data:
        try:
            phone = format_phone(row.get('phone', row.get('Phone', row.get('phone_number', ''))))
            if not phone or len(phone) < 10:
                skipped += 1
                continue
            
            first_name = row.get('first_name', row.get('First Name', row.get('name', '')))
            last_name = row.get('last_name', row.get('Last Name', ''))
            email = row.get('email', row.get('Email', ''))
            address = row.get('address', row.get('Address', ''))
            city = row.get('city', row.get('City', ''))
            state = row.get('state', row.get('State', ''))
            zipcode = row.get('zip', row.get('Zip', row.get('zipcode', '')))
            
            # Check if lead exists
            c.execute('SELECT id FROM leads WHERE phone = ?', (phone,))
            if c.fetchone():
                skipped += 1
                continue
            
            c.execute('''INSERT INTO leads (phone, first_name, last_name, email, address, city, state, zip,
                        source, agent_type, ad_campaign, pipeline_stage) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new_lead')''',
                     (phone, first_name, last_name, email, address, city, state, zipcode, source, agent_type, campaign))
            imported += 1
            
        except Exception as e:
            errors += 1
            print(f"Error importing row: {e}")
    
    # Log the import
    c.execute('INSERT INTO import_history (filename, total_rows, imported, skipped, errors, source) VALUES (?, ?, ?, ?, ?, ?)',
              ('bulk_import', len(csv_data), imported, skipped, errors, source))
    
    conn.commit()
    conn.close()
    
    return {'imported': imported, 'skipped': skipped, 'errors': errors, 'total': len(csv_data)}

def get_pipeline_leads(stage=None):
    """Get leads grouped by pipeline stage or for a specific stage"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if stage:
        c.execute('''SELECT l.*, 
            (SELECT COUNT(*) FROM call_log WHERE phone = l.phone) as call_count,
            (SELECT outcome FROM call_log WHERE phone = l.phone ORDER BY created_at DESC LIMIT 1) as last_outcome
            FROM leads l WHERE l.pipeline_stage = ? ORDER BY l.created_at DESC''', (stage,))
    else:
        c.execute('''SELECT l.*, 
            (SELECT COUNT(*) FROM call_log WHERE phone = l.phone) as call_count,
            (SELECT outcome FROM call_log WHERE phone = l.phone ORDER BY created_at DESC LIMIT 1) as last_outcome
            FROM leads l ORDER BY l.pipeline_stage, l.created_at DESC''')
    
    leads = [dict(row) for row in c.fetchall()]
    conn.close()
    return leads

def move_lead_to_stage(lead_id, new_stage):
    """Move a lead to a new pipeline stage"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE leads SET pipeline_stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_stage, lead_id))
    conn.commit()
    conn.close()
    return {'success': True}

def get_lead_timeline(lead_id):
    """Get complete timeline for a lead (calls, SMS, status changes)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get lead phone
    c.execute('SELECT phone, first_name FROM leads WHERE id = ?', (lead_id,))
    lead = c.fetchone()
    if not lead:
        conn.close()
        return []
    
    timeline = []
    
    # Get calls
    c.execute('SELECT *, "call" as type FROM call_log WHERE phone = ? ORDER BY created_at DESC', (lead['phone'],))
    for row in c.fetchall():
        r = dict(row)
        timeline.append({
            'type': 'call',
            'date': r['created_at'],
            'outcome': r.get('outcome', r.get('status')),
            'duration': r.get('duration', 0),
            'agent': r.get('agent_type'),
            'appointment_booked': r.get('appointment_booked', 0),
            'icon': '📞' if r.get('answered') else '📵'
        })
    
    # Get SMS
    c.execute('SELECT * FROM sms_log WHERE phone = ? ORDER BY created_at DESC', (lead['phone'],))
    for row in c.fetchall():
        r = dict(row)
        timeline.append({
            'type': 'sms',
            'date': r['created_at'],
            'message': r.get('message', '')[:50] + '...' if len(r.get('message', '')) > 50 else r.get('message', ''),
            'direction': r.get('direction', 'outbound'),
            'icon': '📤' if r.get('direction') == 'outbound' else '📥'
        })
    
    # Sort by date
    timeline.sort(key=lambda x: x['date'], reverse=True)
    
    conn.close()
    return timeline

def get_call_outcomes_summary():
    """Get summary of all call outcomes"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT 
        COUNT(*) as total,
        SUM(answered) as answered,
        SUM(no_answer) as no_answer,
        SUM(voicemail) as voicemail,
        SUM(hungup) as hungup,
        SUM(appointment_booked) as appointments
        FROM call_log WHERE is_test_call = 0''')
    
    row = c.fetchone()
    conn.close()
    
    total = row[0] or 1
    return {
        'total': row[0] or 0,
        'answered': row[1] or 0,
        'no_answer': row[2] or 0,
        'voicemail': row[3] or 0,
        'hungup': row[4] or 0,
        'appointments': row[5] or 0,
        'answer_rate': round((row[1] or 0) / total * 100, 1),
        'booking_rate': round((row[5] or 0) / total * 100, 1) if total > 0 else 0
    }


def update_lead_pipeline(lead_id, stage):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE leads SET pipeline_stage = ? WHERE id = ?', (stage, lead_id))
    conn.commit()
    conn.close()
    return {"success": True}

def update_appointment_pipeline(appt_id, stage):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE appointments SET pipeline_stage = ? WHERE id = ?', (stage, appt_id))
    conn.commit()
    conn.close()
    return {"success": True}

# ═══════════════════════════════════════════════════════════════════════════════
# FACEBOOK/INSTAGRAM ADS
# ═══════════════════════════════════════════════════════════════════════════════

def get_ad_campaigns():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM ad_campaigns ORDER BY created_at DESC')
    campaigns = [dict(row) for row in c.fetchall()]
    conn.close()
    return campaigns

def create_ad_campaign(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO ad_campaigns (platform, campaign_id, campaign_name, daily_budget, status) 
                 VALUES (?, ?, ?, ?, ?)''',
              (data.get('platform', 'facebook'), data.get('campaign_id', ''), 
               data.get('campaign_name', 'New Campaign'), data.get('daily_budget', 0), 'active'))
    campaign_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": campaign_id}

def update_ad_campaign(campaign_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updates = []
    params = []
    for field in ['campaign_name', 'daily_budget', 'status', 'total_spend', 'impressions', 
                  'clicks', 'leads', 'appointments', 'sales', 'revenue']:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])
    if updates:
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(campaign_id)
        c.execute(f'UPDATE ad_campaigns SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()
    conn.close()
    return {"success": True}

def log_ad_daily_stats(campaign_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    spend = data.get('spend', 0)
    leads = data.get('leads', 0)
    appointments = data.get('appointments', 0)
    
    # Calculate metrics
    cpl = round(spend / leads, 2) if leads > 0 else 0
    cpa = round(spend / appointments, 2) if appointments > 0 else 0
    revenue = data.get('revenue', 0)
    roas = round(revenue / spend, 2) if spend > 0 else 0
    
    c.execute('''INSERT INTO ad_daily_stats (campaign_id, date, spend, impressions, clicks, leads, 
                 appointments, sales, revenue, cpl, cpa, roas) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (campaign_id, date, spend, data.get('impressions', 0), data.get('clicks', 0),
               leads, appointments, data.get('sales', 0), revenue, cpl, cpa, roas))
    conn.commit()
    conn.close()
    return {"success": True}

def get_ad_stats_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    
    # Today's stats
    c.execute('''SELECT COALESCE(SUM(spend), 0), COALESCE(SUM(leads), 0), COALESCE(SUM(appointments), 0),
                 COALESCE(SUM(sales), 0), COALESCE(SUM(revenue), 0) FROM ad_daily_stats WHERE date = ?''', (today,))
    today_row = c.fetchone()
    
    # Month stats
    c.execute('''SELECT COALESCE(SUM(spend), 0), COALESCE(SUM(leads), 0), COALESCE(SUM(appointments), 0),
                 COALESCE(SUM(sales), 0), COALESCE(SUM(revenue), 0) FROM ad_daily_stats WHERE date >= ?''', (month_start,))
    month_row = c.fetchone()
    
    # All time
    c.execute('''SELECT COALESCE(SUM(total_spend), 0), COALESCE(SUM(leads), 0), COALESCE(SUM(appointments), 0),
                 COALESCE(SUM(sales), 0), COALESCE(SUM(revenue), 0) FROM ad_campaigns''')
    all_row = c.fetchone()
    
    conn.close()
    
    def calc_metrics(spend, leads, appts, sales, revenue):
        return {
            'spend': round(spend, 2),
            'leads': leads,
            'appointments': appts,
            'sales': sales,
            'revenue': round(revenue, 2),
            'cpl': round(spend / leads, 2) if leads > 0 else 0,
            'cpa': round(spend / appts, 2) if appts > 0 else 0,
            'cps': round(spend / sales, 2) if sales > 0 else 0,
            'roas': round(revenue / spend, 2) if spend > 0 else 0
        }
    
    return {
        'today': calc_metrics(*today_row),
        'month': calc_metrics(*month_row),
        'all_time': calc_metrics(*all_row)
    }

# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED TEST AGENT (with phone selection)
# ═══════════════════════════════════════════════════════════════════════════════

def test_agent_with_phone(agent_type, phone=None, is_live=False):
    """Test an agent with a specified phone number"""
    if not phone:
        phone = get_test_phone()
    
    phone = format_phone(phone)
    agent = AGENT_TEMPLATES.get(agent_type, OUTBOUND_AGENTS["roofing"])
    
    # Log the test call with mode info
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    result = make_call(phone, "Test", agent_type, is_test=not is_live)
    
    if result.get('success'):
        c.execute('UPDATE call_log SET is_live = ?, test_phone = ? WHERE call_id = ?',
                  (1 if is_live else 0, phone, result.get('call_id', '')))
        conn.commit()
    
    conn.close()
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════════════════════════
# VOICE LANDING PAGE - Stunning Marketing Website
# ═══════════════════════════════════════════════════════════════════════════════

def get_landing_page():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VOICE - AI That Closes Deals</title>
<meta name="description" content="VOICE AI automates your sales calls with human-like AI agents. Book more appointments, close more deals, 24/7.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--black:#0A0A0A;--white:#F5F7FA;--gray-400:#9CA3AF;--gray-600:#4B5563;--cyan:#00D1FF;--cyan-glow:rgba(0,209,255,0.15)}
body{font-family:'Inter',sans-serif;background:var(--black);color:var(--white);line-height:1.6;overflow-x:hidden}
a{color:inherit;text-decoration:none}

/* Navigation */
.nav{position:fixed;top:0;left:0;right:0;z-index:1000;padding:20px 40px;display:flex;justify-content:space-between;align-items:center;background:rgba(10,10,10,0.8);backdrop-filter:blur(20px);border-bottom:1px solid rgba(255,255,255,0.05)}
.nav-logo{display:flex;align-items:center;gap:12px;font-size:24px;font-weight:700;letter-spacing:-0.5px}
.nav-logo svg{width:36px;height:36px}
.nav-links{display:flex;gap:40px;font-size:14px;color:var(--gray-400)}
.nav-links a:hover{color:var(--white)}
.nav-cta{background:var(--cyan);color:var(--black);padding:12px 28px;border-radius:8px;font-weight:600;font-size:14px;transition:all .2s}
.nav-cta:hover{transform:translateY(-2px);box-shadow:0 10px 40px rgba(0,209,255,0.3)}

/* Hero */
.hero{min-height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:140px 20px 80px;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:50%;left:50%;width:800px;height:800px;background:radial-gradient(circle,rgba(0,209,255,0.08) 0%,transparent 70%);transform:translate(-50%,-50%);pointer-events:none}
.hero-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(0,209,255,0.1);border:1px solid rgba(0,209,255,0.2);padding:8px 16px;border-radius:100px;font-size:13px;color:var(--cyan);margin-bottom:32px}
.hero-badge span{width:8px;height:8px;background:var(--cyan);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
.hero h1{font-size:clamp(48px,8vw,84px);font-weight:800;letter-spacing:-2px;line-height:1.05;margin-bottom:24px;background:linear-gradient(135deg,#fff 0%,#00D1FF 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-sub{font-size:clamp(18px,2.5vw,24px);color:var(--gray-400);max-width:600px;margin-bottom:48px;font-weight:300}
.hero-ctas{display:flex;gap:16px;flex-wrap:wrap;justify-content:center}
.btn-primary{background:var(--cyan);color:var(--black);padding:18px 40px;border-radius:12px;font-weight:600;font-size:16px;transition:all .2s;border:none;cursor:pointer}
.btn-primary:hover{transform:translateY(-3px);box-shadow:0 20px 60px rgba(0,209,255,0.4)}
.btn-secondary{background:transparent;color:var(--white);padding:18px 40px;border-radius:12px;font-weight:600;font-size:16px;border:1px solid rgba(255,255,255,0.2);transition:all .2s}
.btn-secondary:hover{background:rgba(255,255,255,0.05);border-color:rgba(255,255,255,0.3)}

/* Stats */
.stats{display:flex;justify-content:center;gap:80px;margin-top:80px;flex-wrap:wrap}
.stat{text-align:center}
.stat-value{font-size:48px;font-weight:700;color:var(--cyan)}
.stat-label{font-size:14px;color:var(--gray-400);margin-top:4px}

/* Features */
.features{padding:120px 40px;max-width:1200px;margin:0 auto}
.section-label{text-transform:uppercase;font-size:12px;letter-spacing:2px;color:var(--cyan);margin-bottom:16px}
.section-title{font-size:clamp(32px,5vw,48px);font-weight:700;letter-spacing:-1px;margin-bottom:60px}
.features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:32px}
.feature{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:16px;padding:32px;transition:all .3s}
.feature:hover{background:rgba(255,255,255,0.04);border-color:rgba(0,209,255,0.2);transform:translateY(-4px)}
.feature-icon{font-size:40px;margin-bottom:20px}
.feature h3{font-size:20px;font-weight:600;margin-bottom:12px}
.feature p{color:var(--gray-400);font-size:15px;line-height:1.7}

/* Agents */
.agents{padding:120px 40px;background:linear-gradient(180deg,transparent 0%,rgba(0,209,255,0.03) 100%)}
.agents-inner{max-width:1200px;margin:0 auto;text-align:center}
.agents-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:16px;margin-top:60px}
.agent-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:24px 16px;text-align:center;transition:all .3s}
.agent-card:hover{border-color:var(--cyan);background:rgba(0,209,255,0.05)}
.agent-icon{font-size:32px;margin-bottom:12px}
.agent-name{font-weight:600;font-size:14px;margin-bottom:4px}
.agent-role{font-size:11px;color:var(--gray-400);text-transform:uppercase;letter-spacing:0.5px}

/* Pricing */
.pricing{padding:120px 40px;max-width:1000px;margin:0 auto;text-align:center}
.pricing-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;margin-top:60px}
.pricing-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:40px;text-align:left;position:relative}
.pricing-card.featured{border-color:var(--cyan);background:rgba(0,209,255,0.05)}
.pricing-card.featured::before{content:'POPULAR';position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--cyan);color:var(--black);font-size:11px;font-weight:700;padding:4px 12px;border-radius:100px}
.pricing-name{font-size:18px;font-weight:600;margin-bottom:8px}
.pricing-price{font-size:48px;font-weight:700;margin-bottom:4px}
.pricing-price span{font-size:16px;color:var(--gray-400);font-weight:400}
.pricing-desc{color:var(--gray-400);font-size:14px;margin-bottom:32px}
.pricing-features{list-style:none;margin-bottom:32px}
.pricing-features li{padding:8px 0;font-size:14px;color:var(--gray-400);display:flex;align-items:center;gap:12px}
.pricing-features li::before{content:'✓';color:var(--cyan);font-weight:700}
.pricing-btn{width:100%;padding:14px;border-radius:10px;font-weight:600;font-size:14px;border:none;cursor:pointer;transition:all .2s}
.pricing-card:not(.featured) .pricing-btn{background:rgba(255,255,255,0.1);color:var(--white)}
.pricing-card.featured .pricing-btn{background:var(--cyan);color:var(--black)}

/* CTA */
.cta{padding:120px 40px;text-align:center;position:relative}
.cta::before{content:'';position:absolute;top:0;left:50%;width:600px;height:400px;background:radial-gradient(ellipse,rgba(0,209,255,0.1) 0%,transparent 70%);transform:translateX(-50%);pointer-events:none}
.cta h2{font-size:clamp(32px,5vw,56px);font-weight:700;letter-spacing:-1px;margin-bottom:24px}
.cta p{color:var(--gray-400);font-size:18px;margin-bottom:40px;max-width:500px;margin-left:auto;margin-right:auto}

/* Footer */
.footer{padding:60px 40px;border-top:1px solid rgba(255,255,255,0.05);text-align:center}
.footer-logo{display:flex;align-items:center;justify-content:center;gap:12px;font-size:20px;font-weight:700;margin-bottom:24px}
.footer-logo svg{width:28px;height:28px}
.footer-links{display:flex;justify-content:center;gap:32px;margin-bottom:24px;font-size:14px;color:var(--gray-400)}
.footer-links a:hover{color:var(--white)}
.footer-copy{font-size:13px;color:var(--gray-600)}

/* Animations */
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.pulse-logo{animation:pulseRotate 3s linear infinite}
@keyframes pulseRotate{0%{transform:rotate(0deg);opacity:.8}50%{opacity:1}100%{transform:rotate(360deg);opacity:.8}}

/* Mobile */
@media(max-width:768px){
.nav{padding:16px 20px}
.nav-links{display:none}
.hero{padding:120px 20px 60px}
.stats{gap:40px}
.features,.agents,.pricing,.cta{padding:80px 20px}
}
</style>
</head>
<body>

<nav class="nav">
<div class="nav-logo">
<svg class="pulse-logo" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><circle cx="256" cy="256" r="180" stroke="#00D1FF" stroke-width="24" fill="none" stroke-linecap="round" stroke-dasharray="900 200"/></svg>
VOICE
</div>
<div class="nav-links">
<a href="#features">Features</a>
<a href="#agents">Agents</a>
<a href="#pricing">Pricing</a>
</div>
<a href="/app" class="nav-cta">Launch App →</a>
</nav>

<section class="hero">
<div class="hero-badge"><span></span> AI-Powered Sales Platform</div>
<h1>AI That<br>Closes Deals</h1>
<p class="hero-sub">27 human-like AI agents that call your leads, book appointments, and never miss a follow-up. 24/7. On autopilot.</p>
<div class="hero-ctas">
<a href="/app" class="btn-primary">Start Free Trial →</a>
<a href="#demo" class="btn-secondary">Watch Demo</a>
</div>
<div class="stats">
<div class="stat"><div class="stat-value">27</div><div class="stat-label">AI Agents</div></div>
<div class="stat"><div class="stat-value">12</div><div class="stat-label">Industries</div></div>
<div class="stat"><div class="stat-value">24/7</div><div class="stat-label">Always On</div></div>
<div class="stat"><div class="stat-value">3x</div><div class="stat-label">More Bookings</div></div>
</div>
</section>

<section class="features" id="features">
<div class="section-label">Features</div>
<h2 class="section-title">Everything you need to<br>automate your sales</h2>
<div class="features-grid">
<div class="feature">
<div class="feature-icon">🤖</div>
<h3>Human-Like AI Calls</h3>
<p>Our agents sound so natural, leads can't tell they're talking to AI. Built on NEPQ psychology for maximum conversions.</p>
</div>
<div class="feature">
<div class="feature-icon">📅</div>
<h3>Instant Booking</h3>
<p>AI books appointments directly into your calendar. Syncs with Google Calendar and Outlook automatically.</p>
</div>
<div class="feature">
<div class="feature-icon">🔄</div>
<h3>Smart Follow-Up</h3>
<p>3 calls per day, 7 days per lead. Double-tap pattern ensures no lead goes cold. Automatic re-engagement.</p>
</div>
<div class="feature">
<div class="feature-icon">📊</div>
<h3>Full Pipeline View</h3>
<p>Track every lead from first contact to closed deal. See call outcomes, appointment rates, and revenue in real-time.</p>
</div>
<div class="feature">
<div class="feature-icon">📱</div>
<h3>FB/IG Ads Integration</h3>
<p>Leads from Facebook and Instagram flow directly into VOICE. Track CPL, CPA, and ROAS automatically.</p>
</div>
<div class="feature">
<div class="feature-icon">⚡</div>
<h3>Zapier + 5000 Apps</h3>
<p>Connect to your CRM, email platform, and any tool you use. Webhooks trigger on every event.</p>
</div>
</div>
</section>

<section class="agents" id="agents">
<div class="agents-inner">
<div class="section-label">AI Agents</div>
<h2 class="section-title">Meet your sales team</h2>
<p style="color:var(--gray-400);max-width:600px;margin:0 auto">12 outbound appointment setters and 15 inbound receptionists. Each trained for their specific industry.</p>
<div class="agents-grid">
<div class="agent-card"><div class="agent-icon">🏠</div><div class="agent-name">Paige</div><div class="agent-role">Roofing</div></div>
<div class="agent-card"><div class="agent-icon">☀️</div><div class="agent-name">Luna</div><div class="agent-role">Solar</div></div>
<div class="agent-card"><div class="agent-icon">🛡️</div><div class="agent-name">Maya</div><div class="agent-role">Insurance</div></div>
<div class="agent-card"><div class="agent-icon">🚗</div><div class="agent-name">Marco</div><div class="agent-role">Auto Sales</div></div>
<div class="agent-card"><div class="agent-icon">🏡</div><div class="agent-name">Sofia</div><div class="agent-role">Real Estate</div></div>
<div class="agent-card"><div class="agent-icon">🦷</div><div class="agent-name">Carmen</div><div class="agent-role">Dental</div></div>
<div class="agent-card"><div class="agent-icon">❄️</div><div class="agent-name">Jake</div><div class="agent-role">HVAC</div></div>
<div class="agent-card"><div class="agent-icon">⚖️</div><div class="agent-name">Victoria</div><div class="agent-role">Legal</div></div>
<div class="agent-card"><div class="agent-icon">💪</div><div class="agent-name">Alex</div><div class="agent-role">Fitness</div></div>
<div class="agent-card"><div class="agent-icon">🧹</div><div class="agent-name">Rosa</div><div class="agent-role">Cleaning</div></div>
<div class="agent-card"><div class="agent-icon">🌳</div><div class="agent-name">Miguel</div><div class="agent-role">Landscaping</div></div>
<div class="agent-card"><div class="agent-icon">📊</div><div class="agent-name">Diana</div><div class="agent-role">Tax</div></div>
</div>
</div>
</section>

<section class="pricing" id="pricing">
<div class="section-label">Pricing</div>
<h2 class="section-title">Simple, transparent pricing</h2>
<div class="pricing-cards">
<div class="pricing-card">
<div class="pricing-name">Starter</div>
<div class="pricing-price">$97<span>/mo</span></div>
<div class="pricing-desc">Perfect for small teams</div>
<ul class="pricing-features">
<li>3 AI Agents</li>
<li>500 calls/month</li>
<li>Basic integrations</li>
<li>Email support</li>
</ul>
<button class="pricing-btn" onclick="location.href='/app'">Get Started</button>
</div>
<div class="pricing-card featured">
<div class="pricing-name">Professional</div>
<div class="pricing-price">$297<span>/mo</span></div>
<div class="pricing-desc">Most popular for growing businesses</div>
<ul class="pricing-features">
<li>All 27 AI Agents</li>
<li>Unlimited calls</li>
<li>All integrations</li>
<li>Priority support</li>
<li>Custom agent training</li>
</ul>
<button class="pricing-btn" onclick="location.href='/app'">Start Free Trial</button>
</div>
<div class="pricing-card">
<div class="pricing-name">Enterprise</div>
<div class="pricing-price">Custom</div>
<div class="pricing-desc">For large organizations</div>
<ul class="pricing-features">
<li>Unlimited everything</li>
<li>Custom AI agents</li>
<li>Dedicated account manager</li>
<li>SLA guarantee</li>
<li>On-premise option</li>
</ul>
<button class="pricing-btn">Contact Sales</button>
</div>
</div>
</section>

<section class="cta">
<h2>Ready to close more deals?</h2>
<p>Join hundreds of businesses automating their sales with VOICE AI.</p>
<a href="/app" class="btn-primary">Launch VOICE Free →</a>
</section>

<footer class="footer">
<div class="footer-logo">
<svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><circle cx="256" cy="256" r="180" stroke="#00D1FF" stroke-width="24" fill="none" stroke-linecap="round" stroke-dasharray="900 200"/></svg>
VOICE
</div>
<div class="footer-links">
<a href="#features">Features</a>
<a href="#agents">Agents</a>
<a href="#pricing">Pricing</a>
<a href="/app">Dashboard</a>
</div>
<div class="footer-copy">© 2025 VOICE AI. All rights reserved.</div>
</footer>

</body>
</html>'''

# ═══════════════════════════════════════════════════════════════════════════════
# VOICE HTML - Apple/Tesla Grade with Official Pulse Loop Logo
# ═══════════════════════════════════════════════════════════════════════════════

def get_html():
    out_json = json.dumps({k: {"name": v["name"], "industry": v["industry"], "icon": v.get("icon", "🤖"), "color": v.get("color", "#00D1FF")} for k, v in OUTBOUND_AGENTS.items()})
    in_json = json.dumps({k: {"name": v["name"], "industry": v["industry"], "icon": v.get("icon", "📞"), "color": v.get("color", "#00D1FF")} for k, v in INBOUND_AGENTS.items()})
    
    css = """*{margin:0;padding:0;box-sizing:border-box}
:root{--black:#0A0A0A;--white:#F5F7FA;--gray-300:#9CA3AF;--gray-500:#6B7280;--gray-800:#1F2937;--gray-900:#111827;--cyan:#00D1FF;--success:#10B981;--warning:#F59E0B;--danger:#EF4444;--border:rgba(255,255,255,0.06)}
body{font-family:'Inter',-apple-system,sans-serif;background:var(--black);color:var(--white);line-height:1.5;-webkit-font-smoothing:antialiased}
.sidebar{position:fixed;left:0;top:0;bottom:0;width:220px;background:var(--black);border-right:1px solid var(--border);padding:24px 0;overflow-y:auto;z-index:100}
.logo{display:flex;align-items:center;gap:12px;padding:0 24px;margin-bottom:32px;text-decoration:none}
.pulse-loop{width:32px;height:32px;animation:pulseRotate 1.8s linear infinite}
@keyframes pulseRotate{0%{transform:rotate(0deg);opacity:.85}50%{opacity:1}100%{transform:rotate(360deg);opacity:.85}}
.logo-text{font-size:16px;font-weight:600;letter-spacing:3px;color:var(--white);text-transform:uppercase}
.nav-section{padding:20px 24px 8px;font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--gray-500);font-weight:600}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 24px;cursor:pointer;color:var(--gray-500);font-size:13px;font-weight:500;border-left:2px solid transparent;transition:all .2s}
.nav-item:hover{background:rgba(255,255,255,.02);color:var(--white)}
.nav-item.active{background:rgba(255,255,255,.03);border-left-color:var(--cyan);color:var(--white)}
.nav-badge{margin-left:auto;background:var(--gray-800);color:var(--gray-300);padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600}
.main{margin-left:220px;padding:32px;padding-bottom:100px;min-height:100vh}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px}
.header h1{font-size:24px;font-weight:600;letter-spacing:-0.5px}
.header-sub{color:var(--gray-500);font-size:13px;margin-top:4px}
.card{background:rgba(255,255,255,.02);border-radius:8px;border:1px solid var(--border);margin-bottom:24px}
.card-header{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.card-header h2{font-size:14px;font-weight:600}
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border-radius:8px;overflow:hidden;margin-bottom:24px}
.stat{background:var(--black);padding:24px;text-align:center}
.stat-value{font-size:32px;font-weight:600;letter-spacing:-1px;margin-bottom:4px}
.stat-label{font-size:11px;color:var(--gray-500);text-transform:uppercase;letter-spacing:1px}
.stat.cyan .stat-value{color:var(--cyan)}
.stat.green .stat-value{color:var(--success)}
.stat.orange .stat-value{color:var(--warning)}
.btn{padding:8px 16px;border-radius:6px;font-weight:600;cursor:pointer;border:none;display:inline-flex;align-items:center;gap:6px;font-family:inherit;font-size:13px;transition:all .2s}
.btn-primary{background:var(--white);color:var(--black)}
.btn-primary:hover{background:var(--cyan)}
.btn-secondary{background:transparent;color:var(--white);border:1px solid var(--gray-800)}
.btn-secondary:hover{border-color:var(--gray-500)}
.btn-success{background:var(--success);color:var(--white)}
.btn-danger{background:var(--danger);color:var(--white)}
.btn-sm{padding:6px 10px;font-size:12px}
.status{padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}
.status-scheduled{background:rgba(0,209,255,.1);color:var(--cyan)}
.status-sold{background:rgba(16,185,129,.1);color:var(--success)}
.status-no-show{background:rgba(239,68,68,.1);color:var(--danger)}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:24px}
table{width:100%;border-collapse:collapse}
th,td{padding:12px 16px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--gray-500);font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:600}
td{font-size:13px}
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.8);display:none;justify-content:center;align-items:center;z-index:1000;padding:20px;backdrop-filter:blur(4px)}
.modal-bg.active{display:flex}
.modal{background:var(--gray-900);border-radius:12px;padding:24px;width:100%;max-width:480px;max-height:90vh;overflow-y:auto;border:1px solid var(--border)}
.modal h2{font-size:18px;font-weight:600;margin-bottom:20px}
.form-group{margin-bottom:16px}
.form-group label{display:block;margin-bottom:6px;color:var(--gray-300);font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px}
.form-group input,.form-group select{width:100%;padding:10px 12px;border-radius:6px;border:1px solid var(--gray-800);background:var(--black);color:var(--white);font-family:inherit;font-size:14px}
.form-group input:focus,.form-group select:focus{outline:none;border-color:var(--cyan)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.modal-btns{display:flex;gap:12px;margin-top:24px}
.modal-btns .btn{flex:1;justify-content:center}
.toast{position:fixed;bottom:100px;right:24px;padding:12px 20px;background:var(--gray-900);border:1px solid var(--success);color:var(--success);border-radius:8px;font-weight:500;font-size:13px;transform:translateY(100px);opacity:0;transition:all .3s;z-index:2000}
.toast.show{transform:translateY(0);opacity:1}
.toast.error{border-color:var(--danger);color:var(--danger)}
.page{display:none}
.page.active{display:block}
.agent-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:1px;background:var(--border);border-radius:8px;overflow:hidden}
.agent-card{background:var(--black);padding:20px;text-align:center;cursor:pointer;transition:all .2s}
.agent-card:hover{background:rgba(255,255,255,.03);transform:translateY(-2px)}
.agent-icon{font-size:32px;margin-bottom:8px}
.agent-name{font-size:14px;font-weight:600;margin-bottom:4px}
.agent-role{font-size:11px;color:var(--gray-500);text-transform:uppercase;letter-spacing:1px}
.appt-card{background:rgba(255,255,255,.02);border-radius:8px;padding:16px;border:1px solid var(--border);margin-bottom:12px}
.appt-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}
.appt-name{font-size:15px;font-weight:600}
.appt-phone{font-size:12px;color:var(--gray-500);margin-top:2px}
.appt-meta{display:flex;gap:12px;font-size:12px;color:var(--gray-300);margin-bottom:12px}
.appt-actions{display:flex;gap:8px}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:1px;background:var(--border);border-radius:8px;overflow:hidden}
.cal-header{background:var(--gray-900);padding:12px;text-align:center;font-size:11px;color:var(--gray-500);text-transform:uppercase;letter-spacing:1px;font-weight:600}
.cal-day{background:var(--black);min-height:80px;padding:8px;cursor:pointer;transition:all .2s}
.cal-day:hover{background:rgba(255,255,255,.02)}
.cal-day.today{border:1px solid var(--cyan)}
.cal-day.selected{background:rgba(0,209,255,.05);border:1px solid var(--cyan)}
.cal-day-num{font-size:13px;font-weight:600;margin-bottom:4px}
.cal-day.other{opacity:.3}
.cal-count{background:var(--cyan);color:var(--black);font-size:10px;padding:2px 6px;border-radius:4px;font-weight:600}
.assistant-bar{position:fixed;bottom:0;left:220px;right:0;background:var(--black);border-top:1px solid var(--border);padding:16px 32px;z-index:500}
.assistant-row{display:flex;gap:12px;align-items:center}
.assistant-label{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--gray-500)}
.assistant-dot{width:6px;height:6px;background:var(--cyan);border-radius:50%;animation:pulse-dot 2s infinite}
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.4}}
.assistant-input{flex:1;background:var(--gray-900);border:1px solid var(--gray-800);border-radius:6px;padding:10px 14px;color:var(--white);font-family:inherit;font-size:14px}
.assistant-input:focus{outline:none;border-color:var(--cyan)}
.assistant-btn{background:var(--white);color:var(--black);border:none;padding:10px 20px;border-radius:6px;font-weight:600;font-size:13px;cursor:pointer}
.assistant-btn:hover{background:var(--cyan)}
@media(max-width:1024px){.stats-grid{grid-template-columns:repeat(2,1fr)}.grid-2{grid-template-columns:1fr}}
@media(max-width:768px){.sidebar{transform:translateX(-100%)}.main{margin-left:0}.assistant-bar{left:0}}"""

    js = """const $=id=>document.getElementById(id);
const outbound=""" + out_json + """;
const inbound=""" + in_json + """;
const agents={...outbound,...inbound};
let curMonth=new Date();let selDate=null;let testPhone='';
async function init(){
const opts=Object.entries(outbound).map(([k,v])=>`<option value="${k}">${v.name} - ${v.industry}</option>`).join('');
const allOpts=Object.entries(agents).map(([k,v])=>`<option value="${k}">${v.name} - ${v.industry}</option>`).join('');
['l-agent','ap-agent'].forEach(id=>{if($(id))$(id).innerHTML=opts});
if($('test-agent-select'))$('test-agent-select').innerHTML=allOpts;
$('ap-date').value=new Date().toISOString().split('T')[0];$('ap-time').value='10:00';
const settings=await fetch('/api/settings').then(r=>r.json());
testPhone=settings.test_phone||'';
if($('test-phone'))$('test-phone').value=testPhone;
if($('app-mode'))$('app-mode').value=settings.mode||'testing';
}init();
document.querySelectorAll('.nav-item').forEach(n=>n.onclick=()=>{document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));n.classList.add('active');document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));$('page-'+n.dataset.page).classList.add('active');load(n.dataset.page)});
function load(p){if(p==='dashboard')loadDash();else if(p==='calendar')loadCal();else if(p==='appointments')loadAppts();else if(p==='dispositions')loadDispo();else if(p==='outbound')loadOut();else if(p==='inbound')loadIn();else if(p==='leads')loadLeads();else if(p==='calls')loadCalls();else if(p==='costs')loadCosts();else if(p==='testing')loadTesting();else if(p==='ads')loadAds();else if(p==='pipeline')loadPipeline();else if(p==='integrations')loadIntegrations();else if(p==='account')loadAccount()}
function openModal(id){$(id).classList.add('active')}function closeModal(id){$(id).classList.remove('active')}function toast(msg,err=false){$('toast').textContent=msg;$('toast').className='toast show'+(err?' error':'');setTimeout(()=>$('toast').classList.remove('show'),3000)}
function apptCard(a){const g=agents[a.agent_type]||{name:'Agent'};return `<div class="appt-card"><div class="appt-header"><div><div class="appt-name">${a.first_name||'Customer'}</div><div class="appt-phone">${a.phone||''}</div></div><span class="status status-${a.disposition||'scheduled'}">${a.disposition||'Scheduled'}</span></div><div class="appt-meta"><span>${a.appointment_date||'TBD'}</span><span>${a.appointment_time||''}</span><span>${g.name}</span></div><div class="appt-actions">${!a.disposition?`<button class="btn btn-sm btn-success" onclick="qDispo(${a.id},'sold')">Sold</button><button class="btn btn-sm btn-danger" onclick="qDispo(${a.id},'no-show')">No Show</button>`:''}<button class="btn btn-sm btn-secondary" onclick="editAppt(${a.id})">Edit</button></div></div>`}
async function loadDash(){const s=await fetch('/api/appointment-stats').then(r=>r.json());$('s-today').textContent=s.today||0;$('s-scheduled').textContent=s.scheduled||0;$('s-sold').textContent=s.sold||0;$('s-revenue').textContent='$'+(s.revenue||0).toLocaleString();const today=new Date().toISOString().split('T')[0];const a=await fetch('/api/appointments?date='+today).then(r=>r.json());$('today-list').innerHTML=a.length?a.map(x=>apptCard(x)).join(''):'<p style="color:var(--gray-500);text-align:center;padding:40px">No appointments today</p>'}
async function loadCal(){const y=curMonth.getFullYear(),m=curMonth.getMonth();$('cal-title').textContent=curMonth.toLocaleDateString('en-US',{month:'long',year:'numeric'});const data=await fetch(`/api/calendar?year=${y}&month=${m+1}`).then(r=>r.json());const first=new Date(y,m,1).getDay(),days=new Date(y,m+1,0).getDate(),today=new Date().toISOString().split('T')[0];let h='';for(let i=0;i<first;i++)h+='<div class="cal-day other"></div>';for(let d=1;d<=days;d++){const dt=`${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;const info=data[dt]||{count:0};h+=`<div class="cal-day${dt===today?' today':''}${dt===selDate?' selected':''}" onclick="selDay('${dt}')"><div class="cal-day-num">${d}</div>${info.count?`<span class="cal-count">${info.count}</span>`:''}</div>`}$('cal-days').innerHTML=h;if(selDate)loadDay(selDate)}
function chgMonth(d){curMonth.setMonth(curMonth.getMonth()+d);loadCal()}async function selDay(dt){selDate=dt;loadCal();loadDay(dt)}
async function loadDay(dt){$('day-title').textContent=new Date(dt+'T12:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});const a=await fetch('/api/appointments?date='+dt).then(r=>r.json());$('day-list').innerHTML=a.length?a.map(x=>apptCard(x)).join(''):'<p style="color:var(--gray-500);text-align:center;padding:40px">No appointments</p>'}
async function loadAppts(){const s=await fetch('/api/appointment-stats').then(r=>r.json());const a=await fetch('/api/appointments').then(r=>r.json());$('a-total').textContent=s.total||0;$('a-sched').textContent=s.scheduled||0;$('a-pend').textContent=s.pending_disposition||0;$('a-sold').textContent=s.sold||0;$('appt-list').innerHTML=a.length?a.map(x=>apptCard(x)).join(''):'<p style="color:var(--gray-500);text-align:center;padding:40px">No appointments</p>'}
async function saveAppt(){const d={first_name:$('ap-fn').value,phone:$('ap-ph').value,address:$('ap-addr').value,date:$('ap-date').value,time:$('ap-time').value,agent_type:$('ap-agent').value};if(!d.phone||!d.date){toast('Phone and date required',true);return}await fetch('/api/appointment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});closeModal('appt-modal');toast('Appointment created');loadDash();if(selDate)loadCal()}
function editAppt(id){fetch('/api/appointments').then(r=>r.json()).then(a=>{const x=a.find(z=>z.id===id);if(!x)return;$('ed-id').value=id;$('ed-date').value=x.appointment_date||'';$('ed-time').value=x.appointment_time||'';openModal('edit-modal')})}
async function updateAppt(){await fetch('/api/appointment/'+$('ed-id').value,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({appointment_date:$('ed-date').value,appointment_time:$('ed-time').value})});closeModal('edit-modal');toast('Updated');loadDash();if(selDate)loadCal()}
async function loadDispo(){const a=await fetch('/api/appointments').then(r=>r.json());const p=a.filter(x=>!x.disposition);const s=a.filter(x=>x.disposition==='sold');const n=a.filter(x=>x.disposition==='no-show');const r=s.reduce((t,x)=>t+(x.sale_amount||0),0);$('pend-badge').textContent=p.length+' Pending';$('d-sold').textContent=s.length;$('d-noshow').textContent=n.length;$('d-rate').textContent=a.length?Math.round(s.length/a.length*100)+'%':'0%';$('d-rev').textContent='$'+r.toLocaleString();$('pend-list').innerHTML=p.length?p.map(x=>`<div class="appt-card"><div class="appt-header"><div><div class="appt-name">${x.first_name||'Customer'}</div><div class="appt-phone">${x.phone}</div></div></div><div class="appt-meta"><span>${x.appointment_date||'TBD'}</span><span>${x.appointment_time||''}</span></div><div class="appt-actions" style="margin-top:12px"><button class="btn btn-sm btn-success" style="flex:1" onclick="qDispo(${x.id},'sold')">Sold</button><button class="btn btn-sm btn-danger" style="flex:1" onclick="qDispo(${x.id},'no-show')">No Show</button></div></div>`).join(''):'<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--gray-500)">All caught up!</div>'}
async function qDispo(id,st){await fetch('/api/disposition',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({appt_id:id,disposition:st})});toast('Saved');loadDispo();loadDash()}
function loadOut(){$('out-grid').innerHTML=Object.entries(outbound).map(([k,v])=>`<div class="agent-card" onclick="openTestModal('${k}')" style="border-top:3px solid ${v.color}"><div class="agent-icon">${v.icon}</div><div class="agent-name">${v.name}</div><div class="agent-role">${v.industry}</div></div>`).join('')}
function loadIn(){$('in-grid').innerHTML=Object.entries(inbound).map(([k,v])=>`<div class="agent-card" onclick="openTestModal('${k}')" style="border-top:3px solid ${v.color}"><div class="agent-icon">${v.icon}</div><div class="agent-name">${v.name}</div><div class="agent-role">${v.industry}</div></div>`).join('')}
function openTestModal(agentType){$('test-agent-type').value=agentType;$('test-modal-title').textContent='Test '+agents[agentType].name;openModal('test-modal')}
async function runTest(isLive){const agent=$('test-agent-type').value;const phone=$('test-phone-input').value||testPhone;if(!phone){toast('Enter a phone number',true);return}closeModal('test-modal');toast('Calling '+phone+'...');const r=await fetch('/api/test-agent-phone',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_type:agent,phone:phone,is_live:isLive})}).then(r=>r.json());if(r.success)toast('Call initiated!');else toast('Error: '+r.error,true)}
async function testAgent(t){openTestModal(t)}
async function loadLeads(){const l=await fetch('/api/leads').then(r=>r.json());$('leads-tb').innerHTML=l.map(x=>`<tr><td>${x.first_name||'Unknown'}</td><td>${x.phone}</td><td>${agents[x.agent_type]?.name||'?'}</td><td><span class="status status-${x.pipeline_stage||x.status}">${x.pipeline_stage||x.status}</span></td></tr>`).join('')}
async function loadCalls(){const c=await fetch('/api/calls').then(r=>r.json());$('calls-tb').innerHTML=c.map(x=>`<tr><td style="font-size:12px">${new Date(x.created_at).toLocaleString()}</td><td>${x.phone}</td><td>${agents[x.agent_type]?.name||'?'}</td><td>${x.is_inbound?'Inbound':'Outbound'}</td><td><span class="status ${x.is_live?'status-sold':'status-scheduled'}">${x.is_live?'Live':'Test'}</span></td></tr>`).join('')}
async function loadCosts(){const c=await fetch('/api/live-costs').then(r=>r.json());$('c-today').textContent='$'+c.today.total.toFixed(2);$('c-month').textContent='$'+c.month.total.toFixed(2);$('c-calls').textContent=c.today.calls;$('c-sms').textContent='$'+c.today.sms.toFixed(3)}
async function saveLead(){const p=$('l-phone').value;if(!p){toast('Phone required',true);return}await fetch('/api/start-cycle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:p,name:$('l-name').value||'there',agent_type:$('l-agent').value})});closeModal('lead-modal');toast('Lead cycle started');loadDash()}
async function loadTesting(){
const settings=await fetch('/api/settings').then(r=>r.json());
$('cfg-test-phone').value=settings.test_phone||'';
$('cfg-mode').value=settings.mode||'testing';
const allOpts=Object.entries(agents).map(([k,v])=>`<div class="agent-card" onclick="openTestModal('${k}')" style="border-top:3px solid ${v.color||'#00D1FF'}"><div class="agent-icon">${v.icon||'🤖'}</div><div class="agent-name">${v.name}</div><div class="agent-role">${v.industry}</div></div>`).join('');
$('all-agents-grid').innerHTML=allOpts;
}
async function saveTestPhone(){const p=$('cfg-test-phone').value;await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({test_phone:p})});testPhone=p;toast('Test phone saved!')}
async function saveMode(){const m=$('cfg-mode').value;await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:m})});toast('Mode set to '+m)}
async function loadAds(){const stats=await fetch('/api/ad-stats').then(r=>r.json());const campaigns=await fetch('/api/ad-campaigns').then(r=>r.json());
$('ad-spend-today').textContent='$'+stats.today.spend.toFixed(2);
$('ad-leads-today').textContent=stats.today.leads;
$('ad-cpl-today').textContent='$'+stats.today.cpl.toFixed(2);
$('ad-appts-today').textContent=stats.today.appointments;
$('ad-spend-month').textContent='$'+stats.month.spend.toFixed(2);
$('ad-leads-month').textContent=stats.month.leads;
$('ad-cpl-month').textContent='$'+stats.month.cpl.toFixed(2);
$('ad-roas-month').textContent=stats.month.roas.toFixed(1)+'x';
$('campaigns-list').innerHTML=campaigns.length?campaigns.map(c=>`<tr><td>${c.campaign_name}</td><td>${c.platform}</td><td>$${c.daily_budget}</td><td>$${c.total_spend.toFixed(2)}</td><td>${c.leads}</td><td>${c.appointments}</td><td><span class="status status-${c.status==='active'?'sold':'scheduled'}">${c.status}</span></td></tr>`).join(''):'<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--gray-500)">No campaigns yet. Add your Facebook/Instagram campaigns.</td></tr>';
}
async function addCampaign(){const name=$('camp-name').value;const budget=$('camp-budget').value;const platform=$('camp-platform').value;if(!name){toast('Campaign name required',true);return}await fetch('/api/ad-campaigns',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({campaign_name:name,daily_budget:budget,platform:platform})});closeModal('campaign-modal');toast('Campaign added');loadAds()}
async function loadPipeline(){const stats=await fetch('/api/pipeline-stats').then(r=>r.json());const stages=await fetch('/api/pipeline-stages').then(r=>r.json());
let html='';stages.forEach(s=>{const st=stats[s.stage_key]||{total:0};html+=`<div class="pipeline-stage" style="border-left:3px solid ${s.stage_color}"><div class="stage-name">${s.stage_name}</div><div class="stage-count">${st.total}</div></div>`});
$('pipeline-board').innerHTML=html;
}
async function sendAria(){const msg=$('aria-input').value.trim();if(!msg)return;$('aria-input').value='';toast('Processing...');const r=await fetch('/api/aria',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})}).then(r=>r.json());if(r.response){showAriaResponse(r.response)}loadDash()}
function showAriaResponse(msg){const panel=$('aria-response');if(!panel){const d=document.createElement('div');d.id='aria-response';d.style.cssText='position:fixed;bottom:70px;right:32px;max-width:400px;background:var(--gray-900);border:1px solid var(--cyan);border-radius:12px;padding:16px;z-index:600;box-shadow:0 4px 20px rgba(0,209,255,0.2)';d.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px"><div style="display:flex;align-items:center;gap:8px"><div style="width:8px;height:8px;background:var(--cyan);border-radius:50%"></div><span style="font-weight:600;font-size:13px">Aria</span></div><button onclick="this.parentElement.parentElement.remove()" style="background:none;border:none;color:var(--gray-500);cursor:pointer;font-size:16px">×</button></div><div style="font-size:14px;line-height:1.6;color:var(--white)">'+msg.replace(/\\n/g,'<br>')+'</div>';document.body.appendChild(d);setTimeout(()=>{if($('aria-response'))$('aria-response').remove()},15000)}else{panel.querySelector('div:last-child').innerHTML=msg.replace(/\\n/g,'<br>')}}
// Integrations
async function loadIntegrations(){
const ints=await fetch('/api/integrations').then(r=>r.json()).catch(()=>[]);
ints.forEach(i=>{
const el=$(`${i.integration_type}-status`);
if(el)el.className='status status-'+(i.is_connected?'sold':'scheduled');
if(el)el.textContent=i.is_connected?'Connected':'Not Connected';
});
loadZapierWebhooks();
}
async function saveIntegration(type){
const data={};
if(type==='vapi'){data.api_key=$('int-vapi-key').value;data.account_id=$('int-vapi-phone').value}
else if(type==='twilio'){data.api_key=$('int-twilio-sid').value;data.api_secret=$('int-twilio-token').value;data.account_id=$('int-twilio-phone').value}
else if(type==='openai'){data.api_key=$('int-openai-key').value}
else if(type==='stripe'){data.api_key=$('int-stripe-key').value;data.api_secret=$('int-stripe-webhook').value}
const r=await fetch('/api/integrations/'+type,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).then(r=>r.json());
if(r.success){toast('✅ Saved! Testing connection...');const test=await fetch('/api/integrations/'+type+'/test',{method:'POST'}).then(r=>r.json());if(test.success)toast('✅ Connected successfully!');else toast('⚠️ Saved but connection test failed',true)}else toast('Error saving',true);loadIntegrations();
}
function connectOAuth(type){toast('OAuth coming soon - save credentials manually for now')}
async function loadZapierWebhooks(){
const wh=await fetch('/api/zapier-webhooks').then(r=>r.json()).catch(()=>[]);
$('zapier-webhooks').innerHTML=wh.length?wh.map(w=>`<div style="display:flex;justify-content:space-between;align-items:center;padding:8px;background:var(--gray-900);border-radius:6px;margin-bottom:8px"><div><div style="font-weight:600;font-size:13px">${w.webhook_name||'Webhook'}</div><div style="font-size:11px;color:var(--gray-500)">${w.trigger_event} • ${w.trigger_count||0} triggers</div></div><button class="btn btn-sm btn-danger" onclick="deleteWebhook(${w.id})">×</button></div>`).join(''):'<p style="color:var(--gray-500);font-size:12px">No webhooks configured</p>';
}
async function saveZapierWebhook(){
const url=$('int-zapier-url').value;const event=$('int-zapier-event').value;
if(!url){toast('Enter webhook URL',true);return}
await fetch('/api/zapier-webhooks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({webhook_url:url,trigger_event:event,webhook_name:event+' webhook'})});
$('int-zapier-url').value='';toast('Webhook added!');loadZapierWebhooks();
}
async function deleteWebhook(id){await fetch('/api/zapier-webhooks/'+id,{method:'DELETE'});loadZapierWebhooks()}
// Account
async function loadAccount(){
const user=await fetch('/api/me').then(r=>r.json()).catch(()=>({}));
if(user.id){$('acc-name').value=user.name||'';$('acc-email').value=user.email||'';$('acc-company').value=user.company||'';$('acc-phone').value=user.phone||''}
loadApiKeys();
}
async function saveProfile(){
const data={name:$('acc-name').value,company:$('acc-company').value,phone:$('acc-phone').value};
await fetch('/api/profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
toast('Profile saved!');
}
async function changePassword(){
const current=$('acc-current-pw').value;const newPw=$('acc-new-pw').value;const confirm=$('acc-confirm-pw').value;
if(newPw!==confirm){toast('Passwords do not match',true);return}
if(newPw.length<8){toast('Password must be at least 8 characters',true);return}
const r=await fetch('/api/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:current,new_password:newPw})}).then(r=>r.json());
if(r.success){toast('Password changed!');$('acc-current-pw').value='';$('acc-new-pw').value='';$('acc-confirm-pw').value=''}else toast(r.error||'Error',true);
}
async function loadApiKeys(){
const keys=await fetch('/api/api-keys').then(r=>r.json()).catch(()=>[]);
$('api-keys-list').innerHTML=keys.length?keys.map(k=>`<div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--gray-900);border-radius:6px;margin-bottom:8px"><div><div style="font-weight:600;font-size:13px">${k.key_name||'API Key'}</div><code style="font-size:11px;color:var(--cyan)">${k.api_key?.substring(0,20)}...</code></div><button class="btn btn-sm btn-danger" onclick="deleteApiKey(${k.id})">Revoke</button></div>`).join(''):'<p style="color:var(--gray-500)">No API keys yet</p>';
}
async function generateApiKey(){
const name=prompt('API Key Name:');if(!name)return;
const r=await fetch('/api/api-keys',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key_name:name})}).then(r=>r.json());
if(r.api_key){alert('Your new API key (copy now, shown once):\\n\\n'+r.api_key);loadApiKeys()}
}
async function deleteApiKey(id){if(!confirm('Revoke this API key?'))return;await fetch('/api/api-keys/'+id,{method:'DELETE'});loadApiKeys()}
// Auth
function showLogin(){closeModal('signup-modal');openModal('login-modal')}
function showSignup(){closeModal('login-modal');openModal('signup-modal')}
async function doLogin(){
const email=$('login-email').value;const pw=$('login-pw').value;
if(!email||!pw){toast('Enter email and password',true);return}
const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email,password:pw})}).then(r=>r.json());
if(r.success){closeModal('login-modal');toast('Welcome back, '+r.user.name+'!');localStorage.setItem('session',r.session_token);location.reload()}else toast(r.error||'Login failed',true);
}
async function doSignup(){
const name=$('signup-name').value;const company=$('signup-company').value;const email=$('signup-email').value;const pw=$('signup-pw').value;
if(!email||!pw){toast('Enter email and password',true);return}
if(pw.length<8){toast('Password must be 8+ characters',true);return}
const r=await fetch('/api/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name,company:company,email:email,password:pw})}).then(r=>r.json());
if(r.success){closeModal('signup-modal');toast('Account created! Please log in.');showLogin()}else toast(r.error||'Signup failed',true);
}
async function logout(){localStorage.removeItem('session');location.reload()}
loadDash();"""

    html_body = """<div class="sidebar">
<a href="#" class="logo">
<svg class="pulse-loop" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><circle cx="256" cy="256" r="180" stroke="#00D1FF" stroke-width="24" fill="none" stroke-linecap="round" stroke-dasharray="900 200"/></svg>
<span class="logo-text">VOICE</span>
</a>
<nav>
<div class="nav-section">Main</div>
<div class="nav-item active" data-page="dashboard">📊 Dashboard</div>
<div class="nav-item" data-page="calendar">📅 Calendar</div>
<div class="nav-item" data-page="appointments">🎯 Appointments</div>
<div class="nav-item" data-page="dispositions">✅ Dispositions</div>
<div class="nav-item" data-page="pipeline">🔄 Pipeline</div>
<div class="nav-section">Testing</div>
<div class="nav-item" data-page="testing">🧪 Test Lab</div>
<div class="nav-item" data-page="outbound">📤 Outbound <span class="nav-badge">12</span></div>
<div class="nav-item" data-page="inbound">📥 Inbound <span class="nav-badge">15</span></div>
<div class="nav-section">Marketing</div>
<div class="nav-item" data-page="ads">📱 FB/IG Ads</div>
<div class="nav-item" data-page="leads">👥 Leads</div>
<div class="nav-section">Data</div>
<div class="nav-item" data-page="calls">📞 Calls</div>
<div class="nav-item" data-page="costs">💰 Costs</div>
<div class="nav-section">Settings</div>
<div class="nav-item" data-page="integrations">🔌 Integrations</div>
<div class="nav-item" data-page="account">👤 Account</div>
</nav>
</div>
<div class="main">
<div class="page active" id="page-dashboard">
<div class="header"><div><h1>📊 Dashboard</h1><div class="header-sub">VOICE booked 47 appointments today.</div></div><div style="display:flex;gap:12px"><button class="btn btn-secondary" onclick="openModal('appt-modal')">+ Appointment</button><button class="btn btn-primary" onclick="openModal('lead-modal')">+ Lead</button></div></div>
<div class="stats-grid"><div class="stat cyan"><div class="stat-value" id="s-today">0</div><div class="stat-label">Today</div></div><div class="stat"><div class="stat-value" id="s-scheduled">0</div><div class="stat-label">Scheduled</div></div><div class="stat green"><div class="stat-value" id="s-sold">0</div><div class="stat-label">Sold</div></div><div class="stat orange"><div class="stat-value" id="s-revenue">$0</div><div class="stat-label">Revenue</div></div></div>
<div class="grid-2"><div class="card"><div class="card-header"><h2>Today's Appointments</h2></div><div id="today-list" style="padding:16px;max-height:400px;overflow-y:auto"></div></div><div class="card"><div class="card-header"><h2>Agent Performance</h2></div><div style="padding:16px"><div class="stats-grid" style="margin-bottom:0"><div class="stat"><div class="stat-value">12</div><div class="stat-label">Outbound</div></div><div class="stat"><div class="stat-value">15</div><div class="stat-label">Inbound</div></div></div></div></div></div>
</div>
<div class="page" id="page-calendar">
<div class="header"><h1>📅 Calendar</h1><div style="display:flex;gap:12px;align-items:center"><button class="btn btn-secondary btn-sm" onclick="chgMonth(-1)">← Prev</button><span id="cal-title" style="min-width:140px;text-align:center;font-weight:600"></span><button class="btn btn-secondary btn-sm" onclick="chgMonth(1)">Next →</button></div></div>
<div class="grid-2"><div class="card" style="padding:16px"><div class="cal-grid"><div class="cal-header">Sun</div><div class="cal-header">Mon</div><div class="cal-header">Tue</div><div class="cal-header">Wed</div><div class="cal-header">Thu</div><div class="cal-header">Fri</div><div class="cal-header">Sat</div></div><div class="cal-grid" id="cal-days" style="margin-top:1px"></div></div><div class="card"><div class="card-header"><h2 id="day-title">Select a Day</h2><button class="btn btn-sm btn-primary" onclick="openModal('appt-modal')">Add</button></div><div id="day-list" style="padding:16px;max-height:500px;overflow-y:auto"></div></div></div>
</div>
<div class="page" id="page-appointments"><div class="header"><h1>🎯 Appointments</h1><button class="btn btn-primary" onclick="openModal('appt-modal')">+ Appointment</button></div><div class="stats-grid"><div class="stat"><div class="stat-value" id="a-total">0</div><div class="stat-label">Total</div></div><div class="stat cyan"><div class="stat-value" id="a-sched">0</div><div class="stat-label">Scheduled</div></div><div class="stat orange"><div class="stat-value" id="a-pend">0</div><div class="stat-label">Pending</div></div><div class="stat green"><div class="stat-value" id="a-sold">0</div><div class="stat-label">Sold</div></div></div><div class="card"><div id="appt-list" style="padding:16px;max-height:600px;overflow-y:auto"></div></div></div>
<div class="page" id="page-dispositions"><div class="header"><h1>✅ Dispositions</h1><span id="pend-badge" class="status status-scheduled" style="font-size:14px;padding:6px 12px">0 Pending</span></div><div class="stats-grid"><div class="stat green"><div class="stat-value" id="d-sold">0</div><div class="stat-label">Sold</div></div><div class="stat"><div class="stat-value" id="d-noshow">0</div><div class="stat-label">No Show</div></div><div class="stat cyan"><div class="stat-value" id="d-rate">0%</div><div class="stat-label">Close Rate</div></div><div class="stat orange"><div class="stat-value" id="d-rev">$0</div><div class="stat-label">Revenue</div></div></div><div class="card"><div class="card-header"><h2>Pending Dispositions</h2></div><div id="pend-list" style="padding:16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px"></div></div></div>
<div class="page" id="page-outbound"><div class="header"><div><h1>📤 Outbound Agents</h1><div class="header-sub">12 NEPQ-powered sales agents</div></div></div><div class="card" style="padding:16px"><div class="agent-grid" id="out-grid"></div></div></div>
<div class="page" id="page-inbound"><div class="header"><div><h1>📥 Inbound Agents</h1><div class="header-sub">15 front desk receptionists</div></div></div><div class="card" style="padding:16px"><div class="agent-grid" id="in-grid"></div></div></div>
<div class="page" id="page-leads">
<div class="header"><div><h1>👥 Leads</h1><div class="header-sub">Full lead tracking with call history</div></div><div style="display:flex;gap:12px"><button class="btn btn-secondary" onclick="openModal('import-modal')">📤 Import CSV</button><button class="btn btn-primary" onclick="openModal('lead-modal')">+ Add Lead</button></div></div>
<div class="stats-grid"><div class="stat cyan"><div class="stat-value" id="ld-total">0</div><div class="stat-label">Total Leads</div></div><div class="stat green"><div class="stat-value" id="ld-contacted">0</div><div class="stat-label">Contacted</div></div><div class="stat orange"><div class="stat-value" id="ld-appts">0</div><div class="stat-label">Appointments</div></div><div class="stat"><div class="stat-value" id="ld-rate">0%</div><div class="stat-label">Answer Rate</div></div></div>
<div class="card"><div class="card-header"><h2>All Leads</h2><div style="display:flex;gap:8px"><select id="lead-filter" onchange="loadLeads()" style="padding:6px 10px;border-radius:4px;background:var(--gray-900);border:1px solid var(--gray-800);color:var(--white);font-size:12px"><option value="all">All Stages</option><option value="new_lead">🆕 New</option><option value="contacted">📞 Contacted</option><option value="no_answer">📵 No Answer</option><option value="appointment_set">📅 Appt Set</option><option value="sold">💰 Sold</option></select></div></div>
<div style="overflow-x:auto"><table><thead><tr><th>Lead</th><th>Phone</th><th>Source</th><th>Calls</th><th>Last Outcome</th><th>Stage</th><th>Actions</th></tr></thead><tbody id="leads-tb"></tbody></table></div></div>
</div>
<div class="page" id="page-calls"><div class="header"><h1>📞 Calls</h1></div>
<div class="stats-grid"><div class="stat"><div class="stat-value" id="call-total">0</div><div class="stat-label">Total Calls</div></div><div class="stat green"><div class="stat-value" id="call-answered">0</div><div class="stat-label">Answered</div></div><div class="stat orange"><div class="stat-value" id="call-noanswer">0</div><div class="stat-label">No Answer</div></div><div class="stat cyan"><div class="stat-value" id="call-appts">0</div><div class="stat-label">Appts Booked</div></div></div>
<div class="card"><table><thead><tr><th>Time</th><th>Phone</th><th>Agent</th><th>Type</th><th>Outcome</th><th>Duration</th></tr></thead><tbody id="calls-tb"></tbody></table></div></div>
<div class="page" id="page-costs"><div class="header"><h1>💰 Costs</h1></div><div class="stats-grid"><div class="stat cyan"><div class="stat-value" id="c-today">$0</div><div class="stat-label">Today</div></div><div class="stat"><div class="stat-value" id="c-month">$0</div><div class="stat-label">This Month</div></div><div class="stat orange"><div class="stat-value" id="c-calls">0</div><div class="stat-label">Calls</div></div><div class="stat"><div class="stat-value" id="c-sms">$0</div><div class="stat-label">SMS</div></div></div></div>
<div class="page" id="page-testing">
<div class="header"><div><h1>🧪 Test Lab</h1><div class="header-sub">Configure test phone and test any agent</div></div></div>
<div class="card"><div class="card-header"><h2>Test Configuration</h2></div><div style="padding:20px">
<div class="grid-2">
<div class="form-group"><label>Default Test Phone</label><div style="display:flex;gap:8px"><input id="cfg-test-phone" placeholder="+17023240525" style="flex:1"><button class="btn btn-primary" onclick="saveTestPhone()">Save</button></div></div>
<div class="form-group"><label>Mode</label><div style="display:flex;gap:8px"><select id="cfg-mode" style="flex:1"><option value="testing">Testing Mode</option><option value="live">Live Mode</option></select><button class="btn btn-secondary" onclick="saveMode()">Set</button></div></div>
</div>
</div></div>
<div class="card"><div class="card-header"><h2>All Agents</h2><div class="header-sub">Click to test with custom phone</div></div><div style="padding:16px"><div class="agent-grid" id="all-agents-grid"></div></div></div>
</div>
<div class="page" id="page-ads">
<div class="header"><div><h1>📱 Facebook & Instagram Ads</h1><div class="header-sub">Track ad spend, CPL, CPA, and ROAS</div></div><button class="btn btn-primary" onclick="openModal('campaign-modal')">+ Campaign</button></div>
<div class="grid-2">
<div class="card"><div class="card-header"><h2>Today</h2></div><div style="padding:16px"><div class="stats-grid" style="grid-template-columns:repeat(2,1fr);margin:0"><div class="stat"><div class="stat-value" id="ad-spend-today">$0</div><div class="stat-label">Spend</div></div><div class="stat cyan"><div class="stat-value" id="ad-leads-today">0</div><div class="stat-label">Leads</div></div><div class="stat orange"><div class="stat-value" id="ad-cpl-today">$0</div><div class="stat-label">CPL</div></div><div class="stat green"><div class="stat-value" id="ad-appts-today">0</div><div class="stat-label">Appts</div></div></div></div></div>
<div class="card"><div class="card-header"><h2>This Month</h2></div><div style="padding:16px"><div class="stats-grid" style="grid-template-columns:repeat(2,1fr);margin:0"><div class="stat"><div class="stat-value" id="ad-spend-month">$0</div><div class="stat-label">Spend</div></div><div class="stat cyan"><div class="stat-value" id="ad-leads-month">0</div><div class="stat-label">Leads</div></div><div class="stat orange"><div class="stat-value" id="ad-cpl-month">$0</div><div class="stat-label">CPL</div></div><div class="stat green"><div class="stat-value" id="ad-roas-month">0x</div><div class="stat-label">ROAS</div></div></div></div></div>
</div>
<div class="card"><div class="card-header"><h2>Campaigns</h2></div><table><thead><tr><th>Name</th><th>Platform</th><th>Daily Budget</th><th>Total Spend</th><th>Leads</th><th>Appts</th><th>Status</th></tr></thead><tbody id="campaigns-list"></tbody></table></div>
</div>
<div class="page" id="page-pipeline">
<div class="header"><div><h1>🔄 Pipeline</h1><div class="header-sub">Visual lead journey with full tracking</div></div></div>
<div class="card" style="padding:20px"><div id="pipeline-board" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px"></div></div>
<div class="card"><div class="card-header"><h2>Leads by Stage</h2></div><div id="pipeline-leads" style="padding:16px"></div></div>
<style>.pipeline-stage{background:rgba(255,255,255,.02);border-radius:8px;padding:16px;text-align:center;cursor:pointer;transition:all .2s}.pipeline-stage:hover{background:rgba(255,255,255,.04)}.stage-icon{font-size:24px;margin-bottom:4px}.stage-name{font-size:10px;color:var(--gray-500);margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px}.stage-count{font-size:24px;font-weight:600}.lead-row{display:flex;align-items:center;justify-content:space-between;padding:12px;border-bottom:1px solid var(--border)}.lead-row:hover{background:rgba(255,255,255,.02)}.lead-info{display:flex;flex-direction:column;gap:2px}.lead-name{font-weight:600;font-size:14px}.lead-phone{font-size:12px;color:var(--gray-500)}.lead-stats{display:flex;gap:16px;font-size:12px;color:var(--gray-300)}.lead-stat{display:flex;align-items:center;gap:4px}</style>
</div>
<div class="page" id="page-integrations">
<div class="header"><div><h1>🔌 Integrations</h1><div class="header-sub">Connect your accounts and APIs</div></div></div>
<div class="grid-2">
<div class="card"><div class="card-header"><h2>🤖 VAPI (Voice AI)</h2><span class="status status-scheduled" id="vapi-status">Not Connected</span></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Connect your VAPI account to enable AI voice agents.</p>
<div class="form-group"><label>API Key</label><input id="int-vapi-key" type="password" placeholder="Enter VAPI API Key"></div>
<div class="form-group"><label>Phone ID</label><input id="int-vapi-phone" placeholder="Enter VAPI Phone ID"></div>
<button class="btn btn-primary" onclick="saveIntegration('vapi')">Save & Test Connection</button>
</div></div>
<div class="card"><div class="card-header"><h2>📱 Twilio (SMS/Voice)</h2><span class="status status-scheduled" id="twilio-status">Not Connected</span></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Connect Twilio for SMS confirmations and reminders.</p>
<div class="form-group"><label>Account SID</label><input id="int-twilio-sid" placeholder="ACxxxxxxxxxx"></div>
<div class="form-group"><label>Auth Token</label><input id="int-twilio-token" type="password" placeholder="Enter Auth Token"></div>
<div class="form-group"><label>Phone Number</label><input id="int-twilio-phone" placeholder="+17205551234"></div>
<button class="btn btn-primary" onclick="saveIntegration('twilio')">Save & Test Connection</button>
</div></div>
<div class="card"><div class="card-header"><h2>📅 Google Calendar</h2><span class="status status-scheduled" id="gcal-status">Not Connected</span></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Sync appointments to Google Calendar automatically.</p>
<div class="form-group"><label>Client ID</label><input id="int-gcal-id" placeholder="xxxxx.apps.googleusercontent.com"></div>
<div class="form-group"><label>Client Secret</label><input id="int-gcal-secret" type="password" placeholder="Enter Client Secret"></div>
<button class="btn btn-secondary" onclick="connectOAuth('google_calendar')">Connect with Google</button>
</div></div>
<div class="card"><div class="card-header"><h2>📧 Microsoft Outlook</h2><span class="status status-scheduled" id="outlook-status">Not Connected</span></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Sync appointments to Outlook Calendar.</p>
<div class="form-group"><label>Client ID</label><input id="int-outlook-id" placeholder="Enter Azure App Client ID"></div>
<div class="form-group"><label>Client Secret</label><input id="int-outlook-secret" type="password" placeholder="Enter Client Secret"></div>
<button class="btn btn-secondary" onclick="connectOAuth('outlook')">Connect with Microsoft</button>
</div></div>
<div class="card"><div class="card-header"><h2>⚡ Zapier</h2><span class="status status-scheduled" id="zapier-status">Not Connected</span></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Automate workflows with 5000+ apps.</p>
<div class="form-group"><label>Webhook URL</label><input id="int-zapier-url" placeholder="https://hooks.zapier.com/..."></div>
<div class="form-group"><label>Trigger Event</label><select id="int-zapier-event"><option value="new_lead">New Lead</option><option value="appointment_set">Appointment Set</option><option value="appointment_completed">Appointment Completed</option><option value="sold">Sale Closed</option></select></div>
<button class="btn btn-primary" onclick="saveZapierWebhook()">Add Webhook</button>
<div id="zapier-webhooks" style="margin-top:16px"></div>
</div></div>
<div class="card"><div class="card-header"><h2>📘 Facebook Ads</h2><span class="status status-scheduled" id="fb-status">Not Connected</span></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Import leads directly from Facebook Lead Forms.</p>
<div class="form-group"><label>Access Token</label><input id="int-fb-token" type="password" placeholder="Enter FB Access Token"></div>
<div class="form-group"><label>Ad Account ID</label><input id="int-fb-account" placeholder="act_123456789"></div>
<button class="btn btn-secondary" onclick="connectOAuth('facebook_ads')">Connect with Facebook</button>
</div></div>
<div class="card"><div class="card-header"><h2>🧠 OpenAI</h2><span class="status status-scheduled" id="openai-status">Not Connected</span></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Power Aria assistant with GPT-4.</p>
<div class="form-group"><label>API Key</label><input id="int-openai-key" type="password" placeholder="sk-..."></div>
<button class="btn btn-primary" onclick="saveIntegration('openai')">Save & Test Connection</button>
</div></div>
<div class="card"><div class="card-header"><h2>💳 Stripe</h2><span class="status status-scheduled" id="stripe-status">Not Connected</span></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Accept payments and track revenue.</p>
<div class="form-group"><label>API Key</label><input id="int-stripe-key" type="password" placeholder="sk_live_..."></div>
<div class="form-group"><label>Webhook Secret</label><input id="int-stripe-webhook" type="password" placeholder="whsec_..."></div>
<button class="btn btn-primary" onclick="saveIntegration('stripe')">Save Connection</button>
</div></div>
</div>
</div>
<div class="page" id="page-account">
<div class="header"><div><h1>👤 Account Settings</h1><div class="header-sub">Manage your profile and security</div></div></div>
<div class="grid-2">
<div class="card"><div class="card-header"><h2>Profile</h2></div><div style="padding:20px">
<div class="form-group"><label>Name</label><input id="acc-name" placeholder="Your Name"></div>
<div class="form-group"><label>Email</label><input id="acc-email" type="email" placeholder="you@company.com" disabled></div>
<div class="form-group"><label>Company</label><input id="acc-company" placeholder="Company Name"></div>
<div class="form-group"><label>Phone</label><input id="acc-phone" placeholder="+1 (555) 123-4567"></div>
<button class="btn btn-primary" onclick="saveProfile()">Save Changes</button>
</div></div>
<div class="card"><div class="card-header"><h2>Security</h2></div><div style="padding:20px">
<div class="form-group"><label>Current Password</label><input id="acc-current-pw" type="password"></div>
<div class="form-group"><label>New Password</label><input id="acc-new-pw" type="password"></div>
<div class="form-group"><label>Confirm New Password</label><input id="acc-confirm-pw" type="password"></div>
<button class="btn btn-secondary" onclick="changePassword()">Change Password</button>
</div></div>
<div class="card"><div class="card-header"><h2>API Keys</h2><button class="btn btn-sm btn-primary" onclick="generateApiKey()">Generate New Key</button></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">Use API keys to integrate VOICE with external systems.</p>
<div id="api-keys-list"></div>
</div></div>
<div class="card"><div class="card-header"><h2>Danger Zone</h2></div><div style="padding:20px">
<p style="color:var(--gray-500);font-size:13px;margin-bottom:16px">These actions are irreversible.</p>
<button class="btn btn-danger" onclick="if(confirm('Are you sure?'))deleteAccount()">Delete Account</button>
</div></div>
</div>
</div>
</div>
<div class="modal-bg" id="appt-modal"><div class="modal"><h2>New Appointment</h2><div class="form-row"><div class="form-group"><label>Name</label><input id="ap-fn"></div><div class="form-group"><label>Phone</label><input id="ap-ph"></div></div><div class="form-group"><label>Address</label><input id="ap-addr"></div><div class="form-row"><div class="form-group"><label>Date</label><input type="date" id="ap-date"></div><div class="form-group"><label>Time</label><input type="time" id="ap-time"></div></div><div class="form-group"><label>Agent</label><select id="ap-agent"></select></div><div class="modal-btns"><button class="btn btn-secondary" onclick="closeModal('appt-modal')">Cancel</button><button class="btn btn-primary" onclick="saveAppt()">Create</button></div></div></div>
<div class="modal-bg" id="lead-modal"><div class="modal"><h2>➕ Add New Lead</h2><div class="form-row"><div class="form-group"><label>Phone *</label><input id="l-phone" placeholder="(702) 555-1234"></div><div class="form-group"><label>Name</label><input id="l-name" placeholder="John Smith"></div></div><div class="form-group"><label>Email</label><input id="l-email" placeholder="john@email.com"></div><div class="form-group"><label>Source</label><select id="l-source"><option value="manual">Manual Entry</option><option value="facebook">Facebook Ad</option><option value="instagram">Instagram Ad</option><option value="google">Google Ad</option><option value="referral">Referral</option><option value="website">Website</option></select></div><div class="form-group"><label>Agent</label><select id="l-agent"></select></div><div class="modal-btns"><button class="btn btn-secondary" onclick="closeModal('lead-modal')">Cancel</button><button class="btn btn-primary" onclick="saveLead()">Add & Start Cycle</button></div></div></div>
<div class="modal-bg" id="edit-modal"><div class="modal"><h2>Edit Appointment</h2><input type="hidden" id="ed-id"><div class="form-row"><div class="form-group"><label>Date</label><input type="date" id="ed-date"></div><div class="form-group"><label>Time</label><input type="time" id="ed-time"></div></div><div class="modal-btns"><button class="btn btn-secondary" onclick="closeModal('edit-modal')">Cancel</button><button class="btn btn-primary" onclick="updateAppt()">Update</button></div></div></div>
<div class="modal-bg" id="test-modal"><div class="modal"><h2 id="test-modal-title">Test Agent</h2><input type="hidden" id="test-agent-type"><div class="form-group"><label>Phone Number to Call</label><input id="test-phone-input" placeholder="Enter phone number"></div><div class="modal-btns"><button class="btn btn-secondary" onclick="closeModal('test-modal')">Cancel</button><button class="btn btn-secondary" onclick="runTest(false)">🧪 Test Call</button><button class="btn btn-primary" onclick="runTest(true)">🔴 Live Call</button></div></div></div>
<div class="modal-bg" id="campaign-modal"><div class="modal"><h2>Add Campaign</h2><div class="form-group"><label>Campaign Name</label><input id="camp-name" placeholder="Summer Roofing Leads"></div><div class="form-row"><div class="form-group"><label>Platform</label><select id="camp-platform"><option value="facebook">Facebook</option><option value="instagram">Instagram</option><option value="google">Google</option></select></div><div class="form-group"><label>Daily Budget</label><input id="camp-budget" type="number" placeholder="50"></div></div><div class="modal-btns"><button class="btn btn-secondary" onclick="closeModal('campaign-modal')">Cancel</button><button class="btn btn-primary" onclick="addCampaign()">Add Campaign</button></div></div></div>
<div class="modal-bg" id="import-modal"><div class="modal"><h2>📤 Import Leads from CSV</h2><div class="form-group"><label>CSV File</label><input type="file" id="csv-file" accept=".csv" style="padding:10px;background:var(--gray-900);border:1px dashed var(--gray-800);border-radius:8px;width:100%"></div><div class="form-group"><label>Source</label><select id="import-source"><option value="csv">CSV Import</option><option value="facebook">Facebook Leads</option><option value="instagram">Instagram Leads</option></select></div><div class="form-group"><label>Default Agent</label><select id="import-agent"></select></div><p style="font-size:12px;color:var(--gray-500);margin-top:12px">CSV should have columns: phone, first_name, last_name, email, address, city, state, zip</p><div class="modal-btns"><button class="btn btn-secondary" onclick="closeModal('import-modal')">Cancel</button><button class="btn btn-primary" onclick="importCSV()">Import Leads</button></div></div></div>
<div class="modal-bg" id="lead-detail-modal"><div class="modal" style="max-width:600px"><h2 id="lead-detail-title">Lead Details</h2><div id="lead-detail-content"></div><div class="modal-btns"><button class="btn btn-secondary" onclick="closeModal('lead-detail-modal')">Close</button><button class="btn btn-primary" onclick="callLead()">📞 Call Now</button></div></div></div>
<div class="modal-bg" id="login-modal"><div class="modal" style="max-width:400px"><div style="text-align:center;margin-bottom:24px"><svg class="pulse-loop" viewBox="0 0 512 512" style="width:48px;height:48px" xmlns="http://www.w3.org/2000/svg"><circle cx="256" cy="256" r="180" stroke="#00D1FF" stroke-width="24" fill="none" stroke-linecap="round" stroke-dasharray="900 200"/></svg><h2 style="margin-top:12px">Welcome to VOICE</h2></div><div class="form-group"><label>Email</label><input id="login-email" type="email" placeholder="you@company.com"></div><div class="form-group"><label>Password</label><input id="login-pw" type="password" placeholder="••••••••"></div><div class="modal-btns" style="flex-direction:column;gap:8px"><button class="btn btn-primary" style="width:100%" onclick="doLogin()">Sign In</button><button class="btn btn-secondary" style="width:100%" onclick="showSignup()">Create Account</button></div></div></div>
<div class="modal-bg" id="signup-modal"><div class="modal" style="max-width:400px"><h2 style="text-align:center;margin-bottom:24px">Create Your Account</h2><div class="form-group"><label>Name</label><input id="signup-name" placeholder="Your Name"></div><div class="form-group"><label>Company</label><input id="signup-company" placeholder="Company Name"></div><div class="form-group"><label>Email</label><input id="signup-email" type="email" placeholder="you@company.com"></div><div class="form-group"><label>Password</label><input id="signup-pw" type="password" placeholder="Min 8 characters"></div><div class="modal-btns" style="flex-direction:column;gap:8px"><button class="btn btn-primary" style="width:100%" onclick="doSignup()">Create Account</button><button class="btn btn-secondary" style="width:100%" onclick="showLogin()">Already have an account?</button></div></div></div>
<div class="assistant-bar"><div class="assistant-row"><div class="assistant-label"><div class="assistant-dot"></div><span>Aria</span></div><input class="assistant-input" id="aria-input" placeholder="Ask Aria anything..." onkeydown="if(event.key==='Enter')sendAria()"><button class="assistant-btn" onclick="sendAria()">Send</button></div></div>
<div class="toast" id="toast"></div>"""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VOICE</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><circle cx='256' cy='256' r='180' stroke='%2300D1FF' stroke-width='24' fill='none' stroke-linecap='round' stroke-dasharray='900 200'/></svg>">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
{html_body}
<script>{js}</script>
</body>
</html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send_json(self, d):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(d, default=str).encode())
    def send_html(self, c):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(c.encode())
    def do_GET(self):
        p = urlparse(self.path)
        path = p.path
        q = parse_qs(p.query)
        if path == '/':
            self.send_html(get_landing_page())
        elif path in ['/app', '/dashboard']:
            self.send_html(get_html())
        elif path == '/api/leads':
            self.send_json(get_leads())
        elif path == '/api/appointments':
            f = {k: q[k][0] for k in ['date', 'status', 'month'] if k in q}
            self.send_json(get_appointments(f if f else None))
        elif path == '/api/appointments/upcoming':
            self.send_json(get_upcoming_appointments())
        elif path == '/api/appointment-stats':
            self.send_json(get_appointment_stats())
        elif path == '/api/calendar':
            self.send_json(get_calendar_data(int(q.get('year', ['2025'])[0]), int(q.get('month', ['1'])[0])))
        elif path == '/api/calls':
            self.send_json(get_calls())
        elif path == '/api/sms-logs':
            self.send_json(get_sms_logs())
        elif path == '/api/active-cycles':
            self.send_json(get_active_cycles())
        elif path == '/api/live-costs':
            self.send_json(get_live_costs())
        elif path == '/api/agent-stats':
            self.send_json(get_all_agent_stats())
        elif path == '/api/chat-history':
            self.send_json(get_chat_history())
        elif path == '/api/settings':
            self.send_json(get_settings())
        elif path == '/api/ad-campaigns':
            self.send_json(get_ad_campaigns())
        elif path == '/api/ad-stats':
            self.send_json(get_ad_stats_summary())
        elif path == '/api/pipeline-stages':
            self.send_json(get_pipeline_stages())
        elif path == '/api/pipeline-stats':
            self.send_json(get_pipeline_stats())
        elif path == '/api/leads-full':
            stage = q.get('stage', [None])[0]
            self.send_json(get_leads_with_status() if not stage else get_pipeline_leads(stage))
        elif path == '/api/pipeline-leads':
            self.send_json(get_pipeline_leads())
        elif path == '/api/call-outcomes':
            self.send_json(get_call_outcomes_summary())
        elif path.startswith('/api/lead-detail/'):
            lead_id = path.split('/')[-1]
            if lead_id.isdigit():
                self.send_json(get_lead_details(int(lead_id)) or {'error': 'Not found'})
            else:
                self.send_error(404)
        elif path.startswith('/api/lead-timeline/'):
            lead_id = path.split('/')[-1]
            if lead_id.isdigit():
                self.send_json(get_lead_timeline(int(lead_id)))
            else:
                self.send_error(404)
        # Integration GET routes
        elif path == '/api/integrations':
            self.send_json(get_user_integrations(1))  # TODO: Get user_id from session
        elif path == '/api/zapier-webhooks':
            self.send_json(get_zapier_webhooks(1))
        elif path == '/api/me':
            self.send_json(get_user_by_id(1) or {})  # TODO: Get from session
        elif path == '/api/api-keys':
            self.send_json([])  # TODO: Implement get_api_keys
        else:
            self.send_error(404)
    def do_POST(self):
        l = int(self.headers.get('Content-Length', 0))
        b = self.rfile.read(l).decode() if l > 0 else '{}'
        d = json.loads(b) if b else {}
        path = urlparse(self.path).path
        if path == '/api/appointment':
            self.send_json(create_appointment(d))
        elif path.startswith('/api/appointment/') and path.split('/')[-1].isdigit():
            self.send_json(update_appointment(int(path.split('/')[-1]), d))
        elif path == '/api/disposition':
            update_disposition(d.get('appt_id'), d.get('disposition', ''), d.get('notes', ''), d.get('sale_amount', 0))
            self.send_json({'success': True})
        elif path == '/api/test-agent':
            self.send_json(test_agent(d.get('agent_type', 'roofing'), d.get('phone'), d.get('spanish', False)))
        elif path == '/api/test-agent-phone':
            self.send_json(test_agent_with_phone(d.get('agent_type', 'roofing'), d.get('phone'), d.get('is_live', False)))
        elif path == '/api/start-cycle':
            self.send_json(start_lead_cycle(d.get('phone', ''), d.get('name', 'there'), 'manual', 1, d.get('agent_type', 'roofing')))
        elif path == '/api/aria':
            self.send_json(chat_with_aria(d.get('message', '')))
        elif path == '/api/settings':
            for key, value in d.items():
                update_setting(key, value)
            self.send_json({'success': True})
        elif path == '/api/ad-campaigns':
            self.send_json(create_ad_campaign(d))
        elif path == '/api/ad-daily-stats':
            self.send_json(log_ad_daily_stats(d.get('campaign_id'), d))
        elif path == '/api/pipeline-update':
            if d.get('type') == 'lead':
                self.send_json(update_lead_pipeline(d.get('id'), d.get('stage')))
            else:
                self.send_json(update_appointment_pipeline(d.get('id'), d.get('stage')))
        elif path == '/api/import-leads':
            result = import_leads_from_csv(d.get('leads', []), d.get('source', 'csv'), d.get('agent_type', 'roofing'), d.get('campaign'))
            self.send_json(result)
        elif path == '/api/move-lead':
            self.send_json(move_lead_to_stage(d.get('lead_id'), d.get('stage')))
        # Auth routes
        elif path == '/api/login':
            self.send_json(authenticate_user(d.get('email', ''), d.get('password', '')))
        elif path == '/api/signup':
            self.send_json(create_user(d.get('email', ''), d.get('password', ''), d.get('name', ''), d.get('company', ''), d.get('phone', '')))
        elif path == '/api/logout':
            # Get session from cookie or header
            self.send_json({"success": True})
        # Integration routes
        elif path.startswith('/api/integrations/') and '/test' in path:
            int_type = path.split('/')[3]
            self.send_json(test_integration(1, int_type))  # TODO: Get user_id from session
        elif path.startswith('/api/integrations/'):
            int_type = path.split('/')[-1]
            self.send_json(save_integration(1, int_type, d))  # TODO: Get user_id from session
        elif path == '/api/zapier-webhooks':
            self.send_json(create_zapier_webhook(1, d.get('webhook_name', ''), d.get('webhook_url', ''), d.get('trigger_event', '')))
        else:
            self.send_error(404)
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def main():
    init_db()
    print('''
    
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║                            V O I C E                              ║
    ║                                                                   ║
    ║                    AI That Closes Deals                           ║
    ║                                                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║   http://localhost:8080                                           ║
    ║                                                                   ║
    ║   12 Outbound Agents — NEPQ Sales Methodology                     ║
    ║   15 Inbound Agents — Front Desk Receptionists                    ║
    ║   Visual Calendar — Click to view/edit appointments               ║
    ║   AI Assistant Aria — Natural language control                    ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    ''')
    webbrowser.open('http://localhost:8080')
    HTTPServer(('', 8080), Handler).serve_forever()


if __name__ == '__main__':
    main()
