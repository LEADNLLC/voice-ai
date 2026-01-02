# VOICE - AI That Closes Deals

27 AI agents that call your leads, book appointments, and never miss a follow-up.

![VOICE](https://img.shields.io/badge/VOICE-AI%20Sales%20Platform-00D1FF)

## 🚀 One-Click Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/voice-ai)

Or manually:

1. Fork this repo
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your forked repo
5. Done! Your app will be live in ~2 minutes

## 🏠 Local Development

```bash
# Clone the repo
git clone https://github.com/yourusername/voice-ai.git
cd voice-ai

# Run the app
python voice_app.py

# Open http://localhost:8080
```

## 🔑 Default Login

- **Email**: admin@voice.ai
- **Password**: admin123

⚠️ Change this immediately in production!

## ✨ Features

- **27 AI Agents** - 12 outbound sales + 15 inbound receptionists
- **Human-Like Calls** - NEPQ-trained, natural conversations
- **Smart Follow-Up** - 3 calls/day, 7-day cycles
- **Full Pipeline** - Track leads from contact to close
- **FB/IG Ads** - Import leads, track CPL/CPA/ROAS
- **Integrations** - VAPI, Twilio, Zapier, Google Calendar, Stripe
- **Multi-Tenant** - Each user has their own API keys

## 📁 Files

```
voice_app.py      # Main application (all-in-one)
requirements.txt  # Python dependencies
Procfile          # Railway/Heroku start command
railway.json      # Railway configuration
```

## 🔌 Integrations Setup

### VAPI (Voice AI)
1. Sign up at [vapi.ai](https://vapi.ai)
2. Get your API Key and Phone ID
3. Add in Settings → Integrations

### Twilio (SMS)
1. Sign up at [twilio.com](https://twilio.com)
2. Get Account SID, Auth Token, Phone Number
3. Add in Settings → Integrations

### Zapier
1. Create a Zap with Webhook trigger
2. Copy the webhook URL
3. Add in Settings → Integrations → Zapier

## 📄 License

MIT License - feel free to use commercially!

---

Built with ❤️ by VOICE AI
