import re
from telebot.types import CallbackQuery, Message

from app.bot.bot_instance import bot
from app.bot.keyboards import get_main_menu
from app.db.db_session import SessionLocal
from app.services import CategoryService
from app.logger import logger
from app.bot.temp_message import _clear_temp_message, _save_temp_message


@bot.callback_query_handler(func=lambda call: call.data == "add_category")
def add_category(call: CallbackQuery):
    tg_id = call.from_user.id
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    # Удаляем старое temp_message
    _clear_temp_message(chat_id, tg_id)
    
    msg = bot.send_message(
        chat_id,
        'Введите название категории 🏷️:\nИмя должно содержать только буквы/цифры (минимум 3 символа)'
    )
    _save_temp_message(tg_id, msg.message_id)
    
    bot.register_next_step_handler(msg, check_to_correct_name_category)


def check_to_correct_name_category(message: Message):
    tg_id = message.from_user.id
    chat_id = message.chat.id
    msg_text = message.text.strip()
    
    # --- Удаляем предыдущий temp_message ---
    _clear_temp_message(chat_id, tg_id)
    
    # Проверка формата имени
    correct_msg = bool(re.match(r'^[\wА-Яа-я\s-]{3,}$', msg_text))
    
    try:
        with SessionLocal() as session:
            category_service = CategoryService(session=session)
            
            if correct_msg:
                # Проверка на существующую категорию
                existing = category_service.get_category_by_name(msg_text)
                if existing:
                    msg = bot.send_message(
                        chat_id,
                        f'⚠️ Категория *{msg_text}* уже существует.\nВведите другое имя:',
                        parse_mode="Markdown",
                    )
                    _save_temp_message(tg_id, msg.message_id)
                    
                    
                    
                    bot.register_next_step_handler(msg, check_to_correct_name_category)
                else:
                    new_category = category_service.create_category(msg_text)
                    if new_category:
                        msg = bot.send_message(
                            chat_id,
                            f'✅ Категория *{msg_text}* создана',
                            parse_mode="Markdown"
                        )
                        _save_temp_message(tg_id, msg.message_id)
                        
                        menu_msg = bot.send_message(
                            chat_id,
                            "📌 Главное меню",
                            reply_markup=get_main_menu(tg_id)
                        )
                        _save_temp_message(tg_id, menu_msg.message_id)
                    else:
                        msg = bot.send_message(chat_id, '❌ Ошибка при создании категории')
                        _save_temp_message(tg_id, msg.message_id)
            else:
                msg = bot.send_message(
                    chat_id,
                    '⚠️ Имя должно содержать только буквы/цифры (минимум 3 символа).\nПопробуйте снова:'
                )
                _save_temp_message(tg_id, msg.message_id)
                bot.register_next_step_handler(msg, check_to_correct_name_category)
    except Exception as e:
        logger.error(e)
        msg = bot.send_message(chat_id, '⚠️ Ошибка при создании категории')
        _save_temp_message(tg_id, msg.message_id)
