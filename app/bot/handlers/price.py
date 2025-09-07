from telebot.types import CallbackQuery

from app.bot.bot_instance import bot
from app.bot.keyboards import back


@bot.callback_query_handler(func=lambda call: call.data == "actual_price")
def get_actual_price(call: CallbackQuery):
    bot.answer_callback_query(call.id)
    
    price_ = {
        "MAD": 400,
        "ICE COOL": 450,
        "LYFT": 400,
        "IRON EAGLE": 450,
        "ARQA": 450,
        "KASTA": 450,
        "ODEN'S 13gr": 550
    }
    
    msg_text = "\n".join(f"{name} - {pr}" for name, pr in price_.items())
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=msg_text,
        reply_markup=back()
    )
