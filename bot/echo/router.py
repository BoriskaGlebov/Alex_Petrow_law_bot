from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.types import Message
from loguru import logger

echo_router = Router()


@echo_router.message(F.text)
async def echo_start(message: Message, **kwargs) -> None:
    """
    Обработчик для получения текстовых сообщений от пользователя и отправки стандартного ответа.

    Если бот не может обработать запрос, он информирует пользователя о том, что произошло непредвиденное действие.
    В случае ошибки, это действие логируется.

    Args:
        message (Message): Объект, представляющий сообщение, которое пользователь отправил боту.
        **kwargs: Дополнительные аргументы, которые могут быть переданы через декоратор.

    Returns:
        None: Функция не возвращает значений, но отправляет ответное сообщение пользователю.

    Raises:
        Exception: Если возникает ошибка при обработке сообщения, она будет зафиксирована в логе и пользователю будет отправлено сообщение о произошедшей ошибке.
    """
    try:
        # Сообщение о том, что что-то пошло не так
        await message.answer(
            "Что-то пошло не так, и я не смог обработать ваш запрос. 😅 Я скоро разберусь! "
            "Возможно, это что-то непредвиденное. Пожалуйста, подождите немного."
        )
        # Дополнительное сообщение, что можно выбрать команду
        await message.answer(
            "А пока вы можете попробовать выбрать команду 📲 в списке Меню."
        )

    except Exception as e:
        # Логируем ошибку
        logger.error(
            f"Ошибка при обработке сообщения от пользователя {message.from_user.id} на echo: {e}"
        )

        # Отправляем сообщение пользователю о том, что произошла ошибка
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже."
        )
