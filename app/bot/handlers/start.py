from telebot.types import Message

from app.bot.bot_instance import bot
from app.bot.keyboards import get_main_menu
from app.db.db_session import SessionLocal
from app.services import UserService
from app.logger import logger


@bot.message_handler(commands=['start'])
def welcome(message: Message):
    tg_user = message.from_user
    tg_id = tg_user.id
    username = tg_user.username or ""
    first_name = tg_user.first_name or "Пользователь"
    
    try:
        with SessionLocal() as session:
            user_service = UserService(session)
            user = user_service.create_user(tg_id, username, first_name)
            
            role = user.role if user and user.role else "user"
            
            if role == "admin":
                msg = bot.send_message(
                    chat_id=message.chat.id,
                    text=f"Добро пожаловать, администратор 👑 {first_name}!",
                    reply_markup=get_main_menu(tg_id)
                )
            
            else:
                msg = bot.send_message(
                    chat_id=message.chat.id,
                    text=f"Здравствуйте, {first_name} 🙋!",
                    reply_markup=get_main_menu(tg_id)
                )
    
    
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")