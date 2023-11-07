import os
import dotenv
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, ApplicationBuilder, Application
import requests
from models import WeatherForecastModel
from gpt import forecast_summary

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)




async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Узнать погоду", callback_data='get_weather_forecast')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Пожалуйста выберите:', reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query.data == 'get_weather_forecast':
        await query.edit_message_text(text="Пожалуйста, введите название города.")
        context.user_data['awaiting_city'] = True

async def handle_city_forecast_request(update: Update, context: CallbackContext) -> None:
    city = update.message.text
    response = requests.get('http://0.0.0.0:8000/forecast', params={'city': city})
    try:
        if response.status_code == 200:
            weather_data = WeatherForecastModel(**response.json())
            reply_message = forecast_summary(city, weather_data)
        elif response.status_code == 422:
            reply_message = f'Город \'{city}\' не найден. Пожалуйста проверьте, правильно ли вы написали название города.'
        else:
            reply_message = 'Что-то пошло не так. Попробуйте еще раз.'
    except Exception as e:
        logger.error(e)
        reply_message = 'Что-то пошло не так. Попробуйте еще раз.'

    await update.message.reply_text(reply_message)
    context.user_data['awaiting_city'] = False

async def handle_invalid_request(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Отправьте /start чтобы получить список опций для запроса.')

async def handle_message(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_city'):
        await handle_city_forecast_request(update, context)
    else:
        await handle_invalid_request(update, context)
    

async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([('start', 'Запускает бота.')])

if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).post_init(post_init).build()
        handlers = [CommandHandler('start', start), CallbackQueryHandler(button), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)]
        application.add_handlers(handlers)
        application.run_polling()
    except Exception as e:
        logger.error(e)