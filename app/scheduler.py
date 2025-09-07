from functools import partial

from apscheduler.schedulers.background import BackgroundScheduler
from app.bot.notification import send_notification


def start_scheduler():
    scheduler = BackgroundScheduler()
    
    tasks = {0: [{"task": "Сделать заказ Мегаполис", "hours": 10, "minute": 0},
                 {"task": "Сделать заказ по ПЕПСИко", "hours": 10, "minute": 0},
                 {"task": "Сделать заказ по СНС", "hours": 10, "minute": 0},
                 {"task": "Сделать заказ по Сатурну", "hours": 10, "minute": 0}],
             1: [{"task": "Сделать заказ по Флешу", "hours": 10, "minute": 0},
                 {"task": "Сделать заказ по берну", "hours": 10, "minute": 0}],
             3: [{"task": "Сделать заказ Мегаполис", "hours": 10, "minute": 0},
                 {"task": "Сделать заказ по ЛИТэнерджи", "hours": 12, "minute": 0},
                 {"task": "Сделать заказ по Сатурн", "hours": 10, "minute": 0},
                 {"task": "Сделать заказ по СНС", "hours": 12, "minute": 0}
                 ]}
    scheduler.remove_all_jobs()
    for day, task in tasks.items():
        for job in task:
            scheduler.add_job(
                func=partial(send_notification, job["task"]),
                trigger='cron',
                day_of_week=int(day),
                hour=job["hours"],
                minute=job["minute"]
            )
    
    scheduler.start()
    
    return scheduler
