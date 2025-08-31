from telebot.types import CallbackQuery

from app.bot.bot_instance import bot
from app.bot.keyboards import get_inline_keyboard_category, user_pages_by_cart, cart, create_cart_keyboard, \
    get_category_by_user, get_main_menu, temp_messages
from app.db.db_session import SessionLocal
from app.services import CategoryService, ProductService, UserService, OrderService
from app.logger import logger


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
        product_service = ProductService(session=session)
        product = product_service.get_product_by_id(product_id)
        
        current_markup = call.message.reply_markup

        
        if cart[user_tg_id][product.name]["target"] > 0:
            # Увеличиваем актуальное количество на 1
            cart[user_tg_id][product.name]['actual'] += 1
            
            if cart[user_tg_id][product.name]["actual"] > cart[user_tg_id][product.name]['target']:
                cart[user_tg_id][product.name]["actual"] = 0
                bot.answer_callback_query(call.id,
                                          text=f"Превышен лимит по продукту {product.name}, Количество сброшено")
            else:
                bot.answer_callback_query(call.id,
                                          text=f'{product.name} + 1 Факт: {cart[user_tg_id][product.name]["actual"]}')
        else:
            bot.answer_callback_query(call.id,
                                      text=f"Продукт {product.name} редактируется вручную. Невозможно изменить количество.",
                                      show_alert=True)
    
        
        # Формируем новую клавиатуру
        keyboard = create_cart_keyboard(user_tg_id, sep="_")
        
        # Меняем клавиатуру на новую
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )

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