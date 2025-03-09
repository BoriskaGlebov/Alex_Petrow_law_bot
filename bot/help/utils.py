# def get_refer_id_or_none(command_args: str, user_id: int) -> int | None:
#     """
#     Определяет реферальный ID из аргументов команды. Возвращает реферальный ID, если он валиден, или None,
#     если аргументы не соответствуют требованиям (например, если это не число или это ID самого пользователя).
#
#     Args:
#         command_args (str): Аргументы команды, содержащие потенциальный реферальный ID.
#         user_id (int): ID текущего пользователя, чтобы убедиться, что он не пытается использовать свой собственный ID в качестве реферала.
#
#     Returns:
#         int | None: Если аргумент команды является валидным реферальным ID (целое число, больше 0 и не равное user_id),
#                     то возвращается этот ID. Иначе возвращается None.
#     """
#     return int(command_args) if command_args and command_args.isdigit() and int(command_args) > 0 and int(
#         command_args) != user_id else None
