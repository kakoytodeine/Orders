from telebot import TeleBot
from app.config import _config

bot = TeleBot(_config.tg_token)