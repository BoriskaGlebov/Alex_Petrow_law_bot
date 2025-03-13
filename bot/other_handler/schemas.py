# from pydantic import BaseModel, ConfigDict, Field, validator
# import re
#
#
# class TelegramIDModel(BaseModel):
#     """
#     Базовая модель для хранения идентификатора пользователя в Telegram.
#
#     Атрибуты:
#         telegram_id (int): Уникальный идентификатор пользователя в Telegram.
#     """
#     telegram_id: int
#
#     model_config = ConfigDict(from_attributes=True)
#
#
# class UserModel(TelegramIDModel):
#     """
#     Модель пользователя с дополнительными полями, включая номер телефона.
#
#     Атрибуты:
#         username (Optional[str]): Имя пользователя в Telegram (может быть None).
#         first_name (Optional[str]): Имя пользователя (может быть None).
#         last_name (Optional[str]): Фамилия пользователя (может быть None).
#         referral_id (Optional[int]): Идентификатор реферала (может быть None).
#         phone_number (Optional[str]): Номер телефона пользователя (может быть None).
#     """
#
#     username: str | None = Field(None, description="Имя пользователя в Telegram")
#     first_name: str | None = Field(None, description="Имя пользователя")
#     last_name: str | None = Field(None, description="Фамилия пользователя")
#     referral_id: int | None = Field(None, description="Идентификатор реферала")
#
#
# class UpdateNumberSchema(BaseModel):
#     phone_number: str | None = Field(
#         None,
#         description="Номер телефона пользователя в международном формате (+71234567890)",
#         min_length=10,
#         max_length=16
#     )
#
#     @validator("phone_number")
#     def validate_phone_number(cls, phone_number: str | None) -> str | None:
#         """
#         Валидирует номер телефона, приводя его к международному формату (+7XXXXXXXXXX).
#         Поддерживает ввод в формате:
#         - +7XXXXXXXXXX
#         - 8XXXXXXXXXX (конвертируется в +7XXXXXXXXXX)
#
#         Args:
#             phone_number (Optional[str]): Введенный номер телефона.
#
#         Returns:
#             Optional[str]: Приведенный к международному формату номер или None.
#
#         Raises:
#             ValueError: Если номер телефона имеет некорректный формат.
#         """
#         if phone_number is None:
#             return None
#
#         # Удаляем лишние пробелы и символы (если вдруг введены)
#         phone_number = phone_number.strip()
#
#         # Проверяем, начинается ли номер с +7 или 8, затем конвертируем его в международный формат
#         if phone_number.startswith("+7") and re.fullmatch(r"\+7\d{10}", phone_number):
#             return phone_number
#         elif phone_number.startswith("8") and re.fullmatch(r"8\d{10}", phone_number):
#             return "+7" + phone_number[1:]  # Заменяем 8 на +7
#         else:
#             raise ValueError("Некорректный номер телефона. Используйте формат +71234567890 или 8XXXXXXXXXX.")
