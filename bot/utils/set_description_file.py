# TODO необходимо придумать описание для бота с картинками
# TODO так же в BOTFAther поменяй информацию о боте и картинку если надо
from aiogram import Bot


async def set_description(bot: Bot) -> None:
    """
    Устанавливает описание бота в Telegram.

    Аргументы:
        bot (Bot): Экземпляр бота из aiogram.

    Эта функция получает информацию о боте и устанавливает описание,
    которое включает имя бота и краткое объяснение его функционала.
    """
    inf = await bot.get_me()
    await bot.set_my_description(
        f"{inf.first_name} приветствует тебя!\n"
        "Этот 🤖 БОТ занимается обработкой заказов, "
        "управлением пользователями и отправкой уведомлений."
    )
