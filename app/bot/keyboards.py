from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.services import CategoryService
from app.db.db_session import SessionLocal

def get_main_menu_for_user() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    
    kb.row('📦 Начать заказ', '🕘 Последний заказ')
    kb.row('ℹ️ Инфо')
    
    return kb

def get_main_menu_for_admin() -> ReplyKeyboardMarkup:
    kb = get_main_menu_for_user()
    kb.row('Добавить категорию', 'Добавить товар')
    return  kb

def category_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    with SessionLocal() as session:
        category_service = CategoryService(session)
        buttons = [KeyboardButton(c.name) for c in category_service.get_all_categories()]
        
        for i in range(0, len(buttons), 3):
            kb.add(*buttons[i:i+3])
            
        kb.add(KeyboardButton('⬅ Назад'))
            
    return kb

cart = {}

def get_category_by_user(user_id: int):
    for p, data in cart[user_id].items():
        return data['category']

def create_cart_keyboard(user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for product_name, data in cart[user_id].items():
        kb.add(InlineKeyboardButton(
            text=f'{product_name} - План {data["target"]}бл, Факт '
                 f'{data["actual"]}.',
            callback_data=f'product_{data["id"]}'
            ))
    kb.add(InlineKeyboardButton(
       text=f'✅ Завершить заказ',
         callback_data=f'finished_order'
    ))
    return kb

    
    