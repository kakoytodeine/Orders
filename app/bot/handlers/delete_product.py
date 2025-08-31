from telebot.types import CallbackQuery

from app.bot.bot_instance import bot
from app.bot.keyboards import get_inline_keyboard_category, create_product_keyboard_from_db, \
    user_pages_by_product_from_db, temp_messages, get_main_menu
from app.db.db_session import SessionLocal
from app.logger import logger
from app.services import ProductService


@bot.callback_query_handler(func=lambda call: call.data == "delete_product")
def start_delete_product(call: CallbackQuery):
    bot.answer_callback_query(call.id, "Меню удаления категории")
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="Выберите категорию",
                          reply_markup=get_inline_keyboard_category(sep="4_4"))


@bot.callback_query_handler(func=lambda call: call.data.startswith("category4_4"))
def select_product_by_category(call: CallbackQuery):
    category_id = int(call.data.split("4_4")[1])
    bot.answer_callback_query(call.id)
    
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=f"Выберите товар для удаления",
                          reply_markup=create_product_keyboard_from_db(category_id, call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "back_to_delete_category")
def back_to_delete_category(call: CallbackQuery):
    tg_id = call.from_user.id
    
    if tg_id in user_pages_by_product_from_db:
        user_pages_by_product_from_db.pop(tg_id)
    
    bot.answer_callback_query(call.id, f"Вы вернулись назад")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'🏷️ Выберите категорию:',
        reply_markup=get_inline_keyboard_category('4_4'))


@bot.callback_query_handler(func=lambda call: call.data == "back_to_main_menu")
def back_to_main_menu(call: CallbackQuery):
    tg_id = call.from_user.id
    chat_id = call.message.chat.id
    
    # Удаляем предыдущее временное сообщение
    if tg_id in temp_messages:
        try:
            bot.delete_message(chat_id, temp_messages[tg_id])
        except:
            pass
        temp_messages.pop(tg_id)
    bot.answer_callback_query(call.id, "Вы вернулись в Главное меню")
    tg_id = call.from_user.id
    bot.edit_message_text("📌 Главное меню",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=get_main_menu(tg_id))


@bot.callback_query_handler(func=lambda call: call.data in ["prev_page_product", "next_page_product"])
def paginate_product_from_db(call: CallbackQuery):
    tg_id = call.from_user.id
    try:
        if tg_id not in user_pages_by_product_from_db:
            return
        category_id = user_pages_by_product_from_db[tg_id]["category_id"]
        if call.data == "prev_page_product":
            user_pages_by_product_from_db[tg_id]["current_page"] -= 1
            bot.answer_callback_query(call.id, f"Prev page")
        elif call.data == "next_page_product":
            user_pages_by_product_from_db[tg_id]["current_page"] += 1
            bot.answer_callback_query(call.id, f"Next page")
        
        kb = create_product_keyboard_from_db(category_id, tg_id)
        
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Error {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("productdelete_"))
def delete_product_by_category(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    tg_id = call.from_user.id
    
    try:
        with SessionLocal() as session:
            product_service = ProductService(session=session)
            
            product = product_service.get_product_by_id(product_id)
            if not product:
                bot.answer_callback_query(call.id, "Продукт не найден")
                return
            
            category_id = product.category_id
            success = product_service.delete_product_for_admin(product_id=product_id)
            if success:
                bot.answer_callback_query(call.id, f"✅ Продукт {product.name} удален", show_alert=True)
                
                if tg_id in user_pages_by_product_from_db:
                    user_pages_by_product_from_db.pop(tg_id)
                kb = create_product_keyboard_from_db(category_id, tg_id)
                try:
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=kb
                    )
                except Exception as e:
                    logger.warning(f"Skip edit_message_reply_markup: {e}")
            else:
                bot.answer_callback_query(call.id, "❌ Ошибка при удалении продукта")
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка")
