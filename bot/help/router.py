# TODO Пока нет точного понимания команд и описания будет так , потом для админ панели будут доп сообщения
from aiogram.filters import CommandObject, CommandStart, Command
from loguru import logger
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.dispatcher.router import Router
from bot.database import connection
from bot.users.dao import UserDAO
from bot.users.schemas import TelegramIDModel, UserModel
from bot.users.utils import get_refer_id_or_none
from bot.utils.commands import commands

help_router = Router()

#
# @help_router.message(Command('help'))
# async def help_start(message: Message, command: CommandObject, **kwargs) -> None:
#     """
#     Обработчик команды /start для Telegram-бота. Проверяет, существует ли пользователь в базе данных,
#     и если нет — регистрирует нового пользователя, привязывая его к реферальному ID (если он передан).
#
#     Args:
#         message (Message): Сообщение, которое пользователь отправил боту.
#         command (CommandObject): Объект, содержащий информацию о команде и ее аргументах.
#         session: Сессия для работы с базой данных.
#         **kwargs: Дополнительные аргументы, которые могут быть переданы через декоратор.
#
#     Returns:
#         None: Функция не возвращает значения, но отправляет сообщения в чат с пользователем.
#
#     Raises:
#         Exception: Если при обработке команды возникает ошибка, она будет зафиксирована в логе.
#     """
#     try:
#         # Получаем ID пользователя из сообщения
#         user_id = message.from_user.id
#
#         # Проверяем, существует ли уже пользователь в базе данных
#         user_info = await UserDAO.find_one_or_none(session=session,
#                                                    filters=TelegramIDModel(telegram_id=user_id))
#
#         # Если пользователь уже существует, отправляем приветственное сообщение
#         if user_info:
#             await message.answer(f"👋 Привет, {message.from_user.full_name}! Выберите необходимое действие")
#             return
#
#         # Определяем реферальный ID, если он был передан в аргументах команды
#         ref_id = get_refer_id_or_none(command_args=command.args, user_id=user_id)
#
#         # Создаем нового пользователя и добавляем его в базу данных
#         values = UserModel(telegram_id=user_id,
#                            username=message.from_user.username,
#                            first_name=message.from_user.first_name,
#                            last_name=message.from_user.last_name,
#                            referral_id=ref_id)
#         await UserDAO.add(session=session, values=values)
#
#         # Формируем сообщение для пользователя, в зависимости от наличия реферального ID
#         ref_message = f" Вы успешно закреплены за пользователем с ID {ref_id}" if ref_id else ""
#         msg = f"🎉 <b>Благодарим за регистрацию!{ref_message}</b>."
#
#         # Отправляем сообщение пользователю
#         await message.answer(msg)
#
#     except Exception as e:
#         # Логируем ошибку, если она возникла
#         logger.error(f"Ошибка при выполнении команды /start для пользователя {message.from_user.id}: {e}")
#         await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")


@help_router.message(Command('help'))
async def help_cmd(message: Message):
    """Кнопка помощи"""
    logger.debug(f'{help_cmd.__name__} - нажал кнопку помощи')
    text = [f'{el.command} - {el.description}' for el in commands]
    # if not message.from_user.username == 'BorisisTheBlade':
    #     text = [f'{el.command} - {el.description}' for el in main_menu_commands[:-1]]
    # else:
    #     text = [f'{el.command} - {el.description}' for el in main_menu_commands]

    await message.answer(text='\n'.join(text), reply_markup=ReplyKeyboardRemove())
    logger.info(f'{help_cmd.__name__} - кнопка отработала')