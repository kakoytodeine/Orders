from app.scheduler import start_scheduler
from app.bot.bot_instance import bot

def main():
    import app.bot.handlers
    start_scheduler()
    print("bot started")
    bot.infinity_polling(skip_pending=True)


    
if __name__=="__main__":
    main()
