from telebot.types import CallbackQuery, Message

from app.bot.bot_instance import bot
from app.bot.notification import send_notification


@bot.callback_query_handler(func=lambda call: call.data == "add_notification")
def create_new_task(call: CallbackQuery):
    tg_id = call.from_user.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"⏰Напишите уведомление и оно отправится всем пользователям")
    bot.register_next_step_handler(msg, create_notification)

    
def create_notification(message: Message):
    msg_text = message.text.strip()
    send_notification(msg_text)
    