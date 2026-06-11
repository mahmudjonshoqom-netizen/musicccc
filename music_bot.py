"""
CEOOOZ MUSIC FREE - Telegram Bot
Jamendo API Integration + Admin Ad System
"""

import logging
import os
from typing import Optional
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import asyncio
import json
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

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

# ============= AD STORAGE =============
ADS_FILE = "ads.json"

def load_ads():
    """Load ads from file"""
    if Path(ADS_FILE).exists():
        with open(ADS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_ads(ads):
    """Save ads to file"""
    with open(ADS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)

def get_ad_to_send():
    """Get ad that should be sent now (24hr interval)"""
    ads = load_ads()
    if not ads:
        return None
    
    now = datetime.now().timestamp()
    for ad in ads:
        last_sent = ad.get("last_sent", 0)
        if now - last_sent >= 86400:  # 24 hours = 86400 seconds
            return ad
    return None

def mark_ad_sent(ad_id):
    """Mark ad as sent"""
    ads = load_ads()
    for ad in ads:
        if ad["id"] == ad_id:
            ad["last_sent"] = datetime.now().timestamp()
            save_ads(ads)
            break

# ============= FSM STATES =============
class SearchState(StatesGroup):
    waiting_for_query = State()
    waiting_for_track_selection = State()

class AdState(StatesGroup):
    waiting_for_ad_text = State()
    waiting_for_ad_photo = State()

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
        """Search for tracks on Jamendo"""
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

# ============= API INSTANCE =============
jamendo = JamendoAPI(JAMENDO_CLIENT_ID, JAMENDO_SECRET)

# ============= HANDLERS =============
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Start command"""
    await state.clear()
    
    # Check if there's an ad to send
    ad = get_ad_to_send()
    
    if ad:
        try:
            if ad.get("photo"):
                await message.answer_photo(
                    photo=ad["photo"],
                    caption=ad["text"],
                    parse_mode="HTML"
                )
            else:
                await message.answer(ad["text"], parse_mode="HTML")
            mark_ad_sent(ad["id"])
            logger.info(f"Sent ad: {ad['id']}")
        except Exception as e:
            logger.error(f"Error sending ad: {str(e)}")
    
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
async def cmd_help(message: types.Message, state: FSMContext):
    """Help command"""
    await state.clear()
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
async def cmd_about(message: types.Message, state: FSMContext):
    """About command"""
    await state.clear()
    await message.answer(
        "ℹ️ *CEOOOZ MUSIC FREE Haqida*\n\n"
        "Bu bot siz uchun Jamendodagi bepul, copyright-free musiqalarni topish va tinglash imkoniyatini beradi.\n\n"
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
        "🔍 Qanday musiqani qidirasiz?\n\n"
        "Misollar:\n"
        "• Artisdtning nomi (masalan: 'Ólafur Arnalds')\n"
        "• Qoshiqning nomi (masalan: 'ambient music')\n"
        "• Janr (masalan: 'jazz', 'electronic')",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(SearchState.waiting_for_query)
async def process_search(message: types.Message, state: FSMContext):
    """Process search query"""
    query = message.text.strip()
    
    if len(query) < 2:
        await message.answer("❌ Qidirish so'zi juda qisqa. Qayta urinib ko'ring.")
        return
    
    if len(query) > 100:
        await message.answer("❌ Qidirush so'zi juda uzun. 100 belgidan kam bo'lsin.")
        return
    
    # Show loading
    status_msg = await message.answer("🔄 Jamendoda qidirilmoqda...")
    
    try:
        tracks = await jamendo.search_tracks(query, limit=8)
        
        if not tracks:
            await status_msg.delete()
            await message.answer(
                f"❌ '{query}' uchun natija topilmadi\n\n"
                "Boshqa qidirish termini yoki artisdtning nomini urinib ko'ring.",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="🔍 Musiqani qidirish")]],
                    resize_keyboard=True
                )
            )
            await state.clear()
            return
        
        # Build results message
        results_text = f"🎵 *{len(tracks)} ta qoshiq topildi*\n\n"
        
        for i, track in enumerate(tracks, 1):
            artist = track.get("artist_name", "Noma'lum")
            title = track.get("name", "Noma'lum")
            results_text += f"{i}. *{title}*\n   {artist}\n"
        
        results_text += "\n_Raqamni bosing_"
        
        await status_msg.delete()
        await message.answer(
            results_text,
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text=f"{i}", callback_data=f"track_{i-1}")]
                    for i in range(1, len(tracks) + 1)
                ]
            )
        )
        
        # Store tracks in state
        await state.update_data(tracks=tracks)
        await state.set_state(SearchState.waiting_for_track_selection)
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        await status_msg.delete()
        await message.answer("❌ Qidirishda xato. Qayta urinib ko'ring.")
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
            await callback.answer("❌ Noto'g'ri tanlov", show_alert=True)
            return
        
        track = tracks[track_idx]
        
        # Build track details
        artist = track.get("artist_name", "Noma'lum Artisdт")
        title = track.get("name", "Noma'lum Qoshiq")
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
            f"🎵 <b>{title}</b>\n\n"
            f"👤 <b>Artisdт:</b> {artist}\n"
            f"💿 <b>Albom:</b> {album}\n"
            f"⏱️ <b>Vaqti:</b> {duration_str}\n"
            f"📜 <b>Litsenziya:</b> Creative Commons\n"
        )
        
        # Send with photo if available
        if image:
            try:
                await callback.message.delete()
                await callback.from_user.send_photo(
                    photo=image,
                    caption=details,
                    parse_mode="HTML",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [types.InlineKeyboardButton(text="🔗 Jamendoda tingla", url=track_url)],
                            [types.InlineKeyboardButton(text="📜 Litsenziya", url=license_url)],
                            [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_search")]
                        ]
                    )
                )
            except Exception as e:
                logger.error(f"Photo send error: {str(e)}")
                await callback.message.edit_text(
                    details,
                    parse_mode="HTML",
                    reply_markup=types.InlineKeyboardMarkup(
                        inline_keyboard=[
                            [types.InlineKeyboardButton(text="🔗 Jamendoda tingla", url=track_url)],
                            [types.InlineKeyboardButton(text="📜 Litsenziya", url=license_url)],
                            [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_search")]
                        ]
                    )
                )
        else:
            await callback.message.edit_text(
                details,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(text="🔗 Jamendoda tingla", url=track_url)],
                        [types.InlineKeyboardButton(text="📜 Litsenziya", url=license_url)],
                        [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_search")]
                    ]
                )
            )
        
        await callback.answer()
        
        # Log track view
        logger.info(f"User {callback.from_user.id} viewed track: {title} by {artist}")
        
    except Exception as e:
        logger.error(f"Track details error: {str(e)}")
        await callback.answer("❌ Xato yuz berdi", show_alert=True)

@dp.callback_query(F.data == "back_search")
async def back_to_search(callback: types.CallbackQuery, state: FSMContext):
    """Go back to search"""
    await state.set_state(SearchState.waiting_for_query)
    await callback.message.delete()
    await callback.from_user.send_message(
        "🔍 Yana musiqani qidiring:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="🔍 Musiqani qidirish")]],
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
async def quick_help(message: types.Message, state: FSMContext):
    """Quick help button"""
    await state.clear()
    await cmd_help(message, state)

# ============= ADMIN COMMANDS =============

@dp.message(Command("add"))
async def cmd_add_ad(message: types.Message, state: FSMContext):
    """Add advertisement (admin only)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ruxsati yo'q")
        logger.warning(f"User {message.from_user.id} tried /add command")
        return
    
    await state.set_state(AdState.waiting_for_ad_text)
    await message.answer(
        "📢 Reklama matni yozing (HTML format qo'llab-quvvatlanadi):\n\n"
        "Misollar:\n"
        "<b>Qalin matn</b>\n"
        "<i>Kursiv</i>\n"
        "<u>Pastiga chiziq</u>\n\n"
        "Rasm ham yuborish mumkin (ixtiyoriy).",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(AdState.waiting_for_ad_text)
async def process_ad_text(message: types.Message, state: FSMContext):
    """Process ad text"""
    if not message.text:
        await message.answer("❌ Matn yozing")
        return
    
    await state.update_data(ad_text=message.text)
    await state.set_state(AdState.waiting_for_ad_photo)
    await message.answer(
        "Rasm yuborish kerakmi? (ixtiyoriy)\n"
        "/skip bosing agar rasm kerak bo'lmasa",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="/skip")]],
            resize_keyboard=True
        )
    )

