from telebot.types import Message, CallbackQuery
from telebot import TeleBot
from app.services import UserService
from app.db.db_session import SessionLocal
from app.bot.keyboards import get_main_menu, create_cart_keyboard, cart, get_category_by_user, \
    get_inline_keyboard_category, user_pages_by_cart, user_pages_by_product_from_db, create_product_keyboard_from_db, \
    back
from app.services import CategoryService, ProductService, OrderService
from app.logger import logger
import re


def handlers(bot: TeleBot):
    temp_messages = {}
    
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
    
    @bot.callback_query_handler(func=lambda call: call.data == "new_order")
    def handle_start_order(call: CallbackQuery):
        tg_id = call.from_user.id
        
        if tg_id in temp_messages:
            try:
                bot.delete_message(call.message.chat.id, temp_messages[tg_id])
            except:
                pass
            temp_messages.pop(tg_id)
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(f'🏷️ Выберите категорию:',
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=get_inline_keyboard_category(sep='2_2'))
    
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_add_category")
    def back_to_add_category(call: CallbackQuery):
        tg_id = call.from_user.id
        
        if tg_id in user_pages_by_cart:
            user_pages_by_cart.pop(tg_id)
        
        bot.answer_callback_query(call.id, f"Вы вернулись назад")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'🏷️ Выберите категорию:',
            reply_markup=get_inline_keyboard_category('2_2')
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('category2_2'))
    def process_category(call: CallbackQuery):
        category_id = int(call.data.split('2_2')[1])
        user_tg_id = call.from_user.id
        try:
            with SessionLocal() as session:
                category_service = CategoryService(session=session)
                product_service = ProductService(session=session)
                user_service = UserService(session=session)
                
                cart[user_tg_id] = {}  # Добавляем юзера в корзину
                products = product_service.get_products_by_category(category_id)  # Список продуктов
                category = category_service.get_category_by_id(category_id)
                
                for prod in products:  # Добавляем продукты в корзину юзера user.id
                    cart[user_tg_id][prod.name] = {
                        'id': prod.id,
                        'target': prod.target_quantity,
                        'actual': 0,
                        'category': category.name,
                    }
                keyboard = create_cart_keyboard(user_tg_id, sep="_")
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="📦 Выберите товар:\n"
                         "(При нажатии на товар фактическое количество увеличивается на один)",
                    reply_markup=keyboard)
                bot.answer_callback_query(call.id,
                                          text=f"Выбрана категория {category.name}")
        except Exception as e:
            logger.error(f'Error started order {e}')
            bot.send_message(chat_id=call.message.chat.id,
                             text='Произошла ошибка при выборе категории, повторите попытку позже.')
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
    def show_product_quantity(call: CallbackQuery):
        product_id = int(call.data.split('_')[1])
        user_tg_id = call.from_user.id
        
        with SessionLocal() as session:
            user_service = UserService(session=session)
            product_service = ProductService(session=session)
            product = product_service.get_product_by_id(product_id)
            
            user = user_service.get_user_by_tg_id(user_tg_id)  # Получаем юзера
            cart[user_tg_id][product.name]['actual'] += 1  # Увеличиваем актуальное количество на 1
            if cart[user_tg_id][product.name]["actual"] > cart[user_tg_id][product.name]['target']:
                cart[user_tg_id][product.name]["actual"] = 0
            
            keyboard = create_cart_keyboard(user_tg_id, sep="_")  # Формируем новую клавиатуру
            
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )  # Меняем клавиатуру на новую
            bot.answer_callback_query(call.id,
                                      text=f'{product.name} + 1')  # Отправляем юзеру текст, что товар увеличен на 1
    
    @bot.callback_query_handler(func=lambda call: call.data == 'finished_order')  # Ловим колл о завершении заказа
    def add_order_in_bd(call: CallbackQuery):
        user_tg_id = call.from_user.id
        
        with SessionLocal() as session:
            order_service = OrderService(session=session)
            user_service = UserService(session=session)
            category_service = CategoryService(session=session)
            
            user_id = user_service.get_user_by_tg_id(call.from_user.id).id
            category_name = get_category_by_user(user_tg_id)  # Получаем категорию нэйм
            category_id = category_service.get_category_by_name(category_name).id  # Получаем ид категории
            items = []  # собираем все айтемы из корзины юзера
            for product, data in cart[user_tg_id].items():
                items.append({
                    'product_id': data['id'],
                    'actual_quantity': data['actual']
                })
            new_order = order_service.create_order(user_id=user_id, category_id=category_id, items=items)  # Новый заказ
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=f'📌 Главное меню',
                                  reply_markup=get_main_menu(user_tg_id),
                                  )
            bot.answer_callback_query(call.id, text=f'Заказ №{new_order["order_id"]} успешно сформирован',
                                      show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data in ["prev_page", "next_page"])
    def paginate_cart(call: CallbackQuery):
        user_tg_id = call.from_user.id
        try:
            with SessionLocal() as session:
                user_service = UserService(session=session)
                if user_tg_id not in user_pages_by_cart:
                    return
                if call.data == "prev_page":
                    user_pages_by_cart[user_tg_id]["current_page"] -= 1
                    bot.answer_callback_query(call.id, f"Prev page")
                elif call.data == "next_page":
                    user_pages_by_cart[user_tg_id]["current_page"] += 1
                    bot.answer_callback_query(call.id, f"Next page")
                
                kb = create_cart_keyboard(user_tg_id, sep="_")
                
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    reply_markup=kb
                )
        except Exception as e:
            logger.error(f"Error {e}")
    
    @bot.callback_query_handler(func=lambda call: call.data == "last_order")
    def get_last_order(call: CallbackQuery):
        bot.answer_callback_query(call.id)
        tg_id = call.from_user.id
        
        if tg_id in temp_messages:
            try:
                bot.delete_message(call.message.chat.id, temp_messages[tg_id])
            except:
                pass
            temp_messages.pop(tg_id)
        
        with SessionLocal() as session:
            user_service = UserService(session=session)
            order_service = OrderService(session=session)
            
            user = user_service.get_user_by_tg_id(tg_id)
            last_order = order_service.get_last_order(user.id)
            if last_order:
                order_id = last_order.id
                order = order_service.get_order_report(order_id)
                day = last_order.created_at
                msg_text = (f'🆔 Заказ №{order_id} (от {str(day)[:10]})\n'
                            f'{"-" * 33}\n')
                for i in order['items']:
                    msg_text += f"📦 {i['product_name']}\n"
                    msg_text += f"Заказ: {i['to_order']} шт\n"
                    # msg_text += f"Факт: {i['actual_quantity']} шт\n"
                
                msg = bot.send_message(call.message.chat.id, text=msg_text)
                temp_messages[call.from_user.id] = msg.message_id
    
    @bot.callback_query_handler(func=lambda call: call.data == "add_category")
    def add_category(call: CallbackQuery):
        tg_id = call.from_user.id
        bot.answer_callback_query(call.id)
        
        if tg_id in temp_messages:
            try:
                bot.delete_message(call.message.chat.id, temp_messages[tg_id])
            except:
                pass
            temp_messages.pop(tg_id)
        
        msg = bot.send_message(call.message.chat.id, f'Введите название категории 🏷️:\n'
                                                     f'Имя должно содержать только буквы/цифры (минимум 3 символа)', )
        temp_messages[tg_id] = msg.message_id
        
        bot.register_next_step_handler(msg, check_to_correct_name_category)
    
    def check_to_correct_name_category(message: Message):
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
        
        # Проверка формата имени
        correct_msg = bool(re.match(r'^[\wА-Яа-я\s-]{3,}$', msg_text))
        
        try:
            if correct_msg:
                with SessionLocal() as session:
                    category_service = CategoryService(session=session)
                    
                    # 🔹 Проверка: есть ли категория с таким именем
                    existing = category_service.get_category_by_name(msg_text)
                    if existing:
                        bot.delete_message(message.chat.id, message.message_id)
                        msg = bot.send_message(
                            chat_id,
                            f'⚠️ Категория *{msg_text}* уже существует.\nВведите другое имя:',
                            parse_mode="Markdown"
                        )
                        bot.register_next_step_handler(msg, check_to_correct_name_category)
                    else:
                        new_category = category_service.create_category(msg_text)
                        if new_category:
                            bot.delete_message(message.chat.id, message.message_id)
                            msg = bot.send_message(chat_id, f'✅ Категория *{msg_text}* создана', parse_mode="Markdown")
                        else:
                            msg = bot.send_message(chat_id, f'❌ Ошибка при создании категории')
            else:
                bot.delete_message(message.chat.id, message.message_id)
                msg = bot.send_message(
                    chat_id,
                    f'⚠️ Имя должно содержать только буквы/цифры (минимум 3 символа).\nПопробуйте снова:'
                )
                bot.register_next_step_handler(msg, check_to_correct_name_category)
            
            # Сохраняем ID нового сообщения
            temp_messages[tg_id] = msg.message_id
        
        except Exception as e:
            logger.error(e)
            msg = bot.send_message(chat_id, f'⚠️ Ошибка при создании категории')
            temp_messages[tg_id] = msg.message_id
    
    @bot.callback_query_handler(func=lambda call: call.data == "delete_category")
    def delete_category(call: CallbackQuery):
        tg_id = call.from_user.id
        
        if tg_id in temp_messages:
            try:
                bot.delete_message(call.message.chat.id, temp_messages[tg_id])
            except:
                pass
            temp_messages.pop(tg_id)
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
            temp_messages[tg_id] = msg.message_id
    
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
    
    @bot.callback_query_handler(func=lambda call: call.data == "back")
    def back_to_menu_with_info(call: CallbackQuery):
        tg_id = call.from_user.id
        bot.answer_callback_query(call.id)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="📌 Главное меню",
                              reply_markup=get_main_menu(tg_id))
