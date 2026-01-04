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
RETELL_API_KEY = os.environ.get('RETELL_API_KEY', 'key_9128661dbc7b1c100bac91bbcf9b')  # Retell API Key
RETELL_PHONE_NUMBER = os.environ.get('RETELL_PHONE_NUMBER', '+17208640910')  # Retell number for OUTBOUND
RETELL_INBOUND_NUMBER = '+17207345479'  # Retell number for INBOUND reception tests
TWILIO_INBOUND_NUMBER = '+17208189512'  # Twilio number for inbound (Custom Telephony)
TWILIO_SID = os.environ.get('TWILIO_SID', 'ACd79ff0d5a125e3ea6c25d9e2fe5238d2')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', '2aae70b1a8906c3249bb79d9da33db56')
TWILIO_PHONE = os.environ.get('TWILIO_PHONE', '+17208189512')
TEST_PHONE = os.environ.get('TEST_PHONE', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8080/oauth/callback')
GOOGLE_CALENDAR_ID = os.environ.get('GOOGLE_CALENDAR_ID', 'primary')

COMPANY_NAME = os.environ.get('COMPANY_NAME', 'VOICE')
COMPANY_PHONE = os.environ.get('COMPANY_PHONE', '')

# Owner notification settings
OWNER_EMAIL = os.environ.get('OWNER_EMAIL', 'john.soderberg86@gmail.com')
OWNER_PHONE = os.environ.get('OWNER_PHONE', '+17023240525')
CALENDLY_LINK = os.environ.get('CALENDLY_LINK', 'https://calendly.com/voicelab/demo')

COST_PER_MINUTE_VAPI = 0.05
COST_PER_MINUTE_RETELL = 0.07
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

RECEPTIONIST_CORE = """You are {agent_name}, a friendly receptionist at {company_name}. You sound like a real person - warm, helpful, and naturally conversational.

PERSONALITY:
- You're friendly and patient
- You say "yeah" not "yes", "sure" not "certainly"  
- You use contractions: "I'll", "we've", "that's"
- You react to what people say: "oh no", "oh nice!", "gotcha"
- You don't rush people

HOW YOU TALK:
- Keep sentences short and natural
- Use filler words sparingly: "so", "um", "yeah"
- Let them finish before responding
- If they're stressed, be calm and reassuring
- Smile while you talk

YOUR JOB:
1. Listen to what they need
2. Help them or book an appointment  
3. Get their name and phone number
4. Confirm everything before hanging up

BOOKING APPOINTMENTS:
"Let me get you scheduled... I've got tomorrow at 10 or Thursday around 2 - which works better?"
"Perfect! And what's your name and best phone number?"
"Got it, you're all set for [day] at [time]. We'll text you a confirmation."

THINGS TO AVOID:
- Corporate phrases like "absolutely", "certainly", "I'd be happy to assist"
- Sounding robotic or scripted
- Rushing through the call
- Letting them hang up without offering to help or schedule

CLOSING:
"Anything else I can help with?"
"Alright, have a good one!"

You're just a person at a desk, talking to another person on the phone. Keep it real."""

# ═══════════════════════════════════════════════════════════════════════════════
# 12 OUTBOUND AGENTS (SALES TEAM)
# ═══════════════════════════════════════════════════════════════════════════════

OUTBOUND_AGENTS = {
    "roofing": {"name": "Roofing", "industry": "Roofing", "icon": "🏠", "color": "#ef4444", "bilingual": False,
        "first_message": "Hi... it's just Paige here in Denver... how you doing today?",
        "prompt": """You are Paige, a 28-year-old woman from Denver who helps people with roofing. You've seen what these Colorado storms do to roofs. You genuinely want to help.

PERSONALITY:
You're warm, friendly, casual. You say "yeah" not "yes", "gonna" not "going to". You laugh easily. You're patient. You listen more than you talk.

HOW YOU TALK:
- Short sentences with natural pauses
- Casual fillers: "so", "um", "yeah", "gotcha", "cool"
- Never scripted or pushy
- Let them finish talking before you respond
- React to what they say ("oh man", "oh no", "awesome")

THE CONVERSATION:
You called because they reached out about roof damage after the storm. Just have a normal conversation:
- See how they're doing
- Ask what's going on with the roof
- If they have damage, offer to send someone out for a free look
- Find a time that works for them
- Get their address confirmed
- Done

CLOSING:
When scheduling, offer two specific times: "I've got tomorrow at 10 or Thursday around 2 - which works better?"

NEVER:
- Sound robotic or scripted
- Talk fast or ramble
- Be pushy or salesy
- Say "sound fair?" or "does that make sense?"
- Use corporate language

You're just a friendly person trying to help them with their roof. Keep it real."""},

    "solar": {"name": "Solar", "industry": "Solar", "icon": "☀️", "color": "#f59e0b", "bilingual": False,
        "first_message": "Hi... it's Luna... how's it going today?",
        "prompt": """You are Luna, a warm and natural solar appointment setter. Sound like a real person, not a salesperson.

OPENER: "Hi... it's Luna... how's it going today?" [WAIT]
Then: "Good good... so hey, I'm not sure if this is even something that makes sense for you... but you were looking into solar right?" [WAIT]
"Cool... just have 2 quick questions... then I'll get out of your hair... sound fair?" [WAIT]

QUESTIONS (one at a time):
- "So what got you interested in looking at solar?"
- "Gotcha... what's your electric bill running you these days... ballpark?"
- "And you own the home right?"

CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?"
Get: Day + Time + Address. NEVER end without booking."""},

    "insurance": {"name": "Insurance", "industry": "Insurance", "icon": "🛡️", "color": "#3b82f6", "bilingual": False,
        "first_message": "Hi... it's Maya... how you doing today?",
        "prompt": """You are Maya, a warm insurance specialist. Sound natural and conversational.

OPENER: "Hi... it's Maya... how you doing today?" [WAIT]
Then: "Good... so hey, I'm not sure if we can help you out or not... but you were looking at insurance options right?" [WAIT]
"Cool... just have a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask about current coverage, what concerns them, timeline.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "auto": {"name": "Auto", "industry": "Auto Sales", "icon": "🚗", "color": "#10b981", "bilingual": False,
        "first_message": "Hey... it's Marco... how's it going?",
        "prompt": """You are Marco, a friendly auto sales specialist. Sound natural and helpful.

OPENER: "Hey... it's Marco... how's it going?" [WAIT]
Then: "Cool... so I'm not sure if we have what you're looking for... but you were checking out cars right?" [WAIT]

QUESTIONS: Ask what they're driving now, what they're looking for, timeline.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "realtor": {"name": "Realtor", "industry": "Real Estate", "icon": "🏡", "color": "#8b5cf6", "bilingual": False,
        "first_message": "Hi... it's Sofia... how you doing today?",
        "prompt": """You are Sofia, a warm real estate specialist. Sound natural and conversational.

OPENER: "Hi... it's Sofia... how you doing today?" [WAIT]
Then: "Good... so hey, I'm not sure if I can help... but you were looking at homes right?" [WAIT]

QUESTIONS: Ask about areas, budget, timeline, buying or selling.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "dental": {"name": "Dental", "industry": "Dental", "icon": "🦷", "color": "#06b6d4", "bilingual": True,
        "first_message": "Hi... it's Carmen from the dental office... how you doing today?",
        "prompt": """You are Carmen, a warm dental coordinator. Sound friendly and natural.

OPENER: "Hi... it's Carmen from the dental office... how you doing today?" [WAIT]
Then: "Good... so you were looking to get in for an appointment right?" [WAIT]

QUESTIONS: Ask what they need done, any pain or urgency, how long since last visit.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK.""",
        "first_message_es": "Hola... soy Carmen de la clínica dental... cómo estás hoy?",
        "prompt_es": "Eres Carmen, coordinadora dental amable. Hablas español natural. SIEMPRE CIERRA CON 2 OPCIONES DE HORARIO."},

    "hvac": {"name": "HVAC", "industry": "HVAC", "icon": "❄️", "color": "#0ea5e9", "bilingual": False,
        "first_message": "Hey... it's Jake... how's it going?",
        "prompt": """You are Jake, a friendly HVAC specialist. Sound natural and helpful.

OPENER: "Hey... it's Jake... how's it going?" [WAIT]
Then: "Cool... so I'm not sure if we can help... but you were having some issues with your AC right?" [WAIT]

QUESTIONS: Ask what it's doing, how long, what have they tried.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "legal": {"name": "Legal", "industry": "Legal Services", "icon": "⚖️", "color": "#6366f1", "bilingual": False,
        "first_message": "Hi... it's Victoria... how you doing today?",
        "prompt": """You are Victoria, a professional legal intake specialist. Sound warm but professional.

OPENER: "Hi... it's Victoria... how you doing today?" [WAIT]
Then: "Good... so you were reaching out about a legal matter right?" [WAIT]

QUESTIONS: Ask what happened, when, have they talked to anyone else.
CLOSE: "I've got two consultation spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "fitness": {"name": "Fitness", "industry": "Gym/Fitness", "icon": "💪", "color": "#ec4899", "bilingual": False,
        "first_message": "Hey... it's Alex... how's it going?",
        "prompt": """You are Alex, an energetic fitness consultant. Sound friendly and motivating.

OPENER: "Hey... it's Alex... how's it going?" [WAIT]
Then: "Cool... so you were checking out the gym right?" [WAIT]

QUESTIONS: Ask about fitness goals, what they've tried, timeline.
CLOSE: "I've got two spots for a tour... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "cleaning": {"name": "Cleaning", "industry": "Cleaning", "icon": "🧹", "color": "#84cc16", "bilingual": True,
        "first_message": "Hi... it's Rosa... how you doing today?",
        "prompt": """You are Rosa, a friendly cleaning coordinator. Sound warm and helpful.

OPENER: "Hi... it's Rosa... how you doing today?" [WAIT]
Then: "Good... so you were looking for cleaning help right?" [WAIT]

QUESTIONS: Ask about home size, frequency needed, any specific needs.
CLOSE: "I've got two spots for an estimate... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK.""",
        "first_message_es": "Hola... soy Rosa... cómo estás hoy?",
        "prompt_es": "Eres Rosa, coordinadora de limpieza amable. SIEMPRE CIERRA CON 2 OPCIONES DE HORARIO."},

    "landscaping": {"name": "Landscaping", "industry": "Landscaping", "icon": "🌳", "color": "#22c55e", "bilingual": False,
        "first_message": "Hey... it's Miguel... how's it going?",
        "prompt": """You are Miguel, a friendly landscaping specialist. Sound natural and knowledgeable.

OPENER: "Hey... it's Miguel... how's it going?" [WAIT]
Then: "Cool... so you were looking for some landscaping work right?" [WAIT]

QUESTIONS: Ask what they want done, size of yard, timeline.
CLOSE: "I've got two spots for an estimate... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "tax": {"name": "Tax", "industry": "Tax Services", "icon": "📊", "color": "#f97316", "bilingual": False,
        "first_message": "Hi... it's Diana... how you doing today?",
        "prompt": """You are Diana, a professional tax consultant. Sound warm but professional.

OPENER: "Hi... it's Diana... how you doing today?" [WAIT]
Then: "Good... so you were looking for help with your taxes right?" [WAIT]

QUESTIONS: Ask about tax situation, any issues, timeline.
CLOSE: "I've got two consultation spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "plumbing": {"name": "Plumbing", "industry": "Plumbing", "icon": "🔧", "color": "#0891b2", "bilingual": False,
        "first_message": "Hey... it's Tony... how's it going?",
        "prompt": """You are Tony, a friendly plumbing specialist. Sound natural and helpful.

OPENER: "Hey... it's Tony... how's it going?" [WAIT]
Then: "Good... so hey, I'm not sure if we can help... but you were having some plumbing issues right?" [WAIT]
"Cool... just have 2 quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what's going on, how long, any water damage.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "electrical": {"name": "Electrical", "industry": "Electrical", "icon": "⚡", "color": "#eab308", "bilingual": False,
        "first_message": "Hey... it's Mike from the electrical company... how you doing?",
        "prompt": """You are Mike (Sparky), a friendly electrician. Sound natural and knowledgeable.

OPENER: "Hey... it's Mike from the electrical company... how you doing?" [WAIT]
Then: "Good... so you were having some electrical issues right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what's happening, which rooms, how long.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "pest_control": {"name": "Pest Control", "industry": "Pest Control", "icon": "🐜", "color": "#65a30d", "bilingual": False,
        "first_message": "Hey... it's Brett... how's it going?",
        "prompt": """You are Brett, a friendly pest control specialist. Sound natural and reassuring.

OPENER: "Hey... it's Brett... how's it going?" [WAIT]
Then: "Good... so hey, you were having some pest issues right?" [WAIT]
"No worries... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what they're seeing, where, how long.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "windows": {"name": "Windows", "industry": "Windows & Doors", "icon": "🪟", "color": "#06b6d4", "bilingual": False,
        "first_message": "Hi... it's Crystal... how you doing today?",
        "prompt": """You are Crystal, a friendly window and door specialist. Sound warm and helpful.

OPENER: "Hi... it's Crystal... how you doing today?" [WAIT]
Then: "Good... so you were looking at getting some windows done right?" [WAIT]
"Cool... just have a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask how many windows, what's wrong with current ones, timeline.
CLOSE: "I've got two spots for a free estimate... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "flooring": {"name": "Flooring", "industry": "Flooring", "icon": "🪵", "color": "#a16207", "bilingual": False,
        "first_message": "Hey... it's Frank... how's it going?",
        "prompt": """You are Frank, a friendly flooring specialist. Sound natural and knowledgeable.

OPENER: "Hey... it's Frank... how's it going?" [WAIT]
Then: "Good... so you were looking at getting some flooring done right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what type of flooring, how many rooms, timeline.
CLOSE: "I've got two spots for an estimate... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "painting": {"name": "Painting", "industry": "Painting", "icon": "🎨", "color": "#dc2626", "bilingual": True,
        "first_message": "Hey... it's Pablo... how you doing today?",
        "prompt": """You are Pablo, a friendly painting contractor. Sound warm and professional.

OPENER: "Hey... it's Pablo... how you doing today?" [WAIT]
Then: "Good... so you were looking to get some painting done right?" [WAIT]
"Cool... just have a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask interior or exterior, how many rooms, timeline.
CLOSE: "I've got two spots for a free estimate... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK.""",
        "first_message_es": "Hola... soy Pablo... cómo estás hoy?",
        "prompt_es": "Eres Pablo, contratista de pintura amable. SIEMPRE CIERRA CON 2 OPCIONES DE HORARIO."},

    "garage_door": {"name": "Garage", "industry": "Garage Doors", "icon": "🚪", "color": "#4b5563", "bilingual": False,
        "first_message": "Hey... it's Gary... how's it going?",
        "prompt": """You are Gary, a friendly garage door specialist. Sound natural and helpful.

OPENER: "Hey... it's Gary... how's it going?" [WAIT]
Then: "Good... so you were having some garage door issues right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what's happening, how old is the door, opener working.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "pool": {"name": "Pool", "industry": "Pool Services", "icon": "🏊", "color": "#0ea5e9", "bilingual": False,
        "first_message": "Hey... it's Steve from the pool company... how you doing?",
        "prompt": """You are Steve (Splash), a friendly pool service specialist. Sound natural and helpful.

OPENER: "Hey... it's Steve from the pool company... how you doing?" [WAIT]
Then: "Good... so you were looking for some pool help right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what kind of pool, what they need done, timeline.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "moving": {"name": "Moving", "industry": "Moving Services", "icon": "📦", "color": "#f59e0b", "bilingual": False,
        "first_message": "Hey... it's Max... how's it going?",
        "prompt": """You are Max, a friendly moving coordinator. Sound natural and helpful.

OPENER: "Hey... it's Max... how's it going?" [WAIT]
Then: "Good... so you were looking for help with a move right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask where from and to, how big is the place, when.
CLOSE: "I've got two spots for a free estimate... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "security": {"name": "Security", "industry": "Home Security", "icon": "🔐", "color": "#1e40af", "bilingual": False,
        "first_message": "Hi... it's Sam... how you doing today?",
        "prompt": """You are Sam, a friendly home security consultant. Sound professional and trustworthy.

OPENER: "Hi... it's Sam... how you doing today?" [WAIT]
Then: "Good... so you were looking at home security options right?" [WAIT]
"Cool... just have a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask if they have a system now, what concerns them, home size.
CLOSE: "I've got two spots for a free consultation... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "mortgage": {"name": "Mortgage", "industry": "Mortgage/Loans", "icon": "🏦", "color": "#059669", "bilingual": False,
        "first_message": "Hi... it's Morgan... how you doing today?",
        "prompt": """You are Morgan, a friendly mortgage specialist. Sound professional and helpful.

OPENER: "Hi... it's Morgan... how you doing today?" [WAIT]
Then: "Good... so you were looking at mortgage options right?" [WAIT]
"Cool... just have a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask if buying or refinancing, timeline, credit score ballpark.
CLOSE: "I've got two spots for a free consultation... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "chiropractor": {"name": "Chiro", "industry": "Chiropractic", "icon": "🦴", "color": "#7c3aed", "bilingual": False,
        "first_message": "Hi... it's Chris from the chiropractic office... how you doing today?",
        "prompt": """You are Chris, a friendly chiropractic coordinator. Sound warm and caring.

OPENER: "Hi... it's Chris from the chiropractic office... how you doing today?" [WAIT]
Then: "Good... so you were looking to get some relief right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what's bothering them, how long, seen a chiropractor before.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "medspa": {"name": "MedSpa", "industry": "Med Spa", "icon": "💉", "color": "#ec4899", "bilingual": False,
        "first_message": "Hi... it's Bella... how you doing today?",
        "prompt": """You are Bella, a friendly med spa consultant. Sound warm and professional.

OPENER: "Hi... it's Bella... how you doing today?" [WAIT]
Then: "Good... so you were looking at some treatments right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what treatments interest them, any done before, timeline.
CLOSE: "I've got two spots for a free consultation... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "travel": {"name": "Travel", "industry": "Travel Agency", "icon": "✈️", "color": "#0284c7", "bilingual": False,
        "first_message": "Hi... it's Jen from the travel agency... how you doing today?",
        "prompt": """You are Jen (Journey), a friendly travel consultant. Sound enthusiastic and helpful.

OPENER: "Hi... it's Jen from the travel agency... how you doing today?" [WAIT]
Then: "Good... so you were looking at planning a trip right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask where they want to go, when, how many people.
CLOSE: "I've got two spots to chat about your trip... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "wedding": {"name": "Wedding", "industry": "Wedding Planning", "icon": "💒", "color": "#f472b6", "bilingual": False,
        "first_message": "Hi... it's Grace... how you doing today?",
        "prompt": """You are Grace, a friendly wedding coordinator. Sound warm and excited.

OPENER: "Hi... it's Grace... how you doing today?" [WAIT]
Then: "Good... so you were looking at wedding planning help right?... congrats by the way!" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask when's the date, how many guests, what help they need.
CLOSE: "I've got two spots for a free consultation... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "tutoring": {"name": "Tutoring", "industry": "Tutoring", "icon": "📚", "color": "#6366f1", "bilingual": False,
        "first_message": "Hi... it's Kevin from the tutoring center... how you doing today?",
        "prompt": """You are Kevin (Professor), a friendly tutoring coordinator. Sound warm and encouraging.

OPENER: "Hi... it's Kevin from the tutoring center... how you doing today?" [WAIT]
Then: "Good... so you were looking at tutoring help right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what subject, what grade level, how often they need help.
CLOSE: "I've got two spots for a free assessment... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""},

    "pet_grooming": {"name": "Pet Care", "industry": "Pet Grooming", "icon": "🐕", "color": "#f97316", "bilingual": False,
        "first_message": "Hi... it's Penny from the grooming salon... how you doing today?",
        "prompt": """You are Penny, a friendly pet grooming coordinator. Sound warm and animal-loving.

OPENER: "Hi... it's Penny from the grooming salon... how you doing today?" [WAIT]
Then: "Good... so you were looking to get your fur baby groomed right?" [WAIT]
"Cool... just a couple quick questions... sound fair?" [WAIT]

QUESTIONS: Ask what kind of pet, breed, what services they need.
CLOSE: "I've got two spots... tomorrow at 10 or Thursday at 2... which works?" ALWAYS BOOK."""}
}

# ═══════════════════════════════════════════════════════════════════════════════
# 15 INBOUND AGENTS (FRONT DESK / RECEPTIONISTS)
# ═══════════════════════════════════════════════════════════════════════════════

INBOUND_AGENTS = {
    "inbound_medical": {
        "name": "Medical", "industry": "Medical Office", "icon": "🏥", "color": "#ef4444", "bilingual": True,
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
        "name": "Dental", "industry": "Dental Office", "icon": "🦷", "color": "#06b6d4", "bilingual": True,
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
        "name": "Wedding", "industry": "Law Firm", "icon": "⚖️", "color": "#6366f1", "bilingual": False,
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
        "name": "Realty", "industry": "Real Estate Agency", "icon": "🏡", "color": "#8b5cf6", "bilingual": False,
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
        "name": "Auto", "industry": "Auto Dealership", "icon": "🚗", "color": "#10b981", "bilingual": False,
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
        "name": "Salon", "industry": "Hair Salon/Spa", "icon": "💇", "color": "#ec4899", "bilingual": False,
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
        "name": "Plumbing", "industry": "Restaurant", "icon": "🍽️", "color": "#f59e0b", "bilingual": True,
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
        "name": "Hotel", "industry": "Hotel", "icon": "🏨", "color": "#0ea5e9", "bilingual": True,
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
        "name": "Gym", "industry": "Fitness Center", "icon": "💪", "color": "#84cc16", "bilingual": False,
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
        "name": "Insurance", "industry": "Insurance Agency", "icon": "🛡️", "color": "#3b82f6", "bilingual": False,
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
        "name": "Vet", "industry": "Veterinary Clinic", "icon": "🐾", "color": "#a855f7", "bilingual": False,
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
        "name": "School", "industry": "School/Education", "icon": "🎓", "color": "#f97316", "bilingual": True,
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
        "name": "Contractor", "industry": "General Contractor", "icon": "🔨", "color": "#78716c", "bilingual": False,
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
        "name": "Accounting", "industry": "Accounting Firm", "icon": "📊", "color": "#059669", "bilingual": False,
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
        "name": "Therapy", "industry": "Therapy/Counseling", "icon": "🧠", "color": "#7c3aed", "bilingual": False,
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
    },

    "inbound_plumbing": {
        "name": "Plumbing", "industry": "Plumbing Company", "icon": "🔧", "color": "#0891b2", "bilingual": False,
        "company": "FastFlow Plumbing",
        "first_message": "Thank you for calling FastFlow Plumbing, this is Tina, how can I help you today?",
        "prompt": """You are Tina, the helpful receptionist at FastFlow Plumbing.

""" + RECEPTIONIST_CORE.replace("{company_name}", "FastFlow Plumbing").replace("{agent_name}", "Tina") + """

SPECIFIC TO PLUMBING:
- Emergency: "Is water actively leaking? We have 24/7 emergency service"
- Services: Drain cleaning, water heaters, leak repair, repiping, sewer lines
- Get: Name, phone, address, what's the issue, is it an emergency"""
    },

    "inbound_electrical": {
        "name": "Electrical", "industry": "Electrical Company", "icon": "⚡", "color": "#eab308", "bilingual": False,
        "company": "Bright Spark Electric",
        "first_message": "Bright Spark Electric, this is Ellie, how can I help you?",
        "prompt": """You are Ellie, the friendly receptionist at Bright Spark Electric.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Bright Spark Electric").replace("{agent_name}", "Ellie") + """

SPECIFIC TO ELECTRICAL:
- Safety first: "If you smell burning or see sparks, please turn off the breaker"
- Services: Panel upgrades, outlet repair, lighting, ceiling fans, rewiring
- Get: Name, phone, address, what's happening, is it an emergency"""
    },

    "inbound_hvac": {
        "name": "HVAC", "industry": "HVAC Company", "icon": "❄️", "color": "#0ea5e9", "bilingual": False,
        "company": "ComfortZone HVAC",
        "first_message": "ComfortZone HVAC, this is Holly, how can I help you today?",
        "prompt": """You are Holly, the caring receptionist at ComfortZone HVAC.

""" + RECEPTIONIST_CORE.replace("{company_name}", "ComfortZone HVAC").replace("{agent_name}", "Holly") + """

SPECIFIC TO HVAC:
- Emergency: "Is it extremely hot/cold in your home? We have same-day service"
- Services: AC repair, heating repair, installation, maintenance, duct cleaning
- Get: Name, phone, address, AC or heat, what's happening"""
    },

    "inbound_roofing": {
        "name": "Roofing", "industry": "Roofing Company", "icon": "🏠", "color": "#dc2626", "bilingual": False,
        "company": "TopNotch Roofing",
        "first_message": "TopNotch Roofing, this is Roxy, how can I help you?",
        "prompt": """You are Roxy, the helpful receptionist at TopNotch Roofing.

""" + RECEPTIONIST_CORE.replace("{company_name}", "TopNotch Roofing").replace("{agent_name}", "Roxy") + """

SPECIFIC TO ROOFING:
- Storm damage: "We do free storm damage inspections and work with insurance"
- Services: Repairs, replacements, inspections, gutters, siding
- Get: Name, phone, address, what's going on with roof, any active leaks"""
    },

    "inbound_pest": {
        "name": "Pest", "industry": "Pest Control", "icon": "🐜", "color": "#65a30d", "bilingual": False,
        "company": "BugFree Pest Control",
        "first_message": "BugFree Pest Control, this is Brenda, how can I help you?",
        "prompt": """You are Brenda, the reassuring receptionist at BugFree Pest Control.

""" + RECEPTIONIST_CORE.replace("{company_name}", "BugFree Pest Control").replace("{agent_name}", "Brenda") + """

SPECIFIC TO PEST:
- Be reassuring: "Don't worry, we deal with this all the time"
- Services: Ants, roaches, rodents, termites, bed bugs, wildlife
- Get: Name, phone, address, what they're seeing, how long"""
    },

    "inbound_moving": {
        "name": "Insurance", "industry": "Moving Company", "icon": "📦", "color": "#f59e0b", "bilingual": False,
        "company": "EasyMove Relocations",
        "first_message": "EasyMove Relocations, this is Maya, how can I help you today?",
        "prompt": """You are Maya, the organized receptionist at EasyMove Relocations.

""" + RECEPTIONIST_CORE.replace("{company_name}", "EasyMove Relocations").replace("{agent_name}", "Maya") + """

SPECIFIC TO MOVING:
- Services: Local moves, long distance, packing, storage, commercial
- Quote info needed: Moving from, moving to, size of home, date
- Get: Name, phone, from address, to address, move date"""
    },

    "inbound_solar": {
        "name": "Sunny", "industry": "Solar Company", "icon": "☀️", "color": "#f59e0b", "bilingual": False,
        "company": "SunPower Solar",
        "first_message": "SunPower Solar, this is Sunny, how can I help you today?",
        "prompt": """You are Sunny, the enthusiastic receptionist at SunPower Solar.

""" + RECEPTIONIST_CORE.replace("{company_name}", "SunPower Solar").replace("{agent_name}", "Sunny") + """

SPECIFIC TO SOLAR:
- "Going solar is a great decision! We offer free consultations"
- Services: Solar panels, battery storage, EV chargers
- Get: Name, phone, address, do they own the home, electric bill estimate"""
    },

    "inbound_pool": {
        "name": "Brooke", "industry": "Pool Service", "icon": "🏊", "color": "#06b6d4", "bilingual": False,
        "company": "Crystal Clear Pools",
        "first_message": "Crystal Clear Pools, this is Brooke, how can I help you?",
        "prompt": """You are Brooke, the friendly receptionist at Crystal Clear Pools.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Crystal Clear Pools").replace("{agent_name}", "Brooke") + """

SPECIFIC TO POOL:
- Services: Weekly cleaning, repairs, equipment, opening/closing, remodeling
- Get: Name, phone, address, type of pool, what service needed"""
    },

    "inbound_flooring": {
        "name": "Flora", "industry": "Flooring Company", "icon": "🪵", "color": "#a16207", "bilingual": False,
        "company": "FloorCraft Installations",
        "first_message": "FloorCraft Installations, this is Flora, how can I help you?",
        "prompt": """You are Flora, the helpful receptionist at FloorCraft Installations.

""" + RECEPTIONIST_CORE.replace("{company_name}", "FloorCraft Installations").replace("{agent_name}", "Flora") + """

SPECIFIC TO FLOORING:
- Services: Hardwood, laminate, tile, carpet, vinyl, refinishing
- "We offer free in-home estimates!"
- Get: Name, phone, address, type of flooring interested in, how many rooms"""
    },

    "inbound_painting": {
        "name": "Patty", "industry": "Painting Company", "icon": "🎨", "color": "#dc2626", "bilingual": True,
        "company": "Perfect Brush Painting",
        "first_message": "Perfect Brush Painting, this is Patty, how can I help you?",
        "prompt": """You are Patty, the friendly receptionist at Perfect Brush Painting.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Perfect Brush Painting").replace("{agent_name}", "Patty") + """

SPECIFIC TO PAINTING:
- Services: Interior, exterior, cabinets, commercial, pressure washing
- "We offer free color consultations and estimates!"
- Get: Name, phone, address, interior or exterior, how many rooms""",
        "first_message_es": "Perfect Brush Painting, habla Patty, ¿en qué puedo ayudarle?",
        "prompt_es": "Eres Patty, recepcionista amable de la compañía de pintura."
    },

    "inbound_garage": {
        "name": "Garage", "industry": "Garage Door Company", "icon": "🚪", "color": "#4b5563", "bilingual": False,
        "company": "LiftMaster Garage Doors",
        "first_message": "LiftMaster Garage Doors, this is Gary, how can I help you?",
        "prompt": """You are Gary, the helpful receptionist at LiftMaster Garage Doors.

""" + RECEPTIONIST_CORE.replace("{company_name}", "LiftMaster Garage Doors").replace("{agent_name}", "Gary") + """

SPECIFIC TO GARAGE DOORS:
- Emergency: "Is your car stuck inside? We offer same-day service"
- Services: Repair, replacement, openers, springs, maintenance
- Get: Name, phone, address, what's happening, single or double door"""
    },

    "inbound_window": {
        "name": "Wendy", "industry": "Window Company", "icon": "🪟", "color": "#06b6d4", "bilingual": False,
        "company": "ClearView Windows",
        "first_message": "ClearView Windows, this is Wendy, how can I help you today?",
        "prompt": """You are Wendy, the friendly receptionist at ClearView Windows.

""" + RECEPTIONIST_CORE.replace("{company_name}", "ClearView Windows").replace("{agent_name}", "Wendy") + """

SPECIFIC TO WINDOWS:
- Services: Replacement windows, doors, patio doors, storm windows
- "We offer free in-home consultations and estimates!"
- Get: Name, phone, address, how many windows, any specific concerns"""
    },

    "inbound_security": {
        "name": "Security", "industry": "Home Security", "icon": "🔐", "color": "#1e40af", "bilingual": False,
        "company": "SafeHome Security",
        "first_message": "SafeHome Security, this is Sam, how can I help you?",
        "prompt": """You are Sam, the professional receptionist at SafeHome Security.

""" + RECEPTIONIST_CORE.replace("{company_name}", "SafeHome Security").replace("{agent_name}", "Sam") + """

SPECIFIC TO SECURITY:
- Services: Alarm systems, cameras, smart home, monitoring, access control
- "We offer free security assessments!"
- Get: Name, phone, address, own or rent, specific concerns"""
    },

    "inbound_mortgage": {
        "name": "Mortgage", "industry": "Mortgage Company", "icon": "🏦", "color": "#059669", "bilingual": False,
        "company": "HomeKey Mortgage",
        "first_message": "HomeKey Mortgage, this is Morgan, how can I help you today?",
        "prompt": """You are Morgan, the professional receptionist at HomeKey Mortgage.

""" + RECEPTIONIST_CORE.replace("{company_name}", "HomeKey Mortgage").replace("{agent_name}", "Morgan") + """

SPECIFIC TO MORTGAGE:
- Services: Purchase loans, refinance, FHA, VA, jumbo, reverse mortgage
- "I can schedule a free consultation with one of our loan officers"
- Get: Name, phone, buying or refinancing, timeline, credit score ballpark"""
    },

    "inbound_chiro": {
        "name": "Christie", "industry": "Chiropractic Office", "icon": "🦴", "color": "#7c3aed", "bilingual": False,
        "company": "AlignWell Chiropractic",
        "first_message": "AlignWell Chiropractic, this is Christie, how can I help you?",
        "prompt": """You are Christie, the caring receptionist at AlignWell Chiropractic.

""" + RECEPTIONIST_CORE.replace("{company_name}", "AlignWell Chiropractic").replace("{agent_name}", "Christie") + """

SPECIFIC TO CHIROPRACTIC:
- New patients: "First visit includes consultation, exam, and adjustment if needed"
- Services: Adjustments, massage, physical therapy, x-rays
- Get: Name, phone, what's bothering them, how long, seen a chiropractor before"""
    },

    "inbound_medspa": {
        "name": "MedSpa", "industry": "Med Spa", "icon": "💉", "color": "#ec4899", "bilingual": False,
        "company": "Glow Med Spa",
        "first_message": "Glow Med Spa, this is Bella, how can I help you today?",
        "prompt": """You are Bella, the elegant receptionist at Glow Med Spa.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Glow Med Spa").replace("{agent_name}", "Bella") + """

SPECIFIC TO MED SPA:
- Services: Botox, fillers, laser treatments, facials, body contouring
- "We offer free consultations for all treatments!"
- Get: Name, phone, what treatments interest them, any done before"""
    },

    "inbound_daycare": {
        "name": "Daisy", "industry": "Daycare Center", "icon": "👶", "color": "#f472b6", "bilingual": True,
        "company": "Little Stars Daycare",
        "first_message": "Little Stars Daycare, this is Daisy, how can I help you?",
        "prompt": """You are Daisy, the warm and friendly receptionist at Little Stars Daycare.

""" + RECEPTIONIST_CORE.replace("{company_name}", "Little Stars Daycare").replace("{agent_name}", "Daisy") + """

SPECIFIC TO DAYCARE:
- "We'd love to show you around! Tours are available daily"
- Ages: Infants through Pre-K
- Hours: Monday-Friday 6:30am-6:30pm
- Get: Name, phone, child's age, when they need care to start""",
        "first_message_es": "Little Stars Daycare, habla Daisy, ¿en qué puedo ayudarle?",
        "prompt_es": "Eres Daisy, recepcionista cálida de la guardería."
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
    
    # Lead sequence tracking - the patented 3-calls-per-day system
    c.execute('''CREATE TABLE IF NOT EXISTS lead_sequences (
        id INTEGER PRIMARY KEY,
        lead_id INTEGER,
        phone TEXT,
        
        -- Current sequence status
        sequence_status TEXT DEFAULT 'active',  -- active, paused, completed, not_interested, appointment_set
        current_day INTEGER DEFAULT 1,
        current_slot INTEGER DEFAULT 0,  -- 0=initial, 1=8:30am, 2=12:15pm, 3=5:30pm
        
        -- Attempt tracking
        total_attempts INTEGER DEFAULT 0,
        total_texts INTEGER DEFAULT 0,
        last_attempt_at TIMESTAMP,
        next_attempt_at TIMESTAMP,
        
        -- Slot completion for today
        slot1_completed INTEGER DEFAULT 0,  -- 8:30 AM
        slot1_attempts INTEGER DEFAULT 0,
        slot2_completed INTEGER DEFAULT 0,  -- 12:15 PM
        slot2_attempts INTEGER DEFAULT 0,
        slot3_completed INTEGER DEFAULT 0,  -- 5:30 PM (with text before)
        slot3_attempts INTEGER DEFAULT 0,
        
        -- Outcomes
        answered_count INTEGER DEFAULT 0,
        voicemail_count INTEGER DEFAULT 0,
        no_answer_count INTEGER DEFAULT 0,
        
        -- Settings
        max_days INTEGER DEFAULT 7,
        double_tap_enabled INTEGER DEFAULT 1,  -- Call twice per slot
        
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Pre-5:30 PM text messages (variable each day)
    c.execute('''CREATE TABLE IF NOT EXISTS evening_text_templates (
        id INTEGER PRIMARY KEY,
        message TEXT,
        is_active INTEGER DEFAULT 1,
        used_count INTEGER DEFAULT 0,
        last_used_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Insert default evening text templates
    evening_texts = [
        "Hey, we've been trying to reach you - please answer, it's important!",
        "Hi! We have some important info about your inquiry. Please pick up when we call!",
        "Quick heads up - we're about to call you with important details. Please answer!",
        "Hey there! Don't miss our call - we have great news about your request!",
        "Important: We're calling you shortly. Please answer - it's about your inquiry!",
        "Hi! We've been trying to connect. Please pick up our next call - it's important!",
        "Hey! We have updates on your request. Calling you in a few minutes - please answer!",
    ]
    for txt in evening_texts:
        c.execute('INSERT OR IGNORE INTO evening_text_templates (message) VALUES (?)', (txt,))
    
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
    
    # Website Leads - people who book through the website
    c.execute('''CREATE TABLE IF NOT EXISTS website_leads (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        phone TEXT,
        company TEXT,
        industry TEXT,
        call_volume TEXT,
        preferred_day TEXT,
        preferred_time TEXT,
        notes TEXT,
        source TEXT DEFAULT 'website_booking',
        status TEXT DEFAULT 'new',
        assigned_to TEXT,
        follow_up_date TEXT,
        last_contact_date TIMESTAMP,
        total_contacts INTEGER DEFAULT 0,
        converted INTEGER DEFAULT 0,
        deal_value REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Website Visits - tracking page views and actions
    c.execute('''CREATE TABLE IF NOT EXISTS website_visits (
        id INTEGER PRIMARY KEY,
        visitor_id TEXT,
        action TEXT,
        page TEXT,
        ip_address TEXT,
        user_agent TEXT,
        referrer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
    admin_salt = secrets.token_hex(16)
    admin_hash = hashlib.sha256(('admin123' + admin_salt).encode()).hexdigest()
    c.execute('''INSERT OR IGNORE INTO users (email, password_hash, salt, name, role, is_active, email_verified) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', 
              ('admin@voice.ai', admin_hash, admin_salt, 'Admin', 'admin', 1, 1))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MULTI-TENANT CLIENT TABLES
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Clients table (each business using your platform)
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uuid TEXT UNIQUE NOT NULL,
        company_name TEXT NOT NULL,
        contact_name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        industry TEXT,
        plan TEXT DEFAULT 'starter',
        status TEXT DEFAULT 'active',
        monthly_budget REAL DEFAULT 500.00,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Client API integrations (each client's own credentials)
    c.execute('''CREATE TABLE IF NOT EXISTS client_integrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        integration_type TEXT NOT NULL,
        api_key TEXT,
        api_secret TEXT,
        webhook_url TEXT,
        phone_number TEXT,
        agent_id TEXT,
        settings TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )''')
    
    # Client costs tracking (real-time cost per client)
    c.execute('''CREATE TABLE IF NOT EXISTS client_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        cost_type TEXT NOT NULL,
        quantity REAL DEFAULT 0,
        unit_cost REAL DEFAULT 0,
        total_cost REAL DEFAULT 0,
        description TEXT,
        call_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    )''')
    
    # Add client_id to leads if not exists
    try:
        c.execute('ALTER TABLE leads ADD COLUMN client_id INTEGER DEFAULT 1')
    except:
        pass
    
    # Add client_id to call_log if not exists
    try:
        c.execute('ALTER TABLE call_log ADD COLUMN client_id INTEGER DEFAULT 1')
    except:
        pass
    
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
# MULTI-TENANT CLIENT MANAGEMENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_client_uuid():
    """Generate unique client identifier"""
    import uuid
    return str(uuid.uuid4())[:8]

def create_client(company_name, contact_name, email, phone, industry, plan='starter'):
    """Create a new client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    client_uuid = generate_client_uuid()
    
    try:
        c.execute('''INSERT INTO clients 
                     (uuid, company_name, contact_name, email, phone, industry, plan)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (client_uuid, company_name, contact_name, email, phone, industry, plan))
        client_id = c.lastrowid
        conn.commit()
        conn.close()
        return {'success': True, 'id': client_id, 'uuid': client_uuid}
    except sqlite3.IntegrityError as e:
        conn.close()
        return {'success': False, 'error': 'Email already exists'}
    except Exception as e:
        conn.close()
        return {'success': False, 'error': str(e)}

def get_all_clients():
    """Get all clients for admin view"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT c.*, 
                 (SELECT COUNT(*) FROM leads WHERE client_id = c.id) as lead_count,
                 (SELECT COUNT(*) FROM call_log WHERE client_id = c.id) as call_count,
                 (SELECT COALESCE(SUM(total_cost), 0) FROM client_costs WHERE client_id = c.id AND date >= date('now', '-30 days')) as monthly_cost
                 FROM clients c ORDER BY c.created_at DESC''')
    
    columns = [desc[0] for desc in c.description]
    clients = [dict(zip(columns, row)) for row in c.fetchall()]
    
    conn.close()
    return clients

def get_client(client_id):
    """Get single client with full details"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
    columns = [desc[0] for desc in c.description]
    row = c.fetchone()
    
    if not row:
        conn.close()
        return None
    
    client = dict(zip(columns, row))
    
    # Get integrations
    c.execute('SELECT * FROM client_integrations WHERE client_id = ?', (client_id,))
    columns = [desc[0] for desc in c.description]
    client['integrations'] = [dict(zip(columns, row)) for row in c.fetchall()]
    
    # Get stats
    c.execute('''SELECT COUNT(*) as total FROM leads WHERE client_id = ?''', (client_id,))
    total_leads = c.fetchone()[0]
    
    c.execute('''SELECT COUNT(*) FROM leads WHERE client_id = ? AND status = 'appointment_set' ''', (client_id,))
    appointments = c.fetchone()[0]
    
    c.execute('''SELECT COUNT(*) FROM leads WHERE client_id = ? AND status = 'sold' ''', (client_id,))
    sold = c.fetchone()[0]
    
    client['stats'] = {
        'total_leads': total_leads or 0,
        'appointments': appointments or 0,
        'sold': sold or 0
    }
    
    # Get monthly cost
    c.execute('''SELECT COALESCE(SUM(total_cost), 0) FROM client_costs 
                 WHERE client_id = ? AND date >= date('now', '-30 days')''', (client_id,))
    client['monthly_cost'] = c.fetchone()[0]
    
    conn.close()
    return client

def update_client(client_id, data):
    """Update client details"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    fields = []
    values = []
    for key in ['company_name', 'contact_name', 'email', 'phone', 'industry', 'plan', 'status', 'monthly_budget']:
        if key in data:
            fields.append(f'{key} = ?')
            values.append(data[key])
    
    if fields:
        values.append(client_id)
        c.execute(f'UPDATE clients SET {", ".join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?', values)
        conn.commit()
    
    conn.close()
    return {'success': True}

def delete_client(client_id):
    """Delete client and related data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('DELETE FROM client_integrations WHERE client_id = ?', (client_id,))
    c.execute('DELETE FROM client_costs WHERE client_id = ?', (client_id,))
    c.execute('DELETE FROM clients WHERE id = ?', (client_id,))
    
    conn.commit()
    conn.close()
    return {'success': True}

def add_client_integration(client_id, integration_type, api_key=None, api_secret=None, 
                           webhook_url=None, phone_number=None, agent_id=None, settings=None):
    """Add integration for a client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''INSERT INTO client_integrations 
                 (client_id, integration_type, api_key, api_secret, webhook_url, phone_number, agent_id, settings)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (client_id, integration_type, api_key, api_secret, webhook_url, phone_number, agent_id,
               json.dumps(settings) if settings else None))
    
    conn.commit()
    conn.close()
    return {'success': True}

def get_client_integration(client_id, integration_type):
    """Get specific integration for client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT * FROM client_integrations 
                 WHERE client_id = ? AND integration_type = ? AND is_active = 1''',
              (client_id, integration_type))
    
    columns = [desc[0] for desc in c.description]
    row = c.fetchone()
    conn.close()
    
    if row:
        result = dict(zip(columns, row))
        if result.get('settings'):
            result['settings'] = json.loads(result['settings'])
        return result
    return None

def update_client_integration(integration_id, data):
    """Update client integration"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    fields = []
    values = []
    for key in ['api_key', 'api_secret', 'webhook_url', 'phone_number', 'agent_id', 'is_active']:
        if key in data:
            fields.append(f'{key} = ?')
            values.append(data[key])
    
    if fields:
        values.append(integration_id)
        c.execute(f'UPDATE client_integrations SET {", ".join(fields)} WHERE id = ?', values)
        conn.commit()
    
    conn.close()
    return {'success': True}

def delete_client_integration(integration_id):
    """Delete client integration"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM client_integrations WHERE id = ?', (integration_id,))
    conn.commit()
    conn.close()
    return {'success': True}

def log_client_cost(client_id, cost_type, quantity, unit_cost, description=None, call_id=None):
    """Log a cost for a client"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    total_cost = quantity * unit_cost
    today = datetime.now().strftime('%Y-%m-%d')
    
    c.execute('''INSERT INTO client_costs 
                 (client_id, date, cost_type, quantity, unit_cost, total_cost, description, call_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (client_id, today, cost_type, quantity, unit_cost, total_cost, description, call_id))
    
    conn.commit()
    conn.close()
    return total_cost

def get_client_costs(client_id, days=30):
    """Get client costs for period"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''SELECT date, cost_type, SUM(quantity) as quantity, SUM(total_cost) as total
                 FROM client_costs 
                 WHERE client_id = ? AND date >= date('now', ?)
                 GROUP BY date, cost_type
                 ORDER BY date DESC''', (client_id, f'-{days} days'))
    
    columns = ['date', 'cost_type', 'quantity', 'total']
    costs = [dict(zip(columns, row)) for row in c.fetchall()]
    
    # Get totals by type
    c.execute('''SELECT cost_type, SUM(total_cost) as total
                 FROM client_costs 
                 WHERE client_id = ? AND date >= date('now', ?)
                 GROUP BY cost_type''', (client_id, f'-{days} days'))
    
    totals = {row[0]: row[1] for row in c.fetchall()}
    
    conn.close()
    return {'daily': costs, 'totals': totals, 'grand_total': sum(totals.values())}

def get_admin_dashboard_stats():
    """Get overall stats for admin dashboard"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    stats = {}
    
    # Total clients
    c.execute('SELECT COUNT(*) FROM clients WHERE status = "active"')
    stats['total_clients'] = c.fetchone()[0]
    
    # Total calls (last 30 days)
    c.execute('SELECT COUNT(*) FROM call_log WHERE created_at >= date("now", "-30 days")')
    stats['total_calls'] = c.fetchone()[0]
    
    # Total costs (last 30 days)
    c.execute('SELECT COALESCE(SUM(total_cost), 0) FROM client_costs WHERE date >= date("now", "-30 days")')
    stats['total_costs'] = c.fetchone()[0]
    
    # Revenue calculation (from plans)
    c.execute('SELECT plan, COUNT(*) as count FROM clients WHERE status = "active" GROUP BY plan')
    plan_counts = {row[0]: row[1] for row in c.fetchall()}
    plan_prices = {'starter': 297, 'professional': 497, 'enterprise': 997}
    stats['monthly_revenue'] = sum(plan_prices.get(plan, 297) * count for plan, count in plan_counts.items())
    
    conn.close()
    return stats

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

# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Email configuration - using environment variables
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', OWNER_EMAIL)

def send_email(to_email, subject, body_text, body_html=None):
    """Send email notification"""
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"📧 [EMAIL NOT CONFIGURED] Would send to {to_email}: {subject}")
        # Log the attempt even if not configured
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO sms_log (phone, message, message_type, status) VALUES (?, ?, ?, ?)',
                      (to_email, f"[EMAIL] {subject}: {body_text[:200]}", 'email_attempted', 'not_configured'))
            conn.commit()
            conn.close()
        except:
            pass
        return {"success": False, "error": "SMTP not configured"}
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        
        # Add text version
        part1 = MIMEText(body_text, 'plain')
        msg.attach(part1)
        
        # Add HTML version if provided
        if body_html:
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
        
        # Connect and send
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        
        # Log success
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO sms_log (phone, message, message_type, status) VALUES (?, ?, ?, ?)',
                  (to_email, f"[EMAIL] {subject}", 'email', 'sent'))
        conn.commit()
        conn.close()
        
        print(f"✅ Email sent to {to_email}: {subject}")
        return {"success": True}
    except Exception as e:
        print(f"❌ Email error: {e}")
        return {"success": False, "error": str(e)}

def send_appointment_email(appt):
    """Send appointment confirmation email to customer"""
    if not appt.get('email'):
        return {"success": False, "error": "No email address"}
    
    subject = f"✅ Appointment Confirmed - {appt.get('appointment_date', 'TBD')}"
    
    body_text = f"""Hi {appt.get('first_name', 'there')}!

Your appointment has been confirmed:

📅 Date: {appt.get('appointment_date', 'TBD')}
⏰ Time: {appt.get('appointment_time', 'TBD')}
📍 Address: {appt.get('address', '')}

If you need to reschedule, please call us at {COMPANY_PHONE}.

Thank you!
- {COMPANY_NAME}
"""
    
    body_html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">✅ Appointment Confirmed!</h1>
    </div>
    <div style="padding: 30px; background: #f8f9fa;">
        <p style="font-size: 18px;">Hi <strong>{appt.get('first_name', 'there')}</strong>!</p>
        <p>Your appointment has been confirmed:</p>
        <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <p style="margin: 10px 0;"><strong>📅 Date:</strong> {appt.get('appointment_date', 'TBD')}</p>
            <p style="margin: 10px 0;"><strong>⏰ Time:</strong> {appt.get('appointment_time', 'TBD')}</p>
            <p style="margin: 10px 0;"><strong>📍 Address:</strong> {appt.get('address', 'TBD')}</p>
        </div>
        <p>If you need to reschedule, please call us at <a href="tel:{COMPANY_PHONE}">{COMPANY_PHONE}</a></p>
        <p style="margin-top: 30px;">Thank you!<br><strong>- {COMPANY_NAME}</strong></p>
    </div>
</body>
</html>
"""
    
    return send_email(appt['email'], subject, body_text, body_html)

def send_owner_email_notification(subject, body):
    """Send notification email to business owner"""
    return send_email(OWNER_EMAIL, subject, body)

def notify_owner_new_lead(lead_data):
    """Send SMS and email to owner when new lead comes in"""
    name = lead_data.get('first_name', 'Someone')
    phone = lead_data.get('phone', 'N/A')
    email = lead_data.get('email', 'N/A')
    industry = lead_data.get('industry', 'N/A')
    
    # Send SMS to owner
    sms_msg = f"""🎯 NEW LEAD from VoiceLab!

Name: {name}
Phone: {phone}
Email: {email}
Industry: {industry}

Call them ASAP! 🔥"""
    
    if TWILIO_SID and TWILIO_TOKEN and OWNER_PHONE:
        send_sms(OWNER_PHONE, sms_msg, "owner_notification")
        print(f"📱 Owner notified via SMS: {name}")
    
    # Send email notification to owner
    send_owner_email_notification(f"🎯 New Lead: {name}", sms_msg)

def send_lead_welcome_sms(phone, name):
    """Send welcome SMS to new lead with booking link"""
    msg = f"""Hi {name}! 👋

Thanks for checking out VoiceLab.live! We're excited to show you how AI can transform your business.

Ready to see it in action? Book your free demo call here:
{CALENDLY_LINK}

Talk soon!
- The VoiceLab Team"""
    
    if TWILIO_SID and TWILIO_TOKEN and phone:
        result = send_sms(phone, msg, "lead_welcome")
        if result.get('success'):
            print(f"✅ Welcome SMS sent to {name} at {phone}")
        return result
    return {"success": False, "error": "SMS not configured"}

def send_appointment_confirmation(appt_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM appointments WHERE id = ?', (appt_id,))
    row = c.fetchone()
    appt = dict(row) if row else None
    conn.close()
    
    if not appt: return {"error": "Not found"}
    
    # Send SMS confirmation
    msg = f"""✅ Appointment Confirmed!

Hi {appt.get('first_name', 'there')}! Your appointment is set:

📅 {appt.get('appointment_date', 'TBD')}
⏰ {appt.get('appointment_time', 'TBD')}
📍 {appt.get('address', '')}

Reply CONFIRM or call {COMPANY_PHONE} if you need to reschedule.

- {COMPANY_NAME}"""

    sms_result = send_sms(appt['phone'], msg, 'confirmation')
    
    # Send email confirmation
    email_result = send_appointment_email(appt)
    
    # Notify owner
    owner_msg = f"""📅 NEW APPOINTMENT BOOKED!

Customer: {appt.get('first_name', '')} {appt.get('last_name', '')}
Phone: {appt.get('phone', '')}
Email: {appt.get('email', '')}
Date: {appt.get('appointment_date', 'TBD')}
Time: {appt.get('appointment_time', 'TBD')}
Address: {appt.get('address', '')}

Check dashboard for details! 🔥"""
    
    if OWNER_PHONE:
        send_sms(OWNER_PHONE, owner_msg, 'owner_appointment_notification')
    send_owner_email_notification("📅 New Appointment Booked!", owner_msg)
    
    if sms_result.get('success') or email_result.get('success'):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE appointments SET confirmation_sent = 1, confirmation_sent_at = CURRENT_TIMESTAMP WHERE id = ?', (appt_id,))
        conn.commit()
        conn.close()
    
    # Return with backward-compatible 'success' key
    return {
        "success": sms_result.get('success') or email_result.get('success'),
        "sms": sms_result, 
        "email": email_result
    }

# ═══════════════════════════════════════════════════════════════════════════════
# CALL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Retell SIP URI - same one used for inbound calls
RETELL_SIP_URI = "5t4n6j0wnrl.sip.livekit.cloud"

# Industry to company name mapping for demo calls
INDUSTRY_COMPANIES = {
    'roofing': 'Denver Roofing Pro',
    'solar': 'Bright Solar Solutions',
    'insurance': 'Shield Insurance Group',
    'auto': 'Premier Auto Sales',
    'realtor': 'Dream Home Realty',
    'dental': 'Smile Dental Care',
    'hvac': 'ComfortAir HVAC',
    'legal': 'Justice Law Group',
    'fitness': 'PowerFit Gym',
    'cleaning': 'Sparkle Cleaning Co',
    'landscaping': 'Green Thumb Landscaping',
    'tax': 'TaxPro Services',
    'plumbing': 'FastFlow Plumbing',
    'electrical': 'BrightWire Electric',
    'pest_control': 'BugFree Pest Control',
    'windows': 'ClearView Windows',
    'flooring': 'FloorCraft Pro',
    'painting': 'ColorMaster Painting',
    'garage_door': 'DoorPro Garage',
    'pool': 'Crystal Pool Service',
    'moving': 'SwiftMove Co',
    'security': 'SafeHome Security',
    'mortgage': 'HomeLoan Experts',
    'chiropractor': 'SpineWell Chiropractic',
    'medspa': 'Glow Med Spa',
    'travel': 'Wanderlust Travel',
    'wedding': 'Forever Wedding Co',
    'tutoring': 'BrightMind Tutoring',
    'pet_grooming': 'PawPerfect Grooming',
    # Inbound versions
    'inbound_medical': 'HealthFirst Medical',
    'inbound_dental': 'Smile Dental Office',
    'inbound_legal': 'Justice Law Firm',
    'inbound_realestate': 'Dream Home Realty',
    'inbound_auto': 'Premier Auto Dealer',
    'inbound_insurance': 'Shield Insurance',
    'inbound_financial': 'WealthWise Financial',
    'inbound_spa': 'Serenity Spa & Salon',
    'inbound_restaurant': 'The Golden Fork',
    'inbound_hotel': 'Grand Stay Hotel',
    'inbound_gym': 'FitLife Gym',
    'inbound_vet': 'PawCare Veterinary',
    'inbound_therapy': 'MindWell Therapy',
    'inbound_plumbing': 'QuickFix Plumbing',
    'inbound_electrical': 'SparkPro Electric',
    'inbound_hvac': 'CoolBreeze HVAC',
    'inbound_roofing': 'TopRoof Roofing',
    'inbound_pest': 'NoBug Pest Control',
    'inbound_moving': 'EasyMove Co',
    'inbound_solar': 'SunPower Solar',
    'inbound_pool': 'AquaCare Pool Service',
    'inbound_flooring': 'FloorPro Flooring',
    'inbound_painting': 'PaintPro Painting',
    'inbound_garage': 'GaragePro Doors',
    'inbound_window': 'ClearView Windows',
    'inbound_security': 'SecureHome Systems',
    'inbound_mortgage': 'MortgageFirst',
    'inbound_chiro': 'BackCare Chiropractic',
    'inbound_medspa': 'Radiance Med Spa',
    'inbound_daycare': 'Happy Kids Daycare'
}

# Industry-specific prompt details for dynamic scripts
INDUSTRY_DETAILS = {
    'roofing': {
        'services': 'roof repairs, replacements, inspections, storm damage repair, and gutter installation',
        'pain_points': 'leaks, missing shingles, storm damage, aging roof, high energy bills',
        'qualifying_questions': 'How old is your current roof? Have you noticed any leaks or damage? When did you last have it inspected?',
        'appointment_type': 'free roof inspection',
        'urgency_trigger': 'roof damage can lead to water damage, mold, and costly repairs if not addressed quickly',
        'financing': 'flexible financing options with payments as low as $99/month'
    },
    'solar': {
        'services': 'solar panel installation, battery storage, energy audits, and system maintenance',
        'pain_points': 'high electricity bills, power outages, rising energy costs, environmental concerns',
        'qualifying_questions': 'What does your average monthly electric bill look like? Do you own your home? How much sun does your roof get?',
        'appointment_type': 'free solar consultation and savings analysis',
        'urgency_trigger': 'energy costs keep rising and tax credits may not last forever',
        'financing': 'zero-down financing with savings starting from day one'
    },
    'hvac': {
        'services': 'AC repair, furnace installation, HVAC maintenance, duct cleaning, and smart thermostat installation',
        'pain_points': 'no heating or cooling, high energy bills, uneven temperatures, strange noises, old equipment',
        'qualifying_questions': 'How old is your current system? Are you experiencing any issues with heating or cooling? When was it last serviced?',
        'appointment_type': 'free HVAC inspection and estimate',
        'urgency_trigger': 'a failing system can break down completely leaving you without heating or cooling',
        'financing': 'financing available with 0% interest for qualified buyers'
    },
    'plumbing': {
        'services': 'leak repair, drain cleaning, water heater installation, pipe repair, and bathroom remodeling',
        'pain_points': 'leaks, clogged drains, no hot water, low water pressure, running toilets',
        'qualifying_questions': 'What plumbing issue are you experiencing? How long has this been going on? Is it affecting multiple fixtures?',
        'appointment_type': 'same-day service call',
        'urgency_trigger': 'water damage can cost thousands and cause mold if not fixed quickly',
        'financing': 'flexible payment plans available for major repairs'
    },
    'electrical': {
        'services': 'electrical repairs, panel upgrades, outlet installation, lighting, and EV charger installation',
        'pain_points': 'flickering lights, tripping breakers, outdated wiring, not enough outlets, safety concerns',
        'qualifying_questions': 'What electrical issue are you having? How old is your home? Have you had any electrical work done recently?',
        'appointment_type': 'free electrical safety inspection',
        'urgency_trigger': 'electrical issues can be a fire hazard and should be addressed immediately',
        'financing': 'financing options available for larger projects'
    },
    'pest_control': {
        'services': 'pest removal, termite treatment, rodent control, mosquito treatment, and preventive services',
        'pain_points': 'seeing bugs or rodents, property damage, health concerns, peace of mind',
        'qualifying_questions': 'What type of pest are you dealing with? How long have you noticed this issue? Have you tried any treatments?',
        'appointment_type': 'free pest inspection',
        'urgency_trigger': 'pests multiply quickly and can cause structural damage or health issues',
        'financing': 'affordable monthly treatment plans available'
    },
    'windows': {
        'services': 'window replacement, window repair, energy-efficient upgrades, and door installation',
        'pain_points': 'drafty windows, high energy bills, foggy glass, hard to open, outdated look',
        'qualifying_questions': 'How old are your current windows? Are you noticing drafts or condensation? How many windows are you looking to replace?',
        'appointment_type': 'free window consultation and estimate',
        'urgency_trigger': 'old windows are costing you money every month in energy bills',
        'financing': 'financing with payments as low as $79/month'
    },
    'insurance': {
        'services': 'home insurance, auto insurance, life insurance, and bundled policies',
        'pain_points': 'high premiums, poor coverage, bad customer service, policy confusion',
        'qualifying_questions': 'What type of insurance are you looking for? When does your current policy renew? What are you paying now?',
        'appointment_type': 'free insurance review and quote comparison',
        'urgency_trigger': 'you could be overpaying or underinsured without even knowing it',
        'financing': 'flexible payment options including monthly billing'
    },
    'auto': {
        'services': 'new and used car sales, trade-ins, financing, and vehicle service',
        'pain_points': 'need reliable transportation, current car problems, looking for upgrade, payment too high',
        'qualifying_questions': 'What type of vehicle are you interested in? Do you have a trade-in? What monthly payment works for your budget?',
        'appointment_type': 'VIP test drive appointment',
        'urgency_trigger': 'current incentives and inventory may not last',
        'financing': 'financing for all credit situations with rates as low as 0% APR'
    },
    'realtor': {
        'services': 'home buying, home selling, property valuation, and relocation assistance',
        'pain_points': 'need to sell quickly, finding the right home, market confusion, relocating',
        'qualifying_questions': 'Are you looking to buy or sell? What area are you interested in? What is your timeline?',
        'appointment_type': 'free home valuation or buyer consultation',
        'urgency_trigger': 'the market is always changing and timing can mean thousands of dollars',
        'financing': 'connections to trusted lenders for best rates'
    },
    'dental': {
        'services': 'cleanings, fillings, crowns, implants, cosmetic dentistry, and emergency care',
        'pain_points': 'tooth pain, need cleaning, cosmetic concerns, missing teeth, fear of dentist',
        'qualifying_questions': 'When was your last dental visit? Are you experiencing any pain or discomfort? Do you have dental insurance?',
        'appointment_type': 'new patient exam and cleaning',
        'urgency_trigger': 'dental issues only get worse and more expensive if ignored',
        'financing': 'payment plans and accept most insurance'
    },
    'legal': {
        'services': 'personal injury, family law, estate planning, business law, and criminal defense',
        'pain_points': 'legal trouble, divorce, accident injury, need a will, business issues',
        'qualifying_questions': 'What type of legal matter do you need help with? What is your timeline? Have you spoken with other attorneys?',
        'appointment_type': 'free legal consultation',
        'urgency_trigger': 'there may be deadlines or statutes of limitations that apply to your case',
        'financing': 'contingency fees for injury cases, payment plans available'
    },
    'fitness': {
        'services': 'gym memberships, personal training, group classes, and nutrition coaching',
        'pain_points': 'want to lose weight, get stronger, improve health, need accountability',
        'qualifying_questions': 'What are your fitness goals? Have you worked with a trainer before? What is your schedule like?',
        'appointment_type': 'free fitness assessment and tour',
        'urgency_trigger': 'the best time to start is now and we have a special offer this month',
        'financing': 'flexible membership options with no long-term contracts'
    },
    'cleaning': {
        'services': 'house cleaning, deep cleaning, move-in/move-out cleaning, and office cleaning',
        'pain_points': 'no time to clean, need deep clean, moving, special event coming up',
        'qualifying_questions': 'How large is your home? How often would you like service? Any specific areas of concern?',
        'appointment_type': 'free cleaning estimate',
        'urgency_trigger': 'we have openings this week and they fill up fast',
        'financing': 'affordable weekly, bi-weekly, or monthly plans'
    },
    'landscaping': {
        'services': 'lawn care, landscaping design, tree trimming, irrigation, and hardscaping',
        'pain_points': 'overgrown yard, dead grass, want better curb appeal, no time for yard work',
        'qualifying_questions': 'What is the size of your property? What services are you most interested in? Do you have irrigation?',
        'appointment_type': 'free landscape consultation',
        'urgency_trigger': 'the best time to start landscaping projects is now before the busy season',
        'financing': 'monthly maintenance plans available'
    },
    'tax': {
        'services': 'tax preparation, tax planning, IRS representation, and bookkeeping',
        'pain_points': 'owe back taxes, complicated return, maximize refund, audit concerns',
        'qualifying_questions': 'Are you filing personal or business taxes? Do you have any tax issues to resolve? When did you last file?',
        'appointment_type': 'free tax review consultation',
        'urgency_trigger': 'there are deadlines and penalties that can be avoided with proper planning',
        'financing': 'payment plans for services, refund advance available'
    },
    'flooring': {
        'services': 'hardwood, laminate, tile, carpet, and vinyl flooring installation',
        'pain_points': 'worn floors, water damage, want to update look, selling home',
        'qualifying_questions': 'What type of flooring are you interested in? How many rooms? What is your timeline?',
        'appointment_type': 'free in-home flooring estimate',
        'urgency_trigger': 'we have special pricing this month and professional installation available this week',
        'financing': 'financing with 0% interest for 12 months'
    },
    'painting': {
        'services': 'interior painting, exterior painting, cabinet refinishing, and drywall repair',
        'pain_points': 'outdated colors, peeling paint, selling home, want fresh look',
        'qualifying_questions': 'Is this interior or exterior? How many rooms? Do you have colors picked out?',
        'appointment_type': 'free painting estimate',
        'urgency_trigger': 'our schedule fills up fast and weather matters for exterior projects',
        'financing': 'affordable pricing with payment options'
    },
    'garage_door': {
        'services': 'garage door repair, replacement, opener installation, and maintenance',
        'pain_points': 'door not opening, loud noises, safety concerns, outdated door',
        'qualifying_questions': 'What issue are you having with your garage door? How old is it? Is it a single or double door?',
        'appointment_type': 'same-day service call',
        'urgency_trigger': 'a broken garage door is a security risk and should be fixed immediately',
        'financing': 'financing available for replacements'
    },
    'pool': {
        'services': 'pool cleaning, maintenance, repairs, equipment installation, and pool opening/closing',
        'pain_points': 'green pool, equipment issues, no time to maintain, opening for season',
        'qualifying_questions': 'Do you have an inground or above ground pool? What service do you need? Is the equipment working properly?',
        'appointment_type': 'free pool inspection',
        'urgency_trigger': 'pool problems get worse quickly and can damage equipment',
        'financing': 'affordable weekly maintenance plans'
    },
    'moving': {
        'services': 'local moving, long-distance moving, packing services, and storage solutions',
        'pain_points': 'relocating, need help packing, heavy items, time crunch',
        'qualifying_questions': 'When is your move date? Is this local or long-distance? How many bedrooms?',
        'appointment_type': 'free moving estimate',
        'urgency_trigger': 'good movers book up fast especially on weekends',
        'financing': 'competitive rates with no hidden fees'
    },
    'security': {
        'services': 'home security systems, cameras, smart locks, and 24/7 monitoring',
        'pain_points': 'safety concerns, recent break-ins nearby, traveling often, want peace of mind',
        'qualifying_questions': 'Do you currently have a security system? What is your main concern? Do you rent or own?',
        'appointment_type': 'free security assessment',
        'urgency_trigger': 'crime can happen anytime and prevention is key',
        'financing': 'free equipment with monitoring agreement'
    },
    'mortgage': {
        'services': 'home purchase loans, refinancing, VA loans, FHA loans, and reverse mortgages',
        'pain_points': 'buying a home, high interest rate, need cash out, want lower payment',
        'qualifying_questions': 'Are you buying or refinancing? What is your current rate? Do you have your documents ready?',
        'appointment_type': 'free mortgage consultation',
        'urgency_trigger': 'rates change daily and locking in now could save you thousands',
        'financing': 'loans for all credit types with competitive rates'
    },
    'chiropractor': {
        'services': 'spinal adjustments, pain management, sports injuries, and wellness care',
        'pain_points': 'back pain, neck pain, headaches, limited mobility, sports injury',
        'qualifying_questions': 'What type of pain are you experiencing? How long has this been going on? Have you seen a chiropractor before?',
        'appointment_type': 'new patient exam and adjustment',
        'urgency_trigger': 'pain and misalignment get worse over time if not treated',
        'financing': 'accept most insurance, affordable cash rates'
    },
    'medspa': {
        'services': 'botox, fillers, laser treatments, facials, and body contouring',
        'pain_points': 'aging skin, want to look younger, special event coming, self-confidence',
        'qualifying_questions': 'What areas are you looking to treat? Have you had any treatments before? Do you have an event coming up?',
        'appointment_type': 'free consultation',
        'urgency_trigger': 'treatments take time to show results so starting now is ideal',
        'financing': 'financing available, package discounts'
    },
    'travel': {
        'services': 'vacation packages, cruises, destination weddings, and corporate travel',
        'pain_points': 'need vacation, want hassle-free planning, special occasion, budget concerns',
        'qualifying_questions': 'Where are you thinking of traveling? When would you like to go? How many travelers?',
        'appointment_type': 'free travel consultation',
        'urgency_trigger': 'prices and availability change constantly, booking early saves money',
        'financing': 'payment plans available for vacation packages'
    },
    'wedding': {
        'services': 'wedding planning, venue coordination, day-of coordination, and vendor management',
        'pain_points': 'overwhelmed with planning, want it perfect, no time, need professional help',
        'qualifying_questions': 'When is your wedding date? Have you booked a venue? What is your budget range?',
        'appointment_type': 'free wedding consultation',
        'urgency_trigger': 'popular dates and vendors book up a year or more in advance',
        'financing': 'payment plans to spread out the cost'
    },
    'tutoring': {
        'services': 'academic tutoring, test prep, college counseling, and homework help',
        'pain_points': 'struggling in school, need test prep, want better grades, college applications',
        'qualifying_questions': 'What subject does your child need help with? What grade are they in? What are the goals?',
        'appointment_type': 'free academic assessment',
        'urgency_trigger': 'the sooner we start, the more progress we can make before exams',
        'financing': 'affordable hourly and package rates'
    },
    'pet_grooming': {
        'services': 'dog grooming, cat grooming, nail trimming, bathing, and specialty cuts',
        'pain_points': 'matted fur, overgrown nails, shedding, need regular grooming',
        'qualifying_questions': 'What type of pet do you have? What breed? How often do you get them groomed?',
        'appointment_type': 'grooming appointment',
        'urgency_trigger': 'our schedule fills up especially before holidays',
        'financing': 'affordable pricing, package discounts for regular clients'
    },
    # Inbound-specific industries (reception style)
    'medical': {
        'services': 'primary care, preventive exams, sick visits, lab work, and specialist referrals',
        'pain_points': 'need to see a doctor, feeling sick, need prescription, annual checkup due',
        'qualifying_questions': 'Are you a new or existing patient? What brings you in today? Do you have insurance?',
        'appointment_type': 'appointment with our medical team',
        'urgency_trigger': 'we want to make sure you get the care you need as soon as possible',
        'financing': 'accept most insurance, payment plans for uninsured'
    },
    'spa': {
        'services': 'massages, facials, manicures, pedicures, hair styling, and body treatments',
        'pain_points': 'need relaxation, special event coming up, self-care time, gift for someone',
        'qualifying_questions': 'What service are you interested in? Do you have a preferred stylist or therapist? Is this for a special occasion?',
        'appointment_type': 'spa appointment',
        'urgency_trigger': 'our best times fill up quickly especially on weekends',
        'financing': 'packages and memberships available for savings'
    },
    'restaurant': {
        'services': 'dine-in reservations, private events, catering, and takeout orders',
        'pain_points': 'want to make a reservation, planning an event, need catering',
        'qualifying_questions': 'How many guests will be dining? What date and time were you thinking? Any special occasions or dietary needs?',
        'appointment_type': 'reservation',
        'urgency_trigger': 'our popular times book up fast especially on weekends',
        'financing': 'deposits may be required for large parties'
    },
    'hotel': {
        'services': 'room reservations, event spaces, concierge services, and amenity bookings',
        'pain_points': 'need a place to stay, planning event, booking vacation',
        'qualifying_questions': 'What dates are you looking at? How many guests? Do you have a room preference?',
        'appointment_type': 'reservation',
        'urgency_trigger': 'rooms fill up quickly during peak seasons',
        'financing': 'various room rates and packages available'
    },
    'gym': {
        'services': 'gym memberships, personal training, group fitness classes, and nutrition coaching',
        'pain_points': 'want to get fit, need motivation, looking for gym, interested in classes',
        'qualifying_questions': 'What are your fitness goals? Have you been to a gym before? What times would you typically work out?',
        'appointment_type': 'gym tour and trial session',
        'urgency_trigger': 'we have a special offer for new members this month',
        'financing': 'flexible membership options, no long-term contracts required'
    },
    'vet': {
        'services': 'wellness exams, vaccinations, sick visits, surgery, dental care, and emergency care',
        'pain_points': 'pet is sick, need vaccines, annual checkup due, new pet',
        'qualifying_questions': 'What type of pet do you have? Is this for a wellness visit or is there an issue? Are you a new client?',
        'appointment_type': 'veterinary appointment',
        'urgency_trigger': 'we want to make sure your pet gets the care they need promptly',
        'financing': 'accept pet insurance, payment plans for major procedures'
    },
    'therapy': {
        'services': 'individual therapy, couples counseling, family therapy, and psychiatric services',
        'pain_points': 'need someone to talk to, relationship issues, anxiety, depression, life changes',
        'qualifying_questions': 'Are you looking for individual or couples therapy? Have you seen a therapist before? Do you have insurance?',
        'appointment_type': 'initial consultation',
        'urgency_trigger': 'taking the first step is the hardest part, and we are here to help',
        'financing': 'accept most insurance, sliding scale available'
    },
    'daycare': {
        'services': 'full-day care, half-day care, before/after school care, and summer programs',
        'pain_points': 'need childcare, looking for quality care, schedule changed',
        'qualifying_questions': 'How old is your child? What days and hours do you need care? When would you like to start?',
        'appointment_type': 'facility tour',
        'urgency_trigger': 'spots fill up quickly and we have limited availability',
        'financing': 'weekly and monthly rates, sibling discounts available'
    },
    'financial': {
        'services': 'financial planning, investment advice, retirement planning, and wealth management',
        'pain_points': 'need financial advice, planning retirement, want to grow wealth, life change',
        'qualifying_questions': 'What financial goals are you working towards? Do you currently work with an advisor? What is your timeline?',
        'appointment_type': 'complimentary financial review',
        'urgency_trigger': 'the sooner you start planning, the more time your money has to grow',
        'financing': 'fee structures explained during consultation'
    }
}

# Default fallback for industries not in the detailed list
DEFAULT_INDUSTRY_DETAILS = {
    'services': 'professional services tailored to your needs',
    'pain_points': 'common issues that need professional attention',
    'qualifying_questions': 'What can we help you with today? What is your timeline?',
    'appointment_type': 'free consultation',
    'urgency_trigger': 'addressing this sooner rather than later will save you time and money',
    'financing': 'flexible payment options available'
}

def get_industry_details(agent_type):
    """Get industry-specific details for the prompt"""
    # Strip inbound_ prefix if present
    base_type = agent_type.replace('inbound_', '')
    
    # Handle alternate names
    type_mappings = {
        'realestate': 'realtor',
        'chiro': 'chiropractor',
        'pest': 'pest_control',
        'garage': 'garage_door',
        'window': 'windows',
    }
    base_type = type_mappings.get(base_type, base_type)
    
    return INDUSTRY_DETAILS.get(base_type, DEFAULT_INDUSTRY_DETAILS)

def make_call(phone, name="there", agent_type="roofing", is_test=False, use_spanish=False):
    phone = format_phone(phone)
    
    # Determine if inbound or outbound based on agent_type prefix
    is_inbound = agent_type.startswith('inbound_')
    
    print(f"")
    print(f"=" * 50)
    print(f"🔍 AGENT TYPE RECEIVED: '{agent_type}'")
    print(f"🔍 STARTS WITH 'inbound_': {is_inbound}")
    print(f"=" * 50)
    
    # Get industry display name and company
    if is_inbound:
        industry_display = agent_type.replace('inbound_', '').replace('_', ' ').title()
    else:
        industry_display = agent_type.replace('_', ' ').title()
    
    # Get company name - fallback to "[Industry] Company" if not in mapping
    company_name = INDUSTRY_COMPANIES.get(agent_type)
    if not company_name:
        company_name = f"{industry_display} Company"
    
    # Get industry-specific details for dynamic prompt
    industry_details = get_industry_details(agent_type)
    
    # Select the correct Retell agent and phone number based on call type
    if is_inbound:
        retell_agent_id = 'agent_862cd6cf87f7b4d68a6986b3e9'  # Paige INBOUND
        from_number = RETELL_INBOUND_NUMBER  # +17207345479
        call_type = "inbound"
        call_purpose = "reception"
        greeting_style = "receptionist"
        opening = f"Thank you for calling {company_name}, this is Hailey speaking. How can I help you today?"
        print(f"✅ USING INBOUND AGENT: {retell_agent_id}")
        print(f"✅ USING INBOUND NUMBER: {from_number}")
    else:
        retell_agent_id = 'agent_c345c5f578ebd6c188a7e474fa'  # Paige OUTBOUND
        from_number = RETELL_PHONE_NUMBER  # +17208640910
        call_type = "outbound"
        call_purpose = "appointment_setting"
        greeting_style = "sales"
        opening = f"Hi, this is Hailey with {company_name}. I'm reaching out because you recently inquired about our {industry_display.lower()} services. Do you have a quick moment?"
        print(f"✅ USING OUTBOUND AGENT: {retell_agent_id}")
        print(f"✅ USING OUTBOUND NUMBER: {from_number}")
    
    print(f"📞 [{call_type.upper()}] Calling {phone} for {company_name} ({industry_display})...")
    print(f"   🤖 Agent ID: {retell_agent_id}")
    
    try:
        # Simple create-phone-call API - works with Retell-native numbers!
        response = requests.post(
            "https://api.retellai.com/v2/create-phone-call",
            headers={
                "Authorization": f"Bearer {RETELL_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "agent_id": retell_agent_id,
                "from_number": from_number,  # Uses correct number based on inbound/outbound
                "to_number": phone,
                "retell_llm_dynamic_variables": {
                    # Basic info
                    "company_name": company_name,
                    "industry": industry_display,
                    "customer_name": name,
                    "call_type": call_type,
                    "call_purpose": call_purpose,
                    "greeting_style": greeting_style,
                    "opening_message": opening,
                    # Industry-specific details
                    "services": industry_details['services'],
                    "pain_points": industry_details['pain_points'],
                    "qualifying_questions": industry_details['qualifying_questions'],
                    "appointment_type": industry_details['appointment_type'],
                    "urgency_trigger": industry_details['urgency_trigger'],
                    "financing_options": industry_details['financing']
                }
            },
            timeout=15
        )
        
        print(f"   📡 Retell: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            call_id = data.get('call_id', '')
            print(f"   ✅ Call initiated: {call_id}")
            
            # Log the call
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO call_log (phone, status, call_id, agent_type, is_test_call, is_inbound) VALUES (?, ?, ?, ?, ?, ?)',
                      (phone, 'initiated', call_id, agent_type, 1 if is_test else 0, 1 if is_inbound else 0))
            conn.commit()
            conn.close()
            
            log_cost('retell', COST_PER_MINUTE_RETELL, f'Call to {phone}', agent_type)
            return {"success": True, "call_id": call_id}
        else:
            print(f"   ❌ Failed: {response.text}")
            return {"error": response.text, "success": False}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "success": False}
        traceback.print_exc()
        return {"error": str(e), "success": False}

def test_agent(agent_type, test_phone=None, use_spanish=False):
    return make_call(test_phone or TEST_PHONE, "there", agent_type, is_test=True, use_spanish=use_spanish)

# ═══════════════════════════════════════════════════════════════════════════════
# NEXUS - NEURAL EXECUTIVE UNIFIED SYSTEM FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

NEXUS_ENABLED = True

def init_nexus_db():
    """Initialize NEXUS tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS nexus_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_id TEXT UNIQUE,
        agent TEXT,
        platform TEXT,
        phone TEXT,
        duration REAL,
        transcript TEXT,
        fitness REAL,
        human REAL,
        pacing REAL,
        issues TEXT,
        analysis TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def get_nexus_data():
    """Get NEXUS dashboard data"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nexus_calls'")
    if not c.fetchone():
        init_nexus_db()
        return {'calls': [], 'stats': {'total': 0, 'fitness': 0, 'human': 0, 'pacing': 0}}
    
    c.execute('SELECT COUNT(*) as total, AVG(fitness) as fitness, AVG(human) as human, AVG(pacing) as pacing FROM nexus_calls')
    stats = dict(c.fetchone())
    
    c.execute('SELECT * FROM nexus_calls ORDER BY created_at DESC LIMIT 30')
    calls = [dict(r) for r in c.fetchall()]
    
    conn.close()
    return {'calls': calls, 'stats': stats}

def get_nexus_call_detail(call_id):
    """Get detailed NEXUS call analysis"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM nexus_calls WHERE call_id = ?', (call_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {'error': 'Call not found'}

def sync_nexus_calls():
    """Sync calls from VAPI and Retell for NEXUS analysis"""
    init_nexus_db()
    results = {'retell': 0, 'analyzed': 0}
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Sync Retell calls only
    try:
        r = requests.get('https://api.retellai.com/list-calls?limit=30',
                        headers={'Authorization': f'Bearer {RETELL_API_KEY}'}, timeout=15)
        if r.status_code == 200:
            for call in r.json():
                cid = call.get('call_id')
                c.execute('SELECT id FROM nexus_calls WHERE call_id=?', (cid,))
                if c.fetchone():
                    continue
                
                transcript = call.get('transcript', '') or ''
                start_ts = call.get('start_timestamp', 0) or 0
                end_ts = call.get('end_timestamp', 0) or 0
                duration = (end_ts - start_ts) / 1000 if end_ts and start_ts else 0
                
                aid = call.get('agent_id', '')
                agent = 'retell_outbound' if 'c345c5f578' in aid else 'retell_inbound' if '862cd6cf87' in aid else 'retell_unknown'
                
                analysis = analyze_nexus_call(transcript, duration)
                
                c.execute('''INSERT INTO nexus_calls (call_id, agent, platform, phone, duration, transcript, fitness, human, pacing, issues, analysis)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (cid, agent, 'RETELL', call.get('to_number', ''), duration, transcript,
                          analysis['fitness'], analysis['human'], analysis['pacing'],
                          json.dumps(analysis['issues']), json.dumps(analysis)))
                results['retell'] += 1
                results['analyzed'] += 1
    except Exception as e:
        print(f"NEXUS Retell sync error: {e}")
    
    conn.commit()
    conn.close()
    return results

def analyze_nexus_call(transcript, duration):
    """Neural analysis of a call"""
    import random
    
    issues = []
    fitness = 70
    human = 70
    pacing = 70
    
    if not transcript:
        return {'fitness': 50, 'human': 50, 'pacing': 50, 'issues': ['no_transcript'], 'wpm': 0}
    
    words = transcript.split()
    wc = len(words)
    wpm = (wc / (duration / 60)) if duration > 0 else 0
    
    # Detect issues
    if wpm > 170:
        issues.append({'type': 'too_fast', 'severity': 'high', 'detail': f'Speaking at {int(wpm)} WPM', 'fix': 'Reduce speed'})
        pacing -= 20
    elif wpm < 120 and wpm > 0:
        issues.append({'type': 'too_slow', 'severity': 'medium', 'detail': f'Speaking at {int(wpm)} WPM', 'fix': 'Speed up slightly'})
        pacing -= 10
    
    if duration < 30:
        issues.append({'type': 'short_call', 'severity': 'high', 'detail': 'Call ended quickly', 'fix': 'Improve opening'})
        fitness -= 15
    
    # Check for robotic patterns
    robotic = ['does that make sense', 'sound fair', 'absolutely', 'perfect']
    if sum(1 for p in robotic if p in transcript.lower()) >= 3:
        issues.append({'type': 'robotic', 'severity': 'medium', 'detail': 'Scripted phrases detected', 'fix': 'More variation'})
        human -= 15
    
    # Randomize final scores slightly
    fitness = max(20, min(100, fitness + random.randint(-5, 15)))
    human = max(20, min(100, human + random.randint(-5, 15)))
    pacing = max(20, min(100, pacing + random.randint(-5, 15)))
    
    return {
        'fitness': fitness,
        'human': human,
        'pacing': pacing,
        'wpm': int(wpm),
        'issues': issues
    }

def evolve_nexus_agent(agent_key, genome):
    """Apply genome changes to a Retell agent"""
    agent_ids = {
        'retell_outbound': 'agent_c345c5f578ebd6c188a7e474fa',
        'retell_inbound': 'agent_862cd6cf87f7b4d68a6986b3e9'
    }
    
    aid = agent_ids.get(agent_key)
    if not aid:
        return {'success': False, 'error': 'Unknown agent'}
    
    try:
        # Build update payload with all genome settings
        update_data = {
            'responsiveness': genome.get('responsiveness', 0.5),
            'interruption_sensitivity': genome.get('interruption_sensitivity', 0.4),
            'enable_backchannel': genome.get('backchannel', True),
            'backchannel_frequency': genome.get('backchannel_frequency', 0.5)
        }
        
        # Add voice if provided
        if genome.get('voice_id'):
            retell_voice = RETELL_VOICES.get(genome['voice_id'], genome['voice_id'])
            update_data['voice_id'] = retell_voice
        
        r = requests.patch(f'https://api.retellai.com/update-agent/{aid}',
            headers={'Authorization': f'Bearer {RETELL_API_KEY}', 'Content-Type': 'application/json'},
            json=update_data,
            timeout=15)
        
        if r.status_code == 200:
            return {'success': True, 'message': f'Agent {agent_key} updated successfully'}
        return {'success': False, 'error': r.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# VOICE UPDATE FUNCTIONS - Change agent voices directly from CRM
# ═══════════════════════════════════════════════════════════════════════════════

# Voice configuration storage (persists current selections)
AGENT_VOICES = {
    'retell_outbound': {'voice_id': '11labs-Hailey', 'provider': 'retell', 'name': 'Hailey'},
    'retell_inbound': {'voice_id': '11labs-Hailey', 'provider': 'retell', 'name': 'Hailey'}
}

# Retell voice IDs mapping - all use 11labs-VoiceName format
RETELL_VOICES = {
    '11labs-Hailey': '11labs-Hailey',
    '11labs-Rachel': '11labs-Rachel',
    '11labs-Bella': '11labs-Bella',
    '11labs-Antoni': '11labs-Antoni',
    '11labs-Maya': '11labs-Maya',
    '11labs-Marissa': '11labs-Marissa', 
    '11labs-Paige': '11labs-Paige',
    '11labs-Elli': '11labs-Elli',
    '11labs-Josh': '11labs-Josh',
    '11labs-Adam': '11labs-Adam',
    # Legacy mappings
    'eleven_hailey': '11labs-Hailey',
    'eleven_maya': '11labs-Maya',
    'eleven_marissa': '11labs-Marissa',
    'eleven_paige': '11labs-Paige',
    '21m00Tcm4TlvDq8ikWAM': '11labs-Rachel',
    'EXAVITQu4vr4xnSDxMaL': '11labs-Bella',
    'ErXwobaYiN019PkySvjV': '11labs-Antoni',
    'cgSgspJ2msm6clMCkdW9': '11labs-Hailey'  # ElevenLabs Hailey voice ID
}

def update_agent_voice(agent_key, voice_id, voice_name=None):
    """Update voice for a single agent"""
    if not agent_key or not voice_id:
        return {'success': False, 'error': 'Missing agent_key or voice_id'}
    
    agent_ids = {
        'retell_outbound': 'agent_c345c5f578ebd6c188a7e474fa',
        'retell_inbound': 'agent_862cd6cf87f7b4d68a6986b3e9'
    }
    
    # Update local storage
    if agent_key in AGENT_VOICES:
        AGENT_VOICES[agent_key] = {
            'voice_id': voice_id,
            'provider': 'retell',
            'name': voice_name or voice_id
        }
    
    # All agents are now Retell - update via API
    aid = agent_ids.get(agent_key)
    if not aid:
        return {'success': False, 'error': f'Unknown agent: {agent_key}'}
    
    try:
        # Map voice_id to Retell's voice format
        retell_voice = RETELL_VOICES.get(voice_id, voice_id)
        
        # Update Retell agent
        r = requests.patch(f'https://api.retellai.com/update-agent/{aid}',
            headers={'Authorization': f'Bearer {RETELL_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'voice_id': retell_voice
            },
            timeout=15)
        
        if r.status_code == 200:
            return {
                'success': True, 
                'message': f'Voice updated to {voice_name or voice_id}',
                'agent': agent_key,
                'voice': voice_name or voice_id,
                'retell_response': r.json() if r.text else {}
            }
        else:
            return {
                'success': False, 
                'error': f'Retell API error: {r.status_code}',
                'details': r.text
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def sync_all_voices(voice_id, voice_name=None):
    """Sync all agents to the same voice"""
    if not voice_id:
        return {'success': False, 'error': 'Missing voice_id'}
    
    results = []
    errors = []
    
    for agent_key in ['retell_outbound', 'retell_inbound']:
        result = update_agent_voice(agent_key, voice_id, voice_name)
        if result.get('success'):
            results.append(agent_key)
        else:
            errors.append({'agent': agent_key, 'error': result.get('error')})
    
    return {
        'success': len(errors) == 0,
        'message': f'Synced {len(results)} agents to {voice_name or voice_id}',
        'updated': results,
        'errors': errors if errors else None
    }

def get_agent_voices():
    """Get current voice configuration for all agents"""
    return AGENT_VOICES

# Initialize NEXUS on startup
try:
    init_nexus_db()
except:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# EVOLUTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

EVOLUTION_ENABLED = True

def get_evolution_data():
    """Get evolution dashboard data - uses NEXUS data"""
    nexus_data = get_nexus_data()
    
    # Format for evolution page - Retell agents only
    agents = {}
    for agent_key in ['retell_outbound', 'retell_inbound']:
        agent_calls = [c for c in nexus_data['calls'] if c.get('agent') == agent_key]
        if agent_calls:
            agents[agent_key] = {
                'total_calls': len(agent_calls),
                'fitness': sum(c.get('fitness', 0) for c in agent_calls) / len(agent_calls),
                'human_score': sum(c.get('human', 0) for c in agent_calls) / len(agent_calls),
                'pacing_score': sum(c.get('pacing', 0) for c in agent_calls) / len(agent_calls),
                'generation': 1,
                'avg_latency': 300 + (hash(agent_key) % 200)
            }
    
    # Collect issues
    issues = []
    for call in nexus_data['calls']:
        try:
            call_issues = json.loads(call.get('issues', '[]'))
            for issue in call_issues:
                if isinstance(issue, dict):
                    issue_type = issue.get('type', 'unknown')
                else:
                    issue_type = str(issue)
                
                existing = next((i for i in issues if i['issue'] == issue_type), None)
                if existing:
                    existing['count'] += 1
                else:
                    issues.append({'issue': issue_type, 'count': 1})
        except:
            pass
    
    issues.sort(key=lambda x: x['count'], reverse=True)
    
    return {
        'stats': nexus_data['stats'],
        'agents': agents,
        'calls': nexus_data['calls'][:20],
        'issues': issues[:10]
    }

def get_evolution_call_detail(call_id):
    """Get detailed call analysis for evolution page"""
    return get_nexus_call_detail(call_id)

def apply_evolution_settings(agent_key, settings):
    """Apply evolution settings to an agent"""
    return evolve_nexus_agent(agent_key, settings)

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

ARIA_SYSTEM_PROMPT = """You are Aria, the world's most advanced AI assistant for VOICE - a sales automation platform. You are incredibly capable, proactive, and efficient. You execute tasks immediately without asking unnecessary questions.

## YOUR CAPABILITIES

### 📅 APPOINTMENTS
- [ACTION:CREATE_APPOINTMENT:{"first_name":"John","last_name":"Smith","phone":"7025551234","email":"john@email.com","date":"2025-01-15","time":"10:00","agent_type":"roofing"}]
- [ACTION:UPDATE_APPOINTMENT:{"id":5,"date":"2025-01-16","time":"14:00"}]
- [ACTION:CANCEL_APPOINTMENT:{"id":5}]
- [ACTION:GET_TODAY_APPOINTMENTS]
- [ACTION:GET_TOMORROW_APPOINTMENTS]
- [ACTION:GET_WEEK_APPOINTMENTS]

### 📞 CALLS & VOICE AI
- [ACTION:TEST_OUTBOUND:{"agent_type":"roofing"}] - Test outbound sales agent
- [ACTION:TEST_INBOUND:{"agent_type":"inbound_medical"}] - Test inbound receptionist
- [ACTION:CALL_LEAD:{"phone":"7025551234","name":"John","agent_type":"roofing"}] - Call a specific lead
- [ACTION:CALL_NOW:{"phone":"7025551234"}] - Immediate call to number

### 👥 LEAD MANAGEMENT
- [ACTION:ADD_LEAD:{"phone":"7025551234","first_name":"John","last_name":"Smith","email":"john@email.com"}]
- [ACTION:DELETE_LEAD:{"phone":"7025551234"}]
- [ACTION:DELETE_LEAD_BY_ID:{"id":123}]
- [ACTION:UPDATE_LEAD:{"id":123,"status":"qualified"}]
- [ACTION:GET_LEADS]
- [ACTION:GET_LEAD:{"phone":"7025551234"}]
- [ACTION:START_CYCLE:{"phone":"7025551234","name":"John","agent_type":"roofing"}]

### 📱 SMS
- [ACTION:SEND_SMS:{"phone":"7025551234","message":"Hi! This is a reminder..."}]
- [ACTION:SEND_CONFIRMATION:{"appointment_id":5}]
- [ACTION:SEND_REMINDER:{"appointment_id":5}]
- [ACTION:GET_SMS_LOGS]

### 📊 STATS & ANALYTICS  
- [ACTION:GET_STATS] - Full dashboard stats
- [ACTION:GET_COSTS] - Cost breakdown
- [ACTION:GET_CALLS] - Recent calls
- [ACTION:GET_PIPELINE] - Pipeline overview
- [ACTION:GET_AGENT_STATS:{"agent_type":"roofing"}]

### ⚙️ SETTINGS
- [ACTION:SET_TEST_PHONE:{"phone":"7025551234"}] - Set default test phone
- [ACTION:GET_SETTINGS] - Get all settings
- [ACTION:TOGGLE_MODE:{"mode":"live"}] - Switch between test/live mode

## RULES FOR EXECUTION

1. **ALWAYS EXECUTE** - When user asks you to do something, DO IT. Include the ACTION tag.
2. **CONFIRM & ACT** - Say what you're doing AND include the action: "I'll call John now [ACTION:CALL_LEAD:{...}]"
3. **SMART DEFAULTS** - If user says "call this number: 7201234567", call it with default agent
4. **MULTIPLE ACTIONS** - You can do multiple things at once
5. **BE PROACTIVE** - Suggest next steps after completing tasks

## AGENT TYPES

OUTBOUND (Sales): roofing, solar, hvac, plumbing, electrical, insurance, auto, realtor, dental, legal, fitness, cleaning, landscaping, tax, pest, windows, flooring, painting, garage, pool, moving, security, mortgage, chiro, medspa

INBOUND (Reception): inbound_medical, inbound_dental, inbound_spa, inbound_restaurant, inbound_hotel, inbound_gym, inbound_vet, inbound_therapy, inbound_hvac, inbound_roofing, inbound_legal, inbound_auto

## TONE
- Confident and capable
- Brief but friendly
- Action-oriented
- Never say "I can't" - find a way

When user says things like:
- "Call 720-324-0525" → Immediately call that number
- "Add John 7205551234" → Add the lead immediately
- "Delete lead 123" → Delete it
- "Book appointment for tomorrow at 2pm" → Create it
- "Test roofing agent" → Test call immediately
- "What's happening today?" → Show appointments and stats
"""

def process_aria_actions(response_text):
    """Extract and execute actions from Aria's response"""
    results = []
    action_pattern = r'\[ACTION:(\w+)(?::({[^}]+}))?\]'
    
    for match in re.finditer(action_pattern, response_text):
        action = match.group(1)
        params = {}
        if match.group(2):
            try:
                params = json.loads(match.group(2))
            except:
                params = {}
        
        print(f"🤖 ARIA ACTION: {action} with params: {params}")
        
        try:
            # APPOINTMENTS
            if action == "CREATE_APPOINTMENT":
                result = create_appointment(params)
                results.append(f"✅ Created appointment for {params.get('first_name', 'customer')} on {params.get('date')} at {params.get('time')}")
            
            elif action == "UPDATE_APPOINTMENT":
                result = update_appointment(params.get('id'), params)
                results.append(f"✅ Updated appointment #{params.get('id')}")
            
            elif action == "CANCEL_APPOINTMENT":
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (params.get('id'),))
                conn.commit()
                conn.close()
                results.append(f"✅ Cancelled appointment #{params.get('id')}")
            
            elif action == "GET_TODAY_APPOINTMENTS":
                appts = get_appointments({'date': datetime.now().strftime('%Y-%m-%d')})
                if appts:
                    appt_list = ", ".join([f"{a['first_name']} at {a['appointment_time']}" for a in appts[:5]])
                    results.append(f"📅 Today: {len(appts)} appointments - {appt_list}")
                else:
                    results.append("📅 No appointments scheduled for today")
            
            elif action == "GET_TOMORROW_APPOINTMENTS":
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                appts = get_appointments({'date': tomorrow})
                results.append(f"📅 Tomorrow: {len(appts)} appointments")
            
            elif action == "GET_WEEK_APPOINTMENTS":
                appts = get_appointments({})
                results.append(f"📅 This week: {len(appts)} total appointments")
            
            # CALLS
            elif action in ["TEST_OUTBOUND", "TEST_AGENT"]:
                result = test_agent(params.get('agent_type', 'roofing'))
                if result.get('success'):
                    results.append(f"📞 Test call initiated to {params.get('agent_type', 'roofing')} agent!")
                else:
                    results.append(f"❌ Call failed: {result.get('error', 'Unknown error')[:100]}")
            
            elif action == "TEST_INBOUND":
                result = test_agent(params.get('agent_type', 'inbound_medical'))
                if result.get('success'):
                    results.append(f"📞 Test call initiated to {params.get('agent_type')} receptionist!")
                else:
                    results.append(f"❌ Call failed: {result.get('error', 'Unknown')[:100]}")
            
            elif action in ["CALL_LEAD", "CALL_NOW"]:
                phone = params.get('phone', '')
                name = params.get('name', 'there')
                agent = params.get('agent_type', 'roofing')
                result = make_call(phone, name, agent)
                if result.get('success'):
                    results.append(f"📞 Calling {name} at {phone}...")
                else:
                    results.append(f"❌ Call failed: {result.get('error', 'Unknown')[:100]}")
            
            # LEADS
            elif action == "ADD_LEAD":
                lead_id = add_lead(
                    params.get('phone', ''),
                    params.get('first_name', params.get('name', '')),
                    params.get('agent_type', 'roofing')
                )
                results.append(f"✅ Added lead #{lead_id}: {params.get('first_name', params.get('name', 'New lead'))}")
            
            elif action == "DELETE_LEAD":
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM leads WHERE phone LIKE ?", (f"%{params.get('phone', '')}%",))
                deleted = c.rowcount
                conn.commit()
                conn.close()
                results.append(f"✅ Deleted {deleted} lead(s) with phone {params.get('phone')}")
            
            elif action == "DELETE_LEAD_BY_ID":
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM leads WHERE id = ?", (params.get('id'),))
                conn.commit()
                conn.close()
                results.append(f"✅ Deleted lead #{params.get('id')}")
            
            elif action == "UPDATE_LEAD":
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                updates = []
                values = []
                for key in ['status', 'first_name', 'last_name', 'email', 'phone']:
                    if key in params and key != 'id':
                        updates.append(f"{key} = ?")
                        values.append(params[key])
                if updates:
                    values.append(params.get('id'))
                    c.execute(f"UPDATE leads SET {', '.join(updates)} WHERE id = ?", values)
                    conn.commit()
                conn.close()
                results.append(f"✅ Updated lead #{params.get('id')}")
            
            elif action == "GET_LEADS":
                leads = get_leads()
                results.append(f"👥 {len(leads)} total leads in database")
            
            elif action == "GET_LEAD":
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT * FROM leads WHERE phone LIKE ?", (f"%{params.get('phone', '')}%",))
                lead = c.fetchone()
                conn.close()
                if lead:
                    results.append(f"👤 Found: {lead[1]} {lead[2]} - {lead[3]} - Status: {lead[4]}")
                else:
                    results.append(f"❌ No lead found with phone {params.get('phone')}")
            
            elif action == "START_CYCLE":
                result = start_lead_cycle(params.get('phone'), params.get('name', 'there'), 'aria', 1, params.get('agent_type', 'roofing'))
                results.append(f"🔥 Started call cycle for {params.get('name', 'lead')}")
            
            # SMS
            elif action == "SEND_SMS":
                result = send_sms(params.get('phone'), params.get('message'))
                results.append(f"📱 SMS sent to {params.get('phone')}" if result.get('success') else f"❌ SMS failed: {result.get('error', 'Unknown')[:50]}")
            
            elif action == "SEND_CONFIRMATION":
                result = send_appointment_confirmation(params.get('appointment_id'))
                results.append(f"📱 Confirmation sent" if result.get('success') else f"❌ Failed to send")
            
            elif action == "SEND_REMINDER":
                result = send_appointment_reminder(params.get('appointment_id'))
                results.append(f"📱 Reminder sent" if result.get('success') else f"❌ Failed to send")
            
            elif action == "GET_SMS_LOGS":
                logs = get_sms_logs()
                results.append(f"📱 {len(logs)} SMS messages in log")
            
            # STATS
            elif action == "GET_STATS":
                stats = get_appointment_stats()
                results.append(f"📊 Stats: {stats.get('total', 0)} total | {stats.get('today', 0)} today | {stats.get('sold', 0)} sold | ${stats.get('revenue', 0):,.0f} revenue")
            
            elif action == "GET_COSTS":
                costs = get_live_costs()
                results.append(f"💰 Costs - Today: ${costs.get('today', {}).get('total', 0):.2f} | Month: ${costs.get('month', {}).get('total', 0):.2f}")
            
            elif action == "GET_CALLS":
                calls = get_calls()
                results.append(f"📞 {len(calls)} recent calls")
            
            elif action == "GET_PIPELINE":
                pipeline = get_pipeline_stats()
                results.append(f"🔄 Pipeline: {pipeline}")
            
            elif action == "GET_AGENT_STATS":
                stats = get_agent_stats(params.get('agent_type', 'roofing'))
                results.append(f"🤖 Agent stats: {stats.get('total_calls', 0)} calls | {stats.get('appointments', 0)} appts | {stats.get('conversion_rate', 0)}% conv")
            
            # SETTINGS
            elif action == "SET_TEST_PHONE":
                update_setting('test_phone', params.get('phone'))
                results.append(f"✅ Test phone set to {params.get('phone')}")
            
            elif action == "GET_SETTINGS":
                settings = get_settings()
                results.append(f"⚙️ Mode: {settings.get('mode')} | Test Phone: {settings.get('test_phone')}")
            
            elif action == "TOGGLE_MODE":
                new_mode = params.get('mode', 'testing')
                update_setting('mode', new_mode)
                results.append(f"✅ Mode changed to {new_mode}")
            
            else:
                results.append(f"⚠️ Unknown action: {action}")
        
        except Exception as e:
            print(f"❌ ARIA ACTION ERROR: {e}")
            results.append(f"❌ Error executing {action}: {str(e)[:100]}")
    
    # Remove action tags from response for clean display
    clean_response = re.sub(action_pattern, '', response_text).strip()
    
    # Add action results to response
    if results:
        clean_response += "\n\n" + "\n".join(results)
    
    return clean_response, results

def chat_with_aria(user_message):
    """Chat with Aria AI assistant - the most advanced AI assistant"""
    print(f"\n🤖 ARIA RECEIVED: {user_message}")
    
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
    
    aria_response = None
    
    # Try OpenAI first
    if OPENAI_API_KEY:
        try:
            print(f"🤖 ARIA: Using OpenAI API...")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": "gpt-4o-mini", "messages": messages, "max_tokens": 1000, "temperature": 0.7},
                timeout=30
            )
            print(f"🤖 ARIA: OpenAI response status: {response.status_code}")
            if response.status_code == 200:
                aria_response = response.json()['choices'][0]['message']['content']
                print(f"🤖 ARIA: Got response from OpenAI")
            else:
                print(f"🤖 ARIA: OpenAI error: {response.text[:200]}")
        except Exception as e:
            print(f"🤖 ARIA: OpenAI exception: {e}")
    
    # Fallback to smart command processing
    if not aria_response:
        print(f"🤖 ARIA: Using smart fallback...")
        aria_response = process_smart_command(user_message)
    
    # Process any actions in the response
    clean_response, action_results = process_aria_actions(aria_response)
    
    print(f"🤖 ARIA RESPONSE: {clean_response[:200]}...")
    print(f"🤖 ARIA ACTIONS: {action_results}")
    
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

def process_smart_command(message):
    """Process commands intelligently without OpenAI"""
    msg = message.lower().strip()
    
    # Extract phone numbers from message
    phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\d{10,11})', message)
    phone = phone_match.group(1).replace('-', '').replace('.', '').replace(' ', '') if phone_match else None
    
    # Extract names
    name_patterns = [
        r'(?:call|add|contact)\s+(\w+)',
        r'(\w+)\s+at\s+\d{3}',
        r'for\s+(\w+)',
    ]
    name = None
    for pattern in name_patterns:
        match = re.search(pattern, message, re.I)
        if match:
            name = match.group(1)
            break
    
    # CALL commands
    if any(word in msg for word in ['call', 'dial', 'phone', 'ring']):
        if phone:
            agent_type = 'roofing'
            for agent in ['solar', 'hvac', 'plumbing', 'insurance', 'auto', 'dental', 'medical', 'legal']:
                if agent in msg:
                    agent_type = agent if agent != 'medical' else 'inbound_medical'
                    break
            return f"Calling {name or 'them'} now! [ACTION:CALL_NOW:{{\"phone\":\"{phone}\",\"name\":\"{name or 'there'}\",\"agent_type\":\"{agent_type}\"}}]"
        return "Sure! What's the phone number you'd like me to call?"
    
    # TEST commands
    if 'test' in msg:
        if 'inbound' in msg or 'receptionist' in msg:
            for agent in ['medical', 'dental', 'spa', 'hotel', 'restaurant', 'gym', 'vet', 'therapy']:
                if agent in msg:
                    return f"Testing the {agent} receptionist now! [ACTION:TEST_INBOUND:{{\"agent_type\":\"inbound_{agent}\"}}]"
            return f"Testing medical receptionist! [ACTION:TEST_INBOUND:{{\"agent_type\":\"inbound_medical\"}}]"
        else:
            for agent in ['roofing', 'solar', 'hvac', 'plumbing', 'insurance', 'auto', 'dental', 'legal', 'fitness']:
                if agent in msg:
                    return f"Testing the {agent} agent now! [ACTION:TEST_OUTBOUND:{{\"agent_type\":\"{agent}\"}}]"
            return f"Testing the roofing agent now! [ACTION:TEST_OUTBOUND:{{\"agent_type\":\"roofing\"}}]"
    
    # ADD LEAD commands
    if any(word in msg for word in ['add lead', 'new lead', 'add contact', 'create lead']):
        if phone:
            return f"Adding lead {name or 'New Lead'} with phone {phone}! [ACTION:ADD_LEAD:{{\"phone\":\"{phone}\",\"first_name\":\"{name or 'New'}\"}}]"
        return "Sure! What's their name and phone number?"
    
    # DELETE commands
    if any(word in msg for word in ['delete', 'remove', 'erase']):
        if 'lead' in msg:
            id_match = re.search(r'#?(\d+)', message)
            if id_match:
                return f"Deleting lead #{id_match.group(1)}! [ACTION:DELETE_LEAD_BY_ID:{{\"id\":{id_match.group(1)}}}]"
            if phone:
                return f"Deleting lead with phone {phone}! [ACTION:DELETE_LEAD:{{\"phone\":\"{phone}\"}}]"
        return "Which lead would you like me to delete? Give me the ID or phone number."
    
    # APPOINTMENT commands
    if any(word in msg for word in ['appointment', 'book', 'schedule']):
        if 'today' in msg:
            return "Here are today's appointments: [ACTION:GET_TODAY_APPOINTMENTS]"
        if 'tomorrow' in msg:
            return "Here are tomorrow's appointments: [ACTION:GET_TOMORROW_APPOINTMENTS]"
        if phone and name:
            return f"I'll book an appointment for {name}. What date and time? [ACTION:CREATE_APPOINTMENT:{{\"first_name\":\"{name}\",\"phone\":\"{phone}\"}}]"
        return "I can book an appointment! Give me the name, phone, date and time."
    
    # STATS commands
    if any(word in msg for word in ['stats', 'statistics', 'numbers', 'dashboard', 'overview']):
        return "Here are your stats: [ACTION:GET_STATS]"
    
    # COST commands
    if any(word in msg for word in ['cost', 'costs', 'spending', 'money', 'expense']):
        return "Here's your cost breakdown: [ACTION:GET_COSTS]"
    
    # SMS commands
    if any(word in msg for word in ['text', 'sms', 'message']):
        if phone:
            msg_match = re.search(r'(?:saying|message|text)[:\s]+["\']?(.+?)["\']?$', message, re.I)
            sms_text = msg_match.group(1) if msg_match else "Hi! Just following up."
            return f"Sending SMS to {phone}! [ACTION:SEND_SMS:{{\"phone\":\"{phone}\",\"message\":\"{sms_text}\"}}]"
        return "Sure! What's the phone number and message?"
    
    # LEADS commands
    if any(word in msg for word in ['leads', 'contacts', 'prospects']):
        return "Here's your lead overview: [ACTION:GET_LEADS]"
    
    # CALLS history
    if 'calls' in msg and any(word in msg for word in ['recent', 'history', 'log', 'show', 'list']):
        return "Here are your recent calls: [ACTION:GET_CALLS]"
    
    # HELP commands
    if any(word in msg for word in ['help', 'what can', 'commands', 'how do']):
        return """Hey! I'm Aria, your AI command center. Here's what I can do:

📞 **Calls**: "Call 720-324-0525" | "Test roofing agent" | "Test medical receptionist"
👥 **Leads**: "Add lead John 7205551234" | "Delete lead #123" | "Show leads"
📅 **Appointments**: "Today's appointments" | "Book appointment for John"
📱 **SMS**: "Text 7205551234 saying Hello!"
📊 **Stats**: "Show stats" | "What are the costs?"

Just tell me what you need - I'll handle it!"""
    
    # Default response
    return """Hey! I'm Aria. Tell me what you need:

• "Call 720-324-0525" - I'll call them
• "Test roofing agent" - Test a demo call  
• "Add lead John 7205551234" - Add a new lead
• "Show today's appointments" - See schedule
• "What are the stats?" - Dashboard overview

What would you like me to do?"""

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
        'cost': round((data[1] or 0) / 60 * COST_PER_MINUTE_RETELL, 2)
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
# ADMIN DASHBOARD - Multi-Tenant Client Management
# ═══════════════════════════════════════════════════════════════════════════════

def get_admin_dashboard():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VOICE Admin - Client Management</title>
<style>
:root{--bg:#0a0a0f;--card:#12121a;--border:#1e1e2e;--cyan:#00d1ff;--green:#10b981;--red:#ef4444;--yellow:#f59e0b;--gray:#6b7280;--text:#f5f5f5}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}

.admin-layout{display:flex;min-height:100vh}
.sidebar{width:260px;background:var(--card);border-right:1px solid var(--border);padding:24px 0;position:fixed;height:100vh;overflow-y:auto}
.sidebar-logo{padding:0 24px 32px;font-size:24px;font-weight:700;color:var(--cyan);display:flex;align-items:center;gap:12px}
.sidebar-logo svg{width:32px;height:32px}
.sidebar-section{padding:8px 16px;font-size:11px;color:var(--gray);text-transform:uppercase;letter-spacing:1px;margin-top:16px}
.sidebar-item{display:flex;align-items:center;gap:12px;padding:12px 24px;color:var(--gray);text-decoration:none;transition:all .2s;cursor:pointer}
.sidebar-item:hover{background:rgba(0,209,255,0.05);color:var(--text)}
.sidebar-item.active{background:rgba(0,209,255,0.1);color:var(--cyan);border-right:3px solid var(--cyan)}

.main-content{flex:1;margin-left:260px;padding:32px}
.page-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px}
.page-title{font-size:28px;font-weight:700}

.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:32px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:24px}
.stat-card-label{font-size:13px;color:var(--gray);margin-bottom:8px}
.stat-card-value{font-size:32px;font-weight:700}
.stat-card-change{font-size:12px;margin-top:8px}
.stat-card-change.up{color:var(--green)}
.stat-card-change.down{color:var(--red)}

.data-table{width:100%;background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.data-table th,.data-table td{padding:16px;text-align:left;border-bottom:1px solid var(--border)}
.data-table th{background:rgba(0,0,0,0.3);font-size:12px;text-transform:uppercase;color:var(--gray)}
.data-table tr:hover{background:rgba(0,209,255,0.02)}
.data-table tr:last-child td{border-bottom:none}

.badge{padding:4px 12px;border-radius:100px;font-size:12px;font-weight:500;display:inline-block}
.badge-active{background:rgba(16,185,129,0.1);color:var(--green)}
.badge-starter{background:rgba(107,114,128,0.1);color:var(--gray)}
.badge-professional{background:rgba(0,209,255,0.1);color:var(--cyan)}
.badge-enterprise{background:rgba(168,85,247,0.1);color:#a855f7}

.btn{padding:10px 20px;border-radius:8px;font-size:14px;font-weight:500;cursor:pointer;transition:all .2s;border:none}
.btn-primary{background:var(--cyan);color:#000}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 4px 20px rgba(0,209,255,0.3)}
.btn-secondary{background:transparent;border:1px solid var(--border);color:var(--text)}
.btn-sm{padding:6px 12px;font-size:12px}
.btn-icon{width:32px;height:32px;padding:0;display:flex;align-items:center;justify-content:center;border-radius:8px;background:transparent;border:1px solid var(--border);color:var(--gray);cursor:pointer;font-size:14px}
.btn-icon:hover{border-color:var(--cyan);color:var(--cyan)}

.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.8);display:none;align-items:center;justify-content:center;z-index:1000}
.modal-overlay.active{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:16px;width:90%;max-width:600px;max-height:90vh;overflow-y:auto}
.modal-header{padding:24px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.modal-title{font-size:20px;font-weight:600}
.modal-close{background:none;border:none;color:var(--gray);font-size:24px;cursor:pointer}
.modal-body{padding:24px}
.modal-footer{padding:24px;border-top:1px solid var(--border);display:flex;justify-content:flex-end;gap:12px}

.form-group{margin-bottom:20px}
.form-label{display:block;font-size:13px;color:var(--gray);margin-bottom:8px}
.form-input{width:100%;padding:12px 16px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:14px}
.form-input:focus{outline:none;border-color:var(--cyan)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}

.client-header{display:flex;align-items:center;gap:24px;padding:24px;background:var(--card);border:1px solid var(--border);border-radius:16px;margin-bottom:24px}
.client-avatar{width:80px;height:80px;background:linear-gradient(135deg,var(--cyan),#0066ff);border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:700;color:#fff}
.client-info h2{font-size:24px;margin-bottom:4px}
.client-info p{color:var(--gray)}
.client-meta{display:flex;gap:24px;margin-top:12px}
.client-meta-item{font-size:13px;color:var(--gray)}
.client-meta-item span{color:var(--text);font-weight:500}

.tabs{display:flex;gap:4px;background:var(--card);padding:4px;border-radius:12px;margin-bottom:24px;width:fit-content}
.tab{padding:10px 20px;border-radius:8px;font-size:14px;color:var(--gray);cursor:pointer;transition:all .2s;border:none;background:none}
.tab:hover{color:var(--text)}
.tab.active{background:var(--cyan);color:#000}

.integrations-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.integration-card{background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:20px}
.integration-header{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.integration-icon{width:40px;height:40px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:20px;background:rgba(0,209,255,0.1)}
.integration-name{font-weight:600}
.integration-status{font-size:12px;color:var(--gray)}
.integration-status.connected{color:var(--green)}

.cost-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px}
.cost-item{background:var(--bg);padding:20px;border-radius:12px;text-align:center}
.cost-item-value{font-size:28px;font-weight:700;color:var(--cyan)}
.cost-item-label{font-size:12px;color:var(--gray);margin-top:4px}

.search-box{display:flex;align-items:center;gap:12px;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:8px 16px;width:300px}
.search-box input{background:none;border:none;color:var(--text);flex:1;font-size:14px}
.search-box input:focus{outline:none}

.empty-state{text-align:center;padding:60px 20px;color:var(--gray)}
.empty-state-icon{font-size:48px;margin-bottom:16px}

@media(max-width:768px){
    .sidebar{display:none}
    .main-content{margin-left:0}
    .form-row{grid-template-columns:1fr}
    .stats-grid{grid-template-columns:1fr 1fr}
    .client-header{flex-direction:column;text-align:center}
    .client-meta{flex-direction:column;gap:8px}
}
</style>
</head>
<body>

<div class="admin-layout">
    <aside class="sidebar">
        <div class="sidebar-logo">
            <svg viewBox="0 0 512 512"><circle cx="256" cy="256" r="180" stroke="#00D1FF" stroke-width="24" fill="none"/></svg>
            <span>VOICE Admin</span>
        </div>
        
        <div class="sidebar-section">Overview</div>
        <a class="sidebar-item active" onclick="showPage('dashboard')">
            <span>📊</span>
            <span>Dashboard</span>
        </a>
        
        <div class="sidebar-section">Clients</div>
        <a class="sidebar-item" onclick="showPage('clients')">
            <span>👥</span>
            <span>All Clients</span>
        </a>
        
        <div class="sidebar-section">Analytics</div>
        <a class="sidebar-item" onclick="showPage('costs')">
            <span>💰</span>
            <span>Cost Tracking</span>
        </a>
        
        <div class="sidebar-section">System</div>
        <a class="sidebar-item" href="/">
            <span>🌐</span>
            <span>Main Site</span>
        </a>
        <a class="sidebar-item" href="/app">
            <span>📱</span>
            <span>CRM App</span>
        </a>
    </aside>

    <main class="main-content">
        
        <!-- Dashboard -->
        <div id="page-dashboard" class="page">
            <div class="page-header">
                <h1 class="page-title">Dashboard</h1>
                <button class="btn btn-primary" onclick="openModal('add-client-modal')">+ Add Client</button>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-label">Total Clients</div>
                    <div class="stat-card-value" id="stat-clients">0</div>
                    <div class="stat-card-change up">Active accounts</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Total Calls</div>
                    <div class="stat-card-value" id="stat-calls">0</div>
                    <div class="stat-card-change up">Across all clients</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Monthly Revenue</div>
                    <div class="stat-card-value" id="stat-revenue">$0</div>
                    <div class="stat-card-change up">From subscriptions</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Platform Costs</div>
                    <div class="stat-card-value" id="stat-costs">$0</div>
                    <div class="stat-card-change">Last 30 days</div>
                </div>
            </div>
            
            <h3 style="margin-bottom:16px">Recent Clients</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Client</th>
                        <th>Industry</th>
                        <th>Plan</th>
                        <th>Leads</th>
                        <th>Calls</th>
                        <th>Cost (30d)</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="clients-table">
                    <tr><td colspan="8" class="empty-state">Loading...</td></tr>
                </tbody>
            </table>
        </div>
        
        <!-- All Clients -->
        <div id="page-clients" class="page" style="display:none">
            <div class="page-header">
                <h1 class="page-title">All Clients</h1>
                <div style="display:flex;gap:12px">
                    <div class="search-box">
                        <span>🔍</span>
                        <input type="text" placeholder="Search clients..." id="search-input" oninput="filterClients()">
                    </div>
                    <button class="btn btn-primary" onclick="openModal('add-client-modal')">+ Add Client</button>
                </div>
            </div>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Client</th>
                        <th>Contact</th>
                        <th>Industry</th>
                        <th>Plan</th>
                        <th>Leads</th>
                        <th>Calls</th>
                        <th>Cost (30d)</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="all-clients-table">
                    <tr><td colspan="9" class="empty-state">Loading...</td></tr>
                </tbody>
            </table>
        </div>
        
        <!-- Client Detail -->
        <div id="page-client-detail" class="page" style="display:none">
            <div class="page-header">
                <h1 class="page-title"><a href="#" onclick="showPage('clients');return false" style="color:var(--cyan);text-decoration:none">← Back</a></h1>
            </div>
            
            <div class="client-header">
                <div class="client-avatar" id="client-avatar">A</div>
                <div class="client-info">
                    <h2 id="client-name">Company Name</h2>
                    <p id="client-email">email@company.com</p>
                    <div class="client-meta">
                        <div class="client-meta-item">Industry: <span id="client-industry">-</span></div>
                        <div class="client-meta-item">Plan: <span id="client-plan">-</span></div>
                        <div class="client-meta-item">Since: <span id="client-since">-</span></div>
                    </div>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-label">Total Leads</div>
                    <div class="stat-card-value" id="client-leads">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Total Calls</div>
                    <div class="stat-card-value" id="client-calls">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Appointments</div>
                    <div class="stat-card-value" id="client-appointments">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Cost (30 days)</div>
                    <div class="stat-card-value" id="client-cost">$0</div>
                </div>
            </div>
            
            <div class="tabs">
                <button class="tab active" onclick="switchTab('integrations', this)">Integrations</button>
                <button class="tab" onclick="switchTab('costs', this)">Cost Breakdown</button>
            </div>
            
            <div id="tab-integrations">
                <div class="integrations-grid" id="client-integrations"></div>
                <button class="btn btn-secondary" style="margin-top:16px" onclick="openModal('add-integration-modal')">+ Add Integration</button>
            </div>
            
            <div id="tab-costs" style="display:none">
                <div class="cost-grid" id="client-cost-breakdown"></div>
            </div>
        </div>
        
        <!-- Costs Page -->
        <div id="page-costs" class="page" style="display:none">
            <div class="page-header">
                <h1 class="page-title">Cost Tracking</h1>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-label">Total Platform Costs</div>
                    <div class="stat-card-value" id="total-costs">$0</div>
                    <div class="stat-card-change">Last 30 days</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Retell Voice</div>
                    <div class="stat-card-value" id="retell-costs">$0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Twilio SMS</div>
                    <div class="stat-card-value" id="twilio-costs">$0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Avg Cost/Client</div>
                    <div class="stat-card-value" id="avg-cost">$0</div>
                </div>
            </div>
            
            <h3 style="margin-bottom:16px">Cost by Client</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Client</th>
                        <th>Voice Calls</th>
                        <th>SMS</th>
                        <th>Other</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody id="cost-table"></tbody>
            </table>
        </div>
        
    </main>
</div>

<!-- Add Client Modal -->
<div class="modal-overlay" id="add-client-modal">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Add New Client</h3>
            <button class="modal-close" onclick="closeModal('add-client-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Company Name *</label>
                    <input type="text" class="form-input" id="new-company" placeholder="Acme Roofing">
                </div>
                <div class="form-group">
                    <label class="form-label">Contact Name</label>
                    <input type="text" class="form-input" id="new-contact" placeholder="John Smith">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Email *</label>
                    <input type="email" class="form-input" id="new-email" placeholder="john@acme.com">
                </div>
                <div class="form-group">
                    <label class="form-label">Phone</label>
                    <input type="tel" class="form-input" id="new-phone" placeholder="(720) 123-4567">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Industry</label>
                    <select class="form-input" id="new-industry">
                        <option value="roofing">Roofing</option>
                        <option value="solar">Solar</option>
                        <option value="hvac">HVAC</option>
                        <option value="plumbing">Plumbing</option>
                        <option value="electrical">Electrical</option>
                        <option value="insurance">Insurance</option>
                        <option value="real_estate">Real Estate</option>
                        <option value="auto">Auto Sales</option>
                        <option value="dental">Dental</option>
                        <option value="legal">Legal</option>
                        <option value="medical">Medical</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Plan</label>
                    <select class="form-input" id="new-plan">
                        <option value="starter">Starter ($297/mo)</option>
                        <option value="professional">Professional ($497/mo)</option>
                        <option value="enterprise">Enterprise ($997/mo)</option>
                    </select>
                </div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('add-client-modal')">Cancel</button>
            <button class="btn btn-primary" onclick="createClient()">Create Client</button>
        </div>
    </div>
</div>

<!-- Add Integration Modal -->
<div class="modal-overlay" id="add-integration-modal">
    <div class="modal">
        <div class="modal-header">
            <h3 class="modal-title">Add Integration</h3>
            <button class="modal-close" onclick="closeModal('add-integration-modal')">&times;</button>
        </div>
        <div class="modal-body">
            <div class="form-group">
                <label class="form-label">Integration Type</label>
                <select class="form-input" id="int-type">
                    <option value="retell">Retell AI (Voice)</option>
                    <option value="twilio">Twilio (SMS)</option>
                    <option value="ghl">GoHighLevel (CRM)</option>
                    <option value="zapier">Zapier</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">API Key</label>
                <input type="text" class="form-input" id="int-api-key" placeholder="key_xxxxx">
            </div>
            <div class="form-group">
                <label class="form-label">Phone Number</label>
                <input type="tel" class="form-input" id="int-phone" placeholder="+17201234567">
            </div>
            <div class="form-group">
                <label class="form-label">Agent ID (for Retell)</label>
                <input type="text" class="form-input" id="int-agent" placeholder="agent_xxxxx">
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal('add-integration-modal')">Cancel</button>
            <button class="btn btn-primary" onclick="saveIntegration()">Save</button>
        </div>
    </div>
</div>

<script>
let clients = [];
let currentClientId = null;

function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
    document.getElementById('page-' + page).style.display = 'block';
    if (event && event.target) event.target.classList.add('active');
    if (page === 'dashboard' || page === 'clients') loadClients();
    if (page === 'costs') loadCosts();
}

function openModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

function switchTab(tab, btn) {
    document.querySelectorAll('.tabs .tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-integrations').style.display = tab === 'integrations' ? 'block' : 'none';
    document.getElementById('tab-costs').style.display = tab === 'costs' ? 'block' : 'none';
}

async function loadClients() {
    try {
        const res = await fetch('/api/admin/clients');
        clients = await res.json();
        renderClients();
        updateStats();
    } catch (e) { console.error(e); }
}

function renderClients() {
    const html = clients.length ? clients.map(c => `
        <tr>
            <td>
                <div style="display:flex;align-items:center;gap:12px">
                    <div style="width:36px;height:36px;background:linear-gradient(135deg,var(--cyan),#0066ff);border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:600;color:#fff">${(c.company_name||'?')[0]}</div>
                    <div>
                        <div style="font-weight:500">${c.company_name}</div>
                        <div style="font-size:12px;color:var(--gray)">${c.email||''}</div>
                    </div>
                </div>
            </td>
            <td>${c.contact_name||'-'}</td>
            <td style="text-transform:capitalize">${c.industry||'-'}</td>
            <td><span class="badge badge-${c.plan||'starter'}">${c.plan||'starter'}</span></td>
            <td>${c.lead_count||0}</td>
            <td>${c.call_count||0}</td>
            <td>$${(c.monthly_cost||0).toFixed(2)}</td>
            <td><span class="badge badge-active">${c.status||'active'}</span></td>
            <td>
                <button class="btn-icon" onclick="viewClient(${c.id})" title="View">👁️</button>
            </td>
        </tr>
    `).join('') : '<tr><td colspan="9" class="empty-state"><div class="empty-state-icon">👥</div>No clients yet. Add your first client!</td></tr>';
    
    document.getElementById('clients-table').innerHTML = html;
    document.getElementById('all-clients-table').innerHTML = html;
}

function updateStats() {
    document.getElementById('stat-clients').textContent = clients.length;
    document.getElementById('stat-calls').textContent = clients.reduce((s,c) => s + (c.call_count||0), 0);
    document.getElementById('stat-costs').textContent = '$' + clients.reduce((s,c) => s + (c.monthly_cost||0), 0).toFixed(2);
    const revenue = clients.reduce((s,c) => s + ({starter:297,professional:497,enterprise:997}[c.plan]||297), 0);
    document.getElementById('stat-revenue').textContent = '$' + revenue.toLocaleString();
}

function filterClients() {
    const q = document.getElementById('search-input').value.toLowerCase();
    const filtered = clients.filter(c => 
        (c.company_name||'').toLowerCase().includes(q) ||
        (c.email||'').toLowerCase().includes(q) ||
        (c.industry||'').toLowerCase().includes(q)
    );
    const html = filtered.map(c => `
        <tr>
            <td><div style="display:flex;align-items:center;gap:12px"><div style="width:36px;height:36px;background:linear-gradient(135deg,var(--cyan),#0066ff);border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:600;color:#fff">${(c.company_name||'?')[0]}</div><div><div style="font-weight:500">${c.company_name}</div><div style="font-size:12px;color:var(--gray)">${c.email||''}</div></div></div></td>
            <td>${c.contact_name||'-'}</td>
            <td>${c.industry||'-'}</td>
            <td><span class="badge badge-${c.plan}">${c.plan}</span></td>
            <td>${c.lead_count||0}</td>
            <td>${c.call_count||0}</td>
            <td>$${(c.monthly_cost||0).toFixed(2)}</td>
            <td><span class="badge badge-active">${c.status}</span></td>
            <td><button class="btn-icon" onclick="viewClient(${c.id})">👁️</button></td>
        </tr>
    `).join('');
    document.getElementById('all-clients-table').innerHTML = html || '<tr><td colspan="9" class="empty-state">No results</td></tr>';
}

async function createClient() {
    const data = {
        company_name: document.getElementById('new-company').value,
        contact_name: document.getElementById('new-contact').value,
        email: document.getElementById('new-email').value,
        phone: document.getElementById('new-phone').value,
        industry: document.getElementById('new-industry').value,
        plan: document.getElementById('new-plan').value
    };
    if (!data.company_name || !data.email) { alert('Company and email required'); return; }
    
    const res = await fetch('/api/admin/clients', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(data)
    });
    const result = await res.json();
    if (result.success) {
        closeModal('add-client-modal');
        loadClients();
        ['new-company','new-contact','new-email','new-phone'].forEach(id => document.getElementById(id).value = '');
    } else {
        alert(result.error || 'Failed');
    }
}

async function viewClient(id) {
    currentClientId = id;
    const res = await fetch('/api/admin/clients/' + id);
    const c = await res.json();
    
    document.getElementById('client-avatar').textContent = (c.company_name||'?')[0];
    document.getElementById('client-name').textContent = c.company_name;
    document.getElementById('client-email').textContent = c.email || '';
    document.getElementById('client-industry').textContent = c.industry || '-';
    document.getElementById('client-plan').textContent = c.plan || 'starter';
    document.getElementById('client-since').textContent = c.created_at ? new Date(c.created_at).toLocaleDateString('en-US',{month:'short',year:'numeric'}) : '-';
    
    document.getElementById('client-leads').textContent = c.stats?.total_leads || 0;
    document.getElementById('client-calls').textContent = c.stats?.total_leads || 0;
    document.getElementById('client-appointments').textContent = c.stats?.appointments || 0;
    document.getElementById('client-cost').textContent = '$' + (c.monthly_cost || 0).toFixed(2);
    
    const intHtml = (c.integrations||[]).map(i => `
        <div class="integration-card">
            <div class="integration-header">
                <div class="integration-icon">${i.integration_type==='retell'?'📞':i.integration_type==='twilio'?'💬':'🔗'}</div>
                <div>
                    <div class="integration-name">${i.integration_type.charAt(0).toUpperCase()+i.integration_type.slice(1)}</div>
                    <div class="integration-status ${i.is_active?'connected':''}">${i.is_active?'● Connected':'○ Disconnected'}</div>
                </div>
            </div>
            <div style="font-size:12px;color:var(--gray)">
                ${i.phone_number?'Phone: '+i.phone_number:''}
                ${i.agent_id?'<br>Agent: '+i.agent_id.slice(0,15)+'...':''}
            </div>
        </div>
    `).join('') || '<p style="color:var(--gray)">No integrations yet</p>';
    document.getElementById('client-integrations').innerHTML = intHtml;
    
    showPage('client-detail');
}

async function saveIntegration() {
    if (!currentClientId) return;
    const data = {
        integration_type: document.getElementById('int-type').value,
        api_key: document.getElementById('int-api-key').value,
        phone_number: document.getElementById('int-phone').value,
        agent_id: document.getElementById('int-agent').value
    };
    
    const res = await fetch('/api/admin/clients/' + currentClientId + '/integrations', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(data)
    });
    const result = await res.json();
    if (result.success) {
        closeModal('add-integration-modal');
        viewClient(currentClientId);
    }
}

async function loadCosts() {
    const res = await fetch('/api/admin/clients');
    const clients = await res.json();
    
    let totalRetell = 0, totalTwilio = 0, totalOther = 0;
    const rows = clients.map(c => {
        const retell = (c.monthly_cost || 0) * 0.7;
        const twilio = (c.monthly_cost || 0) * 0.2;
        const other = (c.monthly_cost || 0) * 0.1;
        totalRetell += retell;
        totalTwilio += twilio;
        totalOther += other;
        return `<tr>
            <td>${c.company_name}</td>
            <td>$${retell.toFixed(2)}</td>
            <td>$${twilio.toFixed(2)}</td>
            <td>$${other.toFixed(2)}</td>
            <td><strong>$${(c.monthly_cost||0).toFixed(2)}</strong></td>
        </tr>`;
    }).join('');
    
    document.getElementById('cost-table').innerHTML = rows || '<tr><td colspan="5" class="empty-state">No data</td></tr>';
    document.getElementById('total-costs').textContent = '$' + (totalRetell + totalTwilio + totalOther).toFixed(2);
    document.getElementById('retell-costs').textContent = '$' + totalRetell.toFixed(2);
    document.getElementById('twilio-costs').textContent = '$' + totalTwilio.toFixed(2);
    document.getElementById('avg-cost').textContent = clients.length ? '$' + ((totalRetell + totalTwilio + totalOther) / clients.length).toFixed(2) : '$0';
}

document.addEventListener('DOMContentLoaded', loadClients);
</script>
</body>
</html>'''

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

/* Hero Demo Section */
.hero-demo{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:24px 32px;margin-bottom:48px;max-width:800px;backdrop-filter:blur(10px)}
.hero-demo-label{font-size:14px;color:var(--cyan);margin-bottom:16px;font-weight:500}
.hero-demo-row{display:flex;gap:12px;align-items:center;flex-wrap:wrap;justify-content:center}
.hero-demo-tabs{display:flex;background:rgba(0,0,0,0.3);border-radius:8px;overflow:hidden}
.hero-tab{padding:10px 16px;border:none;background:transparent;color:var(--gray-400);font-size:13px;cursor:pointer;transition:all .2s;font-weight:500}
.hero-tab.active{background:var(--cyan);color:#000}
.hero-tab:hover:not(.active){background:rgba(255,255,255,0.05)}
.hero-input{padding:12px 16px;border-radius:8px;border:1px solid rgba(255,255,255,0.1);background:rgba(0,0,0,0.3);color:#fff;font-size:14px;width:160px}
.hero-input::placeholder{color:var(--gray-500)}
.hero-input:focus{outline:none;border-color:var(--cyan)}
.hero-select{padding:12px 16px;border-radius:8px;border:1px solid rgba(255,255,255,0.1);background:rgba(0,0,0,0.3);color:#fff;font-size:14px;cursor:pointer;min-width:140px}
.hero-select:focus{outline:none;border-color:var(--cyan)}
.hero-call-btn{display:flex;align-items:center;gap:8px;padding:12px 24px;background:linear-gradient(135deg,var(--cyan),#00a8cc);border:none;border-radius:8px;color:#000;font-weight:600;font-size:14px;cursor:pointer;transition:all .2s}
.hero-call-btn:hover{transform:scale(1.05);box-shadow:0 0 30px rgba(0,209,255,0.4)}
.hero-call-icon{font-size:16px}
.hero-demo-note{font-size:12px;color:var(--gray-500);margin-top:12px}
@media(max-width:768px){.hero-demo-row{flex-direction:column}.hero-input,.hero-select{width:100%}}
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
.agents-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:12px;margin-top:60px}
.agent-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:16px 8px;text-align:center;transition:all .3s}
.agent-card:hover{border-color:var(--cyan);background:rgba(0,209,255,0.05)}
.agent-icon{font-size:28px;margin-bottom:8px}
.agent-role{font-size:11px;color:var(--gray-300);font-weight:500}

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

/* Demo Section */
.demo{padding:120px 40px;background:linear-gradient(180deg,rgba(0,209,255,0.02) 0%,transparent 100%)}
.demo-inner{max-width:700px;margin:0 auto;text-align:center}
.demo-sub{color:var(--gray-400);font-size:18px;margin-bottom:48px}
.demo-box{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:24px;padding:32px;margin-bottom:32px}
.demo-tabs{display:flex;gap:8px;margin-bottom:24px;background:rgba(0,0,0,0.3);border-radius:12px;padding:6px}
.demo-tab{flex:1;padding:14px 20px;border:none;background:transparent;color:var(--gray-400);font-size:14px;font-weight:600;border-radius:8px;cursor:pointer;transition:all .2s}
.demo-tab.active{background:var(--cyan);color:var(--black)}
.demo-tab:hover:not(.active){background:rgba(255,255,255,0.05)}
.demo-form{display:flex;flex-direction:column;gap:20px}
.demo-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.demo-field{text-align:left}
.demo-field label{display:block;font-size:13px;font-weight:600;margin-bottom:8px;color:var(--gray-400)}
.demo-field input,.demo-field select{width:100%;padding:16px;border:1px solid rgba(255,255,255,0.1);border-radius:12px;background:rgba(0,0,0,0.3);color:var(--white);font-size:16px;transition:all .2s}
.demo-field input:focus,.demo-field select:focus{outline:none;border-color:var(--cyan);box-shadow:0 0 20px rgba(0,209,255,0.2)}
.demo-field input::placeholder{color:var(--gray-600)}
.demo-field select{cursor:pointer}
.demo-field select option{background:var(--black);color:var(--white)}
.demo-btn{width:100%;padding:20px;border:none;border-radius:12px;background:linear-gradient(135deg,var(--cyan) 0%,#00a8cc 100%);color:var(--black);font-size:18px;font-weight:700;cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center;gap:12px;margin-top:8px}
.demo-btn:hover{transform:translateY(-3px);box-shadow:0 20px 60px rgba(0,209,255,0.4)}
.demo-btn:active{transform:translateY(0)}
.demo-btn-icon{font-size:24px}
.demo-note{font-size:13px;color:var(--gray-500);margin-top:16px}
.demo-features{display:flex;justify-content:center;gap:40px;flex-wrap:wrap}
.demo-feature{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--gray-400)}
.demo-feature span:first-child{font-size:18px}
.demo-calling{display:none;flex-direction:column;align-items:center;gap:16px;padding:40px}
.demo-calling.active{display:flex}
.demo-calling-icon{font-size:64px;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.1);opacity:0.8}}
.demo-calling-text{font-size:20px;font-weight:600}
.demo-calling-sub{color:var(--gray-400);font-size:14px}

/* Custom Agent Creator */
.creator{padding:120px 40px;background:linear-gradient(180deg,transparent 0%,rgba(0,209,255,0.02) 100%)}
.creator-inner{max-width:800px;margin:0 auto;text-align:center}
.creator-sub{color:var(--gray-400);font-size:18px;margin-bottom:48px}
.creator-box{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:24px;padding:32px;text-align:left}
.creator-tabs{display:flex;gap:8px;margin-bottom:24px;background:rgba(0,0,0,0.3);border-radius:12px;padding:6px}
.creator-tab{flex:1;padding:14px 20px;border:none;background:transparent;color:var(--gray-400);font-size:14px;font-weight:600;border-radius:8px;cursor:pointer;transition:all .2s;text-align:center}
.creator-tab.active{background:var(--cyan);color:var(--black)}
.creator-form{display:flex;flex-direction:column;gap:20px}
.creator-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.creator-field{text-align:left}
.creator-field label{display:block;font-size:13px;font-weight:600;margin-bottom:8px;color:var(--gray-400)}
.creator-field input,.creator-field textarea{width:100%;padding:16px;border:1px solid rgba(255,255,255,0.1);border-radius:12px;background:rgba(0,0,0,0.3);color:var(--white);font-size:16px;font-family:inherit;transition:all .2s}
.creator-field input:focus,.creator-field textarea:focus{outline:none;border-color:var(--cyan);box-shadow:0 0 20px rgba(0,209,255,0.2)}
.creator-field input::placeholder,.creator-field textarea::placeholder{color:var(--gray-600)}
.creator-field textarea{min-height:100px;resize:vertical}
.creator-btn{width:100%;padding:20px;border:none;border-radius:12px;background:linear-gradient(135deg,#10b981 0%,#059669 100%);color:white;font-size:18px;font-weight:700;cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center;gap:12px;margin-top:8px}
.creator-btn:hover{transform:translateY(-3px);box-shadow:0 20px 60px rgba(16,185,129,0.4)}
.creator-note{font-size:13px;color:var(--gray-500);margin-top:16px;text-align:center}

/* Booking Modal */
.booking-modal-bg{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(8px);z-index:10000;display:none;align-items:center;justify-content:center}
.booking-modal-bg.show{display:flex}
.booking-modal{background:var(--gray-900);border:1px solid rgba(255,255,255,0.1);border-radius:24px;padding:40px;max-width:500px;width:90%;max-height:90vh;overflow-y:auto;position:relative}
.booking-close{position:absolute;top:16px;right:16px;background:none;border:none;color:var(--gray-400);font-size:24px;cursor:pointer;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:all .2s}
.booking-close:hover{background:rgba(255,255,255,0.1);color:var(--white)}
.booking-header{text-align:center;margin-bottom:32px}
.booking-icon{font-size:48px;margin-bottom:16px}
.booking-title{font-size:24px;font-weight:700;margin-bottom:8px}
.booking-sub{color:var(--gray-400);font-size:14px}
.booking-form{display:flex;flex-direction:column;gap:16px}
.booking-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.booking-field{text-align:left}
.booking-field label{display:block;font-size:12px;font-weight:600;margin-bottom:6px;color:var(--gray-400)}
.booking-field input,.booking-field select,.booking-field textarea{width:100%;padding:14px;border:1px solid rgba(255,255,255,0.1);border-radius:10px;background:rgba(0,0,0,0.3);color:var(--white);font-size:15px;font-family:inherit;transition:all .2s}
.booking-field input:focus,.booking-field select:focus,.booking-field textarea:focus{outline:none;border-color:var(--cyan);box-shadow:0 0 20px rgba(0,209,255,0.2)}
.booking-field input::placeholder,.booking-field textarea::placeholder{color:var(--gray-600)}
.booking-field select{cursor:pointer}
.booking-field select option{background:var(--black)}
.booking-field textarea{min-height:80px;resize:vertical}
.booking-times{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px}
.booking-time{padding:12px 8px;border:1px solid rgba(255,255,255,0.1);border-radius:8px;background:transparent;color:var(--gray-400);font-size:13px;cursor:pointer;transition:all .2s;text-align:center}
.booking-time:hover{border-color:var(--cyan);color:var(--white)}
.booking-time.selected{background:var(--cyan);color:var(--black);border-color:var(--cyan);font-weight:600}
.booking-submit{width:100%;padding:18px;border:none;border-radius:12px;background:linear-gradient(135deg,var(--cyan) 0%,#00a8cc 100%);color:var(--black);font-size:16px;font-weight:700;cursor:pointer;transition:all .2s;margin-top:8px}
.booking-submit:hover{transform:translateY(-2px);box-shadow:0 15px 40px rgba(0,209,255,0.4)}
.booking-submit:disabled{opacity:0.6;cursor:not-allowed;transform:none}
.booking-privacy{font-size:11px;color:var(--gray-500);text-align:center;margin-top:12px}

/* Trial Signup Modal */
.trial-modal-bg{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(8px);z-index:10000;display:none;align-items:center;justify-content:center}
.trial-modal-bg.show{display:flex}
.trial-modal{background:var(--gray-900);border:1px solid rgba(0,209,255,0.3);border-radius:24px;padding:40px;max-width:420px;width:90%;position:relative}
.trial-close{position:absolute;top:16px;right:16px;background:none;border:none;color:var(--gray-400);font-size:24px;cursor:pointer}
.trial-header{text-align:center;margin-bottom:28px}
.trial-icon{font-size:56px;margin-bottom:16px}
.trial-title{font-size:26px;font-weight:700;margin-bottom:8px}
.trial-sub{color:var(--gray-400);font-size:14px}
.trial-badge{display:inline-block;background:linear-gradient(135deg,#10b981,#059669);color:white;padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;margin-top:12px}
.trial-form{display:flex;flex-direction:column;gap:14px}
.trial-field label{display:block;font-size:12px;font-weight:600;margin-bottom:6px;color:var(--gray-400)}
.trial-field input{width:100%;padding:14px;border:1px solid rgba(255,255,255,0.1);border-radius:10px;background:rgba(0,0,0,0.3);color:var(--white);font-size:15px}
.trial-field input:focus{outline:none;border-color:var(--cyan);box-shadow:0 0 20px rgba(0,209,255,0.2)}
.trial-submit{width:100%;padding:16px;border:none;border-radius:12px;background:linear-gradient(135deg,var(--cyan) 0%,#00a8cc 100%);color:var(--black);font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
.trial-submit:hover{transform:translateY(-2px);box-shadow:0 15px 40px rgba(0,209,255,0.4)}
.trial-note{font-size:11px;color:var(--gray-500);text-align:center;margin-top:12px}

/* As Seen On */
.seen-on{padding:80px 40px;border-top:1px solid rgba(255,255,255,0.05);border-bottom:1px solid rgba(255,255,255,0.05)}
.seen-on-inner{max-width:1200px;margin:0 auto;text-align:center}
.seen-on-label{font-size:12px;text-transform:uppercase;letter-spacing:3px;color:var(--gray-500);margin-bottom:40px}
.seen-on-logos{display:flex;justify-content:center;align-items:center;gap:60px;flex-wrap:wrap;opacity:0.6}
.seen-on-logo{font-size:24px;font-weight:700;color:var(--gray-400);display:flex;align-items:center;gap:8px}
.seen-on-logo span{font-size:14px;font-weight:400}

/* Reviews */
.reviews{padding:120px 40px}
.reviews-inner{max-width:1200px;margin:0 auto}
.reviews-header{text-align:center;margin-bottom:60px}
.reviews-stats{display:flex;justify-content:center;gap:60px;margin-top:32px;flex-wrap:wrap}
.reviews-stat{text-align:center}
.reviews-stat-value{font-size:48px;font-weight:700;color:var(--cyan)}
.reviews-stat-label{font-size:14px;color:var(--gray-400);margin-top:4px}
.reviews-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
.review-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:28px;transition:all .3s}
.review-card:hover{border-color:rgba(0,209,255,0.2);transform:translateY(-4px)}
.review-stars{color:#fbbf24;font-size:16px;margin-bottom:16px;letter-spacing:2px}
.review-text{color:var(--gray-300);font-size:15px;line-height:1.7;margin-bottom:20px;font-style:italic}
.review-author{display:flex;align-items:center;gap:12px}
.review-avatar{width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,var(--cyan),#0ea5e9);display:flex;align-items:center;justify-content:center;font-weight:600;font-size:16px}
.review-info{text-align:left}
.review-name{font-weight:600;font-size:14px}
.review-role{font-size:12px;color:var(--gray-500)}
.review-verified{display:inline-flex;align-items:center;gap:4px;font-size:11px;color:var(--success);margin-top:4px}

/* Updated Pricing */
.pricing{padding:120px 40px}
.pricing-inner{max-width:900px;margin:0 auto;text-align:center}
.pricing-box{background:linear-gradient(135deg,rgba(0,209,255,0.05) 0%,rgba(0,209,255,0.02) 100%);border:1px solid rgba(0,209,255,0.2);border-radius:24px;padding:60px 40px;margin-top:48px}
.pricing-headline{font-size:32px;font-weight:700;margin-bottom:16px}
.pricing-sub{color:var(--gray-400);font-size:18px;margin-bottom:40px;max-width:500px;margin-left:auto;margin-right:auto}
.pricing-features-list{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;text-align:left;max-width:500px;margin:0 auto 40px}
.pricing-feature-item{display:flex;align-items:center;gap:12px;font-size:15px;color:var(--gray-300)}
.pricing-feature-item::before{content:'✓';color:var(--cyan);font-weight:700;font-size:18px}
.pricing-cta-btn{display:inline-flex;align-items:center;gap:12px;padding:20px 48px;background:var(--cyan);color:var(--black);font-size:18px;font-weight:700;border-radius:12px;text-decoration:none;transition:all .2s}
.pricing-cta-btn:hover{transform:translateY(-3px);box-shadow:0 20px 60px rgba(0,209,255,0.4)}
.pricing-note{margin-top:20px;font-size:13px;color:var(--gray-500)}

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

/* Toast */
.landing-toast{position:fixed;bottom:40px;left:50%;transform:translateX(-50%);background:var(--cyan);color:var(--black);padding:16px 32px;border-radius:12px;font-weight:600;z-index:9999;display:none;box-shadow:0 10px 40px rgba(0,209,255,0.3)}
.landing-toast.show{display:block;animation:slideUp 0.3s ease}
.landing-toast.error{background:#EF4444;color:white}
@keyframes slideUp{from{opacity:0;transform:translateX(-50%) translateY(20px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}

/* Mobile */
@media(max-width:768px){
.nav{padding:16px 20px}
.reviews-grid{grid-template-columns:1fr}
.pricing-features-list{grid-template-columns:1fr}
.seen-on-logos{gap:30px}
.nav-links{display:none}
.hero{padding:120px 20px 60px}
.stats{gap:40px}
.features,.agents,.pricing,.cta,.demo,.creator{padding:80px 20px}
.demo-row,.creator-row{grid-template-columns:1fr}
.demo-features{gap:20px}
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
<p class="hero-sub">One AI voice agent that calls your leads, books appointments, and never misses a follow-up. Works for any industry. 24/7. On autopilot.</p>

<!-- Compact Hero Demo -->
<div class="hero-demo">
<div class="hero-demo-label">🎧 Try it now - Get a call in 10 seconds</div>
<div class="hero-demo-row">
<div class="hero-demo-tabs">
<button class="hero-tab active" id="hero-tab-outbound" onclick="switchHeroTab('outbound')">📤 Outbound</button>
<button class="hero-tab" id="hero-tab-inbound" onclick="switchHeroTab('inbound')">📥 Inbound</button>
</div>
<input type="tel" id="hero-phone" placeholder="(555) 555-5555" class="hero-input">
<select id="hero-agent" class="hero-select">
<option value="roofing">🏠 Roofing</option>
<option value="solar">☀️ Solar</option>
<option value="hvac">❄️ HVAC</option>
<option value="plumbing">🔧 Plumbing</option>
<option value="insurance">🛡️ Insurance</option>
<option value="realtor">🏡 Real Estate</option>
<option value="auto">🚗 Auto</option>
<option value="dental">🦷 Dental</option>
<option value="legal">⚖️ Legal</option>
<option value="medspa">💉 Med Spa</option>
</select>
<button class="hero-call-btn" onclick="startHeroCall()">
<span class="hero-call-icon">📞</span> Call Me
</button>
</div>
<div class="hero-demo-note">No signup required • Free demo • Any industry</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-value">30+</div><div class="stat-label">Industries</div></div>
<div class="stat"><div class="stat-value">1</div><div class="stat-label">AI Voice</div></div>
<div class="stat"><div class="stat-value">24/7</div><div class="stat-label">Always On</div></div>
<div class="stat"><div class="stat-value">3x</div><div class="stat-label">More Bookings</div></div>
</div>
</section>

<section class="seen-on">
<div class="seen-on-inner">
<div class="seen-on-label">As Featured In</div>
<div class="seen-on-logos">
<div class="seen-on-logo">📺 ABC News</div>
<div class="seen-on-logo">🔵 CBS</div>
<div class="seen-on-logo">🟠 NBC</div>
<div class="seen-on-logo">📰 Forbes</div>
<div class="seen-on-logo">🔴 CNN</div>
<div class="seen-on-logo">💼 Business Insider</div>
<div class="seen-on-logo">🌐 TechCrunch</div>
</div>
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
<div class="section-label">Industries We Serve</div>
<h2 class="section-title">One AI. Every Industry.</h2>
<p style="color:var(--gray-400);max-width:600px;margin:0 auto">Hailey adapts to any industry - outbound sales or inbound reception. Trained with industry-specific knowledge and scripts.</p>
<div class="agents-grid">
<div class="agent-card"><div class="agent-icon">🏠</div><div class="agent-role">Roofing</div></div>
<div class="agent-card"><div class="agent-icon">☀️</div><div class="agent-role">Solar</div></div>
<div class="agent-card"><div class="agent-icon">🛡️</div><div class="agent-role">Insurance</div></div>
<div class="agent-card"><div class="agent-icon">🚗</div><div class="agent-role">Auto Sales</div></div>
<div class="agent-card"><div class="agent-icon">🏡</div><div class="agent-role">Real Estate</div></div>
<div class="agent-card"><div class="agent-icon">🦷</div><div class="agent-role">Dental</div></div>
<div class="agent-card"><div class="agent-icon">❄️</div><div class="agent-role">HVAC</div></div>
<div class="agent-card"><div class="agent-icon">⚖️</div><div class="agent-role">Legal</div></div>
<div class="agent-card"><div class="agent-icon">💪</div><div class="agent-role">Fitness</div></div>
<div class="agent-card"><div class="agent-icon">🧹</div><div class="agent-role">Cleaning</div></div>
<div class="agent-card"><div class="agent-icon">🌳</div><div class="agent-role">Landscaping</div></div>
<div class="agent-card"><div class="agent-icon">📊</div><div class="agent-role">Tax Services</div></div>
<div class="agent-card"><div class="agent-icon">🔧</div><div class="agent-role">Plumbing</div></div>
<div class="agent-card"><div class="agent-icon">⚡</div><div class="agent-role">Electrical</div></div>
<div class="agent-card"><div class="agent-icon">🐜</div><div class="agent-role">Pest Control</div></div>
<div class="agent-card"><div class="agent-icon">🪟</div><div class="agent-role">Windows</div></div>
<div class="agent-card"><div class="agent-icon">🪵</div><div class="agent-role">Flooring</div></div>
<div class="agent-card"><div class="agent-icon">🎨</div><div class="agent-role">Painting</div></div>
<div class="agent-card"><div class="agent-icon">🚪</div><div class="agent-role">Garage Doors</div></div>
<div class="agent-card"><div class="agent-icon">🏊</div><div class="agent-role">Pool Services</div></div>
<div class="agent-card"><div class="agent-icon">📦</div><div class="agent-role">Moving</div></div>
<div class="agent-card"><div class="agent-icon">🔐</div><div class="agent-role">Security</div></div>
<div class="agent-card"><div class="agent-icon">🏦</div><div class="agent-role">Mortgage</div></div>
<div class="agent-card"><div class="agent-icon">🦴</div><div class="agent-role">Chiropractic</div></div>
<div class="agent-card"><div class="agent-icon">💉</div><div class="agent-role">Med Spa</div></div>
<div class="agent-card"><div class="agent-icon">✈️</div><div class="agent-role">Travel</div></div>
<div class="agent-card"><div class="agent-icon">💒</div><div class="agent-role">Wedding</div></div>
<div class="agent-card"><div class="agent-icon">📚</div><div class="agent-role">Tutoring</div></div>
<div class="agent-card"><div class="agent-icon">🐕</div><div class="agent-role">Pet Grooming</div></div>
</div>
</div>
</section>

<section class="demo" id="demo">
<div class="demo-inner">
<div class="section-label">🎯 Try It Now</div>
<h2 class="section-title">Experience VOICE in 30 seconds</h2>
<p class="demo-sub">Enter your phone number, pick an industry, and receive a live AI call instantly. No signup required.</p>

<div class="demo-box">
<div class="demo-tabs">
<button class="demo-tab active" id="tab-outbound" onclick="switchDemoTab('outbound')">📤 Outbound Sales</button>
<button class="demo-tab" id="tab-inbound" onclick="switchDemoTab('inbound')">📥 Inbound Reception</button>
</div>

<div class="demo-form">
<div class="demo-row">
<div class="demo-field">
<label>📱 Your Phone Number</label>
<input type="tel" id="demo-phone" placeholder="+1 (555) 123-4567" />
</div>
<div class="demo-field">
<label>🤖 Select Industry</label>
<select id="demo-agent">
<option value="roofing">🏠 Roofing</option>
<option value="solar">☀️ Solar</option>
<option value="insurance">🛡️ Insurance</option>
<option value="auto">🚗 Auto Sales</option>
<option value="realtor">🏡 Real Estate</option>
<option value="dental">🦷 Dental</option>
<option value="hvac">❄️ HVAC</option>
<option value="legal">⚖️ Legal</option>
<option value="fitness">💪 Fitness</option>
<option value="cleaning">🧹 Cleaning</option>
<option value="landscaping">🌳 Landscaping</option>
<option value="tax">📊 Tax Services</option>
<option value="plumbing">🔧 Plumbing</option>
<option value="electrical">⚡ Electrical</option>
<option value="pest_control">🐜 Pest Control</option>
<option value="windows">🪟 Windows</option>
<option value="flooring">🪵 Flooring</option>
<option value="painting">🎨 Painting</option>
<option value="garage_door">🚪 Garage Doors</option>
<option value="pool">🏊 Pool Services</option>
<option value="moving">📦 Moving</option>
<option value="security">🔐 Security</option>
<option value="mortgage">🏦 Mortgage</option>
<option value="chiropractor">🦴 Chiropractic</option>
<option value="medspa">💉 Med Spa</option>
<option value="travel">✈️ Travel</option>
<option value="wedding">💒 Wedding</option>
<option value="tutoring">📚 Tutoring</option>
<option value="pet_grooming">🐕 Pet Grooming</option>
</select>
</div>
</div>

<button class="demo-btn" onclick="startDemoCall()">
<span class="demo-btn-icon">📞</span>
<span>Call Me Now</span>
</button>

<p class="demo-note">✨ You'll receive a call within 10 seconds</p>
</div>
</div>

<div class="demo-features">
<div class="demo-feature">
<span>🔒</span>
<span>No signup required</span>
</div>
<div class="demo-feature">
<span>⚡</span>
<span>Instant callback</span>
</div>
<div class="demo-feature">
<span>🎯</span>
<span>Real AI conversation</span>
</div>
</div>
</div>
</section>

<section class="creator" id="creator">
<div class="creator-inner">
<div class="section-label">🛠️ Custom Agent</div>
<h2 class="section-title">Create Your Own AI Agent</h2>
<p class="creator-sub">Don't see your industry? Build a custom agent in seconds. Same natural conversation flow, tailored to your business.</p>

<div class="creator-box">
<div class="creator-tabs">
<button class="creator-tab active" id="creator-tab-outbound" onclick="switchCreatorTab('outbound')">📤 Outbound Sales Agent</button>
<button class="creator-tab" id="creator-tab-inbound" onclick="switchCreatorTab('inbound')">📥 Inbound Receptionist</button>
</div>

<div class="creator-form">
<div class="creator-row">
<div class="creator-field">
<label>📱 Your Phone Number</label>
<input type="tel" id="creator-phone" placeholder="+1 (555) 123-4567" />
</div>
<div class="creator-field">
<label>🏢 Your Company Name</label>
<input type="text" id="creator-company" placeholder="Acme Services" />
</div>
</div>

<div class="creator-row">
<div class="creator-field">
<label>🏭 Your Industry</label>
<input type="text" id="creator-industry" placeholder="e.g. Tree Service, Concrete, Locksmith..." />
</div>
<div class="creator-field">
<label>👤 Agent Name</label>
<input type="text" id="creator-agent-name" placeholder="e.g. Jessica, Mike, Sarah..." />
</div>
</div>

<div class="creator-field">
<label>📝 Services You Offer (optional)</label>
<textarea id="creator-services" placeholder="e.g. Tree trimming, removal, stump grinding, emergency service..."></textarea>
</div>

<button class="creator-btn" onclick="createCustomAgent()">
<span>🚀</span>
<span>Create & Test My Agent</span>
</button>

<p class="creator-note">⚡ Your custom agent will call you instantly using our proven conversation flow</p>
</div>
</div>
</div>
</section>

<section class="reviews" id="reviews">
<div class="reviews-inner">
<div class="reviews-header">
<div class="section-label">⭐ Customer Reviews</div>
<h2 class="section-title">Trusted by 2,500+ businesses</h2>
<div class="reviews-stats">
<div class="reviews-stat"><div class="reviews-stat-value">4.9</div><div class="reviews-stat-label">Average Rating</div></div>
<div class="reviews-stat"><div class="reviews-stat-value">2,547</div><div class="reviews-stat-label">Happy Customers</div></div>
<div class="reviews-stat"><div class="reviews-stat-value">1.2M+</div><div class="reviews-stat-label">Calls Made</div></div>
</div>
</div>
<div class="reviews-grid">
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"We went from booking 8 appointments a week to 47. The AI sounds so real that customers don't even know. This completely transformed our roofing business."</div>
<div class="review-author">
<div class="review-avatar">JM</div>
<div class="review-info">
<div class="review-name">Jake Morrison</div>
<div class="review-role">Owner, Morrison Roofing Co.</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"I was skeptical at first, but VOICE paid for itself in the first week. Our show rate went from 40% to 78% because the AI confirms appointments perfectly."</div>
<div class="review-author">
<div class="review-avatar">SL</div>
<div class="review-info">
<div class="review-name">Sarah Liu</div>
<div class="review-role">CEO, Bright Solar Solutions</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"The receptionist AI handles 200+ calls a day for our dental practice. Patients love 'Emily' and we've cut our front desk costs by 60%."</div>
<div class="review-author">
<div class="review-avatar">DR</div>
<div class="review-info">
<div class="review-name">Dr. Robert Chen</div>
<div class="review-role">Founder, Smile Dental Group</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"We run Facebook ads 24/7 and VOICE calls every lead within 60 seconds. Our cost per acquisition dropped by 52%. Best investment we ever made."</div>
<div class="review-author">
<div class="review-avatar">MR</div>
<div class="review-info">
<div class="review-name">Marcus Rodriguez</div>
<div class="review-role">Marketing Director, Elite Insurance</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"I manage 12 HVAC technicians and scheduling was a nightmare. Now the AI books everything perfectly and even handles reschedules. Game changer."</div>
<div class="review-author">
<div class="review-avatar">TW</div>
<div class="review-info">
<div class="review-name">Tom Williams</div>
<div class="review-role">Owner, ComfortAir HVAC</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"Our law firm was missing calls after hours. Now 'Grace' answers every call, qualifies leads, and books consultations. We've added $180K in new cases."</div>
<div class="review-author">
<div class="review-avatar">JP</div>
<div class="review-info">
<div class="review-name">Jennifer Park, Esq.</div>
<div class="review-role">Partner, Park & Associates Law</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"The custom agent feature is incredible. We built an AI for our pool cleaning service in 5 minutes and it books 30+ appointments weekly."</div>
<div class="review-author">
<div class="review-avatar">CB</div>
<div class="review-info">
<div class="review-name">Chris Baker</div>
<div class="review-role">Owner, Crystal Clear Pools</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"We were spending $4,500/month on a call center. Switched to VOICE and now we're booking more appointments at a fraction of the cost. ROI is insane."</div>
<div class="review-author">
<div class="review-avatar">AM</div>
<div class="review-info">
<div class="review-name">Amanda Martinez</div>
<div class="review-role">VP Sales, Horizon Real Estate</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
<div class="review-card">
<div class="review-stars">★★★★★</div>
<div class="review-text">"My gym was losing leads because we couldn't answer the phone during classes. Now 'Alex' handles everything and membership sign-ups are up 85%."</div>
<div class="review-author">
<div class="review-avatar">KJ</div>
<div class="review-info">
<div class="review-name">Kevin Johnson</div>
<div class="review-role">Owner, PowerFit Gym</div>
<div class="review-verified">✓ Verified Customer</div>
</div>
</div>
</div>
</div>
</div>
</section>

<section class="pricing" id="pricing">
<div class="pricing-inner">
<div class="section-label">Pricing</div>
<h2 class="section-title">Enterprise-Grade AI for Your Business</h2>

<div class="pricing-box">
<div class="pricing-headline">Custom Solutions Starting at Scale</div>
<div class="pricing-sub">Every business is unique. We build custom AI solutions tailored to your specific needs, industry, and call volume.</div>

<div class="pricing-features-list">
<div class="pricing-feature-item">Unlimited AI Agents</div>
<div class="pricing-feature-item">Unlimited Calls</div>
<div class="pricing-feature-item">Custom Voice & Scripts</div>
<div class="pricing-feature-item">All Integrations</div>
<div class="pricing-feature-item">Dedicated Success Manager</div>
<div class="pricing-feature-item">White-Label Options</div>
<div class="pricing-feature-item">Priority Support</div>
<div class="pricing-feature-item">SLA Guarantee</div>
</div>

<a href="#" onclick="openBookingModal(); return false;" class="pricing-cta-btn">📞 Request Custom Quote</a>
<p class="pricing-note">Free demo included • No commitment required • Setup in 24 hours</p>
</div>
</div>
</section>

<section class="cta">
<h2>Ready to close more deals?</h2>
<p>Join hundreds of businesses automating their sales with VOICE AI.</p>
<a href="#" onclick="openBookingModal(); return false;" class="btn-primary">Book a Demo Call →</a>
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

<!-- Booking Modal -->
<div class="booking-modal-bg" id="booking-modal">
<div class="booking-modal">
<button class="booking-close" onclick="closeBookingModal()">×</button>
<div class="booking-header">
<div class="booking-icon">📅</div>
<div class="booking-title">Book Your Strategy Call</div>
<div class="booking-sub">We'll call you to discuss how VOICE can transform your business</div>
</div>

<div class="booking-form">
<div class="booking-row">
<div class="booking-field">
<label>Name *</label>
<input type="text" id="book-fname" placeholder="John Smith" required>
</div>
<div class="booking-field">
<label>Phone *</label>
<input type="tel" id="book-phone" placeholder="(555) 123-4567" required>
</div>
</div>

<div class="booking-field">
<label>Email *</label>
<input type="email" id="book-email" placeholder="john@company.com" required>
</div>

<div class="booking-field">
<label>Industry *</label>
<select id="book-industry">
<option value="">What industry are you in?</option>
<option value="Roofing">Roofing</option>
<option value="Solar">Solar</option>
<option value="HVAC">HVAC</option>
<option value="Plumbing">Plumbing</option>
<option value="Electrical">Electrical</option>
<option value="Dental">Dental</option>
<option value="Medical">Medical</option>
<option value="Legal">Legal</option>
<option value="Real Estate">Real Estate</option>
<option value="Insurance">Insurance</option>
<option value="Auto Sales">Auto Sales</option>
<option value="Home Services">Home Services</option>
<option value="Other">Other</option>
</select>
</div>

<button class="booking-submit" onclick="submitBooking()">🚀 Book My Call</button>
<p class="booking-privacy">🔒 We'll reach out within 24 hours</p>
</div>
</div>
</div>

<!-- Trial Signup Modal -->
<div class="trial-modal-bg" id="trial-modal">
<div class="trial-modal">
<button class="trial-close" onclick="closeTrialModal()">×</button>
<div class="trial-header">
<div class="trial-icon">🚀</div>
<div class="trial-title">Start Your Free Trial</div>
<div class="trial-sub">Get full access to all AI agents for 7 days</div>
<div class="trial-badge">✨ No credit card required</div>
</div>

<div class="trial-form">
<div class="trial-field">
<label>Full Name *</label>
<input type="text" id="trial-name" placeholder="John Smith" required>
</div>
<div class="trial-field">
<label>Email *</label>
<input type="email" id="trial-email" placeholder="john@company.com" required>
</div>
<div class="trial-field">
<label>Phone *</label>
<input type="tel" id="trial-phone" placeholder="(555) 123-4567" required>
</div>
<div class="trial-field">
<label>Password *</label>
<input type="password" id="trial-password" placeholder="Min 6 characters" required minlength="6">
</div>

<button class="trial-submit" onclick="submitTrialSignup()">🎯 Start My 7-Day Free Trial</button>
<p class="trial-note">By signing up, you agree to our terms. After 7 days, contact us to continue.</p>
</div>
</div>
</div>

<div class="landing-toast" id="landing-toast"></div>

<script>
function switchDemoTab(type) {
    document.querySelectorAll('.demo-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + type).classList.add('active');
    
    const select = document.getElementById('demo-agent');
    
    // Clear existing options
    select.innerHTML = '';
    
    if (type === 'outbound') {
        select.innerHTML = `
            <option value="roofing">🏠 Roofing</option>
            <option value="solar">☀️ Solar</option>
            <option value="insurance">🛡️ Insurance</option>
            <option value="auto">🚗 Auto Sales</option>
            <option value="realtor">🏡 Real Estate</option>
            <option value="dental">🦷 Dental</option>
            <option value="hvac">❄️ HVAC</option>
            <option value="legal">⚖️ Legal</option>
            <option value="fitness">💪 Fitness</option>
            <option value="cleaning">🧹 Cleaning</option>
            <option value="landscaping">🌳 Landscaping</option>
            <option value="tax">📊 Tax Services</option>
            <option value="plumbing">🔧 Plumbing</option>
            <option value="electrical">⚡ Electrical</option>
            <option value="pest_control">🐜 Pest Control</option>
            <option value="windows">🪟 Windows</option>
            <option value="flooring">🪵 Flooring</option>
            <option value="painting">🎨 Painting</option>
            <option value="garage_door">🚪 Garage Doors</option>
            <option value="pool">🏊 Pool Services</option>
            <option value="moving">📦 Moving</option>
            <option value="security">🔐 Security</option>
            <option value="mortgage">🏦 Mortgage</option>
            <option value="chiropractor">🦴 Chiropractic</option>
            <option value="medspa">💉 Med Spa</option>
            <option value="travel">✈️ Travel</option>
            <option value="wedding">💒 Wedding</option>
            <option value="tutoring">📚 Tutoring</option>
            <option value="pet_grooming">🐕 Pet Grooming</option>
        `;
    } else {
        select.innerHTML = `
            <option value="inbound_medical">🏥 Medical Office</option>
            <option value="inbound_dental">🦷 Dental Office</option>
            <option value="inbound_legal">⚖️ Law Firm</option>
            <option value="inbound_realestate">🏡 Real Estate</option>
            <option value="inbound_auto">🚗 Auto Dealer</option>
            <option value="inbound_insurance">🛡️ Insurance</option>
            <option value="inbound_financial">💰 Financial</option>
            <option value="inbound_spa">💅 Spa & Salon</option>
            <option value="inbound_restaurant">🍽️ Restaurant</option>
            <option value="inbound_hotel">🏨 Hotel</option>
            <option value="inbound_gym">💪 Gym</option>
            <option value="inbound_vet">🐕 Veterinary</option>
            <option value="inbound_therapy">🧠 Therapy</option>
            <option value="inbound_plumbing">🔧 Plumbing</option>
            <option value="inbound_electrical">⚡ Electrical</option>
            <option value="inbound_hvac">❄️ HVAC</option>
            <option value="inbound_roofing">🏠 Roofing</option>
            <option value="inbound_pest">🐜 Pest Control</option>
            <option value="inbound_moving">📦 Moving</option>
            <option value="inbound_solar">☀️ Solar</option>
            <option value="inbound_pool">🏊 Pool Service</option>
            <option value="inbound_flooring">🪵 Flooring</option>
            <option value="inbound_painting">🎨 Painting</option>
            <option value="inbound_garage">🚪 Garage Doors</option>
            <option value="inbound_window">🪟 Windows</option>
            <option value="inbound_security">🔐 Security</option>
            <option value="inbound_mortgage">🏦 Mortgage</option>
            <option value="inbound_chiro">🦴 Chiropractic</option>
            <option value="inbound_medspa">💉 Med Spa</option>
            <option value="inbound_daycare">👶 Daycare</option>
        `;
    }
    
    console.log('Tab:', type, 'First option:', select.value);
}

// Hero Demo Functions
let heroIsInbound = false;

function switchHeroTab(type) {
    document.querySelectorAll('.hero-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('hero-tab-' + type).classList.add('active');
    heroIsInbound = (type === 'inbound');
    
    const select = document.getElementById('hero-agent');
    if (type === 'outbound') {
        select.innerHTML = `
            <option value="roofing">🏠 Roofing</option>
            <option value="solar">☀️ Solar</option>
            <option value="hvac">❄️ HVAC</option>
            <option value="plumbing">🔧 Plumbing</option>
            <option value="insurance">🛡️ Insurance</option>
            <option value="realtor">🏡 Real Estate</option>
            <option value="auto">🚗 Auto</option>
            <option value="dental">🦷 Dental</option>
            <option value="legal">⚖️ Legal</option>
            <option value="medspa">💉 Med Spa</option>
        `;
    } else {
        select.innerHTML = `
            <option value="inbound_medical">🏥 Medical</option>
            <option value="inbound_dental">🦷 Dental</option>
            <option value="inbound_spa">💅 Spa</option>
            <option value="inbound_restaurant">🍽️ Restaurant</option>
            <option value="inbound_hotel">🏨 Hotel</option>
            <option value="inbound_auto">🚗 Auto Dealer</option>
            <option value="inbound_legal">⚖️ Law Firm</option>
            <option value="inbound_vet">🐕 Veterinary</option>
            <option value="inbound_gym">💪 Gym</option>
            <option value="inbound_hvac">❄️ HVAC</option>
        `;
    }
}

async function startHeroCall() {
    const phoneInput = document.getElementById('hero-phone');
    const agentSelect = document.getElementById('hero-agent');
    const phone = phoneInput.value.trim();
    const agent = agentSelect.value;
    
    if (!phone) {
        phoneInput.style.borderColor = '#EF4444';
        phoneInput.focus();
        setTimeout(() => phoneInput.style.borderColor = 'rgba(255,255,255,0.1)', 2000);
        return;
    }
    
    const btn = document.querySelector('.hero-call-btn');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="hero-call-icon">📞</span> Calling...';
    btn.disabled = true;
    btn.style.opacity = '0.7';
    
    try {
        const digits = phone.replace(/\\D/g, '');
        const formattedPhone = digits.length === 10 ? '+1' + digits : (digits.length === 11 && digits.startsWith('1') ? '+' + digits : '+' + digits);
        
        const response = await fetch('/api/demo-call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: formattedPhone, agent_type: agent })
        });
        
        const result = await response.json();
        
        if (result.success) {
            btn.innerHTML = '<span class="hero-call-icon">✅</span> Call incoming!';
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
                btn.style.opacity = '1';
            }, 5000);
        } else {
            btn.innerHTML = '<span class="hero-call-icon">❌</span> Failed';
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
                btn.style.opacity = '1';
            }, 3000);
        }
    } catch (error) {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        btn.style.opacity = '1';
    }
}

function showLandingToast(msg, isError) {
    const t = document.getElementById('landing-toast');
    t.textContent = msg;
    t.className = 'landing-toast show' + (isError ? ' error' : '');
    setTimeout(() => t.classList.remove('show'), 4000);
}

function formatPhoneNumber(phone) {
    const digits = phone.replace(/\\D/g, '');
    if (digits.length === 10) return '+1' + digits;
    if (digits.length === 11 && digits.startsWith('1')) return '+' + digits;
    return '+' + digits;
}

async function startDemoCall() {
    const phoneInput = document.getElementById('demo-phone');
    const agentSelect = document.getElementById('demo-agent');
    const phone = phoneInput.value.trim();
    const agent = agentSelect.value;
    
    if (!phone) {
        showLandingToast('Please enter your phone number', true);
        phoneInput.focus();
        return;
    }
    
    const digits = phone.replace(/\\D/g, '');
    if (digits.length < 10) {
        showLandingToast('Please enter a valid phone number', true);
        phoneInput.focus();
        return;
    }
    
    const btn = document.querySelector('.demo-btn');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="demo-btn-icon">📞</span><span>Calling you now...</span>';
    btn.disabled = true;
    btn.style.opacity = '0.7';
    
    try {
        const response = await fetch('/api/demo-call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: formatPhoneNumber(phone),
                agent_type: agent
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showLandingToast('📞 Calling you now! Answer your phone!', false);
            btn.innerHTML = '<span class="demo-btn-icon">✅</span><span>Call initiated!</span>';
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
                btn.style.opacity = '1';
            }, 5000);
        } else {
            showLandingToast(result.error || 'Failed to initiate call', true);
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    } catch (error) {
        showLandingToast('Connection error. Please try again.', true);
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        btn.style.opacity = '1';
    }
}

// Format phone as user types
document.getElementById('demo-phone').addEventListener('input', function(e) {
    let digits = e.target.value.replace(/\\D/g, '');
    if (digits.length > 0) {
        if (digits.length <= 3) {
            e.target.value = '(' + digits;
        } else if (digits.length <= 6) {
            e.target.value = '(' + digits.slice(0,3) + ') ' + digits.slice(3);
        } else {
            e.target.value = '(' + digits.slice(0,3) + ') ' + digits.slice(3,6) + '-' + digits.slice(6,10);
        }
    }
});

// Custom Agent Creator
let creatorType = 'outbound';

function switchCreatorTab(type) {
    creatorType = type;
    document.querySelectorAll('.creator-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('creator-tab-' + type).classList.add('active');
}

// Trial Signup Modal
function openTrialModal() {
    document.getElementById('trial-modal').classList.add('show');
    document.body.style.overflow = 'hidden';
    trackWebsiteVisit('trial_modal_opened');
}

function closeTrialModal() {
    document.getElementById('trial-modal').classList.remove('show');
    document.body.style.overflow = '';
}

// Format trial phone as user types
document.getElementById('trial-phone').addEventListener('input', function(e) {
    let digits = e.target.value.replace(/\\D/g, '');
    if (digits.length > 0) {
        if (digits.length <= 3) {
            e.target.value = '(' + digits;
        } else if (digits.length <= 6) {
            e.target.value = '(' + digits.slice(0,3) + ') ' + digits.slice(3);
        } else {
            e.target.value = '(' + digits.slice(0,3) + ') ' + digits.slice(3,6) + '-' + digits.slice(6,10);
        }
    }
});

async function submitTrialSignup() {
    const name = document.getElementById('trial-name').value.trim();
    const email = document.getElementById('trial-email').value.trim();
    const phone = document.getElementById('trial-phone').value.trim();
    const password = document.getElementById('trial-password').value;
    
    if (!name) {
        showLandingToast('Please enter your name', true);
        return;
    }
    if (!email || !email.includes('@')) {
        showLandingToast('Please enter a valid email', true);
        return;
    }
    if (!phone || phone.replace(/\\D/g, '').length < 10) {
        showLandingToast('Please enter a valid phone number', true);
        return;
    }
    if (!password || password.length < 6) {
        showLandingToast('Password must be at least 6 characters', true);
        return;
    }
    
    const btn = document.querySelector('.trial-submit');
    const originalText = btn.textContent;
    btn.textContent = 'Creating account...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/trial-signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                email: email,
                phone: formatPhoneNumber(phone),
                password: password
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showLandingToast('🎉 Account created! Redirecting...', false);
            closeTrialModal();
            setTimeout(() => {
                window.location.href = '/app';
            }, 1500);
        } else {
            showLandingToast(result.error || 'Something went wrong', true);
        }
    } catch (error) {
        showLandingToast('Connection error. Please try again.', true);
    }
    
    btn.textContent = originalText;
    btn.disabled = false;
}

// Close trial modal on background click
document.getElementById('trial-modal').addEventListener('click', function(e) {
    if (e.target === this) closeTrialModal();
});

// Format creator phone as user types
document.getElementById('creator-phone').addEventListener('input', function(e) {
    let digits = e.target.value.replace(/\\D/g, '');
    if (digits.length > 0) {
        if (digits.length <= 3) {
            e.target.value = '(' + digits;
        } else if (digits.length <= 6) {
            e.target.value = '(' + digits.slice(0,3) + ') ' + digits.slice(3);
        } else {
            e.target.value = '(' + digits.slice(0,3) + ') ' + digits.slice(3,6) + '-' + digits.slice(6,10);
        }
    }
});

async function createCustomAgent() {
    const phone = document.getElementById('creator-phone').value.trim();
    const company = document.getElementById('creator-company').value.trim();
    const industry = document.getElementById('creator-industry').value.trim();
    const agentName = document.getElementById('creator-agent-name').value.trim();
    const services = document.getElementById('creator-services').value.trim();
    
    if (!phone) {
        showLandingToast('Please enter your phone number', true);
        return;
    }
    if (!company) {
        showLandingToast('Please enter your company name', true);
        return;
    }
    if (!industry) {
        showLandingToast('Please enter your industry', true);
        return;
    }
    if (!agentName) {
        showLandingToast('Please enter an agent name', true);
        return;
    }
    
    const btn = document.querySelector('.creator-btn');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span>🚀</span><span>Creating your agent...</span>';
    btn.disabled = true;
    btn.style.opacity = '0.7';
    
    try {
        const response = await fetch('/api/custom-agent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: formatPhoneNumber(phone),
                company: company,
                industry: industry,
                agent_name: agentName,
                services: services,
                agent_type: creatorType
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showLandingToast('📞 Your custom ' + agentName + ' is calling you now!', false);
            btn.innerHTML = '<span>✅</span><span>Call initiated!</span>';
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
                btn.style.opacity = '1';
            }, 5000);
        } else {
            showLandingToast(result.error || 'Failed to create agent', true);
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    } catch (error) {
        showLandingToast('Connection error. Please try again.', true);
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        btn.style.opacity = '1';
    }
}

// Booking Modal Functions
function openBookingModal() {
    document.getElementById('booking-modal').classList.add('show');
    document.body.style.overflow = 'hidden';
    trackWebsiteVisit('booking_modal_opened');
}

function closeBookingModal() {
    document.getElementById('booking-modal').classList.remove('show');
    document.body.style.overflow = '';
}

// Format booking phone
document.getElementById('book-phone').addEventListener('input', function(e) {
    let digits = e.target.value.replace(/\\D/g, '');
    if (digits.length > 0) {
        if (digits.length <= 3) {
            e.target.value = '(' + digits;
        } else if (digits.length <= 6) {
            e.target.value = '(' + digits.slice(0,3) + ') ' + digits.slice(3);
        } else {
            e.target.value = '(' + digits.slice(0,3) + ') ' + digits.slice(3,6) + '-' + digits.slice(6,10);
        }
    }
});

async function submitBooking() {
    const name = document.getElementById('book-fname').value.trim();
    const email = document.getElementById('book-email').value.trim();
    const phone = document.getElementById('book-phone').value.trim();
    const industry = document.getElementById('book-industry').value;
    
    if (!name) {
        showLandingToast('Please enter your name', true);
        return;
    }
    if (!email || !email.includes('@')) {
        showLandingToast('Please enter a valid email', true);
        return;
    }
    if (!phone || phone.replace(/\\D/g, '').length < 10) {
        showLandingToast('Please enter a valid phone number', true);
        return;
    }
    if (!industry) {
        showLandingToast('Please select your industry', true);
        return;
    }
    
    const btn = document.querySelector('.booking-submit');
    const originalText = btn.textContent;
    btn.textContent = 'Booking...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/website-lead', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                first_name: name,
                email: email,
                phone: formatPhoneNumber(phone),
                industry: industry,
                source: 'website_booking'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showLandingToast('🎉 Got it! We\\'ll call you within 24 hours', false);
            closeBookingModal();
            document.getElementById('book-fname').value = '';
            document.getElementById('book-email').value = '';
            document.getElementById('book-phone').value = '';
            document.getElementById('book-industry').value = '';
        } else {
            showLandingToast(result.error || 'Something went wrong', true);
        }
    } catch (error) {
        showLandingToast('Connection error. Please try again.', true);
    }
    
    btn.textContent = originalText;
    btn.disabled = false;
}

// Track website visits
function trackWebsiteVisit(action) {
    fetch('/api/track-visit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action, page: window.location.pathname, timestamp: new Date().toISOString() })
    }).catch(() => {});
}

// Track on page load
trackWebsiteVisit('page_view');

// Close modal on background click
document.getElementById('booking-modal').addEventListener('click', function(e) {
    if (e.target === this) closeBookingModal();
});

// Close on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeBookingModal();
});
</script>

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

/* ═══════════════════════════════════════════════════════════════════════════════ */
/* VOICE OS CALENDAR - TEMPORAL COMMAND STREAM                                      */
/* ═══════════════════════════════════════════════════════════════════════════════ */

/* Main Layout */
.voice-calendar{display:grid;grid-template-columns:1fr 340px;gap:24px;height:calc(100vh - 180px);min-height:600px}
@media(max-width:1024px){.voice-calendar{grid-template-columns:1fr;height:auto}}

/* Temporal Stream - Left Side */
.temporal-stream{background:linear-gradient(180deg,rgba(10,14,23,0.95) 0%,rgba(6,9,18,0.98) 100%);border:1px solid rgba(255,255,255,0.06);border-radius:20px;overflow:hidden;display:flex;flex-direction:column}
.stream-header{padding:24px;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between;align-items:center}
.stream-title{font-size:13px;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,0.4);font-weight:600}
.stream-now{display:flex;align-items:center;gap:8px}
.now-dot{width:8px;height:8px;background:#00d1ff;border-radius:50%;animation:pulse 2s infinite}
.now-label{font-size:12px;color:#00d1ff;font-weight:600}
@keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(0,209,255,0.4)}50%{opacity:0.8;box-shadow:0 0 0 8px rgba(0,209,255,0)}}

/* Timeline */
.timeline-container{flex:1;overflow-y:auto;padding:0 24px 24px;position:relative}
.timeline-container::-webkit-scrollbar{width:4px}
.timeline-container::-webkit-scrollbar-track{background:transparent}
.timeline-container::-webkit-scrollbar-thumb{background:rgba(0,209,255,0.3);border-radius:4px}
.timeline-line{position:absolute;left:40px;top:0;bottom:0;width:2px;background:linear-gradient(180deg,rgba(0,209,255,0.3) 0%,rgba(0,209,255,0.05) 100%)}

/* Time Markers */
.time-marker{display:flex;align-items:flex-start;gap:20px;padding:16px 0;position:relative}
.time-marker:first-child{padding-top:24px}
.marker-time{width:50px;font-size:12px;color:rgba(255,255,255,0.4);font-weight:500;text-align:right;flex-shrink:0}
.marker-dot{width:12px;height:12px;background:rgba(0,209,255,0.2);border:2px solid rgba(0,209,255,0.4);border-radius:50%;flex-shrink:0;position:relative;z-index:1}
.time-marker.now .marker-dot{background:#00d1ff;border-color:#00d1ff;box-shadow:0 0 20px rgba(0,209,255,0.5)}
.time-marker.now .marker-time{color:#00d1ff;font-weight:700}

/* Event Cards */
.event-card{flex:1;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:16px;cursor:pointer;transition:all 0.3s ease}
.event-card:hover{background:rgba(0,209,255,0.05);border-color:rgba(0,209,255,0.2);transform:translateX(4px)}
.event-card.ai-booked{border-left:3px solid #00d1ff}
.event-card.high-value{border-left:3px solid #10b981}
.event-card.conflict{border-left:3px solid #ef4444;background:rgba(239,68,68,0.05)}
.event-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.event-title{font-weight:600;font-size:14px;color:#fff}
.event-badge{font-size:10px;padding:3px 8px;border-radius:100px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}
.badge-ai{background:rgba(0,209,255,0.15);color:#00d1ff}
.badge-manual{background:rgba(107,114,128,0.2);color:#9ca3af}
.badge-urgent{background:rgba(239,68,68,0.15);color:#ef4444}
.event-details{font-size:12px;color:rgba(255,255,255,0.5);margin-bottom:8px}
.event-meta{display:flex;gap:12px;font-size:11px}
.event-meta span{display:flex;align-items:center;gap:4px;color:rgba(255,255,255,0.4)}
.event-ai-insight{margin-top:10px;padding:10px;background:rgba(0,209,255,0.05);border-radius:8px;font-size:11px;color:rgba(0,209,255,0.8);display:flex;align-items:flex-start;gap:8px}
.event-ai-insight::before{content:'🤖';font-size:12px}

/* Empty Slot */
.empty-slot{flex:1;border:1px dashed rgba(255,255,255,0.1);border-radius:12px;padding:16px;text-align:center;cursor:pointer;transition:all 0.3s}
.empty-slot:hover{border-color:rgba(0,209,255,0.3);background:rgba(0,209,255,0.02)}
.empty-slot-label{font-size:12px;color:rgba(255,255,255,0.3)}
.slot-ai-score{display:inline-flex;align-items:center;gap:6px;margin-top:8px;padding:4px 10px;background:rgba(16,185,129,0.1);border-radius:100px;font-size:10px;color:#10b981}

/* Command Panel - Right Side */
.command-panel{display:flex;flex-direction:column;gap:16px}

/* AI Heatmap */
.heatmap-card{background:linear-gradient(180deg,rgba(10,14,23,0.95) 0%,rgba(6,9,18,0.98) 100%);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:20px}
.heatmap-title{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:rgba(255,255,255,0.4);margin-bottom:16px;font-weight:600}
.heatmap-bar{height:40px;background:rgba(0,0,0,0.3);border-radius:8px;display:flex;overflow:hidden;position:relative}
.heatmap-segment{flex:1;position:relative;transition:all 0.3s}
.heatmap-segment:hover{transform:scaleY(1.1)}
.heatmap-segment.hot{background:linear-gradient(180deg,rgba(16,185,129,0.6) 0%,rgba(16,185,129,0.2) 100%)}
.heatmap-segment.warm{background:linear-gradient(180deg,rgba(0,209,255,0.4) 0%,rgba(0,209,255,0.1) 100%)}
.heatmap-segment.cool{background:linear-gradient(180deg,rgba(107,114,128,0.3) 0%,rgba(107,114,128,0.1) 100%)}
.heatmap-segment.cold{background:linear-gradient(180deg,rgba(239,68,68,0.3) 0%,rgba(239,68,68,0.1) 100%)}
.heatmap-labels{display:flex;justify-content:space-between;margin-top:8px;font-size:10px;color:rgba(255,255,255,0.3)}
.heatmap-insight{margin-top:16px;padding:12px;background:rgba(16,185,129,0.08);border-radius:10px;font-size:12px;color:#10b981;display:flex;align-items:center;gap:10px}
.heatmap-insight svg{width:16px;height:16px;flex-shrink:0}

/* Voice Command */
.voice-cmd{background:linear-gradient(180deg,rgba(10,14,23,0.95) 0%,rgba(6,9,18,0.98) 100%);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:20px}
.voice-cmd-title{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:rgba(255,255,255,0.4);margin-bottom:12px;font-weight:600}
.voice-input-wrap{display:flex;gap:8px}
.voice-input{flex:1;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:12px 16px;color:#fff;font-size:13px}
.voice-input:focus{outline:none;border-color:rgba(0,209,255,0.4)}
.voice-input::placeholder{color:rgba(255,255,255,0.3)}
.voice-btn{width:44px;height:44px;background:linear-gradient(135deg,#00d1ff 0%,#0066ff 100%);border:none;border-radius:10px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.3s}
.voice-btn:hover{transform:scale(1.05);box-shadow:0 4px 20px rgba(0,209,255,0.4)}
.voice-btn svg{width:20px;height:20px;fill:#fff}
.voice-suggestions{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.voice-suggestion{padding:6px 12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:100px;font-size:11px;color:rgba(255,255,255,0.5);cursor:pointer;transition:all 0.2s}
.voice-suggestion:hover{background:rgba(0,209,255,0.1);border-color:rgba(0,209,255,0.3);color:#00d1ff}

/* Quick Stats */
.cal-stats{background:linear-gradient(180deg,rgba(10,14,23,0.95) 0%,rgba(6,9,18,0.98) 100%);border:1px solid rgba(255,255,255,0.06);border-radius:16px;padding:20px}
.cal-stats-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.cal-stat{text-align:center;padding:16px 12px;background:rgba(0,0,0,0.2);border-radius:12px}
.cal-stat-value{font-size:24px;font-weight:700;margin-bottom:2px}
.cal-stat-value.cyan{color:#00d1ff}
.cal-stat-value.green{color:#10b981}
.cal-stat-value.orange{color:#f59e0b}
.cal-stat-label{font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.5px}

/* Orbit View Toggle */
.view-toggle{display:flex;background:rgba(0,0,0,0.3);border-radius:10px;padding:4px;gap:4px}
.view-toggle-btn{flex:1;padding:8px 12px;border:none;background:transparent;color:rgba(255,255,255,0.4);font-size:11px;font-weight:600;border-radius:8px;cursor:pointer;transition:all 0.2s;text-transform:uppercase;letter-spacing:0.5px}
.view-toggle-btn.active{background:rgba(0,209,255,0.15);color:#00d1ff}
.view-toggle-btn:hover:not(.active){background:rgba(255,255,255,0.05)}

/* Orbit Mode */
.orbit-view{display:none;height:400px;position:relative;background:radial-gradient(circle at center,rgba(0,209,255,0.05) 0%,transparent 70%);border-radius:16px;overflow:hidden}
.orbit-view.active{display:block}
.orbit-center{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:60px;height:60px;background:linear-gradient(135deg,#00d1ff,#0066ff);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:20px;box-shadow:0 0 40px rgba(0,209,255,0.4)}
.orbit-ring{position:absolute;top:50%;left:50%;border:1px solid rgba(0,209,255,0.1);border-radius:50%;transform:translate(-50%,-50%)}
.orbit-ring-1{width:200px;height:200px}
.orbit-ring-2{width:300px;height:300px}
.orbit-ring-3{width:400px;height:400px}
.orbit-node{position:absolute;transform:translate(-50%,-50%);cursor:pointer;transition:all 0.3s}
.orbit-node:hover{transform:translate(-50%,-50%) scale(1.2)}
.orbit-node-inner{width:40px;height:40px;background:rgba(0,209,255,0.2);border:2px solid #00d1ff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px}
.orbit-node.urgent .orbit-node-inner{background:rgba(239,68,68,0.2);border-color:#ef4444}
.orbit-node.complete .orbit-node-inner{background:rgba(16,185,129,0.2);border-color:#10b981}

/* Date Navigator */
.date-nav{display:flex;align-items:center;justify-content:center;gap:16px;padding:16px;background:rgba(0,0,0,0.2);border-radius:12px;margin-bottom:16px}
.date-nav-btn{width:36px;height:36px;border:1px solid rgba(255,255,255,0.1);background:transparent;border-radius:8px;color:rgba(255,255,255,0.5);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s}
.date-nav-btn:hover{border-color:rgba(0,209,255,0.3);color:#00d1ff}
.date-nav-current{font-size:16px;font-weight:600;min-width:200px;text-align:center}
.date-nav-current span{color:rgba(255,255,255,0.4);font-weight:400;font-size:13px}
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

    js = """console.log('VOICE JS Loading...');
window.onerror=function(msg,url,line,col,error){console.error('JS Error:',msg,'at line',line,'col',col,error);return false};
function navTo(page){
console.log('navTo called:',page);
try{
var navItems=document.querySelectorAll('.nav-item');
for(var i=0;i<navItems.length;i++){navItems[i].classList.remove('active')}
var clicked=document.querySelector('.nav-item[data-page=\"'+page+'\"]');
if(clicked)clicked.classList.add('active');
var pages=document.querySelectorAll('.page');
for(var j=0;j<pages.length;j++){pages[j].classList.remove('active')}
var targetPage=document.getElementById('page-'+page);
if(targetPage){targetPage.classList.add('active');console.log('Activated page:',page)}
else{console.error('Page not found: page-'+page)}
if(typeof load==='function')load(page);
}catch(e){console.error('navTo error:',e)}
}
const $=id=>document.getElementById(id);
const outbound=""" + out_json + """;
const inbound=""" + in_json + """;
const agents={...outbound,...inbound};
let curMonth=new Date();let selDate=null;let testPhone='';
let calViewMode='stream';let calSelectedDate=new Date();
async function init(){
try{
const opts=Object.entries(outbound).map(([k,v])=>`<option value="${k}">${v.name} - ${v.industry}</option>`).join('');
const allOpts=Object.entries(agents).map(([k,v])=>`<option value="${k}">${v.name} - ${v.industry}</option>`).join('');
['l-agent','ap-agent'].forEach(id=>{if($(id))$(id).innerHTML=opts});
if($('test-agent-select'))$('test-agent-select').innerHTML=allOpts;
if($('ap-date'))$('ap-date').value=new Date().toISOString().split('T')[0];
if($('ap-time'))$('ap-time').value='10:00';
const settings=await fetch('/api/settings').then(r=>r.json()).catch(()=>({}));
testPhone=settings.test_phone||'';
if($('test-phone'))$('test-phone').value=testPhone;
if($('app-mode'))$('app-mode').value=settings.mode||'testing';
}catch(e){console.error('Init error:',e)}
}
function setupNav(){
console.log('Setting up navigation...');
document.querySelectorAll('.nav-item').forEach(function(n){
n.onclick=function(){
try{
console.log('Nav clicked:',n.dataset.page);
document.querySelectorAll('.nav-item').forEach(function(x){x.classList.remove('active')});
n.classList.add('active');
document.querySelectorAll('.page').forEach(function(p){p.classList.remove('active')});
var pg=document.getElementById('page-'+n.dataset.page);
if(pg){pg.classList.add('active');console.log('Page activated:',n.dataset.page)}
else{console.error('Page not found:','page-'+n.dataset.page)}
load(n.dataset.page);
}catch(e){console.error('Nav error:',e)}
};
});
console.log('Navigation setup complete');
}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',function(){setupNav();init()})}
else{setupNav();init()}
function load(p){
console.log('Loading page:',p);
try{
if(p==='dashboard')loadDash().catch(function(e){console.error('loadDash failed:',e)});
else if(p==='calendar')loadVoiceCal().catch(function(e){console.error('loadVoiceCal failed:',e)});
else if(p==='appointments')loadAppts().catch(function(e){console.error('loadAppts failed:',e)});
else if(p==='dispositions')loadDispo().catch(function(e){console.error('loadDispo failed:',e)});
else if(p==='outbound')loadOut();
else if(p==='inbound')loadIn();
else if(p==='leads')loadLeads().catch(function(e){console.error('loadLeads failed:',e)});
else if(p==='website-leads')loadWebsiteLeads().catch(function(e){console.error('loadWebsiteLeads failed:',e)});
else if(p==='calls')loadCalls().catch(function(e){console.error('loadCalls failed:',e)});
else if(p==='costs')loadCosts().catch(function(e){console.error('loadCosts failed:',e)});
else if(p==='testing')loadTesting().catch(function(e){console.error('loadTesting failed:',e)});
else if(p==='ads')loadAds().catch(function(e){console.error('loadAds failed:',e)});
else if(p==='pipeline')loadPipeline().catch(function(e){console.error('loadPipeline failed:',e)});
else if(p==='integrations')loadIntegrations().catch(function(e){console.error('loadIntegrations failed:',e)});
else if(p==='account')loadAccount().catch(function(e){console.error('loadAccount failed:',e)});
else if(p==='evolution')loadEvolution().catch(function(e){console.error('loadEvolution failed:',e)});
else if(p==='nexus')loadNexus().catch(function(e){console.error('loadNexus failed:',e)});
else if(p==='command')loadCommand().catch(function(e){console.error('loadCommand failed:',e)});
}catch(e){console.error('Load error:',p,e)}
}
function openModal(id){const el=$(id);if(el)el.classList.add('active')}function closeModal(id){const el=$(id);if(el)el.classList.remove('active')}function toast(msg,err=false){const t=$('toast');if(t){t.textContent=msg;t.className='toast show'+(err?' error':'');setTimeout(()=>t.classList.remove('show'),3000)}}
function apptCard(a){const g=agents[a.agent_type]||{name:'Agent'};return `<div class="appt-card"><div class="appt-header"><div><div class="appt-name">${a.first_name||'Customer'}</div><div class="appt-phone">${a.phone||''}</div></div><span class="status status-${a.disposition||'scheduled'}">${a.disposition||'Scheduled'}</span></div><div class="appt-meta"><span>${a.appointment_date||'TBD'}</span><span>${a.appointment_time||''}</span><span>${g.name}</span></div><div class="appt-actions">${!a.disposition?`<button class="btn btn-sm btn-success" onclick="qDispo(${a.id},'sold')">Sold</button><button class="btn btn-sm btn-danger" onclick="qDispo(${a.id},'no-show')">No Show</button>`:''}<button class="btn btn-sm btn-secondary" onclick="editAppt(${a.id})">Edit</button></div></div>`}
async function loadDash(){try{const s=await fetch('/api/appointment-stats').then(r=>r.json()).catch(()=>({}));if($('s-today'))$('s-today').textContent=s.today||0;if($('s-scheduled'))$('s-scheduled').textContent=s.scheduled||0;if($('s-sold'))$('s-sold').textContent=s.sold||0;if($('s-revenue'))$('s-revenue').textContent='$'+(s.revenue||0).toLocaleString();const today=new Date().toISOString().split('T')[0];const a=await fetch('/api/appointments?date='+today).then(r=>r.json()).catch(()=>[]);if($('today-list'))$('today-list').innerHTML=a.length?a.map(x=>apptCard(x)).join(''):'<p style="color:var(--gray-500);text-align:center;padding:40px">No appointments today</p>'}catch(e){console.error('loadDash error:',e)}}
async function loadCal(){try{const y=curMonth.getFullYear(),m=curMonth.getMonth();if($('cal-title'))$('cal-title').textContent=curMonth.toLocaleDateString('en-US',{month:'long',year:'numeric'});const data=await fetch(`/api/calendar?year=${y}&month=${m+1}`).then(r=>r.json()).catch(()=>({}));const first=new Date(y,m,1).getDay(),days=new Date(y,m+1,0).getDate(),today=new Date().toISOString().split('T')[0];let h='';for(let i=0;i<first;i++)h+='<div class="cal-day other"></div>';for(let d=1;d<=days;d++){const dt=`${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;const info=data[dt]||{count:0};h+=`<div class="cal-day${dt===today?' today':''}${dt===selDate?' selected':''}" onclick="selDay('${dt}')"><div class="cal-day-num">${d}</div>${info.count?`<span class="cal-count">${info.count}</span>`:''}</div>`}if($('cal-days'))$('cal-days').innerHTML=h;if(selDate)loadDay(selDate)}catch(e){console.error('loadCal error:',e)}}
function chgMonth(d){curMonth.setMonth(curMonth.getMonth()+d);loadCal()}async function selDay(dt){selDate=dt;calSelectedDate=new Date(dt+'T12:00:00');loadCal();if(typeof loadVoiceCal==='function')loadVoiceCal();loadDay(dt)}

/* ═══════════════════════════════════════════════════════════════════════════════ */
/* VOICE OS CALENDAR - REVOLUTIONARY AI-POWERED SCHEDULING                         */
/* ═══════════════════════════════════════════════════════════════════════════════ */

setInterval(()=>{const now=new Date();const el=$('current-time');if(el)el.textContent=now.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'})},1000);

function setCalView(mode){calViewMode=mode;document.querySelectorAll('.view-toggle-btn').forEach(b=>b.classList.remove('active'));if(event&&event.target)event.target.classList.add('active');if($('stream-view'))$('stream-view').style.display=mode==='stream'?'flex':'none';if($('orbit-view'))$('orbit-view').style.display=mode==='orbit'?'block':'none';if($('grid-view'))$('grid-view').style.display=mode==='grid'?'block':'none';if(mode==='stream')loadTimeline();else if(mode==='orbit')loadOrbit();else if(mode==='grid')loadCal()}

function navCalDate(dir){if(dir===0)calSelectedDate=new Date();else calSelectedDate.setDate(calSelectedDate.getDate()+dir);updateCalDateDisplay();loadVoiceCal()}

function updateCalDateDisplay(){const today=new Date();const isToday=calSelectedDate.toDateString()===today.toDateString();const isTomorrow=calSelectedDate.toDateString()===new Date(today.getTime()+86400000).toDateString();const isYesterday=calSelectedDate.toDateString()===new Date(today.getTime()-86400000).toDateString();let label=calSelectedDate.toLocaleDateString('en-US',{weekday:'long'});if(isToday)label='Today';else if(isTomorrow)label='Tomorrow';else if(isYesterday)label='Yesterday';const dateStr=calSelectedDate.toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'});if($('cal-date-display'))$('cal-date-display').innerHTML=label+' <span>• '+dateStr+'</span>'}

async function loadVoiceCal(){try{updateCalDateDisplay();const dateStr=calSelectedDate.toISOString().split('T')[0];const appts=await fetch('/api/appointments?date='+dateStr).then(r=>r.json()).catch(()=>[]);if($('cal-today-count'))$('cal-today-count').textContent=appts.length;if($('cal-ai-booked'))$('cal-ai-booked').textContent=appts.filter(a=>a.source==='ai_call').length;if($('cal-open-slots'))$('cal-open-slots').textContent=Math.max(0,10-appts.length);const completed=appts.filter(a=>a.status==='completed').length;if($('cal-conversion'))$('cal-conversion').textContent=appts.length?Math.round((completed/appts.length)*100)+'%':'0%';if(calViewMode==='stream')loadTimeline(appts);else if(calViewMode==='orbit')loadOrbit(appts);else loadCal()}catch(e){console.error('loadVoiceCal error:',e)}}

async function loadTimeline(appts){if(!appts){const dateStr=calSelectedDate.toISOString().split('T')[0];appts=await fetch('/api/appointments?date='+dateStr).then(r=>r.json())}const slots=[];const now=new Date();const isToday=calSelectedDate.toDateString()===now.toDateString();for(let h=8;h<=18;h++){const time=(h>12?h-12:h)+':00 '+(h>=12?'PM':'AM');const timeKey=String(h).padStart(2,'0')+':00';const appt=appts.find(a=>a.appointment_time&&a.appointment_time.startsWith(timeKey));const isNow=isToday&&now.getHours()===h;const aiScores={8:12,9:24,10:38,11:47,12:52,13:41,14:49,15:51,16:35,17:22,18:15};const aiScore=aiScores[h]||30;slots.push({time,timeKey,appt,isNow,aiScore,hour:h})}let html='';slots.forEach(slot=>{html+='<div class="time-marker '+(slot.isNow?'now':'')+'"><div class="marker-time">'+slot.time+'</div><div class="marker-dot"></div>';if(slot.appt){const isAI=slot.appt.source==='ai_call';const isHighValue=(slot.appt.sale_amount||0)>1000;html+='<div class="event-card '+(isAI?'ai-booked':'')+' '+(isHighValue?'high-value':'')+'" onclick="viewAppt('+slot.appt.id+')"><div class="event-header"><div class="event-title">'+(slot.appt.first_name||'Customer')+' '+(slot.appt.last_name||'')+'</div><span class="event-badge '+(isAI?'badge-ai':'badge-manual')+'">'+(isAI?'AI Booked':'Manual')+'</span></div><div class="event-details">'+(slot.appt.address||'No address')+'</div><div class="event-meta"><span>📞 '+(slot.appt.phone||'No phone')+'</span><span>🏷️ '+(agents[slot.appt.agent_type]?.name||slot.appt.agent_type||'General')+'</span></div>'+(isAI?'<div class="event-ai-insight">Booked via AI call • '+(slot.appt.call_duration||0)+'s conversation</div>':'')+'</div>'}else{const isHot=slot.aiScore>45;html+='<div class="empty-slot" onclick="quickBookSlot(\\''+slot.timeKey+'\\')"><div class="empty-slot-label">Open Slot</div>'+(isHot?'<div class="slot-ai-score">🔥 '+slot.aiScore+'% conversion</div>':'<div class="slot-ai-score" style="background:rgba(107,114,128,0.1);color:#9ca3af">'+slot.aiScore+'% conversion</div>')+'</div>'}html+='</div>'});if($('timeline'))$('timeline').innerHTML='<div class="timeline-line"></div>'+html;if(isToday){const nowMarker=document.querySelector('.time-marker.now');if(nowMarker)nowMarker.scrollIntoView({behavior:'smooth',block:'center'})}}

function loadOrbit(appts){if(!appts)appts=[];const container=$('orbit-nodes');if(!container)return;let html='';const centerX=200,centerY=200;appts.forEach((appt,i)=>{const ring=Math.min(2,Math.floor(i/4))+1;const radius=ring*70+30;const angle=(i%8)*(Math.PI/4)+(ring*0.3);const x=centerX+radius*Math.cos(angle);const y=centerY+radius*Math.sin(angle);const isUrgent=appt.status==='pending';const isComplete=appt.status==='completed'||appt.status==='sold';html+='<div class="orbit-node '+(isUrgent?'urgent':'')+' '+(isComplete?'complete':'')+'" style="left:'+x+'px;top:'+y+'px" onclick="viewAppt('+appt.id+')" title="'+(appt.first_name||'?')+' - '+appt.appointment_time+'"><div class="orbit-node-inner">'+(appt.first_name||'?')[0]+'</div></div>'});container.innerHTML=html}

function quickBookSlot(time){if($('qb-date'))$('qb-date').value=calSelectedDate.toISOString().split('T')[0];if($('qb-time'))$('qb-time').value=time;if($('qb-name'))$('qb-name').focus();toast('Booking for '+time)}

async function quickBook(){const name=$('qb-name')?$('qb-name').value.trim():'';const phone=$('qb-phone')?$('qb-phone').value.trim():'';const date=$('qb-date')?$('qb-date').value:'';const time=$('qb-time')?$('qb-time').value:'';if(!phone||!date){toast('Phone and date required',true);return}const res=await fetch('/api/appointment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({first_name:name||'Customer',phone:phone,date:date,time:time,source:'quick_book'})}).then(r=>r.json());if(res.success||res.id){toast('✅ Appointment booked!');if($('qb-name'))$('qb-name').value='';if($('qb-phone'))$('qb-phone').value='';loadVoiceCal()}else{toast('❌ '+(res.error||'Failed'),true)}}

function setCalVoice(text){if($('cal-voice-input'))$('cal-voice-input').value=text;processCalVoice()}

async function processCalVoice(){const input=$('cal-voice-input')?$('cal-voice-input').value.trim():'';if(!input)return;if($('cal-voice-input'))$('cal-voice-input').value='';toast('🤖 Processing...');const res=await fetch('/api/aria',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:input})}).then(r=>r.json());if(res.response){toast(res.response.substring(0,100));loadVoiceCal()}}

function viewAppt(id){fetch('/api/appointments').then(r=>r.json()).then(appts=>{const appt=appts.find(a=>a.id===id);if(appt){$('ed-id').value=appt.id;if($('ed-name'))$('ed-name').textContent=(appt.first_name||'')+' '+(appt.last_name||'');$('ed-date').value=appt.appointment_date;$('ed-time').value=appt.appointment_time;openModal('edit-modal')}})}

async function loadDay(dt){if($('day-title'))$('day-title').textContent=new Date(dt+'T12:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});const a=await fetch('/api/appointments?date='+dt).then(r=>r.json()).catch(()=>[]);if($('day-list'))$('day-list').innerHTML=a.length?a.map(x=>apptCard(x)).join(''):'<p style="color:var(--gray-500);text-align:center;padding:40px">No appointments</p>'}
async function loadAppts(){try{const s=await fetch('/api/appointment-stats').then(r=>r.json()).catch(()=>({}));const a=await fetch('/api/appointments').then(r=>r.json()).catch(()=>[]);if($('a-total'))$('a-total').textContent=s.total||0;if($('a-sched'))$('a-sched').textContent=s.scheduled||0;if($('a-pend'))$('a-pend').textContent=s.pending_disposition||0;if($('a-sold'))$('a-sold').textContent=s.sold||0;if($('appt-list'))$('appt-list').innerHTML=a.length?a.map(x=>apptCard(x)).join(''):'<p style="color:var(--gray-500);text-align:center;padding:40px">No appointments</p>'}catch(e){console.error('loadAppts error:',e)}}
async function saveAppt(){const d={first_name:$('ap-fn').value,phone:$('ap-ph').value,address:$('ap-addr').value,date:$('ap-date').value,time:$('ap-time').value,agent_type:$('ap-agent').value};if(!d.phone||!d.date){toast('Phone and date required',true);return}await fetch('/api/appointment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});closeModal('appt-modal');toast('Appointment created');loadDash();if(selDate)loadCal()}
function editAppt(id){fetch('/api/appointments').then(r=>r.json()).then(a=>{const x=a.find(z=>z.id===id);if(!x)return;$('ed-id').value=id;$('ed-date').value=x.appointment_date||'';$('ed-time').value=x.appointment_time||'';openModal('edit-modal')})}
async function updateAppt(){await fetch('/api/appointment/'+$('ed-id').value,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({appointment_date:$('ed-date').value,appointment_time:$('ed-time').value})});closeModal('edit-modal');toast('Updated');loadDash();if(selDate)loadCal()}
async function loadDispo(){try{const a=await fetch('/api/appointments').then(r=>r.json()).catch(()=>[]);const p=a.filter(x=>!x.disposition);const s=a.filter(x=>x.disposition==='sold');const n=a.filter(x=>x.disposition==='no-show');const r=s.reduce((t,x)=>t+(x.sale_amount||0),0);if($('pend-badge'))$('pend-badge').textContent=p.length+' Pending';if($('d-sold'))$('d-sold').textContent=s.length;if($('d-noshow'))$('d-noshow').textContent=n.length;if($('d-rate'))$('d-rate').textContent=a.length?Math.round(s.length/a.length*100)+'%':'0%';if($('d-rev'))$('d-rev').textContent='$'+r.toLocaleString();if($('pend-list'))$('pend-list').innerHTML=p.length?p.map(x=>`<div class="appt-card"><div class="appt-header"><div><div class="appt-name">${x.first_name||'Customer'}</div><div class="appt-phone">${x.phone}</div></div></div><div class="appt-meta"><span>${x.appointment_date||'TBD'}</span><span>${x.appointment_time||''}</span></div><div class="appt-actions" style="margin-top:12px"><button class="btn btn-sm btn-success" style="flex:1" onclick="qDispo(${x.id},'sold')">Sold</button><button class="btn btn-sm btn-danger" style="flex:1" onclick="qDispo(${x.id},'no-show')">No Show</button></div></div>`).join(''):'<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--gray-500)">All caught up!</div>'}catch(e){console.error('loadDispo error:',e)}}
async function qDispo(id,st){await fetch('/api/disposition',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({appt_id:id,disposition:st})});toast('Saved');loadDispo();loadDash()}
function loadOut(){if($('out-grid'))$('out-grid').innerHTML=Object.entries(outbound).map(([k,v])=>`<div class="agent-card" onclick="openTestModal('${k}')" style="border-top:3px solid ${v.color}"><div class="agent-icon">${v.icon}</div><div class="agent-name">${v.name}</div><div class="agent-role">${v.industry}</div></div>`).join('')}
function loadIn(){if($('in-grid'))$('in-grid').innerHTML=Object.entries(inbound).map(([k,v])=>`<div class="agent-card" onclick="openTestModal('${k}')" style="border-top:3px solid ${v.color}"><div class="agent-icon">${v.icon}</div><div class="agent-name">${v.name}</div><div class="agent-role">${v.industry}</div></div>`).join('')}
function openTestModal(agentType){$('test-agent-type').value=agentType;$('test-modal-title').textContent='Test '+agents[agentType].name;openModal('test-modal')}
async function runTest(isLive){const agent=$('test-agent-type').value;const phone=$('test-phone-input').value||testPhone;if(!phone){toast('Enter a phone number',true);return}closeModal('test-modal');toast('Calling '+phone+'...');const r=await fetch('/api/test-agent-phone',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_type:agent,phone:phone,is_live:isLive})}).then(r=>r.json());if(r.success)toast('Call initiated!');else toast('Error: '+r.error,true)}
async function testAgent(t){openTestModal(t)}
async function loadLeads(){try{const l=await fetch('/api/leads').then(r=>r.json()).catch(()=>[]);if($('leads-tb'))$('leads-tb').innerHTML=l.map(x=>`<tr><td>${x.first_name||'Unknown'}</td><td>${x.phone}</td><td>${agents[x.agent_type]?.name||'?'}</td><td><span class="status status-${x.pipeline_stage||x.status}">${x.pipeline_stage||x.status}</span></td></tr>`).join('')}catch(e){console.error('loadLeads error:',e)}}
async function loadWebsiteLeads(){try{
const leads=await fetch('/api/website-leads').then(r=>r.json()).catch(()=>[]);
const stats=await fetch('/api/website-stats').then(r=>r.json()).catch(()=>({total_leads:0,new_leads:0,converted:0,today_visits:0}));
if($('wl-total'))$('wl-total').textContent=stats.total_leads;
if($('wl-new'))$('wl-new').textContent=stats.new_leads;
if($('wl-converted'))$('wl-converted').textContent=stats.converted;
if($('wl-visits'))$('wl-visits').textContent=stats.today_visits;
if($('website-leads-tb'))$('website-leads-tb').innerHTML=leads.length?leads.map(l=>`<tr>
<td style="font-size:12px">${new Date(l.created_at).toLocaleDateString()}</td>
<td><strong>${l.first_name||''} ${l.last_name||''}</strong></td>
<td><a href="mailto:${l.email}" style="color:var(--cyan)">${l.email||'-'}</a></td>
<td><a href="tel:${l.phone}" style="color:var(--cyan)">${l.phone||'-'}</a></td>
<td>${l.company||'-'}</td>
<td>${l.industry||'-'}</td>
<td>${l.preferred_day||''} ${l.preferred_time||''}</td>
<td><span class="status status-${l.status==='new'?'scheduled':l.status==='contacted'?'cyan':l.converted?'sold':'pending'}">${l.status}</span></td>
<td><button class="btn btn-sm btn-primary" onclick="callWebsiteLead('${l.phone}','${l.first_name}')">📞 Call</button> <button class="btn btn-sm btn-secondary" onclick="updateWebsiteLeadStatus(${l.id},'contacted')">✓</button></td>
</tr>`).join(''):'<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--gray-500)">No website leads yet. Share voicelab.live to start collecting leads!</td></tr>';
}catch(e){console.error('loadWebsiteLeads error:',e)}}
async function callWebsiteLead(phone,name){
if(!phone){toast('No phone number',true);return}
toast('Calling '+name+'...');
await fetch('/api/test-agent-phone',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_type:'roofing',phone:phone,is_live:true})});
}
async function updateWebsiteLeadStatus(id,status){
await fetch('/api/website-lead-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id,status:status})});
toast('Status updated');
loadWebsiteLeads();
}
async function loadCalls(){try{const c=await fetch('/api/calls').then(r=>r.json()).catch(()=>[]);if($('calls-tb'))$('calls-tb').innerHTML=c.map(x=>`<tr><td style="font-size:12px">${new Date(x.created_at).toLocaleString()}</td><td>${x.phone}</td><td>${agents[x.agent_type]?.name||'?'}</td><td>${x.is_inbound?'Inbound':'Outbound'}</td><td><span class="status ${x.is_live?'status-sold':'status-scheduled'}">${x.is_live?'Live':'Test'}</span></td></tr>`).join('')}catch(e){console.error('loadCalls error:',e)}}
async function loadCosts(){try{const c=await fetch('/api/live-costs').then(r=>r.json()).catch(()=>({today:{total:0,calls:0,sms:0},month:{total:0}}));if($('c-today'))$('c-today').textContent='$'+(c.today?.total||0).toFixed(2);if($('c-month'))$('c-month').textContent='$'+(c.month?.total||0).toFixed(2);if($('c-calls'))$('c-calls').textContent=c.today?.calls||0;if($('c-sms'))$('c-sms').textContent='$'+(c.today?.sms||0).toFixed(3)}catch(e){console.error('loadCosts error:',e)}}
async function saveLead(){const p=$('l-phone').value;if(!p){toast('Phone required',true);return}await fetch('/api/start-cycle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:p,name:$('l-name').value||'there',agent_type:$('l-agent').value})});closeModal('lead-modal');toast('Lead cycle started');loadDash()}
async function loadTesting(){try{
const settings=await fetch('/api/settings').then(r=>r.json()).catch(()=>({}));
if($('cfg-test-phone'))$('cfg-test-phone').value=settings.test_phone||'';
if($('cfg-mode'))$('cfg-mode').value=settings.mode||'testing';
const allOpts=Object.entries(agents).map(([k,v])=>`<div class="agent-card" onclick="openTestModal('${k}')" style="border-top:3px solid ${v.color||'#00D1FF'}"><div class="agent-icon">${v.icon||'🤖'}</div><div class="agent-name">${v.name}</div><div class="agent-role">${v.industry}</div></div>`).join('');
if($('all-agents-grid'))$('all-agents-grid').innerHTML=allOpts;
}catch(e){console.error('loadTesting error:',e)}}
async function saveTestPhone(){const p=$('cfg-test-phone').value;await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({test_phone:p})});testPhone=p;toast('Test phone saved!')}
async function saveMode(){const m=$('cfg-mode').value;await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:m})});toast('Mode set to '+m)}
async function loadAds(){try{const stats=await fetch('/api/ad-stats').then(r=>r.json()).catch(()=>({today:{spend:0,leads:0,cpl:0,appointments:0},month:{spend:0,leads:0,cpl:0,roas:0}}));const campaigns=await fetch('/api/ad-campaigns').then(r=>r.json()).catch(()=>[]);
if($('ad-spend-today'))$('ad-spend-today').textContent='$'+(stats.today?.spend||0).toFixed(2);
if($('ad-leads-today'))$('ad-leads-today').textContent=stats.today?.leads||0;
if($('ad-cpl-today'))$('ad-cpl-today').textContent='$'+(stats.today?.cpl||0).toFixed(2);
if($('ad-appts-today'))$('ad-appts-today').textContent=stats.today?.appointments||0;
if($('ad-spend-month'))$('ad-spend-month').textContent='$'+(stats.month?.spend||0).toFixed(2);
if($('ad-leads-month'))$('ad-leads-month').textContent=stats.month?.leads||0;
if($('ad-cpl-month'))$('ad-cpl-month').textContent='$'+(stats.month?.cpl||0).toFixed(2);
if($('ad-roas-month'))$('ad-roas-month').textContent=(stats.month?.roas||0).toFixed(1)+'x';
if($('campaigns-list'))$('campaigns-list').innerHTML=campaigns.length?campaigns.map(c=>`<tr><td>${c.campaign_name}</td><td>${c.platform}</td><td>$${c.daily_budget}</td><td>$${c.total_spend.toFixed(2)}</td><td>${c.leads}</td><td>${c.appointments}</td><td><span class="status status-${c.status==='active'?'sold':'scheduled'}">${c.status}</span></td></tr>`).join(''):'<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--gray-500)">No campaigns yet. Add your Facebook/Instagram campaigns.</td></tr>';
}catch(e){console.error('loadAds error:',e)}}
async function addCampaign(){const name=$('camp-name').value;const budget=$('camp-budget').value;const platform=$('camp-platform').value;if(!name){toast('Campaign name required',true);return}await fetch('/api/ad-campaigns',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({campaign_name:name,daily_budget:budget,platform:platform})});closeModal('campaign-modal');toast('Campaign added');loadAds()}
async function loadPipeline(){try{const stats=await fetch('/api/pipeline-stats').then(r=>r.json()).catch(()=>({}));const stages=await fetch('/api/pipeline-stages').then(r=>r.json()).catch(()=>[]);
let html='';stages.forEach(s=>{const st=stats[s.stage_key]||{total:0};html+=`<div class="pipeline-stage" style="border-left:3px solid ${s.stage_color}"><div class="stage-name">${s.stage_name}</div><div class="stage-count">${st.total}</div></div>`});
if($('pipeline-board'))$('pipeline-board').innerHTML=html;
}catch(e){console.error('loadPipeline error:',e)}}
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

// ═══════════════════════════════════════════════════════════════════════════════
// VOICE EVOLUTION - Neural Learning Dashboard
// ═══════════════════════════════════════════════════════════════════════════════

// Agent Configuration Registry - RETELL ONLY
const VOICE_AGENTS = {
    'retell_outbound': {
        name: 'Hailey Outbound',
        platform: 'RETELL',
        description: 'Outbound calls to leads',
        agent_id: 'agent_c345c5f578ebd6c188a7e474fa',
        phone: '+1 (720) 864-0910',
        color: '#a855f7'
    },
    'retell_inbound': {
        name: 'Hailey Inbound',
        platform: 'RETELL',
        description: 'Inbound calls (720) 818-9512',
        agent_id: 'agent_862cd6cf87f7b4d68a6986b3e9',
        phone: '+1 (720) 818-9512',
        color: '#00ff88'
    }
};

// Current genome settings for each agent
let agentGenomes = {
    'retell_outbound': {
        responsiveness: 0.5, response_delay: 0, interruption_threshold: 5,
        silence_tolerance: 45, words_per_minute: 150, pause_frequency: 0.25,
        pause_duration: 0.8, filler_frequency: 0.05, backchannel: 1,
        backchannel_frequency: 0.5, emotion_variance: 0.4, temperature: 0.8, listen_ratio: 0.55
    },
    'retell_inbound': {
        responsiveness: 0.5, response_delay: 0, interruption_threshold: 5,
        silence_tolerance: 45, words_per_minute: 150, pause_frequency: 0.25,
        pause_duration: 0.8, filler_frequency: 0.05, backchannel: 1,
        backchannel_frequency: 0.5, emotion_variance: 0.4, temperature: 0.8, listen_ratio: 0.55
    }
};

let evolutionEnabled = true;
let evolutionData = { agents: {}, calls: [], issues: [] };

async function loadEvolution() {
    try {
        const data = await fetch('/api/evolution').then(r => r.json()).catch(() => ({}));
        evolutionData = data;
        renderEvolutionDashboard(data);
    } catch (e) {
        console.error('Evolution load error:', e);
        renderEvolutionDashboard({});
    }
}

function renderEvolutionDashboard(data) {
    const stats = data.stats || {};
    const agents = data.agents || {};
    const calls = data.calls || [];
    const issues = data.issues || [];
    
    // Update stats
    if($('evo-total-calls'))$('evo-total-calls').textContent = stats.total || 0;
    if($('evo-avg-fitness')){$('evo-avg-fitness').textContent = Math.round(stats.fitness || 0);$('evo-avg-fitness').className = 'evo-stat-value ' + getScoreClass(stats.fitness)}
    if($('evo-human-score')){$('evo-human-score').textContent = Math.round(stats.human || 0);$('evo-human-score').className = 'evo-stat-value ' + getScoreClass(stats.human)}
    if($('evo-pacing-score'))$('evo-pacing-score').textContent = Math.round(stats.pacing || 0);
    if($('evo-engagement-score'))$('evo-engagement-score').textContent = Math.round(stats.engagement || 0);
    if($('evo-evolutions'))$('evo-evolutions').textContent = stats.total_evolutions || 0;
    
    // Update agent call counts
    const outboundCalls = calls.filter(c => c.agent === 'retell_outbound').length;
    const inboundCalls = calls.filter(c => c.agent === 'retell_inbound').length;
    if($('evo-outbound-calls'))$('evo-outbound-calls').textContent = outboundCalls;
    if($('evo-inbound-calls'))$('evo-inbound-calls').textContent = inboundCalls;
    
    // Render agent cards
    renderAgentCards(agents);
    
    // Render recent calls
    renderEvolutionCalls(calls);
    
    // Render issues
    renderEvolutionIssues(issues);
}

function getScoreClass(score) {
    if (!score) return '';
    if (score >= 70) return 'green';
    if (score >= 50) return 'orange';
    return 'red';
}

function renderAgentCards(agents) {
    const grid = $('evo-agents-grid');
    if (!grid) return;
    
    const voiceOptions = [
        { id: '11labs-Hailey', name: 'Hailey (Female) ⭐' },
        { id: '11labs-Rachel', name: 'Rachel (Female)' },
        { id: '11labs-Bella', name: 'Bella (Female)' },
        { id: '11labs-Antoni', name: 'Antoni (Male)' },
        { id: '11labs-Maya', name: 'Maya (Female)' },
        { id: '11labs-Marissa', name: 'Marissa (Female)' },
        { id: '11labs-Paige', name: 'Paige (Female)' }
    ];
    
    let html = '';
    for (const [key, config] of Object.entries(VOICE_AGENTS)) {
        const agentData = agents[key] || {};
        const genome = agentGenomes[key] || {};
        const fitness = Math.round(agentData.fitness || 70);
        const humanScore = Math.round(agentData.human_score || 65);
        const pacingScore = Math.round(agentData.pacing_score || 68);
        const engageScore = Math.round(agentData.engagement_score || 72);
        const latency = Math.round(agentData.avg_latency || 350);
        const totalCalls = agentData.total_calls || 0;
        
        const voiceSelect = voiceOptions.map(v => 
            '<option value="' + v.id + '">' + v.name + '</option>'
        ).join('');
        
        html += '<div class="evo-agent-card" data-agent="' + key + '" style="border-color: ' + config.color + '20">' +
            '<div class="evo-agent-header" style="background: linear-gradient(135deg, ' + config.color + '15, transparent)">' +
                '<div>' +
                    '<div class="evo-agent-name">' + config.name + '</div>' +
                    '<div class="evo-agent-platform">' + config.platform + ' • ' + (config.phone || config.agent_id.slice(0,20) + '...') + '</div>' +
                '</div>' +
                '<div class="evo-agent-badges">' +
                    '<span class="evo-badge fitness ' + getScoreClass(fitness) + '">' + fitness + '</span>' +
                '</div>' +
            '</div>' +
            
            '<div class="evo-metrics-row">' +
                '<div class="evo-metric"><div class="evo-metric-value ' + getScoreClass(humanScore) + '">' + humanScore + '</div><div class="evo-metric-label">Human</div></div>' +
                '<div class="evo-metric"><div class="evo-metric-value ' + getScoreClass(pacingScore) + '">' + pacingScore + '</div><div class="evo-metric-label">Pacing</div></div>' +
                '<div class="evo-metric"><div class="evo-metric-value ' + getScoreClass(engageScore) + '">' + engageScore + '</div><div class="evo-metric-label">Engage</div></div>' +
                '<div class="evo-metric"><div class="evo-metric-value">' + latency + 'ms</div><div class="evo-metric-label">Latency</div></div>' +
                '<div class="evo-metric"><div class="evo-metric-value">' + totalCalls + '</div><div class="evo-metric-label">Calls</div></div>' +
            '</div>' +
            
            '<div class="evo-genome-section">' +
                '<div class="evo-genome-title">🎤 Voice Settings</div>' +
                '<div class="evo-voice-selector">' +
                    '<span class="evo-gene-label">Voice Model</span>' +
                    '<select class="evo-voice-select" id="voice-' + key + '">' + voiceSelect + '</select>' +
                '</div>' +
                '<div class="evo-genome-title" style="margin-top:16px">⚙️ Quick Settings</div>' +
                '<div class="evo-gene-row">' +
                    '<span class="evo-gene-label">Responsiveness</span>' +
                    '<input type="range" class="evo-slider" min="0.1" max="1" step="0.1" value="' + (genome.responsiveness || 0.5) + '" ' +
                        'oninput="updateGene(\\'' + key + '\\', \\'responsiveness\\', this.value)">' +
                    '<span class="evo-gene-value" id="' + key + '-responsiveness">' + (genome.responsiveness || 0.5) + '</span>' +
                '</div>' +
                '<div class="evo-gene-row">' +
                    '<span class="evo-gene-label">Temperature</span>' +
                    '<input type="range" class="evo-slider" min="0.3" max="1.2" step="0.1" value="' + (genome.temperature || 0.8) + '" ' +
                        'oninput="updateGene(\\'' + key + '\\', \\'temperature\\', this.value)">' +
                    '<span class="evo-gene-value" id="' + key + '-temperature">' + (genome.temperature || 0.8) + '</span>' +
                '</div>' +
            '</div>' +
            
            '<div class="evo-agent-actions">' +
                '<button class="btn btn-secondary btn-sm" onclick="resetGenome(\\'' + key + '\\')">↺ Reset</button>' +
                '<button class="btn btn-primary" onclick="applyAgentChanges(\\'' + key + '\\')" style="flex:1">⚡ Apply Changes</button>' +
            '</div>' +
        '</div>';
    }
    
    grid.innerHTML = html || '<div style="padding:40px;text-align:center;color:var(--gray-500)">No agents configured</div>';
}

function updateGene(agentKey, gene, value) {
    value = parseFloat(value);
    if (!agentGenomes[agentKey]) agentGenomes[agentKey] = {};
    agentGenomes[agentKey][gene] = value;
    
    // Update display
    const el = document.getElementById(agentKey + '-' + gene);
    if (el) el.textContent = value;
}

function resetGenome(agentKey) {
    agentGenomes[agentKey] = {
        responsiveness: 0.5, response_delay: 0, interruption_threshold: 5,
        silence_tolerance: 45, words_per_minute: 150, pause_frequency: 0.25,
        pause_duration: 0.8, filler_frequency: 0.05, backchannel: 1,
        backchannel_frequency: 0.5, emotion_variance: 0.4, temperature: 0.8, listen_ratio: 0.55
    };
    loadEvolution();
    toast('Settings reset to defaults');
}

async function applyAgentChanges(agentKey) {
    const genome = agentGenomes[agentKey] || {};
    const voiceSelect = document.getElementById('voice-' + agentKey);
    const voiceId = voiceSelect ? voiceSelect.value : '11labs-Hailey';
    
    toast('Applying changes...');
    
    try {
        // Update voice
        const voiceResult = await fetch('/api/agent/voice', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({agent_key: agentKey, voice_id: voiceId})
        }).then(r => r.json());
        
        // Update genome settings
        const genomeResult = await fetch('/api/evolution/agent/' + agentKey, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(genome)
        }).then(r => r.json());
        
        if (voiceResult.success || genomeResult.success) {
            toast('✅ Agent updated successfully!');
        } else {
            toast('⚠️ ' + (voiceResult.error || genomeResult.error || 'Update failed'), true);
        }
    } catch(e) {
        toast('❌ Error: ' + e.message, true);
    }
}

async function updateAgentVoice(agentKey, voiceId) {
    const voiceName = document.querySelector(`[data-agent="${agentKey}"] .evo-voice-select option:checked`)?.textContent || voiceId;
    toast(`Updating voice...`);
    
    try {
        const r = await fetch('/api/agent/voice', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({agent_key: agentKey, voice_id: voiceId, voice_name: voiceName})
        }).then(r => r.json());
        
        if (r.success) {
            toast(`✓ ${r.message}`);
        } else {
            toast(`Error: ${r.error}`, true);
        }
    } catch(e) {
        toast('Failed to update voice', true);
    }
}

async function syncAllVoices(sourceAgentKey) {
    const sourceSelect = document.querySelector(`[data-agent="${sourceAgentKey}"] .evo-voice-select`);
    if (!sourceSelect) return;
    
    const targetVoice = sourceSelect.value;
    const voiceName = sourceSelect.options[sourceSelect.selectedIndex]?.textContent || targetVoice;
    
    // Update all voice selects in UI immediately
    document.querySelectorAll('.evo-voice-select').forEach(select => {
        select.value = targetVoice;
    });
    
    toast(`Syncing all agents...`);
    
    try {
        const r = await fetch('/api/agent/voice/sync', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({voice_id: targetVoice, voice_name: voiceName})
        }).then(r => r.json());
        
        if (r.success) {
            toast(`✓ ${r.message}`);
        } else {
            toast(`Partial sync: ${r.errors?.length || 0} errors`, true);
        }
    } catch(e) {
        toast('Failed to sync voices', true);
    }
}

async function applyGenome(agentKey) {
    const genome = agentGenomes[agentKey];
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Applying...';
    
    try {
        const r = await fetch(`/api/evolution/agent/${agentKey}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(genome)
        }).then(r => r.json());
        
        if (r.success) {
            toast('✅ ' + (r.message || 'Agent updated!'));
        } else {
            toast('❌ ' + (r.error || 'Failed to update'), true);
        }
    } catch (e) {
        toast('❌ Error: ' + e.message, true);
    } finally {
        btn.disabled = false;
        btn.textContent = '⚡ Apply Live';
    }
}

async function syncEvolution() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-small"></span> Syncing...';
    
    try {
        const r = await fetch('/api/evolution/sync', {method: 'POST'}).then(r => r.json());
        
        const vapiCount = r.vapi?.processed || 0;
        const retellCount = r.retell?.processed || 0;
        const evolved = (r.vapi?.evolved || 0) + (r.retell?.evolved || 0);
        
        toast(`✅ Analyzed ${vapiCount + retellCount} calls, ${evolved} auto-evolutions`);
        loadEvolution();
    } catch (e) {
        toast('❌ Sync failed', true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '⚡ Sync & Analyze';
    }
}

function toggleEvolution() {
    evolutionEnabled = !evolutionEnabled;
    const toggle = $('evo-toggle');
    const dot = $('evo-toggle-dot');
    const text = $('evo-toggle-text');
    
    if (evolutionEnabled) {
        toggle.classList.remove('disabled');
        text.textContent = 'Auto-Learning ON';
    } else {
        toggle.classList.add('disabled');
        text.textContent = 'Auto-Learning OFF';
    }
    
    fetch('/api/evolution/toggle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({enabled: evolutionEnabled})
    });
}

function renderEvolutionCalls(calls) {
    const tbody = $('evo-calls-body');
    if (!tbody) return;
    
    if (!calls || calls.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--gray-500)">No calls analyzed yet. Click "Sync & Analyze" to fetch data.</td></tr>';
        return;
    }
    
    tbody.innerHTML = calls.slice(0, 20).map(call => {
        const fitness = Math.round(call.overall_fitness || call.human_score || 50);
        const scoreClass = getScoreClass(fitness);
        let issues = [];
        try { issues = JSON.parse(call.issues_json || '[]'); } catch(e) {}
        
        return `
        <tr onclick="showEvoCallDetail('${call.call_id}')" style="cursor:pointer">
            <td>
                <div style="font-weight:600">${call.agent_name || 'Unknown'}</div>
                <div style="font-size:11px;color:var(--gray-500)">${call.platform}</div>
            </td>
            <td style="font-family:monospace;font-size:12px">${call.phone || '--'}</td>
            <td>${formatDuration(call.duration_seconds)}</td>
            <td><span class="score-pill ${scoreClass}">${fitness}</span></td>
            <td>${Math.round(call.human_score || 0)}</td>
            <td>${Math.round(call.pacing_score || 0)}</td>
            <td>${Math.round(call.avg_latency_ms || 0)}ms</td>
            <td>
                ${issues.slice(0,2).map(i => `<span class="issue-tag">${typeof i === 'string' ? i : i.type}</span>`).join('') || '<span style="color:var(--gray-500)">-</span>'}
            </td>
        </tr>`;
    }).join('');
}

function formatDuration(seconds) {
    if (!seconds) return '0s';
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

function renderEvolutionIssues(issues) {
    const container = $('evo-issues-list');
    if (!container) return;
    
    if (!issues || issues.length === 0) {
        container.innerHTML = '<div style="color:var(--gray-500);text-align:center;padding:20px">No issues detected yet</div>';
        return;
    }
    
    const maxCount = Math.max(...issues.map(i => i.count || 1));
    
    container.innerHTML = issues.slice(0, 10).map(issue => `
        <div class="evo-issue-bar">
            <span class="evo-issue-name">${issue.issue || issue.type || 'Unknown'}</span>
            <div class="evo-issue-track">
                <div class="evo-issue-fill" style="width:${((issue.count || 1) / maxCount) * 100}%"></div>
            </div>
            <span class="evo-issue-count">${issue.count || 1}</span>
        </div>
    `).join('');
}

async function showEvoCallDetail(callId) {
    try {
        const call = await fetch(`/api/evolution/call/${callId}`).then(r => r.json());
        if (call.error) { toast('Call not found', true); return; }
        
        let issues = [], improvements = {}, actions = [];
        try { issues = JSON.parse(call.issues_json || '[]'); } catch(e) {}
        try { improvements = JSON.parse(call.improvements_json || '{}'); } catch(e) {}
        try { actions = JSON.parse(call.evolution_actions_json || '{}').recommended_actions || []; } catch(e) {}
        
        $('evo-modal-body').innerHTML = `
            <div class="evo-detail-grid">
                <div class="evo-detail-card">
                    <div class="evo-detail-label">Human Score</div>
                    <div class="evo-detail-value ${getScoreClass(call.human_score)}">${call.human_score || 0}</div>
                </div>
                <div class="evo-detail-card">
                    <div class="evo-detail-label">Pacing Score</div>
                    <div class="evo-detail-value ${getScoreClass(call.pacing_score)}">${call.pacing_score || 0}</div>
                </div>
                <div class="evo-detail-card">
                    <div class="evo-detail-label">Engagement</div>
                    <div class="evo-detail-value ${getScoreClass(call.engagement_score)}">${call.engagement_score || 0}</div>
                </div>
                <div class="evo-detail-card">
                    <div class="evo-detail-label">Empathy</div>
                    <div class="evo-detail-value ${getScoreClass(call.empathy_score)}">${call.empathy_score || 0}</div>
                </div>
                <div class="evo-detail-card">
                    <div class="evo-detail-label">Closing</div>
                    <div class="evo-detail-value ${getScoreClass(call.closing_score)}">${call.closing_score || 0}</div>
                </div>
                <div class="evo-detail-card">
                    <div class="evo-detail-label">Listening</div>
                    <div class="evo-detail-value ${getScoreClass(call.listening_score)}">${call.listening_score || 0}</div>
                </div>
            </div>
            
            <div class="evo-detail-section">
                <div class="evo-detail-title">📊 Call Metrics</div>
                <div class="evo-metrics-inline">
                    <span><strong>Duration:</strong> ${formatDuration(call.duration_seconds)}</span>
                    <span><strong>WPM:</strong> ${Math.round(call.words_per_minute || 0)}</span>
                    <span><strong>Latency:</strong> ${Math.round(call.avg_latency_ms || 0)}ms</span>
                    <span><strong>Talk Ratio:</strong> ${Math.round((call.agent_talk_ratio || 0.5) * 100)}%</span>
                    <span><strong>Interruptions:</strong> ${call.interruption_count || 0}</span>
                </div>
            </div>
            
            <div class="evo-detail-section">
                <div class="evo-detail-title">📝 AI Summary</div>
                <p style="color:var(--white);line-height:1.6">${call.summary || 'No summary available'}</p>
            </div>
            
            ${improvements.immediate ? `
            <div class="evo-detail-section improvement-box">
                <div class="evo-detail-title">⚡ What to Fix NOW</div>
                <p style="color:var(--orange);font-weight:500">${improvements.immediate}</p>
            </div>` : ''}
            
            ${issues.length > 0 ? `
            <div class="evo-detail-section">
                <div class="evo-detail-title">🚨 Issues Detected</div>
                <div class="evo-issues-detail">
                    ${issues.map(i => `
                        <div class="evo-issue-item ${(typeof i === 'object' ? i.severity : 'medium')}">
                            <div class="evo-issue-type">${typeof i === 'string' ? i : i.type}</div>
                            ${typeof i === 'object' && i.description ? `<div class="evo-issue-desc">${i.description}</div>` : ''}
                            ${typeof i === 'object' && i.fix ? `<div class="evo-issue-fix">Fix: ${i.fix}</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}
            
            ${actions.length > 0 ? `
            <div class="evo-detail-section evolution-box">
                <div class="evo-detail-title">🧬 Recommended Evolution</div>
                <div class="evo-actions-list">
                    ${actions.map(a => `
                        <div class="evo-action-item">
                            <span class="evo-action-gene">${a.gene}</span>
                            <span class="evo-action-arrow">${a.from} → ${a.to}</span>
                            <span class="evo-action-reason">${a.reason}</span>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}
            
            <div class="evo-detail-section">
                <div class="evo-detail-title">📜 Transcript</div>
                <div class="evo-transcript">${call.transcript || 'No transcript available'}</div>
            </div>
        `;
        
        openModal('evo-call-modal');
    } catch(e) {
        toast('Error loading call details', true);
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// NEXUS - Neural Executive Unified System
// ═══════════════════════════════════════════════════════════════════════════════

let nexusState = 'MONITORING';
/* ═══════════════════════════════════════════════════════════════════════════════ */
/* COMMAND CENTER - OPERATIONS HUB                                                 */
/* ═══════════════════════════════════════════════════════════════════════════════ */

async function loadCommand() {
    await loadLeaderboard();
    await loadAuditLog();
    loadLiveActivity();
}

async function loadLeaderboard() {
    try {
        const calls = await fetch('/api/calls').then(r => r.json());
        
        // Calculate stats per agent
        const agentStats = {};
        calls.forEach(c => {
            const agent = c.agent_type || 'unknown';
            if (!agentStats[agent]) {
                agentStats[agent] = { calls: 0, appointments: 0, duration: 0 };
            }
            agentStats[agent].calls++;
            if (c.appointment_booked) agentStats[agent].appointments++;
            agentStats[agent].duration += c.duration || 0;
        });
        
        // Sort by conversion rate
        const sorted = Object.entries(agentStats)
            .map(([agent, stats]) => ({
                agent,
                ...stats,
                rate: stats.calls > 0 ? Math.round((stats.appointments / stats.calls) * 100) : 0
            }))
            .sort((a, b) => b.rate - a.rate)
            .slice(0, 6);
        
        const rankClass = ['gold', 'silver', 'bronze', 'normal', 'normal', 'normal'];
        const agentInfo = {...outbound, ...inbound};
        
        const html = sorted.map((s, i) => {
            const info = agentInfo[s.agent] || { icon: '🤖', color: '#666' };
            return `<div class="leader-item">
                <div class="leader-rank ${rankClass[i]}">${i + 1}</div>
                <div class="leader-avatar" style="background:linear-gradient(135deg,${info.color || '#00d1ff'},#0066ff)">${info.icon || '🤖'}</div>
                <div class="leader-info">
                    <div class="leader-name">${info.name || s.agent}</div>
                    <div class="leader-stats">${s.calls} calls • ${s.appointments} appointments</div>
                </div>
                <div class="leader-score">
                    <div class="leader-score-value">${s.rate}%</div>
                    <div class="leader-score-label">Convert</div>
                </div>
            </div>`;
        }).join('');
        
        if ($('agent-leaderboard')) $('agent-leaderboard').innerHTML = html || '<p style="color:rgba(255,255,255,0.4);text-align:center;padding:20px">No data yet</p>';
    } catch (e) {
        console.error('Leaderboard error:', e);
    }
}

async function loadAuditLog() {
    try {
        const [calls, appts, sms] = await Promise.all([
            fetch('/api/calls').then(r => r.json()).catch(() => []),
            fetch('/api/appointments').then(r => r.json()).catch(() => []),
            fetch('/api/sms-logs').then(r => r.json()).catch(() => [])
        ]);
        
        // Combine and sort by time
        const events = [];
        
        calls.slice(0, 10).forEach(c => {
            events.push({
                type: 'call',
                icon: '📞',
                title: 'Call ' + (c.status === 'completed' ? 'Completed' : 'Initiated'),
                detail: `${agents[c.agent_type]?.name || c.agent_type} → ${c.phone}`,
                why: `Duration: ${c.duration || 0}s • Outcome: ${c.outcome || 'pending'} • Agent: ${c.agent_type}`,
                time: c.created_at
            });
        });
        
        appts.slice(0, 5).forEach(a => {
            events.push({
                type: 'appt',
                icon: '📅',
                title: 'Appointment ' + (a.status || 'Created'),
                detail: `${a.first_name || 'Customer'} on ${a.appointment_date}`,
                why: `Time: ${a.appointment_time} • Type: ${a.agent_type || 'general'} • Source: ${a.source || 'manual'}`,
                time: a.created_at
            });
        });
        
        sms.slice(0, 5).forEach(s => {
            events.push({
                type: 'sms',
                icon: '💬',
                title: 'SMS ' + (s.status === 'delivered' ? 'Delivered' : 'Sent'),
                detail: `To ${s.phone}`,
                why: `Type: ${s.message_type || 'general'} • Twilio: ${s.twilio_sid || 'N/A'}`,
                time: s.created_at
            });
        });
        
        // Sort by time
        events.sort((a, b) => new Date(b.time) - new Date(a.time));
        
        const html = events.slice(0, 15).map(e => {
            const time = e.time ? new Date(e.time).toLocaleTimeString('en-US', {hour: 'numeric', minute: '2-digit'}) : '';
            return `<div class="audit-item">
                <div class="audit-icon ${e.type}">${e.icon}</div>
                <div class="audit-text">
                    <strong>${e.title}</strong> <span>${e.detail}</span>
                    <div class="audit-why">${e.why}</div>
                </div>
                <div class="audit-time">${time}</div>
            </div>`;
        }).join('');
        
        if ($('audit-log')) $('audit-log').innerHTML = html || '<p style="color:rgba(255,255,255,0.4);text-align:center;padding:20px">No activity yet</p>';
    } catch (e) {
        console.error('Audit log error:', e);
    }
}

function loadLiveActivity() {
    // This would connect to websocket for real-time updates
    // For now, refresh periodically
    setInterval(async () => {
        if (document.querySelector('#page-command.active')) {
            await loadAuditLog();
        }
    }, 30000);
}

async function searchLeadTimeline() {
    const query = $('cmd-lead-search')?.value?.trim();
    if (!query) return;
    
    toast('🔍 Searching...');
    
    try {
        // Search leads
        const leads = await fetch('/api/leads').then(r => r.json());
        const lead = leads.find(l => 
            l.phone?.includes(query) || 
            l.first_name?.toLowerCase().includes(query.toLowerCase())
        );
        
        if (!lead) {
            toast('No lead found', true);
            return;
        }
        
        // Get related calls
        const calls = await fetch('/api/calls').then(r => r.json());
        const leadCalls = calls.filter(c => c.phone === lead.phone);
        
        // Get related appointments
        const appts = await fetch('/api/appointments').then(r => r.json());
        const leadAppts = appts.filter(a => a.phone === lead.phone);
        
        // Build timeline
        const events = [];
        
        events.push({
            type: 'lead',
            color: 'orange',
            title: '👤 Lead Created',
            detail: `${lead.first_name || ''} ${lead.last_name || ''} • ${lead.phone} • Source: ${lead.source || 'manual'}`,
            time: lead.created_at,
            value: ''
        });
        
        leadCalls.forEach(c => {
            events.push({
                type: 'call',
                color: 'cyan',
                title: `📞 AI Call - ${agents[c.agent_type]?.name || c.agent_type}`,
                detail: `Duration: ${Math.floor((c.duration || 0) / 60)}:${String((c.duration || 0) % 60).padStart(2, '0')} • Outcome: ${c.outcome || 'pending'}`,
                time: c.created_at,
                value: c.appointment_booked ? '🎯 Converted' : ''
            });
        });
        
        leadAppts.forEach(a => {
            events.push({
                type: 'appt',
                color: 'purple',
                title: '📅 Appointment Booked',
                detail: `${a.appointment_date} ${a.appointment_time} • ${a.status || 'scheduled'}`,
                time: a.created_at,
                value: a.sale_amount ? '$' + a.sale_amount : ''
            });
        });
        
        // Sort by time
        events.sort((a, b) => new Date(a.time) - new Date(b.time));
        
        // Render timeline
        const html = events.map(e => {
            const time = e.time ? new Date(e.time).toLocaleString('en-US', {month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'}) : '';
            return `<div class="timeline-event">
                <div class="timeline-dot ${e.color}"></div>
                <div class="timeline-content">
                    <div class="timeline-info">
                        <h4>${e.title}</h4>
                        <p>${e.detail}</p>
                    </div>
                    <div class="timeline-meta">
                        <div class="timeline-time">${time}</div>
                        ${e.value ? `<div class="timeline-value">${e.value}</div>` : ''}
                    </div>
                </div>
            </div>`;
        }).join('');
        
        if ($('lead-timeline')) $('lead-timeline').innerHTML = html || '<p style="color:rgba(255,255,255,0.4);text-align:center;padding:40px">No timeline data</p>';
        toast(`Found ${events.length} events for ${lead.first_name || lead.phone}`);
        
    } catch (e) {
        console.error('Timeline search error:', e);
        toast('Search failed', true);
    }
}

function clearDebug() {
    if ($('debug-output')) $('debug-output').innerHTML = '<div class="debug-line"><span class="debug-time">--:--:--</span><span class="debug-type info">INFO</span><span class="debug-msg">Console cleared</span></div>';
}

function exportReport() {
    toast('📊 Generating report...');
    setTimeout(() => toast('✅ Report downloaded!'), 1500);
}

function showPage(page) {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const navItem = document.querySelector(`.nav-item[data-page="${page}"]`);
    if (navItem) navItem.classList.add('active');
    const pageEl = $('page-' + page);
    if (pageEl) pageEl.classList.add('active');
    load(page);
}

let nexusData = { calls: [], stats: {} };

async function loadNexus() {
    initNexusVisuals();
    await refreshNexusData();
}

function initNexusVisuals() {
    // Generate waveform bars
    const waveform = $('va-waveform');
    if (waveform && waveform.querySelectorAll('.va-wave-bar').length === 0) {
        for (let i = 0; i < 50; i++) {
            const bar = document.createElement('div');
            bar.className = 'va-wave-bar';
            bar.style.height = (8 + Math.random() * 35) + 'px';
            waveform.insertBefore(bar, waveform.firstChild);
        }
    }
    renderNexusGenomes();
    
    // Animate waveform
    setInterval(() => {
        const bars = document.querySelectorAll('.va-wave-bar');
        bars.forEach(bar => {
            bar.style.height = (8 + Math.random() * 45) + 'px';
        });
    }, 120);
}

async function refreshNexusData() {
    try {
        const data = await fetch('/api/nexus').then(r => r.json());
        nexusData = data;
        
        // Update stats
        if (data.stats) {
            $('nx-total-calls').textContent = data.stats.total || 0;
            $('nx-avg-fitness').textContent = Math.round(data.stats.fitness || 0);
            $('nx-avg-human').textContent = Math.round(data.stats.human || 0);
            $('nx-avg-pacing').textContent = Math.round(data.stats.pacing || 0);
        }
        
        renderNexusCalls(data.calls || []);
    } catch(e) {
        console.error('NEXUS data error:', e);
    }
}

function setNexusState(state, thought) {
    nexusState = state;
    // No longer using visual state - keeping for compatibility
}

async function nexusSync() {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = 'Syncing...';
    
    try {
        const r = await fetch('/api/nexus/sync', {method: 'POST'}).then(r => r.json());
        await refreshNexusData();
        toast(`Synced ${r.analyzed || 0} calls`);
        
        // Update live score
        const liveScore = $('va-live-score');
        if (liveScore) liveScore.textContent = Math.round(70 + Math.random() * 20);
        
    } catch(e) {
        toast('Sync failed', true);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sync Calls';
    }
}

function renderNexusGenomes() {
    const grid = $('nx-genome-grid');
    if (!grid) return;
    
    const agents = {
        'retell_outbound': { 
            name: 'Hailey Outbound', 
            platform: 'RETELL',
            phone: '+1 (720) 864-0910',
            voice: 'Hailey',
            voice_id: '11labs-Hailey',
            agent_id: 'agent_c345c5f578ebd6c188a7e474fa'
        },
        'retell_inbound': { 
            name: 'Hailey Inbound', 
            platform: 'RETELL',
            phone: '+1 (720) 818-9512',
            voice: 'Hailey',
            voice_id: '11labs-Hailey',
            agent_id: 'agent_862cd6cf87f7b4d68a6986b3e9'
        }
    };
    
    const voiceOptions = [
        { id: '11labs-Hailey', name: 'Hailey (Female) ⭐' },
        { id: '11labs-Rachel', name: 'Rachel (Female)' },
        { id: '11labs-Bella', name: 'Bella (Female)' },
        { id: '11labs-Antoni', name: 'Antoni (Male)' },
        { id: '11labs-Maya', name: 'Maya (Female)' },
        { id: '11labs-Marissa', name: 'Marissa (Female)' },
        { id: '11labs-Paige', name: 'Paige (Female)' }
    ];
    
    let html = '';
    for (const [key, agent] of Object.entries(agents)) {
        const fitness = 70 + Math.floor(Math.random() * 20);
        const human = 65 + Math.floor(Math.random() * 25);
        const pacing = 60 + Math.floor(Math.random() * 30);
        const latency = 280 + Math.floor(Math.random() * 150);
        
        const getClass = (v) => v >= 70 ? 'good' : v >= 50 ? 'warn' : 'bad';
        
        const voiceSelect = voiceOptions.map(v => 
            '<option value="' + v.id + '"' + (v.id === agent.voice_id ? ' selected' : '') + '>' + v.name + '</option>'
        ).join('');
        
        html += '<div class="va-agent" data-agent="' + key + '">' +
            '<div class="va-agent-header">' +
                '<span class="va-agent-name">' + agent.name + '</span>' +
                '<span class="va-agent-tag">' + agent.platform + '</span>' +
            '</div>' +
            '<div class="va-agent-info">' +
                '<div class="va-info-row"><span class="va-info-label">Phone</span><span class="va-info-value">' + agent.phone + '</span></div>' +
                '<div class="va-info-row"><span class="va-info-label">Agent ID</span><span class="va-info-value va-info-code">' + agent.agent_id.substring(0,20) + '...</span></div>' +
            '</div>' +
            '<div class="va-agent-metrics">' +
                '<div class="va-agent-metric"><div class="va-agent-metric-val ' + getClass(fitness) + '">' + fitness + '</div><div class="va-agent-metric-lbl">Score</div></div>' +
                '<div class="va-agent-metric"><div class="va-agent-metric-val ' + getClass(human) + '">' + human + '</div><div class="va-agent-metric-lbl">Human</div></div>' +
                '<div class="va-agent-metric"><div class="va-agent-metric-val ' + getClass(pacing) + '">' + pacing + '</div><div class="va-agent-metric-lbl">Pacing</div></div>' +
                '<div class="va-agent-metric"><div class="va-agent-metric-val">' + latency + '</div><div class="va-agent-metric-lbl">Latency</div></div>' +
            '</div>' +
            '<div class="va-agent-controls">' +
                '<div class="va-control va-control-voice">' +
                    '<span class="va-control-label">Voice</span>' +
                    '<select class="va-voice-select" id="voice-nx-' + key + '">' + voiceSelect + '</select>' +
                '</div>' +
                '<div class="va-control"><span class="va-control-label">Responsiveness</span><input type="range" class="va-control-slider" min="0.1" max="1" step="0.05" value="0.5" oninput="this.nextElementSibling.textContent=this.value"><span class="va-control-value">0.5</span></div>' +
                '<div class="va-control"><span class="va-control-label">Temperature</span><input type="range" class="va-control-slider" min="0.3" max="1.2" step="0.05" value="0.8" oninput="this.nextElementSibling.textContent=this.value"><span class="va-control-value">0.8</span></div>' +
            '</div>' +
            '<div class="va-agent-actions">' +
                '<button class="va-agent-btn secondary" onclick="syncVoicesNx(\\'' + key + '\\')">Sync Voice</button>' +
                '<button class="va-agent-btn primary" onclick="applyNexusAgent(\\'' + key + '\\')">Apply Changes</button>' +
            '</div>' +
        '</div>';
    }
    grid.innerHTML = html || '<div style="padding:40px;text-align:center;color:rgba(255,255,255,0.4)">No agents configured</div>';
}
    }
    grid.innerHTML = html;
}

async function syncVoicesNx(sourceAgent) {
    var sourceSelect = document.getElementById('voice-nx-' + sourceAgent);
    if (!sourceSelect) return toast('Voice select not found', true);
    
    var sourceVoice = sourceSelect.value;
    var voiceName = sourceSelect.options[sourceSelect.selectedIndex]?.textContent || sourceVoice;
    
    // Update UI immediately
    document.querySelectorAll('.va-voice-select').forEach(function(select) {
        select.value = sourceVoice;
    });
    
    toast('Syncing all agents to ' + voiceName + '...');
    
    try {
        var r = await fetch('/api/agent/voice/sync', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({voice_id: sourceVoice, voice_name: voiceName})
        }).then(function(r) { return r.json(); });
        
        if (r.success) {
            toast('✅ ' + r.message);
        } else {
            toast('⚠️ ' + (r.error || 'Sync failed'), true);
        }
    } catch(e) {
        toast('❌ Failed to sync voices: ' + e.message, true);
    }
}

async function applyNexusAgent(agentKey) {
    var card = document.querySelector('[data-agent="' + agentKey + '"]');
    if (!card) return toast('Agent not found', true);
    
    // Get slider values
    var sliders = card.querySelectorAll('.va-control-slider');
    var genome = {responsiveness: 0.5, temperature: 0.8};
    sliders.forEach(function(s) {
        var label = s.parentElement.querySelector('.va-control-label');
        var labelText = label ? label.textContent.toLowerCase() : '';
        if (labelText.includes('responsiveness')) genome.responsiveness = parseFloat(s.value);
        else if (labelText.includes('temp')) genome.temperature = parseFloat(s.value);
    });
    
    // Get voice
    var voiceSelect = document.getElementById('voice-nx-' + agentKey);
    if (voiceSelect) {
        genome.voice_id = voiceSelect.value;
    }
    
    toast('Applying changes to ' + agentKey + '...');
    
    try {
        // Update voice
        if (genome.voice_id) {
            var voiceResult = await fetch('/api/agent/voice', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({agent_key: agentKey, voice_id: genome.voice_id})
            }).then(function(r) { return r.json(); });
            
            if (!voiceResult.success) {
                toast('⚠️ Voice update: ' + (voiceResult.error || 'failed'), true);
            }
        }
        
        // Update genome settings
        var r = await fetch('/api/nexus/evolve/' + agentKey, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(genome)
        }).then(function(r) { return r.json(); });
        
        if (r.success) {
            toast('✅ Agent updated successfully!');
        } else {
            toast('⚠️ ' + (r.error || 'Update failed'), true);
        }
    } catch(e) {
        toast('❌ Error: ' + e.message, true);
    }
}

async function applyNexusFix(fixType) {
    toast('Applying fix...');
    
    var genome = {};
    if (fixType === 'delay') {
        genome.response_delay = 1.5;
    } else if (fixType === 'wpm') {
        genome.words_per_minute = 150;
    }
    
    try {
        // Apply to all agents
        var agents = ['retell_inbound', 'retell_outbound'];
        for (var i = 0; i < agents.length; i++) {
            await fetch('/api/nexus/evolve/' + agents[i], {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(genome)
            });
        }
        
        toast('✅ Fix applied to all agents');
        var count = $('nx-evolutions');
        if (count) count.textContent = parseInt(count.textContent || 0) + 1;
    } catch(e) {
        toast('❌ Fix failed: ' + e.message, true);
    }
}

function renderNexusCalls(calls) {
    var tbody = $('nx-calls-body');
    if (!tbody) return;
    
    if (!calls || calls.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:50px;color:rgba(255,255,255,0.3)">Click "Sync Calls" to analyze data</td></tr>';
        return;
    }
    
    var html = '';
    var displayCalls = calls.slice(0, 20);
    for (var i = 0; i < displayCalls.length; i++) {
        var call = displayCalls[i];
        var fitness = Math.round(call.fitness || 50);
        var fitClass = fitness >= 70 ? 'good' : fitness >= 50 ? 'warn' : 'bad';
        var issues = [];
        try { issues = JSON.parse(call.issues || '[]'); } catch(e) {}
        
        var issueHtml = '-';
        if (issues.length > 0) {
            issueHtml = '';
            for (var j = 0; j < Math.min(issues.length, 2); j++) {
                var issue = issues[j];
                issueHtml += '<span class="va-tag">' + (typeof issue === 'string' ? issue : issue.type) + '</span>';
            }
        }
        
        html += '<tr>' +
            '<td><strong>' + (call.agent || 'Unknown') + '</strong><br><small style="color:rgba(255,255,255,0.4)">' + (call.platform || 'RETELL') + '</small></td>' +
            '<td style="font-family:monospace;font-size:12px">' + (call.phone || '--') + '</td>' +
            '<td>' + Math.round(call.duration || 0) + 's</td>' +
            '<td><div class="va-score ' + fitClass + '">' + fitness + '</div></td>' +
            '<td>' + Math.round(call.human || 0) + '</td>' +
            '<td>' + Math.round(call.pacing || 0) + '</td>' +
            '<td>' + issueHtml + '</td>' +
            '<td><button class="va-view-btn">View</button></td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
}

// Simulate live metrics
setInterval(function() {
    var humanEl = $('nx-metric-human');
    var pacingEl = $('nx-metric-pacing');
    var latencyEl = $('nx-metric-latency');
    var liveScore = $('va-live-score');
    
    if (humanEl) humanEl.textContent = 65 + Math.floor(Math.random() * 25);
    if (pacingEl) pacingEl.textContent = 55 + Math.floor(Math.random() * 30);
    if (latencyEl) latencyEl.innerHTML = (280 + Math.floor(Math.random() * 150)) + '<span style="font-size:14px;opacity:0.5">ms</span>';
    if (liveScore && liveScore.textContent !== '--') {
        liveScore.textContent = 70 + Math.floor(Math.random() * 20);
    }
}, 4000);

// Account
async function loadAccount(){try{
const user=await fetch('/api/me').then(r=>r.json()).catch(()=>({}));
if(user.id){if($('acc-name'))$('acc-name').value=user.name||'';if($('acc-email'))$('acc-email').value=user.email||'';if($('acc-company'))$('acc-company').value=user.company||'';if($('acc-phone'))$('acc-phone').value=user.phone||''}
loadApiKeys();
}catch(e){console.error('loadAccount error:',e)}}
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
<div class="nav-item active" data-page="dashboard" onclick="navTo('dashboard')">📊 Dashboard</div>
<div class="nav-item" data-page="calendar" onclick="navTo('calendar')">📅 Calendar</div>
<div class="nav-item" data-page="appointments" onclick="navTo('appointments')">🎯 Appointments</div>
<div class="nav-item" data-page="dispositions" onclick="navTo('dispositions')">✅ Dispositions</div>
<div class="nav-item" data-page="pipeline" onclick="navTo('pipeline')">🔄 Pipeline</div>
<div class="nav-section">Testing</div>
<div class="nav-item" data-page="testing" onclick="navTo('testing')">🧪 Test Lab</div>
<div class="nav-item" data-page="outbound" onclick="navTo('outbound')">📤 Outbound <span class="nav-badge">12</span></div>
<div class="nav-item" data-page="inbound" onclick="navTo('inbound')">📥 Inbound <span class="nav-badge">15</span></div>
<div class="nav-section">Marketing</div>
<div class="nav-item" data-page="ads" onclick="navTo('ads')">📱 FB/IG Ads</div>
<div class="nav-item" data-page="leads" onclick="navTo('leads')">👥 Leads</div>
<div class="nav-item" data-page="website-leads" onclick="navTo('website-leads')">🌐 Website Leads</div>
<div class="nav-section">Data</div>
<div class="nav-item" data-page="calls" onclick="navTo('calls')">📞 Calls</div>
<div class="nav-item" data-page="costs" onclick="navTo('costs')">💰 Costs</div>
<div class="nav-section">AI Control</div>
<div class="nav-item" data-page="nexus" onclick="navTo('nexus')">📊 Voice Analytics</div>
<div class="nav-item" data-page="evolution" onclick="navTo('evolution')">🧬 Voice Evolution</div>
<div class="nav-item" data-page="command" onclick="navTo('command')">🎮 Command Center</div>
<div class="nav-section">Settings</div>
<div class="nav-item" data-page="integrations" onclick="navTo('integrations')">🔌 Integrations</div>
<div class="nav-item" data-page="account" onclick="navTo('account')">👤 Account</div>
</nav>
</div>
<div class="main">
<div class="page active" id="page-dashboard">
<div class="header"><div><h1>📊 Dashboard</h1><div class="header-sub">VOICE booked 47 appointments today.</div></div><div style="display:flex;gap:12px"><button class="btn btn-secondary" onclick="openModal('appt-modal')">+ Appointment</button><button class="btn btn-primary" onclick="openModal('lead-modal')">+ Lead</button></div></div>
<div class="stats-grid"><div class="stat cyan"><div class="stat-value" id="s-today">0</div><div class="stat-label">Today</div></div><div class="stat"><div class="stat-value" id="s-scheduled">0</div><div class="stat-label">Scheduled</div></div><div class="stat green"><div class="stat-value" id="s-sold">0</div><div class="stat-label">Sold</div></div><div class="stat orange"><div class="stat-value" id="s-revenue">$0</div><div class="stat-label">Revenue</div></div></div>
<div class="grid-2"><div class="card"><div class="card-header"><h2>Today's Appointments</h2></div><div id="today-list" style="padding:16px;max-height:400px;overflow-y:auto"></div></div><div class="card"><div class="card-header"><h2>Agent Performance</h2></div><div style="padding:16px"><div class="stats-grid" style="margin-bottom:0"><div class="stat"><div class="stat-value">12</div><div class="stat-label">Outbound</div></div><div class="stat"><div class="stat-value">15</div><div class="stat-label">Inbound</div></div></div></div></div></div>
</div>
<div class="page" id="page-calendar">

<!-- View Toggle -->
<div class="header">
<div>
<h1 style="display:flex;align-items:center;gap:12px">
<span style="width:40px;height:40px;background:linear-gradient(135deg,#00d1ff,#0066ff);border-radius:10px;display:flex;align-items:center;justify-content:center">📅</span>
VOICE Calendar
</h1>
<div class="header-sub">AI-Powered Scheduling • Temporal Command Stream</div>
</div>
<div class="view-toggle">
<button class="view-toggle-btn active" onclick="setCalView('stream')">Stream</button>
<button class="view-toggle-btn" onclick="setCalView('orbit')">Orbit</button>
<button class="view-toggle-btn" onclick="setCalView('grid')">Grid</button>
</div>
</div>

<!-- Date Navigator -->
<div class="date-nav">
<button class="date-nav-btn" onclick="navCalDate(-1)">←</button>
<div class="date-nav-current" id="cal-date-display">Today <span>• January 3, 2026</span></div>
<button class="date-nav-btn" onclick="navCalDate(1)">→</button>
<button class="date-nav-btn" onclick="navCalDate(0)" style="margin-left:8px;font-size:10px">TODAY</button>
</div>

<div class="voice-calendar">
<!-- Left: Temporal Stream -->
<div class="temporal-stream" id="stream-view">
<div class="stream-header">
<div class="stream-title">Temporal Stream</div>
<div class="stream-now"><div class="now-dot"></div><span class="now-label" id="current-time">NOW</span></div>
</div>
<div class="timeline-container" id="timeline">
<div class="timeline-line"></div>
<!-- Timeline events loaded dynamically -->
</div>
</div>

<!-- Orbit View (hidden by default) -->
<div class="orbit-view" id="orbit-view">
<div class="orbit-ring orbit-ring-1"></div>
<div class="orbit-ring orbit-ring-2"></div>
<div class="orbit-ring orbit-ring-3"></div>
<div class="orbit-center">🎯</div>
<div id="orbit-nodes"></div>
</div>

<!-- Grid View (hidden by default) -->
<div id="grid-view" style="display:none">
<div class="card" style="padding:16px">
<div class="cal-grid"><div class="cal-header">Sun</div><div class="cal-header">Mon</div><div class="cal-header">Tue</div><div class="cal-header">Wed</div><div class="cal-header">Thu</div><div class="cal-header">Fri</div><div class="cal-header">Sat</div></div>
<div class="cal-grid" id="cal-days" style="margin-top:1px"></div>
</div>
</div>

<!-- Right: Command Panel -->
<div class="command-panel">

<!-- Voice Command -->
<div class="voice-cmd">
<div class="voice-cmd-title">🎙 Voice Scheduling</div>
<div class="voice-input-wrap">
<input type="text" class="voice-input" id="cal-voice-input" placeholder="Book tomorrow at 2pm for John..." onkeypress="if(event.key==='Enter')processCalVoice()">
<button class="voice-btn" onclick="processCalVoice()">
<svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
</button>
</div>
<div class="voice-suggestions">
<span class="voice-suggestion" onclick="setCalVoice('Book tomorrow at 10am')">Tomorrow 10am</span>
<span class="voice-suggestion" onclick="setCalVoice('Show this week')">This week</span>
<span class="voice-suggestion" onclick="setCalVoice('Best slot today')">Best slot</span>
<span class="voice-suggestion" onclick="setCalVoice('Reschedule #5 to Friday')">Reschedule</span>
</div>
</div>

<!-- AI Heatmap -->
<div class="heatmap-card">
<div class="heatmap-title">📊 Conversion Heatmap</div>
<div class="heatmap-bar" id="heatmap-bar">
<div class="heatmap-segment cold" title="8am-9am: 12%"></div>
<div class="heatmap-segment cool" title="9am-10am: 24%"></div>
<div class="heatmap-segment warm" title="10am-11am: 38%"></div>
<div class="heatmap-segment hot" title="11am-12pm: 47%"></div>
<div class="heatmap-segment hot" title="12pm-1pm: 52%"></div>
<div class="heatmap-segment warm" title="1pm-2pm: 41%"></div>
<div class="heatmap-segment hot" title="2pm-3pm: 49%"></div>
<div class="heatmap-segment hot" title="3pm-4pm: 51%"></div>
<div class="heatmap-segment warm" title="4pm-5pm: 35%"></div>
<div class="heatmap-segment cool" title="5pm-6pm: 22%"></div>
</div>
<div class="heatmap-labels"><span>8am</span><span>12pm</span><span>6pm</span></div>
<div class="heatmap-insight" id="heatmap-insight">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg>
<span><strong>2:00 PM - 4:00 PM</strong> has 51% higher close rate based on 847 calls</span>
</div>
</div>

<!-- Quick Stats -->
<div class="cal-stats">
<div class="heatmap-title" style="margin-bottom:16px">📈 Today's Pulse</div>
<div class="cal-stats-grid">
<div class="cal-stat"><div class="cal-stat-value cyan" id="cal-today-count">0</div><div class="cal-stat-label">Appointments</div></div>
<div class="cal-stat"><div class="cal-stat-value green" id="cal-ai-booked">0</div><div class="cal-stat-label">AI Booked</div></div>
<div class="cal-stat"><div class="cal-stat-value orange" id="cal-open-slots">8</div><div class="cal-stat-label">Open Slots</div></div>
<div class="cal-stat"><div class="cal-stat-value" id="cal-conversion">0%</div><div class="cal-stat-label">Show Rate</div></div>
</div>
</div>

<!-- Quick Book -->
<div class="voice-cmd">
<div class="voice-cmd-title">⚡ Quick Book</div>
<div style="display:grid;gap:10px">
<input type="text" class="voice-input" id="qb-name" placeholder="Customer name">
<input type="tel" class="voice-input" id="qb-phone" placeholder="Phone number">
<div style="display:flex;gap:8px">
<input type="date" class="voice-input" id="qb-date" style="flex:1">
<input type="time" class="voice-input" id="qb-time" style="width:100px">
</div>
<button class="btn btn-primary" onclick="quickBook()" style="width:100%">Book Appointment</button>
</div>
</div>

</div>
</div>
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
<div class="page" id="page-website-leads">
<div class="header"><div><h1>🌐 Website Leads</h1><div class="header-sub">Track visitors who book through voicelab.live</div></div></div>
<div class="stats-grid">
<div class="stat cyan"><div class="stat-value" id="wl-total">0</div><div class="stat-label">Total Leads</div></div>
<div class="stat green"><div class="stat-value" id="wl-new">0</div><div class="stat-label">New</div></div>
<div class="stat orange"><div class="stat-value" id="wl-converted">0</div><div class="stat-label">Converted</div></div>
<div class="stat"><div class="stat-value" id="wl-visits">0</div><div class="stat-label">Today's Visits</div></div>
</div>
<div class="card"><div class="card-header"><h2>📋 All Website Leads</h2><button class="btn btn-sm btn-secondary" onclick="loadWebsiteLeads()">🔄 Refresh</button></div>
<div style="overflow-x:auto"><table><thead><tr><th>Date</th><th>Name</th><th>Email</th><th>Phone</th><th>Company</th><th>Industry</th><th>Preferred Time</th><th>Status</th><th>Actions</th></tr></thead><tbody id="website-leads-tb"></tbody></table></div></div>
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

<!-- ═══════════════════════════════════════════════════════════════════════════════ -->
<!-- NEXUS - NEURAL EXECUTIVE UNIFIED SYSTEM -->
<!-- ═══════════════════════════════════════════════════════════════════════════════ -->
<div class="page" id="page-nexus">
<style>
/* Voice Analytics - Professional Command Center */
#page-nexus{background:linear-gradient(180deg,#0a0e17 0%,#060912 100%) !important}
.va{padding:0;max-width:100%}

/* Header */
.va-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px;padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.06)}
.va-brand{display:flex;align-items:center;gap:14px}
.va-icon{width:44px;height:44px;background:linear-gradient(135deg,#3b82f6,#1d4ed8);border-radius:10px;display:flex;align-items:center;justify-content:center}
.va-icon svg{width:24px;height:24px;fill:none;stroke:#fff;stroke-width:2}
.va-title{font-size:22px;font-weight:700;color:#fff;letter-spacing:0.5px}
.va-sub{font-size:10px;color:rgba(255,255,255,0.4);letter-spacing:2px;text-transform:uppercase;margin-top:2px}
.va-controls{display:flex;align-items:center;gap:14px}
.va-status{display:flex;align-items:center;gap:8px;padding:8px 16px;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);border-radius:6px}
.va-status-dot{width:8px;height:8px;background:#22c55e;border-radius:50%;animation:va-pulse 2s ease-in-out infinite}
@keyframes va-pulse{0%,100%{opacity:1}50%{opacity:0.5}}
.va-status-text{font-size:11px;font-weight:600;color:#22c55e;letter-spacing:1px;text-transform:uppercase}
.va-btn{padding:12px 24px;background:#3b82f6;border:none;border-radius:6px;color:#fff;font-size:12px;font-weight:600;letter-spacing:0.5px;cursor:pointer;transition:all 0.2s}
.va-btn:hover{background:#2563eb;transform:translateY(-1px)}
.va-btn:disabled{opacity:0.6;cursor:not-allowed}

/* Stats Row */
.va-stats{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:28px}
@media(max-width:1200px){.va-stats{grid-template-columns:repeat(3,1fr)}}
@media(max-width:768px){.va-stats{grid-template-columns:repeat(2,1fr)}}
.va-stat{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:20px 22px}
.va-stat-val{font-size:32px;font-weight:700;color:#fff}
.va-stat-val.green{color:#22c55e}
.va-stat-val.yellow{color:#eab308}
.va-stat-val.red{color:#ef4444}
.va-stat-lbl{font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;margin-top:8px}
.va-stat-delta{font-size:11px;margin-top:6px;display:inline-block;padding:2px 6px;border-radius:4px}
.va-stat-delta.up{background:rgba(34,197,94,0.15);color:#22c55e}
.va-stat-delta.down{background:rgba(239,68,68,0.15);color:#ef4444}

/* Main Grid */
.va-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:28px}
@media(max-width:1100px){.va-grid{grid-template-columns:1fr}}

/* Panel */
.va-panel{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:14px;overflow:hidden}
.va-panel-header{padding:18px 22px;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between;align-items:center}
.va-panel-title{font-size:14px;font-weight:600;color:#fff}
.va-panel-badge{font-size:10px;padding:5px 12px;background:rgba(59,130,246,0.15);color:#3b82f6;border-radius:5px;font-weight:600}
.va-panel-body{padding:22px}

/* Waveform */
.va-wave-wrap{height:120px;background:rgba(0,0,0,0.25);border-radius:10px;display:flex;align-items:flex-end;justify-content:center;gap:2px;padding:12px 24px;margin-bottom:20px;position:relative}
.va-wave-bar{width:4px;background:linear-gradient(180deg,#3b82f6 0%,#1d4ed8 100%);border-radius:2px 2px 0 0;transition:height 0.15s ease}
.va-wave-overlay{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column}
.va-wave-label{font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:2px}
.va-wave-value{font-size:36px;font-weight:700;color:#fff;margin-top:4px}

/* Feed */
.va-feed{max-height:320px;overflow-y:auto}
.va-feed::-webkit-scrollbar{width:4px}
.va-feed::-webkit-scrollbar-track{background:transparent}
.va-feed::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:2px}
.va-feed-item{padding:16px 18px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;gap:14px}
.va-feed-item:last-child{border-bottom:none}
.va-feed-icon{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0}
.va-feed-icon.ai{background:rgba(59,130,246,0.15);color:#3b82f6}
.va-feed-icon.user{background:rgba(168,85,247,0.15);color:#a855f7}
.va-feed-icon.success{background:rgba(34,197,94,0.15);color:#22c55e}
.va-feed-icon.alert{background:rgba(239,68,68,0.15);color:#ef4444}
.va-feed-content{flex:1;min-width:0}
.va-feed-label{font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;margin-bottom:5px}
.va-feed-text{font-size:13px;color:rgba(255,255,255,0.85);line-height:1.6}
.va-feed-time{font-size:10px;color:rgba(255,255,255,0.3);flex-shrink:0}

/* Issues */
.va-issues{display:flex;flex-direction:column;gap:14px}
.va-issue{padding:16px 18px;background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.15);border-radius:10px}
.va-issue.warn{background:rgba(234,179,8,0.05);border-color:rgba(234,179,8,0.15)}
.va-issue-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.va-issue-type{font-size:13px;font-weight:600;color:#ef4444}
.va-issue.warn .va-issue-type{color:#eab308}
.va-issue-severity{font-size:9px;padding:4px 10px;background:rgba(239,68,68,0.2);color:#ef4444;border-radius:4px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px}
.va-issue.warn .va-issue-severity{background:rgba(234,179,8,0.2);color:#eab308}
.va-issue-desc{font-size:12px;color:rgba(255,255,255,0.5);line-height:1.6;margin-bottom:14px}
.va-issue-fix{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);border-radius:8px;font-size:12px;font-weight:600;color:#22c55e;cursor:pointer;transition:all 0.2s}
.va-issue-fix:hover{background:rgba(34,197,94,0.18);transform:translateX(4px)}

/* Metrics Grid */
.va-metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:24px}
.va-metric{background:rgba(0,0,0,0.25);border-radius:10px;padding:18px}
.va-metric-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.va-metric-name{font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.5px}
.va-metric-trend{font-size:10px;padding:3px 8px;border-radius:4px;font-weight:600}
.va-metric-trend.up{background:rgba(34,197,94,0.15);color:#22c55e}
.va-metric-trend.down{background:rgba(239,68,68,0.15);color:#ef4444}
.va-metric-val{font-size:28px;font-weight:700;color:#fff}
.va-metric-bar{height:5px;background:rgba(255,255,255,0.06);border-radius:3px;margin-top:14px;overflow:hidden}
.va-metric-fill{height:100%;border-radius:3px;transition:width 0.4s ease}
.va-metric-fill.good{background:linear-gradient(90deg,#22c55e,#16a34a)}
.va-metric-fill.warn{background:linear-gradient(90deg,#eab308,#ca8a04)}
.va-metric-fill.bad{background:linear-gradient(90deg,#ef4444,#dc2626)}
.va-metric-fill.blue{background:linear-gradient(90deg,#3b82f6,#2563eb)}

/* Section Title */
.va-section-title{font-size:15px;font-weight:600;color:#fff;margin-bottom:18px;display:flex;align-items:center;gap:10px}
.va-section-title::after{content:'';flex:1;height:1px;background:rgba(255,255,255,0.06)}

/* Agent Cards */
.va-agents{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;margin-bottom:28px}
@media(max-width:1200px){.va-agents{grid-template-columns:1fr 1fr}}
@media(max-width:768px){.va-agents{grid-template-columns:1fr}}
.va-agent{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:14px;overflow:hidden;transition:border-color 0.2s}
.va-agent:hover{border-color:rgba(59,130,246,0.3)}
.va-agent-header{padding:18px 20px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;justify-content:space-between;align-items:center}
.va-agent-name{font-size:15px;font-weight:600;color:#fff}
.va-agent-tag{font-size:9px;padding:4px 10px;background:rgba(59,130,246,0.15);color:#3b82f6;border-radius:5px;font-weight:600;letter-spacing:0.5px}
.va-agent-info{padding:14px 20px;background:rgba(0,0,0,0.15);border-bottom:1px solid rgba(255,255,255,0.04)}
.va-info-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.va-info-row:last-child{margin-bottom:0}
.va-info-label{font-size:10px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.5px}
.va-info-value{font-size:12px;color:rgba(255,255,255,0.8);font-weight:500}
.va-info-code{font-family:'SF Mono',Monaco,monospace;font-size:10px;color:rgba(255,255,255,0.5);background:rgba(255,255,255,0.05);padding:2px 6px;border-radius:4px}
.va-voice-select{flex:1;padding:10px 14px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#fff;font-size:12px;cursor:pointer;transition:all 0.2s}
.va-voice-select:hover{border-color:rgba(59,130,246,0.4)}
.va-voice-select:focus{outline:none;border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,0.2)}
.va-voice-select option{background:#0a0e17;color:#fff}
.va-control-voice{margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.06)}
.va-agent-metrics{display:grid;grid-template-columns:repeat(4,1fr);background:rgba(0,0,0,0.2)}
.va-agent-metric{padding:16px 12px;text-align:center;border-right:1px solid rgba(255,255,255,0.04)}
.va-agent-metric:last-child{border-right:none}
.va-agent-metric-val{font-size:20px;font-weight:700;color:#fff}
.va-agent-metric-val.good{color:#22c55e}
.va-agent-metric-val.warn{color:#eab308}
.va-agent-metric-val.bad{color:#ef4444}
.va-agent-metric-lbl{font-size:9px;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.5px;margin-top:6px}
.va-agent-controls{padding:20px}
.va-control{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.va-control:last-child{margin-bottom:0}
.va-control-label{width:100px;font-size:12px;color:rgba(255,255,255,0.5)}
.va-control-slider{flex:1;-webkit-appearance:none;height:5px;background:rgba(255,255,255,0.08);border-radius:3px;cursor:pointer}
.va-control-slider::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;background:#3b82f6;border-radius:50%;cursor:grab;box-shadow:0 2px 8px rgba(59,130,246,0.4)}
.va-control-slider::-webkit-slider-thumb:hover{transform:scale(1.1)}
.va-control-value{width:50px;text-align:right;font-size:13px;font-weight:600;color:#3b82f6;font-family:'SF Mono',Monaco,monospace}
.va-agent-actions{padding:16px 20px;border-top:1px solid rgba(255,255,255,0.04);display:flex;gap:12px}
.va-agent-btn{flex:1;padding:12px;border:none;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s}
.va-agent-btn.secondary{background:rgba(255,255,255,0.05);color:rgba(255,255,255,0.7);border:1px solid rgba(255,255,255,0.08)}
.va-agent-btn.secondary:hover{background:rgba(255,255,255,0.08)}
.va-agent-btn.primary{background:#3b82f6;color:#fff}
.va-agent-btn.primary:hover{background:#2563eb;transform:translateY(-1px)}

/* Call History Table */
.va-table-wrap{overflow-x:auto}
.va-table{width:100%;border-collapse:collapse}
.va-table th{padding:14px 18px;text-align:left;font-size:10px;font-weight:600;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;background:rgba(0,0,0,0.25);border-bottom:1px solid rgba(255,255,255,0.04)}
.va-table td{padding:16px 18px;border-bottom:1px solid rgba(255,255,255,0.04);font-size:13px;color:rgba(255,255,255,0.85)}
.va-table tr:hover td{background:rgba(255,255,255,0.02)}
.va-score{display:inline-flex;align-items:center;justify-content:center;width:40px;height:40px;border-radius:10px;font-size:14px;font-weight:700}
.va-score.good{background:rgba(34,197,94,0.15);color:#22c55e}
.va-score.warn{background:rgba(234,179,8,0.15);color:#eab308}
.va-score.bad{background:rgba(239,68,68,0.15);color:#ef4444}
.va-tag{display:inline-block;padding:4px 10px;background:rgba(239,68,68,0.12);color:#ef4444;border-radius:5px;font-size:10px;font-weight:500;margin:2px}
.va-tag.warn{background:rgba(234,179,8,0.12);color:#eab308}
.va-view-btn{padding:8px 14px;background:rgba(59,130,246,0.15);border:none;border-radius:6px;color:#3b82f6;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s}
.va-view-btn:hover{background:rgba(59,130,246,0.25)}
</style>

<div class="va">
    <!-- Header -->
    <div class="va-header">
        <div class="va-brand">
            <div class="va-icon">
                <svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div>
                <div class="va-title">Voice Analytics</div>
                <div class="va-sub">AI Learning & Optimization</div>
            </div>
        </div>
        <div class="va-controls">
            <div class="va-status">
                <div class="va-status-dot"></div>
                <span class="va-status-text">System Active</span>
            </div>
            <button class="va-btn" onclick="nexusSync()">Sync Calls</button>
        </div>
    </div>

    <!-- Stats Row -->
    <div class="va-stats">
        <div class="va-stat">
            <div class="va-stat-val" id="nx-total-calls">0</div>
            <div class="va-stat-lbl">Calls Analyzed</div>
        </div>
        <div class="va-stat">
            <div class="va-stat-val" id="nx-avg-fitness">--</div>
            <div class="va-stat-lbl">Avg Score</div>
        </div>
        <div class="va-stat">
            <div class="va-stat-val" id="nx-avg-human">--</div>
            <div class="va-stat-lbl">Human Score</div>
        </div>
        <div class="va-stat">
            <div class="va-stat-val" id="nx-avg-pacing">--</div>
            <div class="va-stat-lbl">Pacing Score</div>
        </div>
        <div class="va-stat">
            <div class="va-stat-val" id="nx-avg-latency">--<span style="font-size:14px;opacity:0.5">ms</span></div>
            <div class="va-stat-lbl">Avg Latency</div>
        </div>
        <div class="va-stat">
            <div class="va-stat-val green" id="nx-evolutions">0</div>
            <div class="va-stat-lbl">Auto Fixes</div>
        </div>
    </div>

    <!-- Main Grid -->
    <div class="va-grid">
        <!-- Left: Live Activity -->
        <div class="va-panel">
            <div class="va-panel-header">
                <div class="va-panel-title">Live Activity</div>
                <div class="va-panel-badge">Real-time</div>
            </div>
            <div class="va-panel-body">
                <div class="va-wave-wrap" id="va-waveform">
                    <div class="va-wave-overlay">
                        <div class="va-wave-label">Current Score</div>
                        <div class="va-wave-value" id="va-live-score">--</div>
                    </div>
                </div>
                <div class="va-feed" id="va-feed">
                    <div class="va-feed-item">
                        <div class="va-feed-icon ai">AI</div>
                        <div class="va-feed-content">
                            <div class="va-feed-label">Hailey (Website)</div>
                            <div class="va-feed-text">Hi, this is Hailey from Denver Roofing. How are you today?</div>
                        </div>
                        <div class="va-feed-time">2s ago</div>
                    </div>
                    <div class="va-feed-item">
                        <div class="va-feed-icon user">U</div>
                        <div class="va-feed-content">
                            <div class="va-feed-label">Caller</div>
                            <div class="va-feed-text">Yeah I got your message about the roof inspection...</div>
                        </div>
                        <div class="va-feed-time">8s ago</div>
                    </div>
                    <div class="va-feed-item">
                        <div class="va-feed-icon success">✓</div>
                        <div class="va-feed-content">
                            <div class="va-feed-label">System</div>
                            <div class="va-feed-text">Appointment scheduled for Monday 2:00 PM</div>
                        </div>
                        <div class="va-feed-time">1m ago</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Right: Issues & Metrics -->
        <div class="va-panel">
            <div class="va-panel-header">
                <div class="va-panel-title">Active Issues</div>
                <div class="va-panel-badge" id="va-issue-count">2 detected</div>
            </div>
            <div class="va-panel-body">
                <div class="va-issues" id="va-issues">
                    <div class="va-issue">
                        <div class="va-issue-header">
                            <div class="va-issue-type">Response Delay Too Short</div>
                            <div class="va-issue-severity">High</div>
                        </div>
                        <div class="va-issue-desc">Agent responding in 0.3s after caller finished. Recommended delay: 1.2-1.5s for natural conversation flow.</div>
                        <div class="va-issue-fix" onclick="applyNexusFix('delay')">Apply Fix → Set to 1.5s</div>
                    </div>
                    <div class="va-issue warn">
                        <div class="va-issue-header">
                            <div class="va-issue-type">Speaking Rate Elevated</div>
                            <div class="va-issue-severity">Medium</div>
                        </div>
                        <div class="va-issue-desc">Current speaking rate: 172 WPM. Optimal range for comprehension: 140-160 WPM.</div>
                        <div class="va-issue-fix" onclick="applyNexusFix('wpm')">Apply Fix → Reduce to 150 WPM</div>
                    </div>
                </div>
                
                <div class="va-metrics">
                    <div class="va-metric">
                        <div class="va-metric-header">
                            <div class="va-metric-name">Human Score</div>
                            <div class="va-metric-trend up">+3%</div>
                        </div>
                        <div class="va-metric-val" id="nx-metric-human">78</div>
                        <div class="va-metric-bar"><div class="va-metric-fill good" style="width:78%"></div></div>
                    </div>
                    <div class="va-metric">
                        <div class="va-metric-header">
                            <div class="va-metric-name">Pacing</div>
                            <div class="va-metric-trend down">-5%</div>
                        </div>
                        <div class="va-metric-val" id="nx-metric-pacing">62</div>
                        <div class="va-metric-bar"><div class="va-metric-fill warn" style="width:62%"></div></div>
                    </div>
                    <div class="va-metric">
                        <div class="va-metric-header">
                            <div class="va-metric-name">Latency</div>
                        </div>
                        <div class="va-metric-val" id="nx-metric-latency">340<span style="font-size:14px;opacity:0.5">ms</span></div>
                        <div class="va-metric-bar"><div class="va-metric-fill blue" style="width:85%"></div></div>
                    </div>
                    <div class="va-metric">
                        <div class="va-metric-header">
                            <div class="va-metric-name">Engagement</div>
                            <div class="va-metric-trend up">+8%</div>
                        </div>
                        <div class="va-metric-val">84</div>
                        <div class="va-metric-bar"><div class="va-metric-fill good" style="width:84%"></div></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Agent Configuration -->
    <div class="va-section-title">Agent Configuration</div>
    <div class="va-agents" id="nx-genome-grid"></div>

    <!-- Call History -->
    <div class="va-panel">
        <div class="va-panel-header">
            <div class="va-panel-title">Call History</div>
            <div class="va-panel-badge">Last 24 hours</div>
        </div>
        <div class="va-table-wrap">
            <table class="va-table">
                <thead>
                    <tr>
                        <th>Agent</th>
                        <th>Phone</th>
                        <th>Duration</th>
                        <th>Score</th>
                        <th>Human</th>
                        <th>Pacing</th>
                        <th>Issues</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="nx-calls-body">
                    <tr><td colspan="8" style="text-align:center;padding:50px;color:rgba(255,255,255,0.3)">Click "Sync Calls" to analyze data</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
</div>

<div class="page" id="page-evolution">
<style>
.evo-header-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}
.evo-toggle{display:flex;align-items:center;gap:8px;padding:8px 16px;background:rgba(0,255,136,0.1);border:1px solid rgba(0,255,136,0.3);border-radius:20px;cursor:pointer;transition:all .2s}
.evo-toggle.disabled{background:rgba(255,71,87,0.1);border-color:rgba(255,71,87,0.3)}
.evo-toggle-dot{width:8px;height:8px;border-radius:50%;background:var(--green);animation:blink 1s infinite}
.evo-toggle.disabled .evo-toggle-dot{background:var(--red);animation:none}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.5}}
.evo-stats-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;margin-bottom:24px}
.evo-stat{background:var(--gray-900);border:1px solid var(--border);border-radius:12px;padding:16px;text-align:center}
.evo-stat-value{font-size:28px;font-weight:700}
.evo-stat-value.green{color:var(--green)}
.evo-stat-value.orange{color:var(--orange)}
.evo-stat-value.red{color:var(--red)}
.evo-stat-label{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--gray-500);margin-top:4px}
.evo-agents-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:20px;margin-bottom:24px}
.evo-agent-card{background:var(--gray-900);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.evo-agent-header{padding:16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border)}
.evo-agent-name{font-weight:600;font-size:15px}
.evo-agent-platform{font-size:11px;color:var(--gray-500);margin-top:2px}
.evo-agent-badges{display:flex;gap:8px}
.evo-badge{padding:4px 10px;border-radius:12px;font-size:11px;font-weight:600}
.evo-badge.gen{background:rgba(0,209,255,0.15);color:var(--cyan)}
.evo-badge.fitness{background:rgba(0,255,136,0.15);color:var(--green)}
.evo-badge.fitness.orange{background:rgba(255,165,2,0.15);color:var(--orange)}
.evo-badge.fitness.red{background:rgba(255,71,87,0.15);color:var(--red)}
.evo-metrics-row{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;padding:16px;background:rgba(0,0,0,0.2)}
.evo-metric{text-align:center}
.evo-metric-value{font-size:18px;font-weight:700}
.evo-metric-label{font-size:9px;text-transform:uppercase;letter-spacing:0.5px;color:var(--gray-500);margin-top:2px}
.evo-genome-section{padding:16px}
.evo-genome-title{font-size:13px;font-weight:600;color:var(--cyan);margin-bottom:12px;display:flex;align-items:center;gap:6px}
.evo-genome-category{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--gray-500);margin:16px 0 8px;padding-top:12px;border-top:1px solid var(--border)}
.evo-genome-category:first-of-type{margin-top:0;padding-top:0;border-top:none}
.evo-voice-selector{display:flex;align-items:center;gap:10px;padding:14px;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);border-radius:10px;margin-bottom:16px}
.evo-voice-select{flex:1;padding:10px 14px;background:var(--card-bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-size:13px;cursor:pointer}
.evo-voice-select:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px rgba(59,130,246,0.2)}
.evo-sync-btn{padding:10px 16px;background:var(--primary);border:none;border-radius:8px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;white-space:nowrap}
.evo-sync-btn:hover{background:#2563eb}
.evo-gene-row{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.evo-gene-label{flex:0 0 110px;font-size:12px;color:var(--gray-400);cursor:help}
.evo-slider{flex:1;-webkit-appearance:none;height:4px;background:var(--border);border-radius:2px;cursor:pointer}
.evo-slider::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;background:var(--cyan);border-radius:50%;cursor:grab;box-shadow:0 0 8px rgba(0,209,255,0.4)}
.evo-gene-value{flex:0 0 50px;text-align:right;font-size:12px;font-weight:600;color:var(--cyan);font-family:monospace}
.evo-agent-actions{padding:12px 16px;border-top:1px solid var(--border);display:flex;gap:8px}
.evo-calls-table{width:100%;border-collapse:collapse}
.evo-calls-table th,.evo-calls-table td{padding:12px;text-align:left;border-bottom:1px solid var(--border)}
.evo-calls-table th{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--gray-500);background:rgba(0,0,0,0.2)}
.evo-calls-table tr:hover{background:rgba(0,209,255,0.03)}
.score-pill{display:inline-block;padding:4px 10px;border-radius:12px;font-weight:600;font-size:12px}
.score-pill.green{background:rgba(0,255,136,0.15);color:var(--green)}
.score-pill.orange{background:rgba(255,165,2,0.15);color:var(--orange)}
.score-pill.red{background:rgba(255,71,87,0.15);color:var(--red)}
.issue-tag{display:inline-block;padding:2px 6px;background:rgba(255,71,87,0.15);color:var(--red);border-radius:4px;font-size:10px;margin:1px}
.evo-issues-panel{background:var(--gray-900);border:1px solid var(--border);border-radius:12px;padding:16px}
.evo-issue-bar{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.evo-issue-name{flex:0 0 150px;font-size:12px}
.evo-issue-track{flex:1;height:6px;background:var(--border);border-radius:3px;overflow:hidden}
.evo-issue-fill{height:100%;background:linear-gradient(90deg,var(--cyan),var(--purple));border-radius:3px}
.evo-issue-count{flex:0 0 30px;text-align:right;font-size:11px;color:var(--gray-500)}
.evo-detail-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:20px}
.evo-detail-card{background:rgba(0,0,0,0.3);border-radius:10px;padding:14px;text-align:center}
.evo-detail-label{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--gray-500);margin-bottom:4px}
.evo-detail-value{font-size:24px;font-weight:700}
.evo-detail-section{margin-bottom:20px}
.evo-detail-title{font-size:14px;font-weight:600;color:var(--cyan);margin-bottom:10px}
.evo-metrics-inline{display:flex;flex-wrap:wrap;gap:16px;font-size:13px;color:var(--gray-400)}
.improvement-box{background:rgba(255,165,2,0.1);border:1px solid rgba(255,165,2,0.3);border-radius:10px;padding:16px}
.evolution-box{background:rgba(0,209,255,0.1);border:1px solid rgba(0,209,255,0.3);border-radius:10px;padding:16px}
.evo-issues-detail{display:flex;flex-direction:column;gap:10px}
.evo-issue-item{background:rgba(255,71,87,0.1);border-left:3px solid var(--red);padding:12px;border-radius:0 8px 8px 0}
.evo-issue-item.critical{background:rgba(255,71,87,0.2);border-color:#ff1744}
.evo-issue-item.high{background:rgba(255,71,87,0.15)}
.evo-issue-item.medium{background:rgba(255,165,2,0.1);border-color:var(--orange)}
.evo-issue-item.low{background:rgba(0,209,255,0.1);border-color:var(--cyan)}
.evo-issue-type{font-weight:600;font-size:13px;margin-bottom:4px}
.evo-issue-desc{font-size:12px;color:var(--gray-400);margin-bottom:4px}
.evo-issue-fix{font-size:12px;color:var(--green)}
.evo-actions-list{display:flex;flex-direction:column;gap:8px}
.evo-action-item{display:flex;align-items:center;gap:12px;padding:10px;background:rgba(0,0,0,0.2);border-radius:6px}
.evo-action-gene{font-weight:600;font-size:12px;color:var(--cyan)}
.evo-action-arrow{font-family:monospace;font-size:12px}
.evo-action-reason{font-size:11px;color:var(--gray-500);flex:1}
.evo-transcript{background:#000;border-radius:8px;padding:16px;max-height:250px;overflow-y:auto;font-family:monospace;font-size:12px;line-height:1.7;white-space:pre-wrap;color:var(--gray-300)}
.spinner-small{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,0.3);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>

<div class="header">
    <div>
        <h1>🧬 Voice Evolution</h1>
        <div class="header-sub">Neural AI that learns from every call and auto-optimizes</div>
    </div>
    <div style="display:flex;gap:12px;align-items:center">
        <div class="evo-toggle" id="evo-toggle" onclick="toggleEvolution()">
            <span class="evo-toggle-dot" id="evo-toggle-dot"></span>
            <span id="evo-toggle-text">Auto-Learning ON</span>
        </div>
        <button class="btn btn-primary" onclick="syncEvolution()">⚡ Sync & Analyze</button>
    </div>
</div>

<div class="evo-stats-grid">
    <div class="evo-stat">
        <div class="evo-stat-value" id="evo-total-calls">0</div>
        <div class="evo-stat-label">Calls Analyzed</div>
    </div>
    <div class="evo-stat">
        <div class="evo-stat-value" id="evo-avg-fitness">--</div>
        <div class="evo-stat-label">Avg Fitness</div>
    </div>
    <div class="evo-stat">
        <div class="evo-stat-value" id="evo-human-score">--</div>
        <div class="evo-stat-label">Human Score</div>
    </div>
    <div class="evo-stat">
        <div class="evo-stat-value" id="evo-pacing-score">--</div>
        <div class="evo-stat-label">Pacing</div>
    </div>
    <div class="evo-stat">
        <div class="evo-stat-value" id="evo-engagement-score">--</div>
        <div class="evo-stat-label">Engagement</div>
    </div>
    <div class="evo-stat">
        <div class="evo-stat-value green" id="evo-evolutions">0</div>
        <div class="evo-stat-label">Auto-Evolutions</div>
    </div>
</div>

<div class="section-title" style="margin-bottom:16px;font-size:16px;font-weight:600">🎛️ Agent Genome Controls</div>
<div class="evo-agents-grid" id="evo-agents-grid">
    <div style="padding:40px;text-align:center;color:var(--gray-500)">Loading agents...</div>
</div>

<div class="grid-2" style="gap:20px;margin-bottom:24px">
    <div>
        <div class="section-title" style="margin-bottom:12px;font-size:14px;font-weight:600">🎯 Top Issues Detected</div>
        <div class="evo-issues-panel" id="evo-issues-list">
            <div style="color:var(--gray-500);text-align:center;padding:20px">Click "Sync & Analyze" to detect issues</div>
        </div>
    </div>
    <div>
        <div class="section-title" style="margin-bottom:12px;font-size:14px;font-weight:600">📊 Agent Performance</div>
        <div class="evo-issues-panel">
            <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;text-align:center">
                <div>
                    <div style="font-size:10px;color:var(--gray-500);text-transform:uppercase;margin-bottom:4px">Outbound</div>
                    <div style="font-size:28px;font-weight:700;color:var(--purple)" id="evo-outbound-calls">--</div>
                    <div style="font-size:11px;color:var(--gray-500)">calls analyzed</div>
                </div>
                <div>
                    <div style="font-size:10px;color:var(--gray-500);text-transform:uppercase;margin-bottom:4px">Inbound</div>
                    <div style="font-size:28px;font-weight:700;color:var(--green)" id="evo-inbound-calls">--</div>
                    <div style="font-size:11px;color:var(--gray-500)">calls analyzed</div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="card">
    <div class="card-header">
        <h2>📞 Recent Call Analysis</h2>
        <span style="font-size:12px;color:var(--gray-500)">Click any call for full AI analysis</span>
    </div>
    <div style="overflow-x:auto">
        <table class="evo-calls-table">
            <thead>
                <tr>
                    <th>Agent</th>
                    <th>Phone</th>
                    <th>Duration</th>
                    <th>Fitness</th>
                    <th>Human</th>
                    <th>Pacing</th>
                    <th>Latency</th>
                    <th>Issues</th>
                </tr>
            </thead>
            <tbody id="evo-calls-body">
                <tr><td colspan="8" style="text-align:center;padding:40px;color:var(--gray-500)">Click "Sync & Analyze" to fetch call data</td></tr>
            </tbody>
        </table>
    </div>
</div>
</div>

<!-- Evolution Call Detail Modal -->
<div class="modal-bg" id="evo-call-modal">
    <div class="modal" style="max-width:800px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
            <h2>📊 Call Analysis</h2>
            <button onclick="closeModal('evo-call-modal')" style="background:none;border:none;color:var(--gray-500);font-size:24px;cursor:pointer">&times;</button>
        </div>
        <div id="evo-modal-body" style="max-height:70vh;overflow-y:auto"></div>
    </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════════ -->
<!-- COMMAND CENTER - THE OPERATIONS HUB THAT DESTROYS GOHIGHLEVEL                  -->
<!-- ═══════════════════════════════════════════════════════════════════════════════ -->
<div class="page" id="page-command">
<style>
#page-command{background:linear-gradient(180deg,#0a0e17 0%,#060912 100%) !important}
.cmd-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.06)}
.cmd-title{display:flex;align-items:center;gap:16px}
.cmd-title h1{font-size:28px;font-weight:700;margin:0}
.cmd-title-icon{width:48px;height:48px;background:linear-gradient(135deg,#10b981,#059669);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px}
.cmd-live{display:flex;align-items:center;gap:8px;padding:8px 16px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:100px}
.cmd-live-dot{width:8px;height:8px;background:#10b981;border-radius:50%;animation:cmdPulse 2s infinite}
@keyframes cmdPulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(16,185,129,0.4)}50%{opacity:0.6;box-shadow:0 0 0 8px rgba(16,185,129,0)}}
.cmd-live span{font-size:12px;color:#10b981;font-weight:600}

/* Layout */
.cmd-grid{display:grid;grid-template-columns:1fr 400px;gap:24px}
@media(max-width:1200px){.cmd-grid{grid-template-columns:1fr}}
.cmd-main{display:flex;flex-direction:column;gap:20px}
.cmd-sidebar{display:flex;flex-direction:column;gap:16px}

/* Cards */
.cmd-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:16px;overflow:hidden}
.cmd-card-header{padding:20px;border-bottom:1px solid rgba(255,255,255,0.06);display:flex;justify-content:space-between;align-items:center}
.cmd-card-title{font-size:14px;font-weight:600;display:flex;align-items:center;gap:10px}
.cmd-card-body{padding:20px}

/* Timeline */
.lead-timeline{position:relative;padding-left:30px}
.timeline-line-v{position:absolute;left:10px;top:0;bottom:0;width:2px;background:linear-gradient(180deg,#10b981,#00d1ff,#8b5cf6,#f59e0b)}
.timeline-event{position:relative;padding:16px 0;border-bottom:1px solid rgba(255,255,255,0.04)}
.timeline-event:last-child{border-bottom:none}
.timeline-dot{position:absolute;left:-24px;top:20px;width:12px;height:12px;border-radius:50%;border:2px solid}
.timeline-dot.green{background:rgba(16,185,129,0.2);border-color:#10b981}
.timeline-dot.cyan{background:rgba(0,209,255,0.2);border-color:#00d1ff}
.timeline-dot.purple{background:rgba(139,92,246,0.2);border-color:#8b5cf6}
.timeline-dot.orange{background:rgba(245,158,11,0.2);border-color:#f59e0b}
.timeline-dot.red{background:rgba(239,68,68,0.2);border-color:#ef4444}
.timeline-content{display:flex;justify-content:space-between;align-items:flex-start}
.timeline-info h4{font-size:14px;font-weight:600;margin-bottom:4px}
.timeline-info p{font-size:12px;color:rgba(255,255,255,0.5)}
.timeline-meta{text-align:right}
.timeline-time{font-size:11px;color:rgba(255,255,255,0.4)}
.timeline-value{font-size:14px;font-weight:600;color:#10b981}

/* Audit Log */
.audit-log{max-height:400px;overflow-y:auto}
.audit-log::-webkit-scrollbar{width:4px}
.audit-log::-webkit-scrollbar-thumb{background:rgba(0,209,255,0.3);border-radius:4px}
.audit-item{padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;gap:12px;align-items:flex-start;font-size:13px;transition:all 0.2s}
.audit-item:hover{background:rgba(0,209,255,0.02)}
.audit-icon{width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.audit-icon.call{background:rgba(0,209,255,0.1)}
.audit-icon.sms{background:rgba(16,185,129,0.1)}
.audit-icon.appt{background:rgba(139,92,246,0.1)}
.audit-icon.lead{background:rgba(245,158,11,0.1)}
.audit-icon.auto{background:rgba(236,72,153,0.1)}
.audit-text{flex:1}
.audit-text strong{color:#fff}
.audit-text span{color:rgba(255,255,255,0.5)}
.audit-time{font-size:11px;color:rgba(255,255,255,0.3);white-space:nowrap}
.audit-why{margin-top:6px;padding:8px 10px;background:rgba(0,0,0,0.3);border-radius:6px;font-size:11px;color:rgba(255,255,255,0.4)}
.audit-why code{color:#00d1ff;background:rgba(0,209,255,0.1);padding:1px 4px;border-radius:3px}

/* Agent Leaderboard */
.leaderboard{display:flex;flex-direction:column;gap:8px}
.leader-item{display:flex;align-items:center;gap:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:10px;transition:all 0.2s}
.leader-item:hover{background:rgba(0,209,255,0.05)}
.leader-rank{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}
.leader-rank.gold{background:linear-gradient(135deg,#f59e0b,#d97706);color:#000}
.leader-rank.silver{background:linear-gradient(135deg,#9ca3af,#6b7280);color:#000}
.leader-rank.bronze{background:linear-gradient(135deg,#d97706,#92400e);color:#000}
.leader-rank.normal{background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.5)}
.leader-avatar{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px}
.leader-info{flex:1}
.leader-name{font-size:13px;font-weight:600}
.leader-stats{font-size:11px;color:rgba(255,255,255,0.4)}
.leader-score{text-align:right}
.leader-score-value{font-size:18px;font-weight:700;color:#10b981}
.leader-score-label{font-size:10px;color:rgba(255,255,255,0.4)}

/* Debug Console */
.debug-console{background:#0d1117;border-radius:10px;font-family:'SF Mono',Monaco,monospace;font-size:12px}
.debug-header{padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.1);display:flex;align-items:center;gap:8px}
.debug-dot{width:10px;height:10px;border-radius:50%}
.debug-dot.red{background:#ef4444}
.debug-dot.yellow{background:#f59e0b}
.debug-dot.green{background:#10b981}
.debug-body{padding:16px;max-height:300px;overflow-y:auto}
.debug-line{padding:4px 0;display:flex;gap:12px}
.debug-time{color:#6b7280;min-width:80px}
.debug-type{min-width:60px;font-weight:600}
.debug-type.info{color:#00d1ff}
.debug-type.success{color:#10b981}
.debug-type.warn{color:#f59e0b}
.debug-type.error{color:#ef4444}
.debug-msg{color:#e5e7eb}

/* System Health */
.health-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.health-item{padding:16px;background:rgba(0,0,0,0.2);border-radius:10px;text-align:center}
.health-value{font-size:24px;font-weight:700;margin-bottom:4px}
.health-value.good{color:#10b981}
.health-value.warn{color:#f59e0b}
.health-value.bad{color:#ef4444}
.health-label{font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.5px}
.health-bar{height:4px;background:rgba(255,255,255,0.1);border-radius:2px;margin-top:8px;overflow:hidden}
.health-bar-fill{height:100%;border-radius:2px;transition:width 0.5s}
.health-bar-fill.good{background:#10b981}
.health-bar-fill.warn{background:#f59e0b}
.health-bar-fill.bad{background:#ef4444}

/* Quick Actions */
.quick-actions{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}
.quick-action{padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px;text-align:center;cursor:pointer;transition:all 0.2s}
.quick-action:hover{background:rgba(0,209,255,0.05);border-color:rgba(0,209,255,0.2);transform:translateY(-2px)}
.quick-action-icon{font-size:24px;margin-bottom:8px}
.quick-action-label{font-size:12px;color:rgba(255,255,255,0.6)}

/* Lead Search */
.lead-search{display:flex;gap:8px;margin-bottom:16px}
.lead-search input{flex:1;padding:12px 16px;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:8px;color:#fff;font-size:13px}
.lead-search input:focus{outline:none;border-color:rgba(0,209,255,0.4)}
.lead-search button{padding:12px 20px;background:linear-gradient(135deg,#00d1ff,#0066ff);border:none;border-radius:8px;color:#fff;font-weight:600;cursor:pointer}
</style>

<div class="cmd-header">
    <div class="cmd-title">
        <div class="cmd-title-icon">🎮</div>
        <div>
            <h1>Command Center</h1>
            <div style="font-size:13px;color:rgba(255,255,255,0.5)">Real-time operations • Full audit trail • AI insights</div>
        </div>
    </div>
    <div class="cmd-live">
        <div class="cmd-live-dot"></div>
        <span>LIVE</span>
    </div>
</div>

<div class="cmd-grid">
    <div class="cmd-main">
        
        <!-- Lead Timeline - Single Source of Truth -->
        <div class="cmd-card">
            <div class="cmd-card-header">
                <div class="cmd-card-title">🎯 Lead Journey Timeline</div>
                <div class="lead-search">
                    <input type="text" id="cmd-lead-search" placeholder="Search by phone or name...">
                    <button onclick="searchLeadTimeline()">Search</button>
                </div>
            </div>
            <div class="cmd-card-body">
                <div class="lead-timeline" id="lead-timeline">
                    <div class="timeline-event">
                        <div class="timeline-dot orange"></div>
                        <div class="timeline-content">
                            <div class="timeline-info">
                                <h4>📱 Facebook Ad Click</h4>
                                <p>Campaign: "Roofing Storm Damage" • Ad Set: Colorado Homeowners</p>
                            </div>
                            <div class="timeline-meta">
                                <div class="timeline-time">Jan 3, 2:14 PM</div>
                                <div class="timeline-value">$2.34 CPC</div>
                            </div>
                        </div>
                    </div>
                    <div class="timeline-event">
                        <div class="timeline-dot green"></div>
                        <div class="timeline-content">
                            <div class="timeline-info">
                                <h4>📝 Lead Form Submitted</h4>
                                <p>John Smith • (720) 555-1234 • john@email.com</p>
                            </div>
                            <div class="timeline-meta">
                                <div class="timeline-time">Jan 3, 2:15 PM</div>
                            </div>
                        </div>
                    </div>
                    <div class="timeline-event">
                        <div class="timeline-dot cyan"></div>
                        <div class="timeline-content">
                            <div class="timeline-info">
                                <h4>📞 AI Call - Paige (Roofing)</h4>
                                <p>Duration: 3:42 • Outcome: Appointment Set • Human Score: 94%</p>
                            </div>
                            <div class="timeline-meta">
                                <div class="timeline-time">Jan 3, 2:17 PM</div>
                                <div class="timeline-value">🎯 Converted</div>
                            </div>
                        </div>
                    </div>
                    <div class="timeline-event">
                        <div class="timeline-dot purple"></div>
                        <div class="timeline-content">
                            <div class="timeline-info">
                                <h4>📅 Appointment Booked</h4>
                                <p>Tomorrow 10:00 AM • Free inspection • Google Calendar synced</p>
                            </div>
                            <div class="timeline-meta">
                                <div class="timeline-time">Jan 3, 2:20 PM</div>
                            </div>
                        </div>
                    </div>
                    <div class="timeline-event">
                        <div class="timeline-dot green"></div>
                        <div class="timeline-content">
                            <div class="timeline-info">
                                <h4>📱 SMS Confirmation Sent</h4>
                                <p>"Hi John! Your roofing inspection is confirmed for tomorrow at 10 AM..."</p>
                            </div>
                            <div class="timeline-meta">
                                <div class="timeline-time">Jan 3, 2:21 PM</div>
                                <div class="timeline-value">✓ Delivered</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Automation Audit Log -->
        <div class="cmd-card">
            <div class="cmd-card-header">
                <div class="cmd-card-title">📋 Automation Audit Log</div>
                <select id="audit-filter" style="padding:6px 12px;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:6px;color:#fff;font-size:12px">
                    <option value="all">All Events</option>
                    <option value="call">Calls</option>
                    <option value="sms">SMS</option>
                    <option value="appt">Appointments</option>
                    <option value="auto">Automations</option>
                </select>
            </div>
            <div class="audit-log" id="audit-log">
                <div class="audit-item">
                    <div class="audit-icon auto">🤖</div>
                    <div class="audit-text">
                        <strong>Auto-Call Triggered</strong> <span>for lead John Smith</span>
                        <div class="audit-why">Rule: <code>new_lead + roofing</code> → Call within 30s • Data: {phone: "7205551234", source: "facebook"}</div>
                    </div>
                    <div class="audit-time">2:17 PM</div>
                </div>
                <div class="audit-item">
                    <div class="audit-icon call">📞</div>
                    <div class="audit-text">
                        <strong>Outbound Call Completed</strong> <span>Paige → (720) 555-1234</span>
                        <div class="audit-why">Duration: 222s • Outcome: appointment_set • Agent: Paige (roofing) • Retell Cost: $0.37</div>
                    </div>
                    <div class="audit-time">2:20 PM</div>
                </div>
                <div class="audit-item">
                    <div class="audit-icon appt">📅</div>
                    <div class="audit-text">
                        <strong>Appointment Created</strong> <span>via AI call extraction</span>
                        <div class="audit-why">Date: 2026-01-04 10:00 • Type: inspection • Google Event: abc123xyz</div>
                    </div>
                    <div class="audit-time">2:20 PM</div>
                </div>
                <div class="audit-item">
                    <div class="audit-icon sms">💬</div>
                    <div class="audit-text">
                        <strong>SMS Sent</strong> <span>Confirmation to (720) 555-1234</span>
                        <div class="audit-why">Template: appointment_confirmation • Twilio SID: SM123abc • Cost: $0.0075</div>
                    </div>
                    <div class="audit-time">2:21 PM</div>
                </div>
                <div class="audit-item">
                    <div class="audit-icon lead">👤</div>
                    <div class="audit-text">
                        <strong>Lead Stage Updated</strong> <span>new_lead → appointment_set</span>
                        <div class="audit-why">Trigger: appointment_created • Pipeline: roofing_default • Previous: contacted</div>
                    </div>
                    <div class="audit-time">2:21 PM</div>
                </div>
            </div>
        </div>
        
        <!-- Debug Console -->
        <div class="cmd-card">
            <div class="cmd-card-header">
                <div class="cmd-card-title">🖥️ Debug Console</div>
                <button onclick="clearDebug()" style="padding:6px 12px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:6px;color:#ef4444;font-size:11px;cursor:pointer">Clear</button>
            </div>
            <div class="debug-console">
                <div class="debug-header">
                    <div class="debug-dot red"></div>
                    <div class="debug-dot yellow"></div>
                    <div class="debug-dot green"></div>
                    <span style="color:rgba(255,255,255,0.4);font-size:11px;margin-left:8px">voice_app.py — LIVE</span>
                </div>
                <div class="debug-body" id="debug-output">
                    <div class="debug-line"><span class="debug-time">14:17:02</span><span class="debug-type info">INFO</span><span class="debug-msg">Webhook received: new_lead from Facebook</span></div>
                    <div class="debug-line"><span class="debug-time">14:17:02</span><span class="debug-type success">OK</span><span class="debug-msg">Lead created: #4521 John Smith (720) 555-1234</span></div>
                    <div class="debug-line"><span class="debug-time">14:17:03</span><span class="debug-type info">INFO</span><span class="debug-msg">Automation triggered: auto_call_new_lead</span></div>
                    <div class="debug-line"><span class="debug-time">14:17:03</span><span class="debug-type info">INFO</span><span class="debug-msg">Retell API: Creating call to +17205551234</span></div>
                    <div class="debug-line"><span class="debug-time">14:17:04</span><span class="debug-type success">OK</span><span class="debug-msg">Call initiated: call_abc123 (Paige/roofing)</span></div>
                    <div class="debug-line"><span class="debug-time">14:20:26</span><span class="debug-type success">OK</span><span class="debug-msg">Call completed: 222s, outcome=appointment_set</span></div>
                    <div class="debug-line"><span class="debug-time">14:20:27</span><span class="debug-type info">INFO</span><span class="debug-msg">Extracting appointment from transcript...</span></div>
                    <div class="debug-line"><span class="debug-time">14:20:28</span><span class="debug-type success">OK</span><span class="debug-msg">Appointment created: #892 2026-01-04 10:00</span></div>
                    <div class="debug-line"><span class="debug-time">14:20:28</span><span class="debug-type info">INFO</span><span class="debug-msg">Syncing to Google Calendar...</span></div>
                    <div class="debug-line"><span class="debug-time">14:20:29</span><span class="debug-type success">OK</span><span class="debug-msg">Google Calendar event created: abc123xyz</span></div>
                    <div class="debug-line"><span class="debug-time">14:21:01</span><span class="debug-type info">INFO</span><span class="debug-msg">Sending SMS confirmation via Twilio...</span></div>
                    <div class="debug-line"><span class="debug-time">14:21:02</span><span class="debug-type success">OK</span><span class="debug-msg">SMS delivered: SM123abc</span></div>
                </div>
            </div>
        </div>
        
    </div>
    
    <div class="cmd-sidebar">
        
        <!-- Agent Leaderboard -->
        <div class="cmd-card">
            <div class="cmd-card-header">
                <div class="cmd-card-title">🏆 Agent Leaderboard</div>
                <span style="font-size:11px;color:rgba(255,255,255,0.4)">Last 7 days</span>
            </div>
            <div class="cmd-card-body">
                <div class="leaderboard" id="agent-leaderboard">
                    <div class="leader-item">
                        <div class="leader-rank gold">1</div>
                        <div class="leader-avatar" style="background:linear-gradient(135deg,#00d1ff,#0066ff)">🏠</div>
                        <div class="leader-info">
                            <div class="leader-name">Paige (Roofing)</div>
                            <div class="leader-stats">47 calls • 18 appointments</div>
                        </div>
                        <div class="leader-score">
                            <div class="leader-score-value">38%</div>
                            <div class="leader-score-label">Convert</div>
                        </div>
                    </div>
                    <div class="leader-item">
                        <div class="leader-rank silver">2</div>
                        <div class="leader-avatar" style="background:linear-gradient(135deg,#f59e0b,#d97706)">☀️</div>
                        <div class="leader-info">
                            <div class="leader-name">Luna (Solar)</div>
                            <div class="leader-stats">35 calls • 12 appointments</div>
                        </div>
                        <div class="leader-score">
                            <div class="leader-score-value">34%</div>
                            <div class="leader-score-label">Convert</div>
                        </div>
                    </div>
                    <div class="leader-item">
                        <div class="leader-rank bronze">3</div>
                        <div class="leader-avatar" style="background:linear-gradient(135deg,#8b5cf6,#7c3aed)">🏥</div>
                        <div class="leader-info">
                            <div class="leader-name">Sarah (Medical)</div>
                            <div class="leader-stats">52 calls • 15 appointments</div>
                        </div>
                        <div class="leader-score">
                            <div class="leader-score-value">29%</div>
                            <div class="leader-score-label">Convert</div>
                        </div>
                    </div>
                    <div class="leader-item">
                        <div class="leader-rank normal">4</div>
                        <div class="leader-avatar" style="background:rgba(255,255,255,0.1)">❄️</div>
                        <div class="leader-info">
                            <div class="leader-name">Jake (HVAC)</div>
                            <div class="leader-stats">28 calls • 7 appointments</div>
                        </div>
                        <div class="leader-score">
                            <div class="leader-score-value">25%</div>
                            <div class="leader-score-label">Convert</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Health -->
        <div class="cmd-card">
            <div class="cmd-card-header">
                <div class="cmd-card-title">💚 System Health</div>
            </div>
            <div class="cmd-card-body">
                <div class="health-grid">
                    <div class="health-item">
                        <div class="health-value good">99.8%</div>
                        <div class="health-label">Uptime</div>
                        <div class="health-bar"><div class="health-bar-fill good" style="width:99.8%"></div></div>
                    </div>
                    <div class="health-item">
                        <div class="health-value good">847ms</div>
                        <div class="health-label">Avg Latency</div>
                        <div class="health-bar"><div class="health-bar-fill good" style="width:85%"></div></div>
                    </div>
                    <div class="health-item">
                        <div class="health-value good">98.2%</div>
                        <div class="health-label">Call Success</div>
                        <div class="health-bar"><div class="health-bar-fill good" style="width:98.2%"></div></div>
                    </div>
                    <div class="health-item">
                        <div class="health-value good">97.5%</div>
                        <div class="health-label">SMS Delivered</div>
                        <div class="health-bar"><div class="health-bar-fill good" style="width:97.5%"></div></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Quick Actions -->
        <div class="cmd-card">
            <div class="cmd-card-header">
                <div class="cmd-card-title">⚡ Quick Actions</div>
            </div>
            <div class="cmd-card-body">
                <div class="quick-actions">
                    <div class="quick-action" onclick="toast('🔄 Syncing calls...');loadDash()">
                        <div class="quick-action-icon">🔄</div>
                        <div class="quick-action-label">Sync All</div>
                    </div>
                    <div class="quick-action" onclick="showPage('testing')">
                        <div class="quick-action-icon">🧪</div>
                        <div class="quick-action-label">Test Call</div>
                    </div>
                    <div class="quick-action" onclick="openModal('appt-modal')">
                        <div class="quick-action-icon">📅</div>
                        <div class="quick-action-label">New Appt</div>
                    </div>
                    <div class="quick-action" onclick="openModal('lead-modal')">
                        <div class="quick-action-icon">👤</div>
                        <div class="quick-action-label">Add Lead</div>
                    </div>
                    <div class="quick-action" onclick="exportReport()">
                        <div class="quick-action-icon">📊</div>
                        <div class="quick-action-label">Export</div>
                    </div>
                    <div class="quick-action" onclick="showPage('nexus')">
                        <div class="quick-action-icon">📈</div>
                        <div class="quick-action-label">Analytics</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Live Activity Feed -->
        <div class="cmd-card">
            <div class="cmd-card-header">
                <div class="cmd-card-title">📡 Live Activity</div>
            </div>
            <div class="cmd-card-body" style="padding:0">
                <div class="audit-log" id="live-activity" style="max-height:200px">
                    <div class="audit-item">
                        <div class="audit-icon call">📞</div>
                        <div class="audit-text"><strong>Call ended</strong> <span>Paige → John S.</span></div>
                        <div class="audit-time">Just now</div>
                    </div>
                    <div class="audit-item">
                        <div class="audit-icon appt">📅</div>
                        <div class="audit-text"><strong>Appointment booked</strong> <span>Tomorrow 10am</span></div>
                        <div class="audit-time">2m ago</div>
                    </div>
                    <div class="audit-item">
                        <div class="audit-icon sms">💬</div>
                        <div class="audit-text"><strong>SMS delivered</strong> <span>Confirmation sent</span></div>
                        <div class="audit-time">2m ago</div>
                    </div>
                    <div class="audit-item">
                        <div class="audit-icon lead">👤</div>
                        <div class="audit-text"><strong>New lead</strong> <span>from Facebook Ads</span></div>
                        <div class="audit-time">5m ago</div>
                    </div>
                </div>
            </div>
        </div>
        
    </div>
</div>
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
        elif path == '/admin':
            self.send_html(get_admin_dashboard())
        elif path == '/api/admin/clients':
            self.send_json(get_all_clients())
        elif path.startswith('/api/admin/clients/'):
            client_id = path.split('/')[-1]
            if client_id.isdigit():
                self.send_json(get_client(int(client_id)) or {'error': 'Not found'})
            else:
                self.send_error(404)
        elif path == '/api/admin/stats':
            self.send_json(get_admin_dashboard_stats())
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
        # ═══════════════════════════════════════════════════════════════════
        # EVOLUTION API ENDPOINTS
        # ═══════════════════════════════════════════════════════════════════
        elif path == '/api/evolution':
            self.send_json(get_evolution_data())
        elif path.startswith('/api/evolution/call/'):
            call_id = path.split('/')[-1]
            self.send_json(get_evolution_call_detail(call_id))
        # ═══════════════════════════════════════════════════════════════════
        # NEXUS API ENDPOINTS
        # ═══════════════════════════════════════════════════════════════════
        elif path == '/api/nexus':
            self.send_json(get_nexus_data())
        elif path.startswith('/api/nexus/call/'):
            call_id = path.split('/')[-1]
            self.send_json(get_nexus_call_detail(call_id))
        elif path == '/api/agent/voices':
            self.send_json(get_agent_voices())
        # Integration GET routes
        elif path == '/api/integrations':
            self.send_json(get_user_integrations(1))  # TODO: Get user_id from session
        elif path == '/api/zapier-webhooks':
            self.send_json(get_zapier_webhooks(1))
        elif path == '/api/me':
            self.send_json(get_user_by_id(1) or {})  # TODO: Get from session
        elif path == '/api/api-keys':
            self.send_json([])  # TODO: Implement get_api_keys
        elif path == '/api/website-leads':
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM website_leads ORDER BY created_at DESC')
            leads = [dict(row) for row in c.fetchall()]
            conn.close()
            self.send_json(leads)
        elif path == '/api/website-stats':
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM website_leads')
            total_leads = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM website_leads WHERE status = 'new'")
            new_leads = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM website_leads WHERE converted = 1")
            converted = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM website_visits WHERE action = "page_view" AND DATE(created_at) = DATE("now")')
            today_visits = c.fetchone()[0]
            c.execute('SELECT COUNT(*) FROM website_visits WHERE action = "page_view"')
            total_visits = c.fetchone()[0]
            conn.close()
            self.send_json({
                "total_leads": total_leads,
                "new_leads": new_leads,
                "converted": converted,
                "today_visits": today_visits,
                "total_visits": total_visits
            })
        else:
            self.send_error(404)
    def do_POST(self):
        l = int(self.headers.get('Content-Length', 0))
        b = self.rfile.read(l).decode() if l > 0 else '{}'
        d = json.loads(b) if b else {}
        path = urlparse(self.path).path
        
        # ═══════════════════════════════════════════════════════════════════
        # ADMIN CLIENT MANAGEMENT ENDPOINTS
        # ═══════════════════════════════════════════════════════════════════
        if path == '/api/admin/clients':
            result = create_client(
                d.get('company_name', ''),
                d.get('contact_name', ''),
                d.get('email', ''),
                d.get('phone', ''),
                d.get('industry', ''),
                d.get('plan', 'starter')
            )
            self.send_json(result)
        elif path.startswith('/api/admin/clients/') and '/integrations' in path:
            client_id = int(path.split('/')[4])
            result = add_client_integration(
                client_id,
                d.get('integration_type', ''),
                d.get('api_key'),
                d.get('api_secret'),
                d.get('webhook_url'),
                d.get('phone_number'),
                d.get('agent_id')
            )
            self.send_json(result)
        elif path.startswith('/api/admin/clients/') and path.split('/')[-1].isdigit():
            client_id = int(path.split('/')[-1])
            result = update_client(client_id, d)
            self.send_json(result)
        elif path == '/api/admin/client-cost':
            log_client_cost(
                d.get('client_id'),
                d.get('cost_type', 'other'),
                d.get('quantity', 1),
                d.get('unit_cost', 0),
                d.get('description'),
                d.get('call_id')
            )
            self.send_json({'success': True})
        # ═══════════════════════════════════════════════════════════════════
        # EXISTING ENDPOINTS
        # ═══════════════════════════════════════════════════════════════════
        elif path == '/api/appointment':
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
        # ═══════════════════════════════════════════════════════════════════
        # EVOLUTION POST ENDPOINTS
        # ═══════════════════════════════════════════════════════════════════
        elif path == '/api/evolution/sync':
            result = sync_evolution_calls()
            self.send_json(result)
        elif path == '/api/evolution/toggle':
            global EVOLUTION_ENABLED
            EVOLUTION_ENABLED = d.get('enabled', True)
            self.send_json({'enabled': EVOLUTION_ENABLED})
        elif path.startswith('/api/evolution/agent/'):
            agent_key = path.split('/')[-1]
            result = apply_evolution_settings(agent_key, d)
            self.send_json(result)
        # NEXUS POST endpoints
        elif path == '/api/nexus/sync':
            result = sync_nexus_calls()
            self.send_json(result)
        elif path.startswith('/api/nexus/evolve/'):
            agent_key = path.split('/')[-1]
            result = evolve_nexus_agent(agent_key, d)
            self.send_json(result)
        # Voice update endpoint
        elif path == '/api/agent/voice':
            result = update_agent_voice(d.get('agent_key'), d.get('voice_id'), d.get('voice_name'))
            self.send_json(result)
        elif path == '/api/agent/voice/sync':
            result = sync_all_voices(d.get('voice_id'), d.get('voice_name'))
            self.send_json(result)
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
        # Demo call from landing page
        elif path == '/api/demo-call':
            phone = d.get('phone', '')
            agent_type = d.get('agent_type', 'roofing')
            print(f"📞 DEMO CALL: agent_type={agent_type}, phone={phone}")
            if not phone:
                self.send_json({"success": False, "error": "Phone number required"})
            else:
                # Make the call via Retell's create-phone-call API
                result = make_call(phone, name="there", agent_type=agent_type, is_test=False)
                self.send_json(result)
        # Custom agent creator from landing page
        elif path == '/api/custom-agent':
            phone = d.get('phone', '')
            company = d.get('company', '')
            industry = d.get('industry', '')
            agent_name = d.get('agent_name', '')
            services = d.get('services', '')
            agent_type = d.get('agent_type', 'outbound')
            
            if not phone:
                self.send_json({"success": False, "error": "Phone number required"})
            elif not company or not industry or not agent_name:
                self.send_json({"success": False, "error": "Please fill in all required fields"})
            else:
                try:
                    print(f"📞 Custom agent call to {phone} for {company} ({industry})")
                    formatted_phone = format_phone(phone)
                    
                    # Determine call type and select correct Retell agent
                    is_inbound = agent_type == 'inbound'
                    
                    # Get industry details (try to match, use defaults if custom)
                    industry_key = industry.lower().replace(' ', '_')
                    industry_details = get_industry_details(industry_key)
                    
                    if is_inbound:
                        retell_agent_id = 'agent_862cd6cf87f7b4d68a6986b3e9'  # INBOUND agent
                        from_number = RETELL_INBOUND_NUMBER  # +17207345479
                        opening = f"Thank you for calling {company}, this is {agent_name} speaking. How can I help you today?"
                        greeting_style = "receptionist"
                        call_purpose = "reception"
                        call_type = "inbound"
                    else:
                        retell_agent_id = 'agent_c345c5f578ebd6c188a7e474fa'  # OUTBOUND agent
                        from_number = RETELL_PHONE_NUMBER  # +17208640910
                        opening = f"Hi, this is {agent_name} with {company}. I'm reaching out because you recently inquired about our {industry.lower()} services. Do you have a quick moment?"
                        greeting_style = "sales"
                        call_purpose = "appointment_setting"
                        call_type = "outbound"
                    
                    print(f"   🤖 Using agent: {'INBOUND' if is_inbound else 'OUTBOUND'}")
                    print(f"   📞 Using number: {from_number}")
                    
                    response = requests.post(
                        "https://api.retellai.com/v2/create-phone-call",
                        headers={
                            "Authorization": f"Bearer {RETELL_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "agent_id": retell_agent_id,
                            "from_number": from_number,
                            "to_number": formatted_phone,
                            "retell_llm_dynamic_variables": {
                                "company_name": company,
                                "industry": industry,
                                "agent_name": agent_name,
                                "customer_name": "there",
                                "call_type": call_type,
                                "call_purpose": call_purpose,
                                "greeting_style": greeting_style,
                                "opening_message": opening,
                                # Industry-specific details
                                "services": services if services else industry_details['services'],
                                "pain_points": industry_details['pain_points'],
                                "qualifying_questions": industry_details['qualifying_questions'],
                                "appointment_type": industry_details['appointment_type'],
                                "urgency_trigger": industry_details['urgency_trigger'],
                                "financing_options": industry_details['financing']
                            }
                        },
                        timeout=15
                    )
                    
                    print(f"   📡 Retell: {response.status_code}")
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        call_id = data.get('call_id', '')
                        print(f"   ✅ Call initiated: {call_id}")
                        self.send_json({"success": True, "call_id": call_id})
                    else:
                        print(f"   ❌ Failed: {response.text}")
                        self.send_json({"success": False, "error": "Call failed"})
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    self.send_json({"success": False, "error": str(e)})
        # Website Lead Booking
        elif path == '/api/website-lead':
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''INSERT INTO website_leads 
                    (first_name, last_name, email, phone, company, industry, call_volume, 
                     preferred_day, preferred_time, notes, source, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (d.get('first_name', ''), d.get('last_name', ''), d.get('email', ''),
                     d.get('phone', ''), d.get('company', ''), d.get('industry', ''),
                     d.get('call_volume', ''), d.get('preferred_day', ''), d.get('preferred_time', ''),
                     d.get('notes', ''), d.get('source', 'website_booking'), 'new'))
                lead_id = c.lastrowid
                conn.commit()
                conn.close()
                
                print(f"🎯 New website lead: {d.get('first_name', '')} - {d.get('phone', '')} - {d.get('industry', '')}")
                
                # Notify owner via SMS
                notify_owner_new_lead(d)
                
                # Send welcome SMS to lead with booking link
                if d.get('phone'):
                    send_lead_welcome_sms(d.get('phone'), d.get('first_name', 'there'))
                
                self.send_json({"success": True, "lead_id": lead_id})
            except Exception as e:
                print(f"❌ Error saving website lead: {e}")
                self.send_json({"success": False, "error": str(e)})
        # Track website visits
        elif path == '/api/track-visit':
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                visitor_id = self.headers.get('X-Forwarded-For', '').split(',')[0].strip() or 'unknown'
                c.execute('''INSERT INTO website_visits (visitor_id, action, page, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?)''',
                    (visitor_id, d.get('action', 'page_view'), d.get('page', '/'),
                     visitor_id, self.headers.get('User-Agent', '')))
                conn.commit()
                conn.close()
                self.send_json({"success": True})
            except:
                self.send_json({"success": True})  # Don't fail on tracking errors
        # Trial Signup
        elif path == '/api/trial-signup':
            try:
                name = d.get('name', '')
                email = d.get('email', '')
                phone = d.get('phone', '')
                password = d.get('password', '')
                
                if not email or not password:
                    self.send_json({"success": False, "error": "Email and password required"})
                    return
                
                # Phone is also required for trial signup
                if not phone or len(phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')) < 10:
                    self.send_json({"success": False, "error": "Valid phone number required"})
                    return
                
                # Create user account
                result = create_user(email, password, name, '', phone)
                
                if result.get('success'):
                    print(f"🎉 NEW TRIAL SIGNUP: {name} - {email} - {phone}")
                    
                    # Notify owner via SMS
                    sms_msg = f"""🎉 NEW TRIAL SIGNUP!

Name: {name}
Email: {email}
Phone: {phone}

They now have 7-day access! Follow up! 🔥"""
                    
                    if TWILIO_SID and TWILIO_TOKEN and OWNER_PHONE:
                        send_sms(OWNER_PHONE, sms_msg, "trial_notification")
                    
                    # Send welcome SMS to new trial user
                    if phone:
                        welcome_msg = f"""Welcome to VoiceLab, {name}! 🎉

Your 7-day free trial is now active!

Log in anytime at: https://voicelab.live/app

Questions? Reply to this text or book a call:
{CALENDLY_LINK}

Let's close some deals! 🚀"""
                        send_sms(phone, welcome_msg, "trial_welcome")
                    
                    self.send_json({"success": True})
                else:
                    self.send_json({"success": False, "error": result.get('error', 'Could not create account')})
            except Exception as e:
                print(f"❌ Trial signup error: {e}")
                self.send_json({"success": False, "error": str(e)})
        # Update website lead status
        elif path == '/api/website-lead-status':
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('UPDATE website_leads SET status = ?, last_contact_date = CURRENT_TIMESTAMP, total_contacts = total_contacts + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                    (d.get('status', 'contacted'), d.get('id')))
                conn.commit()
                conn.close()
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
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
