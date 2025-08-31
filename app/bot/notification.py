from app.db.db_session import SessionLocal
from app.services import UserService


def send_notification(msg_text: str):
    from app.bot.bot_instance import bot
    with SessionLocal() as session:
        user_service = UserService(session=session)
        users = user_service.get_all_users()
        for user in users:
            bot.send_message(user.tg_id, msg_text)