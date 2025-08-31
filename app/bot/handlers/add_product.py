import re

from telebot.types import CallbackQuery, Message

from app.bot.bot_instance import bot
from app.bot.keyboards import temp_messages, get_inline_keyboard_category
from app.db.db_session import SessionLocal
from app.logger import logger
from app.services import CategoryService, ProductService


@bot.callback_query_handler(func=lambda call: call.data == "add_product")
def add_product_by_category(call: CallbackQuery):
    tg_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if tg_id in temp_messages:
        try:
            bot.delete_message(call.message.chat.id, temp_messages[tg_id])
        except:
            pass
        temp_messages.pop(tg_id)
    
    bot.edit_message_text(chat_id=chat_id,
                          message_id=call.message.message_id,
                          text="🏷️ Выбери категорию куда добавить товар:",
                          reply_markup=get_inline_keyboard_category("3_3"))


@bot.callback_query_handler(func=lambda call: call.data.startswith("category3_3"))
def process_selected_category(call: CallbackQuery):
    category_id = int(call.data.split("3_3")[1])
    tg_id = call.from_user.id
    bot.answer_callback_query(call.id)
    
    msg = bot.send_message(call.message.chat.id, f'Введите название продукта📦\n'
                                                 f'Название продукта + пробел + целевое количество (1-2 цифры). Например: Winston 10', )
    temp_messages[tg_id] = msg.message_id
    
    bot.register_next_step_handler(msg, check_to_correct_name_product, category_id)


def check_to_correct_name_product(message: Message, category_id: int):
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
    
    # Регулярное выражение: имя + пробелы + 1-2 цифры в конце
    pattern = r'^(?P<name>[\wА-Яа-я\s-]{2,}?)\s*(?P<qty>\d{1,2})$'
    match = re.match(pattern, msg_text)
    
    if not match:
        bot.delete_message(message.chat.id, message.message_id)
        msg = bot.send_message(
            chat_id,
            "⚠️ Введите корректно: Название продукта + пробел + целевое количество (1-2 цифры). Например: Winston 10"
        )
        bot.register_next_step_handler(msg, check_to_correct_name_product, category_id)
        temp_messages[tg_id] = msg.message_id
        return
    
    # Извлекаем данные
    name_product = match.group('name').strip()
    target_quantity = int(match.group('qty'))
    
    try:
        with SessionLocal() as session:
            category_service = CategoryService(session=session)
            product_service = ProductService(session=session)
            
            category = category_service.get_category_by_id(category_id)
            if not category:
                bot.send_message(chat_id, "❌ Ошибка: категория не найдена.")
                return
            category_name = category.name
            
            # Проверка: есть ли продукт с таким именем
            existing = product_service.get_product_by_name_in_category(product_name=name_product,
                                                                       category_id=category_id)
            if existing:
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(
                    chat_id,
                    f'⚠️ Продукт *{name_product}* уже существует.\nВведите другое имя:',
                    parse_mode="Markdown"
                )
                bot.register_next_step_handler(msg, check_to_correct_name_product, category_id)
                temp_messages[tg_id] = msg.message_id
                return
            
            # Создание нового продукта
            new_product = product_service.create_product_for_admin(name_product, target_quantity, category_id)
            if new_product:
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(
                    chat_id,
                    f'✅ Продукт *{name_product}* добавлен в категорию {category_name}',
                    parse_mode="Markdown"
                )
            
            else:
                msg = bot.send_message(chat_id, f'❌ Ошибка при создании продукта')
            
            temp_messages[tg_id] = msg.message_id
    
    except Exception as e:
        logger.error(e)
        msg = bot.send_message(chat_id, f'⚠️ Ошибка при создании продукта')
        temp_messages[tg_id] = msg.message_id
