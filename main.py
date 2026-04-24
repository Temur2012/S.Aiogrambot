import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
import yt_dlp

# --- SOZLAMALAR ---
TOKEN = "8735752102:AAGwz3iG9dePS8Tdi2vfYAwHVJFGupxe-mo"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- VIDEO YUKLASH FUNKSIYASI ---
async def download_instagram_video(url):
    ydl_opts = {
        # 'mp4' formatida va eng yaxshi sifatda yuklash
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'noplaylist': True,
        # Instagram bloklaridan qochish uchun yangilangan user-agent
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Video haqida ma'lumot olish va yuklash
            info = await asyncio.to_thread(lambda: ydl.extract_info(url, download=True))
            # Yuklangan faylning to'liq manzili
            file_path = ydl.prepare_filename(info)
            return file_path, info.get('title', 'Instagram Video')
    except Exception as e:
        return None, str(e)


# --- HANDLERLAR ---
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Salom, Temur! Instagram Reels yoki video havolasini yuboring, men uni yuklab beraman. 🎬")


@dp.message(F.text.contains("instagram.com"))
async def handle_instagram_video(message: Message):
    status_msg = await message.answer("⏳ Video yuklanmoqda, kuting...")

    path, title = await download_instagram_video(message.text)

    if path and os.path.exists(path):
        try:
            await status_msg.edit_text("📤 Telegramga yuborilmoqda...")
            video_file = FSInputFile(path)
            # Videoni yuborish
            await message.answer_video(video_file, caption=f"🎬 {title}")
            await status_msg.delete()
        except Exception as send_error:
            await status_msg.edit_text(f"❌ Yuborishda xatolik: {str(send_error)[:100]}")
        finally:
            # Faylni serverdan (kompyuterdan) o'chirish
            if os.path.exists(path):
                os.remove(path)
    else:
        await status_msg.edit_text(f"❌ Yuklab bo'lmadi.\nSabab: {title[:100]}")


async def main():
    print("Instagram Video Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())