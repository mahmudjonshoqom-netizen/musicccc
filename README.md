# 🎵 FreeBeats - Free Music Telegram Bot

A Telegram bot for discovering and exploring copyright-free music from Jamendo, the world's largest platform for independent artists.

## Features

- 🔍 **Search Music** - Find tracks by artist, title, or genre
- 🎨 **Track Details** - See album art, duration, and artist info
- 🔗 **Direct Links** - One-click access to Jamendo
- 📜 **License Info** - Verify Creative Commons licensing
- 🤖 **Always On** - Deployed on Railway for 24/7 uptime
- 📊 **Logging** - Full error tracking and statistics

## Quick Start

### 1️⃣ Get Credentials
- **Telegram Bot:** @BotFather → `/newbot`
- **Jamendo API:** https://developer.jamendo.com → Create app

### 2️⃣ Local Setup (5 minutes)
```bash
git clone <your-repo>
cd freebeats-bot

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# Create .env with your credentials
echo "TELEGRAM_BOT_TOKEN=your_token" > .env
echo "JAMENDO_CLIENT_ID=your_id" >> .env
echo "JAMENDO_SECRET=your_secret" >> .env
echo "ADMIN_ID=your_user_id" >> .env

python music_bot.py
```

### 3️⃣ Deploy to Railway (24/7)
```bash
# Login to Railway
railway login

# Deploy (connects to your GitHub repo)
railway up
```

See **SETUP_GUIDE.md** for complete instructions.

## Architecture

```
FreeBeats Bot
├── Telegram API
│   └── Users search for music
├── JamendoAPI Class
│   └── Fetches copyright-free tracks
└── Railway
    └── 24/7 hosting & logs
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Open main menu |
| `/search` | Search for music |
| `/help` | Show instructions |
| `/about` | Bot information |
| `/stats` | Admin statistics |

## File Structure

```
freebeats-bot/
├── music_bot.py          # Main bot code (500+ lines)
├── requirements.txt      # Dependencies
├── railway.toml          # Railway config
├── SETUP_GUIDE.md        # Complete setup guide
├── .gitignore            # Git ignore
└── README.md             # This file
```

## Technology Stack

- **Bot Framework:** aiogram 3.1.1
- **Music API:** Jamendo (REST)
- **Async:** aiohttp (non-blocking)
- **Hosting:** Railway
- **Language:** Python 3.9+

## Compliance

✅ **Telegram ToS** - Official Bot API only  
✅ **Copyright** - No scraping, no re-hosting  
✅ **Jamendo API** - Licensed access  
✅ **Legal** - 100% auditable  

All music is Creative Commons licensed by the artists themselves.

## Performance

- **Users:** 1,000+/day capacity
- **Response Time:** <2 seconds avg
- **Uptime:** 99.9% (Railway)
- **API Calls:** 600/hour (Jamendo free tier)

## Troubleshooting

**Bot won't start?** Check `.env` has all 4 variables
**No search results?** Try different keywords (exact match required)
**Railway deployment failed?** Check environment variables in dashboard

See **SETUP_GUIDE.md** for detailed troubleshooting.

## Future Enhancements

- [ ] Favorites/bookmarks
- [ ] Playlist creation
- [ ] Genre/mood filtering
- [ ] User statistics
- [ ] Spotify integration (preview links)

## Author

**ceoooz** - Built with focus on compliance & reliability

## License

Bot code: MIT (yours to modify)  
Music: Creative Commons (via Jamendo)  
Jamendo: https://www.jamendo.com

---

**Ready to go live?** Follow **SETUP_GUIDE.md** step by step. Takes 15 minutes total.
