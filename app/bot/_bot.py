from telebot import TeleBot
from app.bot.handlers import handlers
from app.config import _config


class Bot:
    def __init__(self):
        self.bot = TeleBot(_config.tg_token)
        self.setup_handlers()
        
    def setup_handlers(self):
        handlers(self.bot)
    
    
    def run(self):
        print('bot started')
        self.bot.infinity_polling(skip_pending=True)
    
def main():
    bot = Bot()
    bot.run()
    
if __name__=='__main__':
    main()
