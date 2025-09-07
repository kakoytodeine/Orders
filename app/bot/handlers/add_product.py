import re

from telebot.types import CallbackQuery, Message

from app.bot.bot_instance import bot
from app.bot.keyboards import  get_inline_keyboard_category, get_keyboard_add_product
from app.bot.temp_message import _clear_temp_message, _save_temp_message
from app.db.db_session import SessionLocal
from app.logger import logger
from app.services import CategoryService, ProductService


@bot.callback_query_handler(func=lambda call: call.data == "add_product")
def add_product_by_category(call: CallbackQuery):
    tg_id = call.from_user.id
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    # удаляем старое временное сообщение (если есть)
    # _clear_temp_message(chat_id, tg_id)

    try:
        # Редактируем текущее сообщение (список категорий)
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="🏷️ Выбери категорию куда добавить товар:",
            reply_markup=get_inline_keyboard_category("3_3")
        )
        # сохраняем это отредактированное сообщение как temp (используем message_id, который мы редактировали)
        _save_temp_message(tg_id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось редактировать сообщение с категориями: {e}. Отправлю новое.")
        try:
            msg = bot.send_message(chat_id, "🏷️ Выбери категорию куда добавить товар:",
                                   reply_markup=get_inline_keyboard_category("3_3"))
            _save_temp_message(tg_id, msg.message_id)
        except Exception as send_err:
            logger.error(f"Ошибка при отправке сообщения с категориями: {send_err}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("category3_3"))
def process_selected_category(call: CallbackQuery):
    tg_id = call.from_user.id
    chat_id = call.message.chat.id
    category_id = int(call.data.split("3_3")[1])

    bot.answer_callback_query(call.id)

    try:
        # Попробуем редактировать то же сообщение (которое было)
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="Выберите действие:",
            reply_markup=get_keyboard_add_product(category_id)
        )
        # сохраняем в temp_messages
        _save_temp_message(tg_id, call.message.message_id)
    except Exception as e:
        logger.warning(f"Не удалось редактировать сообщение на 'Выберите действие': {e}. Отправлю новое.")
        try:
            msg = bot.send_message(chat_id, "Выберите действие:", reply_markup=get_keyboard_add_product(category_id))
            _save_temp_message(tg_id, msg.message_id)
        except Exception as send_err:
            logger.error(f"Ошибка при отправке 'Выберите действие': {send_err}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("add_new_product_"))
def add_new_product_by_category(call: CallbackQuery):
    tg_id = call.from_user.id
    chat_id = call.message.chat.id
    category_id = int(call.data.split("_")[3])
    bot.answer_callback_query(call.id)

    # Попытка убрать inline-клавиатуру (не критично, если упадёт)
    try:
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=None)
    except Exception as e:
        logger.debug(f"edit_message_reply_markup не удался: {e}")

    # Удаляем текущее временное сообщение (например "Выберите действие"), чтобы не оставлять его висеть
    _clear_temp_message(chat_id, tg_id)

    try:
        # Отправляем запрос на ввод как временное сообщение (и сразу сохраняем его id)
        msg = bot.send_message(chat_id, "Введите название продукта\n📦 Название + количество (например: Winston 10)")
        _save_temp_message(tg_id, msg.message_id)
        bot.register_next_step_handler(msg, check_to_correct_name_product, category_id)
    except Exception as e:
        logger.error(f"Ошибка при запросе названия продукта: {e}")
        try:
            bot.send_message(chat_id, "⚠️ Не удалось запросить название продукта. Попробуйте ещё раз.")
        except Exception:
            pass


def check_to_correct_name_product(message: Message, category_id: int):
    tg_id = message.chat.id
    chat_id = message.chat.id
    msg_text = (message.text or "").strip()

    pattern = r'^(?P<name>[\wА-Яа-яЁё\s\-]{2,}?)\s+(?P<qty>\d{1,2})$'
    match = re.match(pattern, msg_text)

    # Если формат неверный — удалить сообщение пользователя (если возможно), заменить бот-сообщение на подсказку и ждать снова
    if not match:
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            # если не можем удалить пользовательское сообщение — ок, просто продолжаем
            pass

        # удаляем старое временное сообщение от бота и отправляем новое (подсказку)
        _clear_temp_message(chat_id, tg_id)
        try:
            hint = bot.send_message(chat_id, "⚠️ Введите корректно: Название продукта + количество (например: Winston 10)")
            _save_temp_message(tg_id, hint.message_id)
            bot.register_next_step_handler(hint, check_to_correct_name_product, category_id)
        except Exception as e:
            logger.error(f"Ошибка при отправке подсказки о корректном вводе: {e}")
        return

    name_product = match.group("name").strip()
    target_quantity = int(match.group("qty"))

    try:
        with SessionLocal() as session:
            product_service = ProductService(session=session)
            category_service = CategoryService(session=session)

            category = category_service.get_category_by_id(category_id)
            if not category:
                _clear_temp_message(chat_id, tg_id)
                try:
                    m = bot.send_message(chat_id, "❌ Категория не найдена.")
                    _save_temp_message(tg_id, m.message_id)
                except Exception as e:
                    logger.error(f"Ошибка при сообщении о ненайденной категории: {e}")
                return

            # Проверка на дубликат
            existing = product_service.get_product_by_name_in_category(name_product, category_id)
            if existing:
                # удаляем сообщение пользователя (чтобы не засорять)
                try:
                    bot.delete_message(chat_id, message.message_id)
                except Exception:
                    pass

                _clear_temp_message(chat_id, tg_id)
                try:
                    m = bot.send_message(chat_id,
                                         f"⚠️ Продукт *{name_product}* уже существует. Введите другое имя:",
                                         parse_mode="Markdown")
                    _save_temp_message(tg_id, m.message_id)
                    bot.register_next_step_handler(m, check_to_correct_name_product, category_id)
                except Exception as e:
                    logger.error(f"Ошибка при уведомлении о дубликате: {e}")
                return

            # Создаём новый продукт
            try:
                product_service.create_product_for_admin(name_product, target_quantity, category_id)
            except Exception as e:
                logger.error(f"Ошибка при создании продукта в базе: {e}")
                _clear_temp_message(chat_id, tg_id)
                try:
                    m = bot.send_message(chat_id, "❌ Ошибка при создании продукта")
                    _save_temp_message(tg_id, m.message_id)
                except Exception:
                    pass
                return

            # Успех: удаляем пользовательское сообщение (чтобы не оставлять ввод) и старое temp, затем отправляем подтверждение с клавой
            try:
                bot.delete_message(chat_id, message.message_id)
            except Exception:
                pass

            _clear_temp_message(chat_id, tg_id)
            try:
                m = bot.send_message(chat_id,
                                     f"✅ Продукт *{name_product}* добавлен в категорию {category.name}",
                                     parse_mode="Markdown",
                                     reply_markup=get_keyboard_add_product(category_id))
                _save_temp_message(tg_id, m.message_id)
            except Exception as e:
                logger.error(f"Ошибка при отправке подтверждения добавления продукта: {e}")

    except Exception as e:
        logger.error(f"Необработанная ошибка в check_to_correct_name_product: {e}")
        _clear_temp_message(chat_id, tg_id)
        try:
            m = bot.send_message(chat_id, "⚠️ Ошибка при создании продукта")
            _save_temp_message(tg_id, m.message_id)
        except Exception:
            pass
