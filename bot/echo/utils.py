# import re
# from typing import Optional
#
#
# def extract_number(text: str) -> Optional[int]:
#     """
#     Извлекает первое число из строки.
#
#     Функция использует регулярное выражение для поиска первого числа в тексте.
#     Возвращает первое найденное число в виде целого числа, либо None, если число не найдено.
#
#     Args:
#         text (str): Строка, из которой будет извлечено число.
#
#     Returns:
#         Optional[int]: Первое найденное число в строке или None, если число не найдено.
#
#     Example:
#         extract_number("Цена: 150 рублей") -> 150
#         extract_number("Нет чисел здесь") -> None
#     """
#     match = re.search(r'\b(\d+)\b', text)
#     if match:
#         return int(match.group(1))
#     else:
#         return None
