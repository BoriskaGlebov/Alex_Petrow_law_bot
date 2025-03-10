# from bot.application_form.models import Application, MediaFile
# from bot.dao.base import BaseDAO
# from bot.users.models import User
#
#
# class ApplicationDAO(BaseDAO[Application]):
#     """
#     Класс для работы с данными заявок в базе данных.
#
#     Наследует методы от BaseDAO и предоставляет дополнительные
#     операции для работы с заявками, такие как создание, чтение,
#     обновление и удаление заявок.
#
#     Атрибуты:
#         model (Application): Модель, с которой работает этот DAO.
#     """
#     model: Application  # Модель для работы с данными заявки
#
#
# class MediaFileDAO(BaseDAO[MediaFile]):
#     """
#     Класс для работы с данными медиафайлов в базе данных.
#
#     Наследует методы от BaseDAO и предоставляет дополнительные
#     операции для работы с медиафайлами, такие как создание, чтение,
#     обновление и удаление медиафайлов.
#
#     Атрибуты:
#         model (MediaFile): Модель, с которой работает этот DAO.
#     """
#     model: MediaFile  # Модель для работы с данными медиафайла
