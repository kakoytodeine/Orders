from telebot.types import CallbackQuery

from app.bot.bot_instance import bot
from app.bot.keyboards import temp_messages, back


@bot.callback_query_handler(func=lambda call: call.data == "info")
def handler_info(call: CallbackQuery):
    tg_id = call.from_user.id
    
    if tg_id in temp_messages:
        try:
            bot.delete_message(call.message.chat.id, temp_messages[tg_id])
        except:
            pass
        temp_messages.pop(tg_id)
    
    bot.answer_callback_query(call.id)
    info_text = (
        "🤖*Версия бота:* 1.0.0\n"
        "💡Просто выбирай категорию, вводи остатки — и бот сформирует заказ за тебя!\n"
    )
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=info_text,
                          parse_mode='Markdown',
                          reply_markup=back())
