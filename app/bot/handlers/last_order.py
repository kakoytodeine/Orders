from telebot.types import CallbackQuery
from app.bot.bot_instance import bot
from app.bot.keyboards import  get_last_order_keyboard, cart
from app.db.db_session import SessionLocal
from app.services import UserService, OrderService, ProductService


@bot.callback_query_handler(func=lambda call: call.data == "last_order")
def get_last_order(call: CallbackQuery):
    bot.answer_callback_query(call.id)
    tg_id = call.from_user.id
    
    
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="Выберите тип формирования заказа:",
                          reply_markup=get_last_order_keyboard())


@bot.callback_query_handler(
    func=lambda call: call.data in ["with_actual_zeros_product", "without_actual_zeros_product"])
def get_actual_order(call: CallbackQuery):
    tg_id = call.from_user.id
    bot.answer_callback_query(call.id)
    with SessionLocal() as session:
        user_service = UserService(session=session)
        order_service = OrderService(session=session)
        product_service = ProductService(session=session)
        
        user = user_service.get_user_by_tg_id(tg_id)
        last_order = order_service.get_last_order(user.id)
        products = {p.name:p.target_quantity for p in product_service.get_all_products()}
        
        if last_order:
            order_id = last_order.id
            order = order_service.get_order_report(order_id)
            day = last_order.created_at
            msg_text = (f'🆔 Заказ №{order_id} (от {str(day)[:10]})\n'
                        f'❗️Восклицательный знак - убедитесь, что ячейка этого продукта заполнена\n'
                        f'{"-" * 33}\n')
            
            # Множество для отслеживания товаров с actual_quantity == 0
            already_warned = set()
            already_displayed = set()  # Для отслеживания всех товаров, которые уже отображены
            
            for i in order['items']:
                # Если товар с actual_quantity == 0 и не был еще добавлен
                if products[i["product_name"]] == 0 and i['product_name'] not in already_warned:
                    msg_text += f"❗️{i['product_name']} | {i['to_order']} бл.\n"
                    already_warned.add(i['product_name'])
                    already_displayed.add(i['product_name'])  # Помечаем как отображенный
                
                # Логика для отображения товаров
                if call.data == "without_actual_zeros_product" and i["to_order"] > 0:
                    if i['product_name'] not in already_displayed:
                        msg_text += f"{i['product_name']} | {i['to_order']} бл.\n"
                        already_displayed.add(i['product_name'])
                
                elif call.data == "with_actual_zeros_product":
                    # Добавляем все товары, включая с actual_quantity != 0, но только если они еще не были показаны
                    if i["product_name"] not in already_displayed:
                        msg_text += f"{i['product_name']} | {i['to_order']} бл.\n"
                        already_displayed.add(i['product_name'])
            
            # Функция для отправки длинных сообщений
            def send_long_message(chat_id, text, chunk_size=4000):
                message_id = None
                for i in range(0, len(text), chunk_size):
                    msg = bot.send_message(chat_id, text[i:i + chunk_size], parse_mode='HTML')
                    message_id = msg.message_id  # сохраняем id последнего куска
                return message_id
            
            # Отправляем длинное сообщение
            last_msg_id = send_long_message(call.message.chat.id, msg_text)