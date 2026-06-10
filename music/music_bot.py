"""
FreeBeats - Telegram Bot for Copyright-Free Music
Powered by Jamendo API
"""

import logging
import os
from typing import Optional
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F

# Load environment variables from .env file
load_dotenv()
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import asyncio

# ============= CONFIG =============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID")
JAMENDO_SECRET = os.getenv("JAMENDO_SECRET")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============= BOT SETUP =============
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ============= FSM STATES =============
class SearchState(StatesGroup):
    waiting_for_query = State()
    waiting_for_track_selection = State()

# ============= JAMENDO API CLASS =============
class JamendoAPI:
    """Handles all Jamendo API interactions"""
    
    BASE_URL = "https://api.jamendo.com/v3.0"
    
    def __init__(self, client_id: str, secret: str):
        self.client_id = client_id
        self.secret = secret
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def search_tracks(self, query: str, limit: int = 10) -> list:
        """
        Search for tracks on Jamendo
        Returns list of track objects
        """
        await self.init_session()
        
        try:
            params = {
                "client_id": self.client_id,
                "search": query,
                "limit": limit,
                "imagesize": 100,
                "include": "musicinfo",
                "order": "popularity_total"
            }
            
            async with self.session.get(
                f"{self.BASE_URL}/tracks",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"Search query: '{query}' - Found {len(data.get('results', []))} tracks")
                    return data.get("results", [])
                else:
                    logger.error(f"Jamendo API error: {resp.status}")
                    return []
        
        except asyncio.TimeoutError:
            logger.error("Jamendo API request timeout")
            return []
        except Exception as e:
            logger.error(f"Jamendo search error: {str(e)}")
            return []
    
    async def get_track_details(self, track_id: str) -> dict:
        """Get detailed info for a track"""
        await self.init_session()
        
        try:
            params = {
                "client_id": self.client_id,
                "id": track_id,
                "include": "musicinfo"
            }
            
            async with self.session.get(
                f"{self.BASE_URL}/tracks",
                params=params,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("results", [{}])[0]
                return {}
        except Exception as e:
            logger.error(f"Error fetching track details: {str(e)}")
            return {}

# ============= API INSTANCE =============
jamendo = JamendoAPI(JAMENDO_CLIENT_ID, JAMENDO_SECRET)

# ============= HANDLERS =============
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Start command"""
    await message.answer(
        "🎵 *CEOOOZ MUSIC FREE*\n\n"
        "Bepul musiqalarni qidirish va topish\n\n"
        "Buyruqlar:\n"
        "/search - Musiqani qidirish\n"
        "/help - Yordam\n"
        "/about - Bot haqida\n\n"
        "_Barcha musiqalar Creative Commons litsenziyasi bilan_",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🔍 Musiqani qidirish")],
                [types.KeyboardButton(text="ℹ️ Yordam")],
            ],
            resize_keyboard=True
        )
    )
    logger.info(f"User {message.from_user.id} started bot")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command"""
    await message.answer(
        "📖 *CEOOOZ MUSIC FREE - Qo'llanma*\n\n"
        "1️⃣ /search yoki 'Musiqani qidirish' tugmasini bosing\n"
        "2️⃣ Artisdtning nomi yoki qoshiqning nomini yozing\n"
        "3️⃣ Natijalarni ko'ring\n"
        "4️⃣ Qoshiqni bosing - rasmi bilan ko'ring\n"
        "5️⃣ 'Jamendoda tingla' linkiga bosing\n\n"
        "*Musiqalar haqida:*\n"
        "• Barcha qoshiqlar Creative Commons litsenziyali\n"
        "• Bepul yuklab olish mumkin\n"
        "• Artisdtlar to'liq kredit bilan\n\n"
        "Yordam kerakmi? /about",
        parse_mode="Markdown"
    )

@dp.message(Command("about"))
async def cmd_about(message: types.Message):
    """About command"""
    await message.answer(
        "ℹ️ *CEOOOZ MUSIC FREE Haqida*\n\n"
        "Bu bot siz uchun Jamendodagi bepul, copyright-free musiqalarni topish va yugurish imkoniyatini beradi.\n\n"
        "*Musiqalar Manba:*\n"
        "Jamendo - 500k+ mustaqil artisdtlar platformasi\n"
        "Litsenziya: Creative Commons\n\n"
        "*Yaratuvchi:* ceoooz\n"
        "*Texnologiya:* aiogram, Jamendo API\n"
        "*Hosting:* Railway (24/7)\n\n"
        "Barcha musiqalar artisdtning huquqlariga hurmat bilan.",
        parse_mode="Markdown"
    )

@dp.message(Command("search"), StateFilter(None))
async def cmd_search(message: types.Message, state: FSMContext):
    """Initiate search"""
    await state.set_state(SearchState.waiting_for_query)
    await message.answer(
        "🔍 What would you like to search for?\n\n"
        "Examples:\n"
        "• artist name (e.g., 'Ólafur Arnalds')\n"
        "• song title (e.g., 'ambient music')\n"
        "• genre (e.g., 'jazz', 'electronic')",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(SearchState.waiting_for_query)
async def process_search(message: types.Message, state: FSMContext):
    """Process search query"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Search query too short. Try again.")
        return
    
    if len(query) > 100:
        await message.answer("❌ Search query too long. Keep it under 100 characters.")
        return
    
    # Show loading
    status_msg = await message.answer("🔄 Searching Jamendo...")
    
    try:
        tracks = await jamendo.search_tracks(query, limit=8)
        
        if not tracks:
            await status_msg.delete()
            await message.answer(
                f"❌ No results for '{query}'\n\n"
                "Try a different search term or artist name.",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔍 Search Again")]],
                    resize_keyboard=True
                )
            )
            await state.clear()
            return
        
        # Build results message
        results_text = f"🎵 *Found {len(tracks)} tracks*\n\n"
        
        for i, track in enumerate(tracks, 1):
            artist = track.get("artist_name", "Unknown")
            title = track.get("name", "Unknown")
            results_text += f"{i}. *{title}*\n   by {artist}\n"
        
        results_text += "\n_Tap a number to see details_"
        
        await status_msg.delete()
        await message.answer(
            results_text,
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text=f"Track {i}", callback_data=f"track_{i-1}_{query}")]
                    for i in range(1, len(tracks) + 1)
                ]
            )
        )
        
        # Store tracks in state
        await state.update_data(tracks=tracks, query=query)
        await state.set_state(SearchState.waiting_for_track_selection)
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        await status_msg.delete()
        await message.answer("❌ Search failed. Please try again.")
        await state.clear()

@dp.callback_query(SearchState.waiting_for_track_selection)
async def show_track_details(callback: types.CallbackQuery, state: FSMContext):
    """Show track details"""
    try:
        # Parse callback data
        parts = callback.data.split("_")
        track_idx = int(parts[1])
        
        # Get stored tracks
        data = await state.get_data()
        tracks = data.get("tracks", [])
        
        if track_idx >= len(tracks):
            await callback.answer("❌ Invalid selection", show_alert=True)
            return
        
        track = tracks[track_idx]
        
        # Build track details
        artist = track.get("artist_name", "Unknown Artist")
        title = track.get("name", "Unknown Track")
        duration = track.get("duration", 0)
        album = track.get("album_name", "N/A")
        image = track.get("image", "")
        track_url = track.get("shareurl", "")
        license_url = track.get("licenseurl", "")
        
        # Format duration
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}:{seconds:02d}"
        
        # Build message
        details = (
            f"🎵 *{title}*\n\n"
            f"👤 *Artist:* {artist}\n"
            f"💿 *Album:* {album}\n"
            f"⏱️ *Duration:* {duration_str}\n"
            f"📜 *License:* Creative Commons\n"
        )
        
        # Send with photo if available
        if image:
            try:
                await callback.message.delete()
                await callback.from_user.send_photo(
                    photo=image,
                    caption=details,
                    parse_mode="Markdown",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [types.InlineKeyboardButton(text="🔗 Listen on Jamendo", url=track_url)],
                            [types.InlineKeyboardButton(text="📜 License", url=license_url)],
                            [types.InlineKeyboardButton(text="🔙 Back to Results", callback_data="back_search")]
                        ]
                    )
                )
            except Exception as e:
                logger.error(f"Photo send error: {str(e)}")
                await callback.message.edit_text(
                    details,
                    parse_mode="Markdown",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [types.InlineKeyboardButton(text="🔗 Listen on Jamendo", url=track_url)],
                            [types.InlineKeyboardButton(text="📜 License", url=license_url)],
                            [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_search")]
                        ]
                    )
                )
        else:
            await callback.message.edit_text(
                details,
                parse_mode="Markdown",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔗 Listen on Jamendo", url=track_url)],
                        [types.InlineKeyboardButton(text="📜 License", url=license_url)],
                        [types.InlineKeyboardButton(text="🔙 Back", callback_data="back_search")]
                    ]
                )
            )
        
        await callback.answer()
        
        # Log track view
        logger.info(f"User {callback.from_user.id} viewed track: {title} by {artist}")
        
    except Exception as e:
        logger.error(f"Track details error: {str(e)}")
        await callback.answer("❌ Error loading track details", show_alert=True)

@dp.callback_query(F.data == "back_search")
async def back_to_search(callback: types.CallbackQuery, state: FSMContext):
    """Go back to search"""
    await state.set_state(SearchState.waiting_for_query)
    await callback.message.delete()
    await callback.from_user.send_message(
        "🔍 Search for more music:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔍 Search Music")]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@dp.message(F.text == "🔍 Musiqani qidirish")
async def quick_search(message: types.Message, state: FSMContext):
    """Quick search button"""
    await state.set_state(SearchState.waiting_for_query)
    await message.answer("🔍 Qanday musiqani qidirasiz?")

@dp.message(F.text == "ℹ️ Yordam")
async def quick_help(message: types.Message):
    """Quick help button"""
    await cmd_help(message)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Stats command (admin only)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Unauthorized")
        return
    
    stats = (
        f"📊 *Bot Statistics*\n\n"
        f"⏰ Last check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"✅ Bot is running\n"
        f"🔌 Jamendo API: Connected"
    )
    await message.answer(stats, parse_mode="Markdown")

@dp.message()
async def echo(message: types.Message):
    """Fallback handler"""
    await message.answer(
        "I didn't understand that command.\n\n"
        "Try:\n/search - Search for music\n/help - Show help\n/start - Main menu"
    )

# ============= SHUTDOWN HANDLER =============
async def on_shutdown():
    """Cleanup on shutdown"""
    await jamendo.close_session()
    logger.info("Bot shutdown complete")

# ============= MAIN =============
async def main():
    """Start the bot"""
    logger.info("Starting FreeBeats bot...")
    
    try:
        await jamendo.init_session()
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await on_shutdown()

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not JAMENDO_CLIENT_ID:
        logger.error("Missing required environment variables!")
        exit(1)
    
    asyncio.run(main())