@dp.message(AdState.waiting_for_ad_photo)
async def process_ad_photo(message: types.Message, state: FSMContext):
    """Process ad photo"""
    data = await state.get_data()
    ad_text = data.get("ad_text", "")
    
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text == "/skip":
        photo_id = None
    else:
        await message.answer("❌ Rasm yuborish kerak yoki /skip bosing")
        return
    
    # Save ad
    ads = load_ads()
    ad_id = max([ad.get("id", 0) for ad in ads], default=0) + 1
    
    new_ad = {
        "id": ad_id,
        "text": ad_text,
        "photo": photo_id,
        "created_at": datetime.now().timestamp(),
        "last_sent": 0
    }
    
    ads.append(new_ad)
    save_ads(ads)
    
    await message.answer(
        f"✅ Reklama qo'shildi (ID: {ad_id})\n\n"
        "Har 24 soatda 1 marta jo'natiladi",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    logger.info(f"Admin {message.from_user.id} added ad: {ad_id}")
    await state.clear()

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Statistics (admin only)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ruxsati yo'q")
        logger.warning(f"User {message.from_user.id} tried /stats command")
        return
    
    ads = load_ads()
    stats = (
        f"📊 *Bot Statistikasi*\n\n"
        f"⏰ Vaqti: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"✅ Bot ishlayapti\n"
        f"🔌 Jamendo API: Ulanish topildi\n"
        f"📢 Reklamalar soni: {len(ads)}\n\n"
        f"*Reklama buyruqlari:*\n"
        f"/add - Reklama qo'shish\n"
        f"/delete [ID] - Reklama o'chirish\n"
        f"/ads - Barcha reklamalar"
    )
    await message.answer(stats, parse_mode="Markdown")
    logger.info(f"Admin {message.from_user.id} checked stats")

@dp.message(Command("ads"))
async def cmd_list_ads(message: types.Message):
    """List all ads (admin only)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ruxsati yo'q")
        return
    
    ads = load_ads()
    if not ads:
        await message.answer("📢 Hech qanday reklama yo'q")
        return
    
    ads_text = "*📢 Barcha Reklamalar:*\n\n"
    for ad in ads:
        created = datetime.fromtimestamp(ad["created_at"]).strftime("%Y-%m-%d %H:%M")
        last_sent = datetime.fromtimestamp(ad["last_sent"]).strftime("%Y-%m-%d %H:%M") if ad["last_sent"] else "Jo'natilmadi"
        ads_text += f"*ID {ad['id']}* - {created}\nOxirgi jo'natilish: {last_sent}\n\n"
    
    await message.answer(ads_text, parse_mode="Markdown")

@dp.message(Command("delete"))
async def cmd_delete_ad(message: types.Message):
    """Delete ad (admin only)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Ruxsati yo'q")
        return
    
    try:
        ad_id = int(message.text.split()[1])
        ads = load_ads()
        ads = [ad for ad in ads if ad["id"] != ad_id]
        save_ads(ads)
        await message.answer(f"✅ Reklama {ad_id} o'chirildi")
        logger.info(f"Admin {message.from_user.id} deleted ad: {ad_id}")
    except:
        await message.answer("❌ Xato format: /delete [ID]")

@dp.message()
async def echo(message: types.Message, state: FSMContext):
    """Fallback handler"""
    current_state = await state.get_state()
    
    # If in search state, ignore commands
    if current_state in [SearchState.waiting_for_query, SearchState.waiting_for_track_selection]:
        await message.answer("🔍 Qidirish davomida. Yuqoridagi raqamlardan birini tanlang yoki /start bosing")
        return
    
    await message.answer(
        "Buyruqni tushunmadim.\n\n"
        "Buyruqlar:\n"
        "/search - Musiqani qidirish\n"
        "/help - Yordam\n"
        "/start - Asosiy menu"
    )

# ============= SHUTDOWN HANDLER =============
async def on_shutdown():
    """Cleanup on shutdown"""
    await jamendo.close_session()
    logger.info("Bot shutdown complete")

# ============= MAIN =============
async def main():
    """Start the bot"""
    logger.info("Starting CEOOOZ MUSIC FREE bot...")
    
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
