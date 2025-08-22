from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app.services import CategoryService, UserService, ProductService
from app.db.db_session import SessionLocal


def get_main_menu(tg_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    inline_buttons = []
    inline_buttons.append(InlineKeyboardButton('📝 Сделать заказ', callback_data="new_order"))
    inline_buttons.append(InlineKeyboardButton('🕘 Последний заказ', callback_data="last_order"))
    
    with SessionLocal() as session:
        user_service = UserService(session=session)
        user = user_service.get_user_by_tg_id(tg_id)
        if getattr(user, "role") == "admin":
            inline_buttons.append(InlineKeyboardButton('🗂️ Добавить категорию', callback_data="add_category"))
            inline_buttons.append(InlineKeyboardButton("️❌ Удалить категорию", callback_data="delete_category"))
            inline_buttons.append(InlineKeyboardButton("➕ Добавить товар", callback_data="add_product"))
            inline_buttons.append((InlineKeyboardButton("❌ Удалить товар", callback_data="delete_product")))
            inline_buttons.append(InlineKeyboardButton("⏰ Запланировать уведомление", callback_data="add_task"))
            kb.add(*inline_buttons)
        else:
            kb.add(*inline_buttons)
        kb.add(InlineKeyboardButton("ℹ️ Инфо", callback_data="info"))
        return kb


cart = {}


def get_category_by_user(user_id: int):
    for p, data in cart[user_id].items():
        return data['category']


user_pages_by_cart = {}
PAGE_SIZE = 5


def create_cart_keyboard(user_id: int, sep: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    
    if user_id not in user_pages_by_cart:
        user_pages_by_cart[user_id] = {
            "current_page": 0,
            "items": list(cart[user_id].items())
        }
    
    current_page = user_pages_by_cart[user_id]["current_page"]
    items = user_pages_by_cart[user_id]["items"]
    
    start = current_page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = items[start:end]
    
    for product_name, data in page_items:
        kb.row(
            InlineKeyboardButton(
                text=f'{product_name} - План {data["target"]}бл, Факт {data["actual"]}.',
                callback_data=f'product{sep}{data["id"]}'
            ),
        )
    
    pagination_buttons = []
    
    if current_page > 0:
        pagination_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="prev_page"))
    if (current_page + 1) * PAGE_SIZE < len(items):
        pagination_buttons.append(InlineKeyboardButton("▶️ Вперёд", callback_data="next_page"))
    if pagination_buttons:
        kb.row(*pagination_buttons)
    kb.add(InlineKeyboardButton(
        text=f'✅ Завершить заказ',
        callback_data=f'finished_order'
    ))
    kb.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_add_category"
    ))
    return kb


def get_inline_keyboard_category(sep: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    with SessionLocal() as session:
        category_service = CategoryService(session=session)
        for category in category_service.get_all_categories():
            kb.add(InlineKeyboardButton(
                text=f"{category.name}",
                callback_data=f"category{sep}{category.id}"
            ))
    kb.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main_menu"
    ))
    return kb

def back() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    return kb

user_pages_by_product_from_db = {}


def create_product_keyboard_from_db(category_id: int, user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)

    with SessionLocal() as session:
        product_service = ProductService(session=session)
        products = [(p.id, p.name) for p in product_service.get_products_by_category(category_id)]

        if user_id not in user_pages_by_product_from_db:
            user_pages_by_product_from_db[user_id] = {
                "current_page": 0,
                "items": products,
                "category_id": category_id
            }

        current_page = user_pages_by_product_from_db[user_id]["current_page"]
        items = user_pages_by_product_from_db[user_id]["items"]

        start = current_page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_items = items[start:end]

        for id, name in page_items:
            kb.add(InlineKeyboardButton(name, callback_data=f"productdelete_{id}"))

        # Пагинация
        pagination_buttons = []
        if current_page > 0:
            pagination_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="prev_page_product"))
        if end < len(items):
            pagination_buttons.append(InlineKeyboardButton("▶️ Вперёд", callback_data="next_page_product"))
        if pagination_buttons:
            kb.row(*pagination_buttons)

        kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_delete_category"))

    return kb
