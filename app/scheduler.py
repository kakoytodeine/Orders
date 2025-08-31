from apscheduler.schedulers.background import BackgroundScheduler
from app.bot.notification import send_notification

def start_scheduler():
    scheduler = BackgroundScheduler()

    # scheduler.add_job(lambda: send_notification("Сделать заказ 'Мегаполис'"),
    #                   "interval",
    #                   minutes=1)
    scheduler.start()

    return scheduler