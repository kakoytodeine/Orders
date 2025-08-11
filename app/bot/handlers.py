from telebot.types import Message, CallbackQuery
from telebot import TeleBot
from app.services import UserService
from app.db.db_session import SessionLocal
from app.bot.keyboards import get_main_menu_for_user, category_menu, create_cart_keyboard, cart, get_category_by_user, \
    get_main_menu_for_admin
from app.services import CategoryService, ProductService, OrderService
from app.logger import logger


def handlers(bot: TeleBot):
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
                    bot.send_message(
                        chat_id=message.chat.id,
                        text=f"Добро пожаловать, администратор {first_name}!",
                        reply_markup=get_main_menu_for_admin()
                    )
                else:
                    bot.send_message(
                        chat_id=message.chat.id,
                        text=f"Здравствуйте, {first_name}!",
                        reply_markup=get_main_menu_for_user()
                    )
        
        except Exception as e:
            logger.error(f"Ошибка при обработке команды /start: {e}")
            bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
    
    @bot.message_handler(func=lambda message: message.text == "📦 Начать заказ")
    def handle_start_order(message):
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, f'🏷️ Выберите категорию:', reply_markup=category_menu())
        bot.register_next_step_handler(message, process_category)
    
    def process_category(message: Message):
        category = message.text
        user_tg_id = message.from_user.id
        try:
            with SessionLocal() as session:
                category_service = CategoryService(session=session)
                product_service = ProductService(session=session)
                user_service = UserService(session=session)
                
                user = user_service.get_user_by_tg_id(user_tg_id)
                cart[user.id] = {}  # Добавляем юзера в корзину
                categories = {c.name: c.id for c in category_service.get_all_categories()}  # Список категорий
                if category in categories:
                    id_category = categories[category]
                    products = product_service.get_products_by_category(id_category)  # Список продуктов
                    
                    for prod in products:  # Добавляем продукты в корзину юзера user.id
                        cart[user.id][prod.name] = {
                            'id': prod.id,
                            'target': prod.target_quantity,
                            'actual': 0,
                            'category': category,
                        }
                    keyboard = create_cart_keyboard(user.id)
                    bot.send_message(message.chat.id, 'Выберите товар для указания количества', reply_markup=keyboard)
        except Exception as e:
            logger.error(f'Error started order {e}')
            bot.send_message(message.chat.id, text=f'Ошибка при начале заказа')
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
    def show_product_quantity(call: CallbackQuery):
        product_id = int(call.data.split('_')[1])
        user_tg_id = call.from_user.id
        
        with SessionLocal() as session:
            user_service = UserService(session=session)
            product_service = ProductService(session=session)
            product = product_service.get_product_by_id(product_id)
            
            user = user_service.get_user_by_tg_id(user_tg_id)  # Получаем юзера
            cart[user.id][product.name]['actual'] += 1  # Увеличиваем актуальное количество на 1
            
            keyboard = create_cart_keyboard(user.id)  # Формируем новую клавиатуру
            
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )  # Меняем клавиатуру на новую
            bot.answer_callback_query(call.id,
                                      text=f'{product.name} + 1')  # Отправляем юзеру текст, что товар увеличен на 1
    
    @bot.callback_query_handler(func=lambda call: call.data == 'finished_order')  # Ловим колл о завершении заказа
    def add_order_in_bd(call: CallbackQuery):
        bot.answer_callback_query(call.id, text=f'🔄 Заказ формируется')
        
        with SessionLocal() as session:
            order_service = OrderService(session=session)
            user_service = UserService(session=session)
            category_service = CategoryService(session=session)
            
            user_id = user_service.get_user_by_tg_id(call.from_user.id).id
            category_name = get_category_by_user(user_id)  # Получаем категорию нэйм
            category_id = category_service.get_category_by_name(category_name).id  # Получаем ид категории
            items = []  # собираем все айтемы из корзины юзера
            for product, data in cart[user_id].items():
                items.append({
                    'product_id': data['id'],
                    'actual_quantity': data['actual']
                })
            new_order = order_service.create_order(user_id=user_id, category_id=category_id, items=items)  # Новый заказ
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text=f'Заказ №{new_order["order_id"]} успешно сформирован')
    
    @bot.message_handler(func=lambda msg: msg.text == "⬅ Назад")
    def go_back_to_main_menu(message: Message):
        bot.delete_message(message.chat.id, message.message_id)
        user_tg_id = message.from_user.id
        try:
            with SessionLocal() as session:
                user_service = UserService(session=session)
                user = user_service.get_user_by_tg_id(user_tg_id)
                if user.role == 'admin':
                    bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_menu_for_admin())
                else:
                    bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_menu_for_user())
        except Exception as e:
            logger.error(f'Error back to main_menu')
            bot.send_message(message.chat.id, f'Ошибка при возврате в глв меню')
    
    @bot.message_handler(func=lambda msg: msg.text == "🕘 Последний заказ")
    def get_last_order(message: Message):
        user_tg_id = message.from_user.id
        
        with SessionLocal() as session:
            user_service = UserService(session=session)
            order_service = OrderService(session=session)
            
            user_id = user_service.get_user_by_tg_id(user_tg_id).id
            last_order = order_service.get_last_order(user_id=user_id)
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
                
                bot.send_message(message.chat.id, text=msg_text)
    
    @bot.message_handler(func=lambda message: message.text == "ℹ️ Инфо")
    def handler_info(message):
        info_text = (
            "🤖*Версия бота:* 1.0.0\n"
            "💡Просто выбирай категорию, вводи остатки — и бот сформирует заказ за тебя!\n"
        )
        bot.send_message(message.chat.id, info_text, parse_mode='Markdown')
