from telebot.types import CallbackQuery

from app.bot.bot_instance import bot
from app.bot.notification import send_notification


@bot.callback_query_handler(func=lambda call: call.data == "add_task")
def create_new_task(call: CallbackQuery):
    send_notification("Hello Bro")