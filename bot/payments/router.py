import json

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

import bot.application_form.dao
from bot.application_form.keyboards.inline_kb import product_kb
from bot.config import bot
from bot.database import connection

payment_router = Router()

# class CheckForm(StatesGroup):
#     age = State()
#     resident = State()

PROVIDER_TOKEN = "381764678:TEST:116392"


@payment_router.message(Command("pay"))
@payment_router.message(F.text.contains("Внесение предоплаты"))
@connection()
async def page_catalog_products(message: Message, session):
    await message.answer(f"В данной категории Каких-то  товаров.")
    product_text = (
        f"📦 <b>Название товара:</b> Товар1\n\n"
        f"💰 <b>Цена:</b> 1000 руб.\n\n"
        f"📝 <b>Описание:</b>\n<i>Во тут какое то описание товара</i>\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(product_text, reply_markup=product_kb(1, 1000))


@payment_router.callback_query(F.data.startswith("buy_"))
@connection()
async def process_about(call: CallbackQuery, session: AsyncSession):
    _, product_id, price = call.data.split("_")
    (
        await bot.send_invoice(
            chat_id=call.from_user.id,
            title="Оплата товара",
            description="Оплата с пробитием чека",
            payload="order_12345",
            provider_token=PROVIDER_TOKEN,
            currency="rub",
            prices=[LabeledPrice(label="Товар", amount=10000)],  # 100 руб
            provider_data=json.dumps(
                {
                    "receipt": {
                        "customer": {
                            "email": "test@example.com"  # Или phone: "+79990000000"
                        },
                        "items": [
                            {
                                "description": "Цифровой товар",
                                "quantity": "1.00",
                                "amount": {"value": "100.00", "currency": "RUB"},
                                "vat_code": "1",  # 1 – Без НДС, 2 – НДС 10%, 3 – НДС 20%
                                "payment_mode": "full_payment",
                                "payment_subject": "service",
                            }
                        ],
                    }
                }
            ),
        ),
    )
    await call.message.delete()


#
@payment_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@payment_router.message()
async def process_successful_payment(message: Message):
    if message.successful_payment:
        # Обработка успешного платежа
        payload = message.successful_payment.invoice_payload
        # Выполняйте действия после успешной оплаты
        await message.answer("Оплата прошла успешно!")
        # Отправка уведомления админу
        await bot.send_message(
            chat_id=439653349, text=f"Оплата прошла успешно! Payload: {payload}"
        )


# @user_router.message(F.text, CheckForm.resident)
# async def mistakes_handler_user(message: Message, state: FSMContext) -> None:
#     """
#     Обработчик сообщений пользователя, который проверяет данные, введенные пользователем в рамках
#     формы (например, возраст и место жительства), и обрабатывает ошибки.
#
#     Этот обработчик вызывает функцию `mistakes_handler` для дальнейшей обработки сообщений и ошибок,
#     если введенные данные некорректны.
#
#     Параметры:
#     ----------
#     message : Message
#         Сообщение от пользователя, содержащее текстовый ввод. Включает данные, которые были отправлены
#         пользователем в рамках ввода (например, возраст или место жительства).
#
#     state : FSMContext
#         Контекст состояния машины состояний (FSM) для отслеживания данных состояния пользователя.
#         Используется для хранения промежуточных данных в процессе ввода формы.
#
#     Возвращаемое значение:
#     ----------------------
#     None
#         Функция не возвращает значение, так как она выполняет побочные эффекты — обработку
#         и корректировку состояния бота в ответ на сообщение пользователя.
#
#     Логика:
#     -------
#     - Обработчик срабатывает на текстовые сообщения, которые соответствуют полям ввода формы:
#       `CheckForm.age` и `CheckForm.resident`.
#     - Он передает сообщение и текущий контекст состояния в функцию `mistakes_handler` для дальнейшей
#       обработки ошибок ввода, таких как неверный возраст или место жительства.
#     """
#     await mistakes_handler(message=message, bot=bot, state=state)
