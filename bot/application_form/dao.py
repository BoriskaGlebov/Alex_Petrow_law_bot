from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.application_form.models import Application, Photo, Video, BankDebt
from bot.dao.base import BaseDAO, T
from bot.config import logger
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete


class ApplicationDAO(BaseDAO[Application]):
    """
    Класс для работы с данными заявок в базе данных.

    Этот класс предоставляет операции для работы с заявками, такие как:
    - создание заявки
    - чтение заявки
    - обновление заявки
    - удаление заявки

    Наследует базовые методы для работы с сущностями от BaseDAO.

    Атрибуты:
        model (Application): Модель, с которой работает этот DAO. В данном случае модель Application,
                              которая описывает заявку.

    Методы:
        - get_all() -> List[Application]: Возвращает все заявки.
        - get_by_id(id: int) -> Application: Получает заявку по идентификатору.
        - create(data: dict) -> Application: Создает новую заявку на основе данных.
        - update(id: int, data: dict) -> Application: Обновляет заявку по идентификатору.
        - delete(id: int) -> None: Удаляет заявку по идентификатору.
    """

    model: Application = Application  # Тип данных модели для работы с заявками

    @classmethod
    async def add(cls, session: AsyncSession, values: dict) -> T:
        """
        Добавляет одну запись в базу данных.

        Args:
            session (AsyncSession): Сессия для взаимодействия с БД.
            values (BaseModel): Значения для новой записи.

        Returns:
            T: Добавленная запись.
        """
        values_dict = values
        logger.info(
            f"Добавление записи {cls.model.__name__} с параметрами: {values_dict}"
        )
        new_instance = cls.model(**values_dict)
        session.add(new_instance)
        try:
            await session.commit()
            logger.info(f"Запись {cls.model.__name__} успешно добавлена.")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при добавлении записи: {e}")
            raise e
        return new_instance

    @classmethod
    async def delete(cls, session: AsyncSession, filters: dict) -> int:
        """
        Удаляет записи по фильтрам.

        Args:
            session (AsyncSession): Сессия для взаимодействия с БД.
            filters (BaseModel): Фильтры для удаления.

        Returns:
            int: Количество удаленных записей.
        """
        filter_dict = filters
        logger.info(f"Удаление записей {cls.model.__name__} по фильтру: {filter_dict}")
        if not filter_dict:
            logger.error("Нужен хотя бы один фильтр для удаления.")
            raise ValueError("Нужен хотя бы один фильтр для удаления.")

        query = sqlalchemy_delete(cls.model).filter_by(**filter_dict)
        try:
            result = await session.execute(query)
            await session.commit()
            logger.info(f"Удалено {result.rowcount} записей.")
            return result.rowcount
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при удалении записей: {e}")
            raise e

    @classmethod
    async def update(cls, session: AsyncSession, filters: dict, values: dict) -> int:
        """
        Обновляет записи в таблице заявок (или в других связанных моделях),
        которые соответствуют заданным фильтрам.

        Этот метод используется для массового обновления записей в базе данных
        на основе фильтров, предоставленных в виде словаря, и установки новых значений для выбранных столбцов.

        Аргументы:
            session (AsyncSession): Сессия для взаимодействия с базой данных. Используется для выполнения запросов и коммитов.
            filters (dict): Словарь, содержащий фильтры, по которым будут обновляться записи.
                            Пример: {'status': 'pending', 'user_id': 123}.
            values (dict): Словарь, содержащий новые значения, которые будут применены к записям,
                           соответствующим фильтрам. Пример: {'status': 'approved'}.

        Возвращает:
            int: Количество обновленных записей, если операция успешна.

        Исключения:
            SQLAlchemyError: Если произошла ошибка при обновлении записи, операция откатывается,
                             и ошибка будет залогирована и передана выше.
        """
        filter_dict = filters
        values_dict = values

        logger.info(
            f"Обновление записей в {cls.model.__name__} по фильтру: {filter_dict} с параметрами: {values_dict}"
        )

        # Формируем запрос для обновления
        query = (
            sqlalchemy_update(cls.model)
            .where(
                *[getattr(cls.model, k) == v for k, v in filter_dict.items()]
            )  # Применяем фильтры
            .values(**values_dict)  # Устанавливаем новые значения
            .execution_options(
                synchronize_session="fetch"
            )  # Обновляем с синхронизацией сессии
        )

        try:
            # Выполняем запрос и коммитим изменения
            result = await session.execute(query)
            await session.commit()
            logger.info(f"Обновлено {result.rowcount} записей.")
            return result.rowcount

        except SQLAlchemyError as e:
            # В случае ошибки откатываем транзакцию и логируем ошибку
            await session.rollback()
            logger.error(f"Ошибка при обновлении записей: {e}")
            raise e


