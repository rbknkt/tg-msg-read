from aiogram import Router, Bot
from aiogram.types import Message, BusinessMessagesDeleted
from aiogram.enums import ParseMode

from config import ADMIN_ID
from utils import message_cache, get_user_identifier

router = Router()

@router.business_message()
async def handle_new_business_message(message: Message):
    message_cache[message.message_id] = message

@router.edited_business_message()
async def handle_edited_business_message(message: Message, bot: Bot):
    if message.from_user and message.from_user.id == ADMIN_ID:
        message_cache[message.message_id] = message
        return
    original = message_cache.get(message.message_id)
    old_text = original.text or original.caption if original else "НЕТ В КЭШЕ"
    new_text = message.text or message.caption or "МЕДИА БЕЗ ТЕКСТА"
    if old_text == new_text: 
        return
    user_ident = get_user_identifier(message.from_user)
    log_text = (
        f"✏️ **ИЗМЕНЕНО СООБЩЕНИЕ**\n"
        f"В ЧАТЕ {user_ident}\n\n"
        f"❌ **Было:**\n{old_text}\n\n"
        f"✅ **Стало:**\n{new_text}"
    )
    await bot.send_message(ADMIN_ID, log_text, parse_mode=ParseMode.MARKDOWN)
    message_cache[message.message_id] = message

@router.deleted_business_messages()
async def handle_deleted_business_messages(deleted: BusinessMessagesDeleted, bot: Bot):
    chat_title = deleted.chat.full_name or deleted.chat.title or "Неизвестный чат"
    for msg_id in deleted.message_ids:
        if msg_id in message_cache:
            original = message_cache[msg_id]
            if original.from_user and original.from_user.id == ADMIN_ID:
                continue
            user_ident = get_user_identifier(original.from_user)
            log_header = f"🗑 **УДАЛЕНО СООБЩЕНИЕ**\nВ ЧАТЕ {user_ident}\n\n"
            if original.text:
                await bot.send_message(ADMIN_ID, f"{log_header}📄 **Текст:**\n{original.text}", parse_mode=ParseMode.MARKDOWN)
                continue
            caption_text = original.caption if original.caption else ""
            full_caption = f"{log_header}📄 **Подпись:**\n{caption_text}" if caption_text else log_header
            try:
                if original.photo:
                    await bot.send_photo(ADMIN_ID, original.photo[-1].file_id, caption=full_caption, parse_mode=ParseMode.MARKDOWN)
                elif original.video:
                    await bot.send_video(ADMIN_ID, original.video.file_id, caption=full_caption, parse_mode=ParseMode.MARKDOWN)
                elif original.document:
                    await bot.send_document(ADMIN_ID, original.document.file_id, caption=full_caption, parse_mode=ParseMode.MARKDOWN)
                elif original.sticker:
                    await bot.send_message(ADMIN_ID, log_header + "🎭 УДАЛЕН СТИКЕР")
                    await bot.send_sticker(ADMIN_ID, original.sticker.file_id)
                elif original.voice:
                    try:
                        await bot.send_voice(ADMIN_ID, original.voice.file_id, caption=full_caption, parse_mode=ParseMode.MARKDOWN)
                    except Exception as e:
                        if "VOICE_MESSAGES_FORBIDDEN" in str(e):
                            await bot.send_document(ADMIN_ID, original.voice.file_id, caption=full_caption + "\n*(Отправлено файлом из-за настроек приватности)*", parse_mode=ParseMode.MARKDOWN)
                        else:
                            raise e
                elif original.video_note:
                    await bot.send_message(ADMIN_ID, log_header + "🎥 УДАЛЕН КРУЖОЧЕК", parse_mode=ParseMode.MARKDOWN)
                    try:
                        await bot.send_video_note(ADMIN_ID, original.video_note.file_id)
                    except Exception as e:
                        if "VOICE_MESSAGES_FORBIDDEN" in str(e):
                            await bot.send_document(ADMIN_ID, original.video_note.file_id, caption="*(Отправлено файлом из-за настроек приватности)*", parse_mode=ParseMode.MARKDOWN)
                        else:
                            raise e
                else:
                    await bot.send_message(ADMIN_ID, full_caption + "\n*[Доступен только текст]*", parse_mode=ParseMode.MARKDOWN)
            
            except Exception as e:
                error_msg = f"{full_caption}\n\n⚠️ **Файл недоступен** (Telegram удалил его с серверов).\n*(Ошибка: {e})*"
                await bot.send_message(ADMIN_ID, error_msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(ADMIN_ID, f"🗑 **Удалено неизвестное сообщение** в чате {chat_title}\n\n*(В кэше бота его нет)*")