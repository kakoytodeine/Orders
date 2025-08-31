from telebot.types import CallbackQuery, Message

from app.bot.bot_instance import bot
from app.bot.keyboards import temp_messages
from app.bot.notification import send_notification


@bot.callback_query_handler(func=lambda call: call.data == "add_notification")
def create_new_task(call: CallbackQuery):
    tg_id = call.from_user.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"⏰Напишите уведомление и оно отправится всем пользователям")
    temp_messages[tg_id] = msg.message_id
    bot.register_next_step_handler(msg, create_notification)

    
def create_notification(message: Message):
    msg_text = message.text.strip()
    send_notification(msg_text)
    
    tg_id = message.from_user.id
    chat_id = message.chat.id
    if tg_id in temp_messages:
        try:
            bot.delete_message(chat_id, temp_messages[tg_id])
        except:
            pass
        temp_messages.pop(tg_id)
    