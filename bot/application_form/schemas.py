from pydantic import BaseModel

# class ApplicationStatusSchema(str, Enum):  # Наследуем str, чтобы Pydantic понимал его как строку
#     PENDING = "pending"
#     APPROVED = "approved"
#     REJECTED = "rejected"
#
#
# class ApplicationModelSchema(BaseModel):
#     """
#     Модель для создания заявки пользователя.
#
#     Атрибуты:
#         user_id (int): Идентификатор пользователя, к которому относится заявка.
#         status (str): Статус заявки (по умолчанию 'pending').
#         photos (List[int]): Список ID фотографий, связанных с заявкой.
#         videos (List[int]): Список ID видео, связанных с заявкой.
#         debts (List[dict]): Список задолженностей, каждая задолженность представлена словарем с ключами 'bank_name' и 'total_amount'.
#
#     Методы:
#         model_dump() -> dict: Возвращает словарь с данными модели.
#     """
#     user_id: int  # ID пользователя, к которому относится заявка
#     status: ApplicationStatusSchema = ApplicationStatusSchema.PENDING  # Статус заявки (по умолчанию 'pending')
#     # photos: List[int] = []  # Список ID фотографий
#     # videos: List[int] = []  # Список ID видео
#     # debts: List[dict] = []  # Список задолженностей в банках
#
#     model_config = ConfigDict(from_attributes=True)  # Позволяет работать с атрибутами объектов


class PhotoModelSchema(BaseModel):
    """
    Модель для создания фотографии, связанной с заявкой.

    Атрибуты:
        file_id (str): Идентификатор файла фотографии в Telegram.
        application_id (int): Идентификатор заявки, к которой привязана фотография.
    """

    file_id: str  # ID файла фотографии (например, Telegram file_id)
    application_id: int  # ID заявки, к которой привязана фотография


class VideoModelSchema(BaseModel):
    """
    Модель для создания видео, связанного с заявкой.

    Атрибуты:
        file_id (str): Идентификатор файла видео в Telegram.
        application_id (int): Идентификатор заявки, к которой привязано видео.
    """

    file_id: str  # ID файла видео (например, Telegram file_id)
    application_id: int  # ID заявки, к которой привязано видео


class BankDebtModelSchema(BaseModel):
    """
    Модель для создания записи о задолженности в банке, связанной с заявкой.

    Атрибуты:
        bank_name (str): Название банка, где имеется задолженность.
        total_amount (float): Общая сумма задолженности.
        application_id (int): Идентификатор заявки, к которой привязана задолженность.
    """

    bank_name: str  # Название банка
    total_amount: float  # Общая сумма задолженности
    application_id: int  # ID заявки, к которой привязана задолженность
