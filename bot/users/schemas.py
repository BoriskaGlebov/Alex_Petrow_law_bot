import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelegramIDModel(BaseModel):
    """
    Базовая модель для хранения идентификатора пользователя в Telegram.

    Атрибуты:
        telegram_id (int): Уникальный идентификатор пользователя в Telegram.
    """

    telegram_id: int

    model_config = ConfigDict(from_attributes=True)


class UserModel(TelegramIDModel):
    """
    Модель пользователя с дополнительными полями, включая номер телефона.

    Атрибуты:
        username (Optional[str]): Имя пользователя в Telegram (может быть None).
        first_name (Optional[str]): Имя пользователя (может быть None).
        last_name (Optional[str]): Фамилия пользователя (может быть None).
        referral_id (Optional[int]): Идентификатор реферала (может быть None).
        phone_number (Optional[str]): Номер телефона пользователя (может быть None).
    """

    username: str | None = Field(None, description="Имя пользователя в Telegram")
    first_name: str | None = Field(None, description="Имя пользователя")
    last_name: str | None = Field(None, description="Фамилия пользователя")
    referral_id: int | None = Field(None, description="Идентификатор реферала")


class UpdateNumberSchema(BaseModel):
    """
       Схема для обновления номера телефона.

       Поддерживает два формата ввода:
       - `+7XXXXXXXXXX` (например, `+71234567890`)
       - `8XXXXXXXXXX` (например, `81234567890`), который будет преобразован в `+7XXXXXXXXXX`.

       Attributes:
           phone_number (Optional[str]): Номер телефона в международном формате.
       """
    phone_number: Optional[str] = Field(
        None,
        description="Номер телефона пользователя в международном формате (+71234567890), поддерживает форматы: +7XXXXXXXXXX или 8XXXXXXXXXX",
        min_length=10,
        max_length=16,
    )

    @field_validator("phone_number")
    def validate_phone_number(cls, phone_number: Optional[str]) -> Optional[str]:
        """
        Валидирует номер телефона и приводит его к международному формату (+7XXXXXXXXXX).

        Поддерживаются следующие форматы ввода:
        - +7XXXXXXXXXX (например, +71234567890)
        - 8XXXXXXXXXX (например, 81234567890), который будет конвертирован в формат +7XXXXXXXXXX.

        Если номер не соответствует ожидаемым форматам, будет поднято исключение ValueError.

        Args:
            phone_number (Optional[str]): Введенный номер телефона пользователя.

        Returns:
            Optional[str]: Приведенный номер телефона в международном формате (+7XXXXXXXXXX), или None, если телефон не был передан.

        Raises:
            ValueError: Если номер телефона не соответствует одному из поддерживаемых форматов.
        """
        if phone_number is None:
            return None

        # Удаляем лишние пробелы и символы
        phone_number = phone_number.strip()

        # Проверяем формат номера и приводим к международному
        if phone_number.startswith("+7") and re.fullmatch(r"\+7\d{10}", phone_number):
            return phone_number
        elif phone_number.startswith("8") and re.fullmatch(r"8\d{10}", phone_number):
            return "+7" + phone_number[1:]  # Заменяем 8 на +7
        else:
            raise ValueError(
                "Некорректный номер телефона. Используйте формат +71234567890 или 8XXXXXXXXXX."
            )
