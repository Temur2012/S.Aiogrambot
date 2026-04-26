import asyncio
import os
import glob
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, MediaGroupBuilder
import yt_dlp

# --- SOZLAMALAR ---
TOKEN = "8735752102:AAGwz3iG9dePS8Tdi2vfYAwHVJFGupxe-mo"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- VIDEO / STORIES YUKLASH FUNKSIYASI ---
async def download_instagram_media(url: str):
    """
    Reels, post video, yoki Stories yuklab beradi.
    Bir nechta media bo'lsa (carousel/stories) — barchasini qaytaradi.
    """
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(autonumber)s.%(ext)s'),
        'noplaylist': False,   # Stories playlist bo'lishi mumkin
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        # Stories uchun cookies kerak bo'lsa quyidagini yoqing:
        # 'cookiefile': os.path.join(BASE_DIR, 'cookies.txt'),
        'quiet': True,
        'no_warnings': True,
        'writeinfojson': False,
        'writethumbnail': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(lambda: ydl.extract_info(url, download=True))

            # Bir nechta media (stories, carousel)
            entries = info.get('entries')
            if entries:
                files = []
                for entry in entries:
                    if entry is None:
                        continue
                    fp = ydl.prepare_filename(entry)
                    if not os.path.exists(fp):
                        base = os.path.splitext(fp)[0]
                        found = glob.glob(base + '.*')
                        fp = found[0] if found else None
                    if fp and os.path.exists(fp):
                        files.append((fp, entry.get('title', 'Story')))
                return files, info.get('title', 'Instagram Stories'), True

            # Bitta media (Reels / oddiy video)
            fp = ydl.prepare_filename(info)
            if not os.path.exists(fp):
                base = os.path.splitext(fp)[0]
                found = glob.glob(base + '.*')
                fp = found[0] if found else None

            if fp and os.path.exists(fp):
                return [(fp, info.get('title', 'Instagram Video'))], info.get('title', 'Instagram Video'), False
            return [], "Fayl topilmadi", False

    except Exception as e:
        return [], str(e), False


def is_video_file(path: str) -> bool:
    return path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm'))


def is_image_file(path: str) -> bool:
    return path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))


def cleanup(files: list):
    for fp, _ in files:
        if fp and os.path.exists(fp):
            os.remove(fp)


# --- HANDLERLAR ---
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "👋 Salom, Temur!\n\n"
        "Men quyidagilarni yuklab beraman:\n"
        "🎬 Instagram Reels / Video\n"
        "📖 Instagram Stories\n"
        "🖼 Instagram Post (rasm/video)\n\n"
        "Shunchaki havolani yuboring!"
    )


@dp.message(F.text.contains("instagram.com"))
async def handle_instagram(message: Message):
    url = message.text.strip()
    is_stories = "/stories/" in url

    label = "📖 Stories" if is_stories else "🎬 Video"
    status_msg = await message.answer(f"⏳ {label} yuklanmoqda, kuting...")

    files, title, is_playlist = await download_instagram_media(url)

    if not files:
        await status_msg.edit_text(f"❌ Yuklab bo'lmadi.\nSabab: {title[:200]}")
        return

    try:
        await status_msg.edit_text("📤 Telegramga yuborilmoqda...")

        # Bir nechta fayl — media group qilib yuborish (max 10 ta)
        if len(files) > 1:
            for i in range(0, len(files), 10):
                chunk = files[i:i+10]
                media_group = MediaGroupBuilder(caption=f"📦 {title} ({i+1}–{i+len(chunk)})")
                for fp, ftitle in chunk:
                    if is_video_file(fp):
                        media_group.add_video(FSInputFile(fp))
                    elif is_image_file(fp):
                        media_group.add_photo(FSInputFile(fp))
                await message.answer_media_group(media_group.build())
        else:
            # Bitta fayl
            fp, ftitle = files[0]
            if is_video_file(fp):
                await message.answer_video(
                    FSInputFile(fp),
                    caption=f"🎬 {ftitle}"
                )
            elif is_image_file(fp):
                await message.answer_photo(
                    FSInputFile(fp),
                    caption=f"📸 {ftitle}"
                )
            else:
                await message.answer_document(
                    FSInputFile(fp),
                    caption=f"📎 {ftitle}"
                )

        await status_msg.delete()

    except Exception as send_error:
        await status_msg.edit_text(f"❌ Yuborishda xatolik: {str(send_error)[:200]}")
    finally:
        cleanup(files)


async def main():
    print("✅ Instagram Bot ishga tushdi (Video + Stories)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())