import math  # математический модуль для округления
# подтягиваем константы из config файла
from config import LOGS, MAX_USERS, MAX_USER_GPT_TOKENS, MAX_USER_TTS_SYMBOLS, MAX_USER_STT_BLOCKS
# подтягиваем функции для работы с БД
from db3 import count_users, count_all_limits
# подтягиваем функцию для подсчета токенов в списке сообщений
from yandex_gpt import count_gpt_tokens
import logging

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.ERROR, format="%(asctime)s FILE: %(filename)s IN: %(funcName)s "
                                                               "MESSAGE: %(message)s", filemode="w")


# получаем количество уникальных пользователей, кроме самого пользователя
def check_number_of_users(user_id):
    count = count_users(user_id)
    if count is None:
        return None, "Ошибка при работе с БД"
    if count > MAX_USERS:
        return None, "Превышено максимальное количество пользователей"
    return True, ""


# проверяем, не превысил ли пользователь лимиты на общение с GPT
def is_gpt_token_limit(messages, total_spent_tokens):
    all_tokens = count_gpt_tokens(messages) + total_spent_tokens
    if all_tokens > MAX_USER_GPT_TOKENS:
        return None, f"Превышен общий лимит GPT-токенов {MAX_USER_GPT_TOKENS}"
    return all_tokens, ""


def is_stt_block_limit(user_id, duration):
    try:
        # Получаем количество использованных блоков для пользователя
        used_blocks, error_message = count_all_limits(user_id, 'stt_blocks')
        if error_message:
            return None, error_message

        # Округляем продолжительность аудиосообщения до ближайшего целого числа (вверх)
        duration_blocks = math.ceil(duration / 15)  # 1 блок = 15 секунд

        # Проверяем, достаточно ли блоков у пользователя
        remaining_blocks = MAX_USER_STT_BLOCKS - used_blocks
        if duration_blocks > remaining_blocks:
            return None, f"Недостаточно блоков для преобразования аудио. Осталось: {remaining_blocks}"

        return duration_blocks, ""  # Возвращаем количество использованных блоков и пустую строку при успехе

    except Exception as e:
        logging.error(e)
        return None, "Ошибка при проверке лимитов преобразования аудио"


# проверяем, не превысил ли пользователь лимиты на преобразование текста в аудио
def is_tts_symbol_limit(user_id, text):
    try:
        # Получаем количество использованных символов для пользователя
        used_symbols, error_message = count_all_limits(user_id, 'tts_symbols')
        if error_message:
            return None, error_message

        # Проверяем, достаточно ли символов у пользователя
        remaining_symbols = MAX_USER_TTS_SYMBOLS - used_symbols
        if len(text) > remaining_symbols:
            return None, f"Недостаточно символов для преобразования текста в речь. Осталось: {remaining_symbols}"

        return len(text), ""  # Возвращаем количество использованных символов и пустую строку при успехе

    except Exception as e:
        logging.error(e)
        return None, "Ошибка при проверке лимитов преобразования текста в речь"
