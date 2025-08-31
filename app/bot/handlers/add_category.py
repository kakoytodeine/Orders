import re

from telebot.types import CallbackQuery, Message

from app.bot.bot_instance import bot
from app.bot.keyboards import temp_messages
from app.db.db_session import SessionLocal
from app.services import CategoryService
from app.logger import logger


@bot.callback_query_handler(func=lambda call: call.data == "add_category")
def add_category(call: CallbackQuery):
    tg_id = call.from_user.id
    bot.answer_callback_query(call.id)
    
    if tg_id in temp_messages:
        try:
            bot.delete_message(call.message.chat.id, temp_messages[tg_id])
        except:
            pass
        temp_messages.pop(tg_id)
    
    msg = bot.send_message(call.message.chat.id, f'Введите название категории 🏷️:\n'
                                                 f'Имя должно содержать только буквы/цифры (минимум 3 символа)', )
    temp_messages[tg_id] = msg.message_id
    
    bot.register_next_step_handler(msg, check_to_correct_name_category)


def check_to_correct_name_category(message: Message):
    tg_id = message.from_user.id
    chat_id = message.chat.id
    msg_text = message.text.strip()
    
    # Удаляем предыдущее временное сообщение
    if tg_id in temp_messages:
        try:
            bot.delete_message(chat_id, temp_messages[tg_id])
        except:
            pass
        temp_messages.pop(tg_id)
    
    # Проверка формата имени
    correct_msg = bool(re.match(r'^[\wА-Яа-я\s-]{3,}$', msg_text))
    
    try:
        if correct_msg:
            with SessionLocal() as session:
                category_service = CategoryService(session=session)
                
                # 🔹 Проверка: есть ли категория с таким именем
                existing = category_service.get_category_by_name(msg_text)
                if existing:
                    bot.delete_message(message.chat.id, message.message_id)
                    msg = bot.send_message(
                        chat_id,
                        f'⚠️ Категория *{msg_text}* уже существует.\nВведите другое имя:',
                        parse_mode="Markdown"
                    )
                    bot.register_next_step_handler(msg, check_to_correct_name_category)
                else:
                    new_category = category_service.create_category(msg_text)
                    if new_category:
                        bot.delete_message(message.chat.id, message.message_id)
                        msg = bot.send_message(chat_id, f'✅ Категория *{msg_text}* создана', parse_mode="Markdown")
                    else:
                        msg = bot.send_message(chat_id, f'❌ Ошибка при создании категории')
        else:
            bot.delete_message(message.chat.id, message.message_id)
            msg = bot.send_message(
                chat_id,
                f'⚠️ Имя должно содержать только буквы/цифры (минимум 3 символа).\nПопробуйте снова:'
            )
            bot.register_next_step_handler(msg, check_to_correct_name_category)
        
        # Сохраняем ID нового сообщения
        temp_messages[tg_id] = msg.message_id
    
    except Exception as e:
        logger.error(e)
        msg = bot.send_message(chat_id, f'⚠️ Ошибка при создании категории')
        temp_messages[tg_id] = msg.message_id
