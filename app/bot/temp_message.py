from app.bot.bot_instance import bot
from app.logger import logger

temp_messages = {}


def _clear_temp_message(chat_id: int, tg_id: int):
    """Удалить предыдущее временное сообщение бота для пользователя, если есть, и убрать из temp_messages."""
    if tg_id in temp_messages:
        old_msg_id = temp_messages[tg_id]
        try:
            bot.delete_message(chat_id, old_msg_id)
            logger.debug(f"Удалено старое temp_message {old_msg_id} для {tg_id}")
        except Exception as e:
            # логируем, но продолжаем
            logger.warning(f"Не удалось удалить temp_message {old_msg_id} для {tg_id}: {e}")
        temp_messages.pop(tg_id, None)


def _save_temp_message(tg_id: int, message_id: int):
    """Сохранить id временного сообщения в temp_messages."""
    temp_messages[tg_id] = message_id
    logger.debug(f"Сохранён temp_message {message_id} для {tg_id}")