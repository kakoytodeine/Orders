from telebot.types import CallbackQuery

from app.bot.bot_instance import bot
from app.bot.keyboards import  get_inline_keyboard_category
from app.db.db_session import SessionLocal
from app.services import CategoryService
from app.logger import logger


@bot.callback_query_handler(func=lambda call: call.data == "delete_category")
def delete_category(call: CallbackQuery):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=f"Выберите категорию для удаления:",
                          reply_markup=get_inline_keyboard_category(sep="1_1"))


@bot.callback_query_handler(func=lambda call: call.data.startswith('category1_1'))
def handle_category_callback(call: CallbackQuery):
    category_id = int(call.data.split('1_1')[1])
    tg_id = call.from_user.id
    
    try:
        with SessionLocal() as session:
            category_service = CategoryService(session=session)
            category = category_service.get_category_by_id(category_id)
            if category:
                category_service.delete_category(category_id)
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text=f"Выберите категорию для удаления",
                                      reply_markup=get_inline_keyboard_category(sep="_"))
                bot.answer_callback_query(call.id, text=f"Категория удалена {category.name} успешно",
                                          show_alert=True)
            else:
                logger.error(f'Error delete category')
                bot.edit_message_text(chat_id=call.message.chat.id,
                                      message_id=call.message.message_id,
                                      text=f"Выберите категорию для удаления",
                                      reply_markup=get_inline_keyboard_category(sep="_"))
                bot.answer_callback_query(call.id, f"Ошибка при удалении {category.name}, повторите попытку")
    except Exception as e:
        logger.error(f'Error delete category {e}')
        msg = bot.send_message(chat_id=call.message.chat.id,
                               text='Произошла ошибка при удалении категории, повторите попытку позже.')