from dotenv import dotenv_values
from telebot import TeleBot, types
import logging
from cats import get_cat_photo


config = dotenv_values()
bot = TeleBot(token=config['API_TOKEN'])

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='primarius.log',
    filemode='a',
    level=logging.INFO,
    encoding='utf-8'
)


@bot.message_handler(commands=['start'])
def handle_start_command(message):
    chat_id = message.chat.id
    name = message.chat.first_name

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_newcat = types.KeyboardButton('/newcat')
    keyboard.add(button_newcat)
    
    bot.send_message(
        chat_id=chat_id,
        text=f'Здравствуйте, {name}, я бот Primarius.',
        reply_markup=keyboard
    )


@bot.message_handler(commands=['newcat'])
def new_cat(message):
    chat_id = message.chat.id
    response = get_cat_photo()

    if response['is_succeed']:
        bot.send_photo(chat_id, response['url'])
    else:
        logging.error(f'Ответ от Cat API не получен')
        bot.send_message(
            chat_id=chat_id,
            text='К сожалению, не получилось загрузить фото кота :('
        )


@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id=chat_id,
        text='Пока что я не понимаю сообщения :('
    )


if __name__ == '__main__':
    bot.polling()
