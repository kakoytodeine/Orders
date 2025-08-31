from telebot.types import CallbackQuery

from app.bot.bot_instance import bot
from app.bot.keyboards import get_main_menu


@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_to_menu_with_info(call: CallbackQuery):
    tg_id = call.from_user.id
    bot.answer_callback_query(call.id)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="📌 Главное меню",
                          reply_markup=get_main_menu(tg_id))