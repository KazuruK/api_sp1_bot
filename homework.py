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
HOMEWORK_STATUSES_API_URL = ('https://practicum.yandex.ru/api/user_api/homework_statuses/')
WAIT_TIME = 20 * 60
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
bot = telegram.Bot(TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None or homework_status is None:
        return 'Неверный ответ сервера.'
    if homework_status == 'reviewing':
        return
    if homework_status == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(HOMEWORK_STATUSES_API_URL,
                                         headers=HEADERS, params=payload)
        try:
            json = homework_statuses.json()
            return json
        except (TypeError, ValueError) as e:
            error_message = ('Преобразование ответа Яндекс.Практикума в json'
                             f' вернуло ошибку: {e}')
            logger.error(error_message)
    except requests.RequestException as e:
        error_message = f'Запрос к api Яндекс.Практикума вернул ошибку: {e}'
        logger.error(error_message)


def send_message(message):
    logger.info(f'Бот отправляет сообщение юзеру {CHAT_ID}')
    return bot.send_message(CHAT_ID, message)


def main():
    logger.debug('Отслеживание статуса запущено')
    send_message('Запущено отслеживание обновлений ревью')
    current_timestamp = int(time.time())

    while True:
        try:
            answer = get_homeworks(current_timestamp)
            homework = answer['homeworks']
            if homework:
                message = parse_homework_status(homework[0])
                if message == 'Неверный ответ сервера.':
                    raise KeyError(message)
                if message:
                    send_message(message)
            current_timestamp = answer.get('current_date')
            time.sleep(WAIT_TIME)

        except Exception as e:
            error_message = f'Бот упал с ошибкой: {e}'
            logger.error(error_message)
            send_message(error_message)
            time.sleep(WAIT_TIME)


if __name__ == '__main__':
    main()
