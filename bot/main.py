import asyncio
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger
from bot.config import bot, admins, dp
from bot.faq.router import faq_router
from bot.help.router import help_router
from bot.users.router import user_router
from bot.utils.commands import set_commands, commands
from bot.utils.set_description_file import set_description


# Функция, которая выполнится, когда бот запустится
async def start_bot():
    """
    Инициализация и запуск бота.

    Эта функция устанавливает команды для бота с помощью `set_commands()`,
    устанавливает описание с помощью `set_description()`,
    а также отправляет сообщение администраторам, информируя их о запуске бота.
    """
    await set_commands(commands_list=commands)
    await set_description(bot=bot)
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, f'Я запущен🥳.')
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение админу {admin_id}: {e}")
            pass
    logger.info("Бот успешно запущен.")


# Функция, которая выполнится, когда бот завершит свою работу
async def stop_bot():
    """
    Остановка бота.

    Эта функция отправляет сообщение администраторам, уведомляя их о том,
    что бот был остановлен, и логирует это событие.
    """
    try:
        for admin_id in admins:
            await bot.send_message(admin_id, 'Бот остановлен. За что?😔')
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение админу {admin_id} об остановке бота: {e}")
        pass
    logger.error("Бот остановлен!")


async def main():
    """
    Основная функция запуска бота.

    Эта функция регистрирует роутеры, функции старта и остановки бота, а также
    запускает бота с использованием long polling для получения обновлений.
    """
    # регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(faq_router)
    dp.include_router(help_router)

    # регистрация функций
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    # запуск бота в режиме long polling при запуске бот очищает все обновления, которые были за его моменты бездействия
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
