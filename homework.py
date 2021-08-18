import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    filename='bot.log',
    format='(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.FileHandler('bot.log', mode='w'))

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HOMEWORK_STATUSES_API_URL = ('https://praktikum.yandex.ru/api/user_api/'
                             'homework_statuses/')
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
bot = telegram.Bot(TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    payload = {'from_date': current_timestamp}
    homework_statuses = requests.get(HOMEWORK_STATUSES_API_URL,
                                     headers=HEADERS, params=payload)
    return homework_statuses.json()


def send_message(message):
    logger.info(f'Бот отправляет сообщение юзеру {CHAT_ID}')
    return bot.send_message(CHAT_ID, message)


def main():
    logger.debug('Отслеживание статуса запущено')
    current_timestamp = int(time.time())

    while True:
        try:
            homework = get_homeworks(current_timestamp)['homeworks']
            if homework and homework[0]['status'] != 'reviewing':
                send_message(parse_homework_status(homework[0]))
                break
            time.sleep(20 * 60)

        except Exception as e:
            error_message = f'Бот упал с ошибкой: {e}'
            logger.error(error_message)
            send_message(error_message)
            time.sleep(5)


if __name__ == '__main__':
    main()