class PhotoDAO(BaseDAO[Photo]):
    """
    Класс для работы с данными фотографий пользователей в базе данных.

    Этот класс предоставляет операции для работы с медиафайлами (фотографиями), такие как:
    - создание фотографии
    - чтение фотографии
    - обновление фотографии
    - удаление фотографии

    Наследует базовые методы для работы с сущностями от BaseDAO.

    Атрибуты:
        model (Photo): Модель, с которой работает этот DAO. В данном случае модель Photo,
                        которая описывает фотографию.

    Методы:
        - get_all() -> List[Photo]: Возвращает все фотографии.
        - get_by_id(id: int) -> Photo: Получает фотографию по идентификатору.
        - create(data: dict) -> Photo: Создает новую фотографию на основе данных.
        - update(id: int, data: dict) -> Photo: Обновляет фотографию по идентификатору.
        - delete(id: int) -> None: Удаляет фотографию по идентификатору.
    """

    model: Photo = Photo  # Тип данных модели для работы с фотографиями


class VideoDAO(BaseDAO[Video]):
    """
    Класс для работы с данными видеофайлов пользователей в базе данных.

    Этот класс предоставляет операции для работы с видеофайлами, такие как:
    - создание видеофайла
    - чтение видеофайла
    - обновление видеофайла
    - удаление видеофайла

    Наследует базовые методы для работы с сущностями от BaseDAO.

    Атрибуты:
        model (Video): Модель, с которой работает этот DAO. В данном случае модель Video,
                        которая описывает видеофайл.

    Методы:
        - get_all() -> List[Video]: Возвращает все видеофайлы.
        - get_by_id(id: int) -> Video: Получает видеофайл по идентификатору.
        - create(data: dict) -> Video: Создает новый видеофайл на основе данных.
        - update(id: int, data: dict) -> Video: Обновляет видеофайл по идентификатору.
        - delete(id: int) -> None: Удаляет видеофайл по идентификатору.
    """

    model: Video = Video  # Тип данных модели для работы с видеофайлами


class BankDebtDAO(BaseDAO[BankDebt]):
    """
    Класс для работы с данными задолженности пользователей в банках.

    Этот класс предоставляет операции для работы с задолженностями, такие как:
    - создание задолженности
    - чтение задолженности
    - обновление задолженности
    - удаление задолженности

    Наследует базовые методы для работы с сущностями от BaseDAO.

    Атрибуты:
        model (BankDebt): Модель, с которой работает этот DAO. В данном случае модель BankDebt,
                           которая описывает задолженность в банке.

    Методы:
        - get_all() -> List[BankDebt]: Возвращает все задолженности.
        - get_by_id(id: int) -> BankDebt: Получает задолженность по идентификатору.
        - create(data: dict) -> BankDebt: Создает новую задолженность на основе данных.
        - update(id: int, data: dict) -> BankDebt: Обновляет задолженность по идентификатору.
        - delete(id: int) -> None: Удаляет задолженность по идентификатору.
    """

    model: BankDebt = BankDebt  # Тип данных модели для работы с задолженностями
