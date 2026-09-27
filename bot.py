import asyncio
import logging
import os
import json
import requests

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import FSInputFile
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv


# =========================================================
# SOZLAMALAR
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")

CHANNEL_USERNAME = "@EFShop_UZ"
CHANNEL_URL = "https://t.me/EFShop_UZ"
HAMYON_API = "https://efkhaydarov.uz/projects/tranzaksiyalarbot/index.php?r=api"
HAMYON_API_KEY = os.getenv("HAMYON_API_KEY")


# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# =========================================================
# FOYDALANUVCHINING HOZIRGI BOT XABARI
# =========================================================

# Har bir foydalanuvchining botdagi oxirgi oynasi/xabari ID'si.
# Keyingi amal boshlanganda eski xabar o'chiriladi.
user_messages = {}
main_messages = {}
user_data = {}


# =========================================================
# ESKI BOT XABARINI O'CHIRISH
# =========================================================

async def delete_previous_message(user_id: int):
    message_id = user_messages.get(user_id)

    if not message_id:
        return

    try:
        await bot.delete_message(
            chat_id=user_id,
            message_id=message_id
        )
    except TelegramBadRequest:
        pass

    user_messages.pop(user_id, None)


# =========================================================
# YANGI BOT XABARINI SAQLASH
# =========================================================

async def send_new_message(
    user_id: int,
    text: str,
    reply_markup=None
):
    # Avval eski amalni yopamiz
    await delete_previous_message(user_id)

    # Keyin yangi amalni ochamiz
    message = await bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=reply_markup
    )

    user_messages[user_id] = message.message_id

    return message
# =========================================================
# HAMYON TO‘LOV
# =========================================================

def get_payment_fee(price):
    if price <= 500_000:
        return 3000
    elif price <= 1_000_000:
        return 4000
    else:
        return 5000


def create_hamyon_payment(amount, order_id):
    try:
        response = requests.post(
            HAMYON_API,
            headers={
                "X-API-Key": HAMYON_API_KEY
            },
            data={
                "action": "create",
                "amount": amount,
                "order_id": order_id
            },
            timeout=10
        )

        return response.json()

    except Exception as e:
        logging.error(f"Hamyon API xatosi: {e}")

        return {
            "ok": False,
            "error": "connection_error"
        }


# =========================================================
# MAJBURIY OBUNA OYNASI
# =========================================================

def subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 EF SHOP UZ",
                    url=CHANNEL_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Davom etish",
                    callback_data="check_subscription"
                )
            ]
        ]
    )


async def subscription_message(user_id: int):
    await send_new_message(
        user_id=user_id,
        text=(
            "📢 <b>Botdan foydalanish uchun kanalga obuna bo‘ling:</b>\n\n"
            "🛍 <b>EF SHOP UZ</b>\n\n"
            "Kanalga obuna bo‘lgach, "
            "<b>«✅ Davom etish»</b> tugmasini bosing."
        ),
        reply_markup=subscription_keyboard()
    )


# =========================================================
# OBUNANI TEKSHIRISH
# =========================================================

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )

        return member.status in {
            "creator",
            "administrator",
            "member",
            "restricted"
        }

    except TelegramBadRequest:
        return False


# =========================================================
# ASOSIY MENYU
# =========================================================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔍 Akkount qidirish"),
                KeyboardButton(text="➕ Elon berish"),
            ],
            [
                KeyboardButton(text="📂 Elonlarim"),
                KeyboardButton(text="👮 Adminlar"),
            ],
            [
                KeyboardButton(text="📚 Qoidalar"),
                KeyboardButton(text="💰 Elon narxlari"),
            ],
        ],
        resize_keyboard=True
    )


# =========================================================
# ASOSIY MENYU OYNASI
# =========================================================

async def open_main_menu(user_id: int):
    # Agar asosiy sahifa allaqachon mavjud bo‘lsa,
    # uni qaytadan yubormaymiz.
    if user_id in main_messages:
        return

    message = await bot.send_message(
        chat_id=user_id,
        text=(
            "👋 <b>EF SHOP UZ</b> botiga xush kelibsiz!\n\n"
            "🛍 <b>Kerakli bo‘limni tanlang:</b>"
        ),
        reply_markup=main_menu()
    )

    main_messages[user_id] = message.message_id

# =========================================================
# /START
# =========================================================

@dp.message(CommandStart())
async def start_handler(message: Message):

    user_id = message.from_user.id

    # Foydalanuvchining /start xabarini o'chiramiz
    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    # Obunani tekshiramiz
    subscribed = await check_subscription(user_id)

    if not subscribed:
        await subscription_message(user_id)
        return

    # Obuna bor bo'lsa asosiy menyu
    await open_main_menu(user_id)


# =========================================================
# "DAVOM ETISH"
# =========================================================

@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):

    user_id = callback.from_user.id

    subscribed = await check_subscription(user_id)

    if not subscribed:

        await callback.answer(
            "❌ Siz hali EF SHOP UZ kanaliga obuna bo‘lmagansiz!",
            show_alert=True
        )

        return

    # Obuna tasdiqlandi
    await callback.answer("✅ Obuna tasdiqlandi!")

    # Eski obuna oynasini o'chiramiz
    await delete_previous_message(user_id)

    # Yangi amal — asosiy menyu
    await open_main_menu(user_id)
# =========================
# ELON NARXLARI
# =========================

def prices_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    return keyboard


@dp.message(F.text == "💰 Elon narxlari")
async def prices_handler(message: Message):
    user_id = message.from_user.id

    # Eski bot oynasini o‘chirish
    await delete_previous_message(user_id)

    text = (
        "💰 <b>«ELON NARXLARI»</b>\n\n"
        "╔════════════════════╗\n"
        "║ <b>1 – 500 000 so‘m</b>\n"
        "║ ➜ <b>3 000 so‘m</b>\n"
        "╠════════════════════╣\n"
        "║ <b>500 000 – 1 000 000 so‘m</b>\n"
        "║ ➜ <b>4 000 so‘m</b>\n"
        "╠════════════════════╣\n"
        "║ <b>1 000 000 so‘mdan yuqori</b>\n"
        "║ ➜ <b>5 000 so‘m</b>\n"
        "╚════════════════════╝"
    )

    await send_new_message(
        user_id,
        text,
        reply_markup=prices_keyboard()
    )


@dp.message(F.text == "🔙 Orqaga")
async def back_to_main_handler(message: Message):
    user_id = message.from_user.id

    # Foydalanuvchining "Orqaga" xabarini o‘chirish
    try:
        await message.delete()
    except Exception:
        pass

    # Eski narxlar oynasini o‘chirish
    await delete_previous_message(user_id)

    # Asosiy menyuni qaytarish
    await send_new_message(
        user_id,
        "🏠 <b>Asosiy menyu</b>\n\nKerakli bo‘limni tanlang:",
        reply_markup=main_menu()
    )
# =========================
# QOIDALAR
# =========================

@dp.message(F.text == "📚 Qoidalar")
async def rules_handler(message: Message):
    user_id = message.from_user.id

    # Eski bot oynasini o‘chirish
    await delete_previous_message(user_id)

    text = (
        "📚 <b>«EF SHOP UZ QOIDALARI»</b>\n\n"
        "1️⃣ <b>Barcha akkaunt ma’lumotlari to‘g‘ri va aniq</b> "
        "ko‘rsatilishi shart.\n\n"
        
        "2️⃣ <b>Soxta, o‘g‘irlangan yoki boshqa shaxsga tegishli "
        "akkauntlarni</b> joylashtirish taqiqlanadi.\n\n"
        
        "3️⃣ E’lon joylashtirishdan oldin barcha ma’lumotlarni "
        "<b>diqqat bilan tekshiring.</b>\n\n"
        
        "4️⃣ To‘lov faqat <b>EF SHOP UZ botida ko‘rsatilgan rasmiy "
        "tartib</b> orqali amalga oshiriladi.\n\n"
        
        "5️⃣ Xaridor va sotuvchi o‘rtasidagi kelishuvda "
        "<b>garant/admin ko‘rsatmalariga amal qilish shart.</b> "
        "Qoidalarga zid e’lonlar o‘chirib tashlanishi mumkin."
    )

    await send_new_message(
        user_id,
        text,
        reply_markup=prices_keyboard()
    )
# =========================
# ADMINLAR
# =========================

def admins_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 BOSH ADMIN",
                    url="tg://user?id=6595240938"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="back_to_main"
                )
            ]
        ]
    )
    return keyboard
@dp.message(F.text == "👮 Adminlar")
async def admins_handler(message: Message):
    user_id = message.from_user.id

    # Eski bot oynasini o‘chirish
    await delete_previous_message(user_id)

    text = (
        "👮 <b>«ADMINLAR»</b>\n\n"
        "👤 <b>BOSH ADMIN</b>\n\n"
        "Savollar va murojaatlar uchun Bosh Admin bilan bog‘lanishingiz mumkin."
    )

    await send_new_message(
        user_id,
        text,
        reply_markup=admins_keyboard()
    )
@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    await callback.answer()

    # Ichki oynani o‘chirish
    await delete_previous_message(user_id)

    # Asosiy sahifa allaqachon mavjud bo‘lsa,
    # uni qaytadan yubormaymiz
    await open_main_menu(user_id)
# =========================
# ELON BERISH
# =========================

def ad_type_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Sotish eloni",
                    callback_data="sell_ad"
                ),
                InlineKeyboardButton(
                    text="🔵 Olish eloni",
                    callback_data="buy_ad"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="back_to_main"
                )
            ]
        ]
    )
    return keyboard


@dp.message(F.text == "➕ Elon berish")
async def add_ad_handler(message: Message):
    user_id = message.from_user.id

    # Foydalanuvchining tugma bosgan xabarini o‘chirish
    try:
        await message.delete()
    except Exception:
        pass

    # Eski bot oynasini o‘chirish
    await delete_previous_message(user_id)

    text = (
        "➕ <b>«ELON BERISH»</b>\n\n"
        "Kerakli e’lon turini tanlang:"
    )

    await send_new_message(
        user_id,
        text,
        reply_markup=ad_type_keyboard()
    )


@dp.callback_query(F.data == "sell_ad")
async def sell_ad_handler(callback: CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    user_data[user_id] = {}

    # Eski bot oynasini o‘chirish
    await delete_previous_message(user_id)

    # Asosiy menyu tugmalarini olib tashlash
    try:
        await bot.send_message(
            user_id,
            " ",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception:
        pass

    # Faqat Orqaga tugmasi
    back_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

    # Namuna rasmi
    photo = FSInputFile("sample.png.jpg")

    message = await bot.send_photo(
        chat_id=user_id,
        photo=photo,
        caption=(
            "📸 <b>Namuna</b>\n\n"
            "O‘z akkauntingiz rasmini namunadagidek yuboring."
        ),
        reply_markup=back_keyboard
    )

    user_messages[user_id] = message.message_id

@dp.callback_query(F.data == "buy_ad")
async def buy_ad_handler(callback: CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id

    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "🔵 <b>«OLISH ELONI»</b>\n\n"
        "Keyingi bosqichni boshlaymiz."
    )

# =========================
# AKKAUNT RASMINI QABUL QILISH
# =========================

@dp.message(F.photo)
async def account_photo_handler(message: Message):
    user_id = message.from_user.id

    # Faqat Sotish eloni jarayonida rasm qabul qilamiz
    if user_id not in user_data:
        return
    # Eng katta sifatdagi rasmning file_id'si
    photo = message.photo[-1]
    file_id = photo.file_id

    # Rasm tahrirlanayotgan bo‘lsa
    if user_data[user_id].get("editing_photo"):
        user_data[user_id]["account_photo"] = file_id
        user_data[user_id]["editing_photo"] = False

        try:
            await message.delete()
        except Exception:
            pass

        await delete_previous_message(user_id)

        await send_new_message(
            user_id,
            "✅ <b>Rasm yangilandi.</b>\n\n"
            "E’loningizni qayta tekshiring:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👀 Previewni ko‘rish",
                            callback_data="back_to_preview"
                        )
                    ]
                ]
            )
        )
        return

      
    user_data[user_id]["account_photo"] = file_id

    # Foydalanuvchining yuborgan rasmini o‘chirish
    try:
        await message.delete()
    except Exception:
        pass

    # Namuna oynasini o‘chirish
    await delete_previous_message(user_id)

    # Keyingi bosqich
    keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Ha",
                callback_data="google_game_yes"
            ),
            InlineKeyboardButton(
                text="❌ Yo‘q",
                callback_data="google_game_no"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Orqaga",
                callback_data="back_to_main"
            )
        ]
    ]
)
    await send_new_message(
        user_id,
        "🔐 <b>Google yoki Game Center ulanganmi?</b>",
        reply_markup=keyboard
    )

# =========================
# GOOGLE / GAME CENTER JAVOBI
# =========================
def exchange_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💱 Obmen",
                    callback_data="exchange_yes"
                ),
                InlineKeyboardButton(
                    text="💵 Naqdga",
                    callback_data="exchange_no"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data="back_to_main"
                )
            ]
        ]
    )
    return keyboard

@dp.callback_query(F.data.in_({"google_game_yes", "google_game_no"}))
async def google_game_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Agar foydalanuvchi ma'lumotlari mavjud bo'lmasa,
    # yangi ma'lumotlar oynasini yaratamiz
    if user_id not in user_data:
        user_data[user_id] = {}

    # Javobni saqlash
    if callback.data == "google_game_yes":
        user_data[user_id]["google_game"] = "Ha"
    else:
        user_data[user_id]["google_game"] = "Yo‘q"

    await callback.answer()

    # Eski savol oynasini o‘chirish
    await delete_previous_message(user_id)

    # Keyingi savol
    await send_new_message(
        user_id,
        "💰 <b>Akkauntni qanday sotasiz?</b>\n\n"
        "Kerakli variantni tanlang:",
        reply_markup=exchange_keyboard()
    )
@dp.callback_query(F.data.in_({"exchange_yes", "exchange_no"}))
async def exchange_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}

    if callback.data == "exchange_yes":
        user_data[user_id]["sale_type"] = "Obmen"

        await callback.answer()
        await delete_previous_message(user_id)

        await send_new_message(
            user_id,
            "📝 <b>Izoh yozing</b>\n\n"
            "Akkaunt haqida qo‘shimcha ma’lumot yozing:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Orqaga",
                            callback_data="back_to_main"
                        )
                    ]
                ]
            )
        )

    else:
        user_data[user_id]["sale_type"] = "Naqdga"

        await callback.answer()
        await delete_previous_message(user_id)

        await send_new_message(
            user_id,
            "💵 <b>Akkaunt narxini yuboring</b>\n\n"
            "Masalan: <b>250.000</b> so‘m",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Orqaga",
                            callback_data="back_to_main"
                        )
                    ]
                ]
            )
        )
@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    user_id = message.from_user.id

    try:
        data = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, TypeError):
        return

    if data.get("action") == "payment_done":

        # Mini App yuborgan xabarni o‘chirish
        try:
            await message.delete()
        except TelegramBadRequest:
            pass

        # Eski oynani yopish
        await delete_previous_message(user_id)

        # To‘lov tekshirilmoqda oynasi
        await send_new_message(
            user_id,
            "⏳ <b>To‘lov tekshirilmoqda...</b>\n\n"
            "💳 To‘lovingiz qabul qilindi.\n"
            "Iltimos, biroz kuting."
        )

@dp.message()
async def sell_text_handler(message: Message):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""

    if user_id not in user_data:
        return

    data = user_data[user_id]

    # =========================
    # NAQDGA — NARX
    # =========================
    if data.get("sale_type") == "Naqdga" and not data.get("price"):

        clean_price = (
            text.replace(".", "")
            .replace(",", "")
            .replace(" ", "")
        )

        if not clean_price.isdigit():
            try:
                await message.delete()
            except Exception:
                pass

            await delete_previous_message(user_id)

            await send_new_message(
                user_id,
                "❌ <b>Narx noto‘g‘ri kiritildi.</b>\n\n"
                "Masalan: <b>250000</b>"
            )
            return

        data["price"] = int(clean_price)

        try:
            await message.delete()
        except Exception:
            pass

        await delete_previous_message(user_id)

        await send_new_message(
            user_id,
            "💬 <b>Izoh yuboring</b>\n\n"
            "Akkount haqida qo‘shimcha ma’lumot yozing."
        )
        return

    # =========================
    # IZOHDAN KEYIN PREVIEW
    # =========================
    if data.get("sale_type") == "Obmen" or data.get("price"):

        data["comment"] = text

        try:
            await message.delete()
        except Exception:
            pass

        # =========================
        # SOTUV / OBMEN
        # =========================
        if data.get("sale_type") == "Obmen":
            sale_tag = "🔄 <b>SOTILMAYDI</b>  •  <b>FAQAT OBMEN</b>"
            price_text = "💱 <b>FAQAT OBMEN</b>"
        else:
            sale_tag = "🔥 <b>SOTILADI</b>"
            price_text = (
                f"💰 <b>{data.get('price')}</b> so‘m\n"
                f"🚫 <b>OBMEN YO‘Q</b>"
            )

        # =========================
        # GOOGLE / GAME CENTER
        # =========================
        google_game = data.get("google_game", "Yo‘q")

        if google_game == "Ha":
            connection_text = (
                "🔐 <b>Google / Game Center:</b> ✅ Ulangan"
            )
        else:
            connection_text = (
                "🔐 <b>Google / Game Center:</b> ❌ Ulanmagan"
            )

        # =========================
        # ALOQA
        # =========================
        user = message.from_user

        if user.username:
            contact_text = (
                f'👤 <b>Aloqa uchun:</b> '
                f'<a href="tg://user?id={user.id}">'
                f'@{user.username}</a>'
            )
        else:
            contact_text = (
                f'👤 <b>Aloqa uchun:</b> '
                f'<a href="tg://user?id={user.id}">'
                f'Profilga kirish</a>'
            )

        # =========================
        # IZOHI
        # =========================
        comment_block = (
            "💬 <b>IZOH</b>\n"
            "╭──────────────────\n"
            f"│ <i>“{text}”</i>\n"
            "╰──────────────────"
        )

        # =========================
        # PREVIEW
        # =========================
        preview_text = (
            f"{sale_tag}\n\n"
            f"{price_text}\n\n"
            f"{connection_text}\n\n"
            f"{contact_text}\n\n"
            f"{comment_block}\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🛡 <b>GARANT | ADMIN</b>\n"
            '👤 <a href="tg://user?id=6595240938">@khasanow17</a>\n\n'
            "🤖 <b>EF SHOP UZ</b>\n"
            '<a href="https://t.me/EFShopUzBot">@EFShopUzBot</a>\n'
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✏️ <i>Agar e’loningizda xatolik bo‘lsa, "
            "uni tahrirlashingiz mumkin.</i>\n\n"
            "✅ <b>Agar hammasi to‘g‘ri bo‘lsa, "
            "e’lonni tasdiqlang.</b>"
        )

        # =========================
        # TUGMALAR
        # =========================
        preview_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Tahrirlash",
                        callback_data="edit_preview"
                    ),
                    InlineKeyboardButton(
                        text="✅ Tasdiqlash",
                        callback_data="confirm_preview"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Bekor qilish",
                        callback_data="back_to_main"
                    )
                ]
            ]
        )

        # Eski oynani o‘chiramiz
        await delete_previous_message(user_id)

        # =========================
        # RASM BILAN PREVIEW
        # =========================
        await bot.send_photo(
            chat_id=user_id,
            photo=data["account_photo"],
            caption=preview_text,
            reply_markup=preview_keyboard
        )

        return
@dp.callback_query(F.data == "confirm_preview")
async def confirm_preview_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    await callback.answer()

    if user_id not in user_data:
        return

    data = user_data[user_id]

    # =========================
    # XIZMAT HAQINI ANIQLASH
    # =========================

    if data.get("sale_type") == "Obmen":
        fee = 5000
    else:
        price = int(data.get("price", 0))
        fee = get_payment_fee(price)

    # =========================
    # BUYURTMA ID
    # =========================

    import time

    order_id = f"EF-{user_id}-{int(time.time())}"

    # =========================
    # HAMYON TO‘LOV YARATISH
    # =========================

    payment = await asyncio.to_thread(
        create_hamyon_payment,
        fee,
        order_id
    )

    if not payment.get("ok"):
        await delete_previous_message(user_id)

        await send_new_message(
            user_id,
            "❌ <b>To‘lov yaratishda xatolik yuz berdi.</b>\n\n"
            "Iltimos, birozdan keyin qayta urinib ko‘ring.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Orqaga",
                            callback_data="back_to_main"
                        )
                    ]
                ]
            )
        )
        return

    # =========================
    # TO‘LOV MA’LUMOTLARINI SAQLASH
    # =========================

    user_data[user_id]["order_id"] = order_id
    user_data[user_id]["invoice_id"] = payment.get("invoice_id")
    user_data[user_id]["payment_amount"] = payment.get("amount")
    user_data[user_id]["payment_card"] = payment.get("card")
    user_data[user_id]["payment_card_holder"] = payment.get("card_holder")
    user_data[user_id]["payment_url"] = payment.get("pay_url")

    # =========================
    # TO‘LOV OYNASI
    # =========================

    payment_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 To‘lov qilish",
                    url=payment.get("pay_url")
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 To‘lovni tekshirish",
                    callback_data="check_payment"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="back_to_main"
                )
            ]
        ]
    )

    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "💳 <b>TO‘LOV</b>\n\n"
        "📢 <b>EF SHOP UZ</b> kanaliga e’lon joylashtirish uchun:\n\n"
        f"💰 <b>Xizmat haqi:</b> {fee:,} so‘m\n"
        f"💳 <b>To‘lanadigan summa:</b> {payment.get('amount'):,} so‘m\n\n"
        f"💳 <b>Karta:</b> <code>{payment.get('card')}</code>\n"
        f"👤 <b>Karta egasi:</b> {payment.get('card_holder')}\n"
        f"🏦 <b>Bank:</b> {payment.get('bank', '—')}\n\n"
        "⏱ <b>To‘lov 5 daqiqa davomida amal qiladi.</b>\n\n"
        "⚠️ <b>Aynan yuqorida ko‘rsatilgan summani to‘lang.</b>\n\n"
        "To‘lovni amalga oshirgach, "
        "<b>«🔄 To‘lovni tekshirish»</b> tugmasini bosing.",
        reply_markup=payment_keyboard
    )
@dp.callback_query(F.data == "edit_preview")
async def edit_preview_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    await callback.answer()

    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "🚧 <b>Tahrirlash bo‘limi hozircha ishlab chiqilmoqda.</b>\n\n"
        "Tez orada ushbu funksiya qo‘shiladi.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👀 Previewni ko‘rish",
                        callback_data="back_to_preview"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Orqaga",
                        callback_data="back_to_main"
                    )
                ]
            ]
        )
    )
@dp.callback_query(F.data == "edit_photo")
async def edit_photo_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer()
        return

    await callback.answer()

    user_data[user_id]["editing_photo"] = True

    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "📸 <b>Yangi akkaunt rasmini yuboring</b>\n\n"
        "Eski rasm o‘rniga yangi rasm yuboring.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Tahrirlashga qaytish",
                        callback_data="edit_preview"
                    )
                ]
            ]
        )
    )
@dp.callback_query(F.data == "back_to_preview")
async def back_to_preview_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer()
        return

    await callback.answer()

    await delete_previous_message(user_id)

    data = user_data[user_id]

    if data.get("sale_type") == "Obmen":
        sale_tag = "🔄 <b>SOTILMAYDI</b>  •  <b>FAQAT OBMEN</b>"
        price_text = "💱 <b>FAQAT OBMEN</b>"
    else:
        sale_tag = "🔥 <b>SOTILADI</b>"
        price_text = (
            f"💰 <b>{data.get('price')}</b> so‘m\n"
            f"🚫 <b>OBMEN YO‘Q</b>"
        )

    google_game = data.get("google_game", "Yo‘q")

    if google_game == "Ha":
        connection_text = (
            "🔐 <b>Google / Game Center:</b> ✅ Ulangan"
        )
    else:
        connection_text = (
            "🔐 <b>Google / Game Center:</b> ❌ Ulanmagan"
        )

    user = callback.from_user

    if user.username:
        contact_text = (
            f'👤 <b>Aloqa uchun:</b> '
            f'<a href="tg://user?id={user.id}">'
            f'@{user.username}</a>'
        )
    else:
        contact_text = (
            f'👤 <b>Aloqa uchun:</b> '
            f'<a href="tg://user?id={user.id}">'
            f'Profilga kirish</a>'
        )

    comment = data.get("comment", "")

    comment_block = (
        "💬 <b>IZOH</b>\n"
        "╭──────────────────\n"
        f"│ <i>“{comment}”</i>\n"
        "╰──────────────────"
    )

    preview_text = (
        f"{sale_tag}\n\n"
        f"{price_text}\n\n"
        f"{connection_text}\n\n"
        f"{contact_text}\n\n"
        f"{comment_block}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🛡 <b>GARANT | ADMIN</b>\n"
        '👤 <a href="tg://user?id=6595240938">@khasanow17</a>\n\n'
        "🤖 <b>EF SHOP UZ</b>\n"
        '<a href="https://t.me/EFShopUzBot">@EFShopUzBot</a>\n'
        "━━━━━━━━━━━━━━━━━━\n\n"
        "✏️ <i>Agar e’loningizda xatolik bo‘lsa, "
        "uni tahrirlashingiz mumkin.</i>\n\n"
        "✅ <b>Agar hammasi to‘g‘ri bo‘lsa, "
        "e’lonni tasdiqlang.</b>"
    )

    preview_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Tahrirlash",
                    callback_data="edit_preview"
                ),
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data="confirm_preview"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="back_to_main"
                )
            ]
        ]
    )

    await bot.send_photo(
        chat_id=user_id,
        photo=data["account_photo"],
        caption=preview_text,
        reply_markup=preview_keyboard
    )
@dp.callback_query(F.data == "edit_google_game")
async def edit_google_game_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer()
        return

    await callback.answer()

    await delete_previous_message(user_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ha",
                    callback_data="edit_google_yes"
                ),
                InlineKeyboardButton(
                    text="❌ Yo‘q",
                    callback_data="edit_google_no"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Tahrirlashga qaytish",
                    callback_data="edit_preview"
                )
            ]
        ]
    )

    await send_new_message(
        user_id,
        "🔐 <b>Google yoki Game Center ulanganmi?</b>\n\n"
        "Yangi holatni tanlang:",
        reply_markup=keyboard
    )
@dp.callback_query(F.data.in_({"edit_google_yes", "edit_google_no"}))
async def edit_google_result_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer()
        return

    if callback.data == "edit_google_yes":
        user_data[user_id]["google_game"] = "Ha"
    else:
        user_data[user_id]["google_game"] = "Yo‘q"

    await callback.answer()
    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "✅ <b>Google / Game Center ma’lumoti yangilandi.</b>\n\n"
        "E’loningizni qayta tekshiring:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👀 Previewni ko‘rish",
                        callback_data="back_to_preview"
                    )
                ]
            ]
        )
    )
@dp.callback_query(F.data == "edit_sale_type")
async def edit_sale_type_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer()
        return

    await callback.answer()
    await delete_previous_message(user_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💱 Obmen",
                    callback_data="edit_exchange"
                ),
                InlineKeyboardButton(
                    text="💵 Naqdga",
                    callback_data="edit_cash"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Tahrirlashga qaytish",
                    callback_data="edit_preview"
                )
            ]
        ]
    )

    await send_new_message(
        user_id,
        "💰 <b>Akkauntni qanday sotasiz?</b>\n\n"
        "Yangi variantni tanlang:",
        reply_markup=keyboard
    )
@dp.callback_query(F.data == "edit_exchange")
async def edit_exchange_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer()
        return

    user_data[user_id]["sale_type"] = "Obmen"
    user_data[user_id]["price"] = ""

    await callback.answer()
    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "💱 <b>Obmen tanlandi.</b>\n\n"
        "Endi akkaunt haqida yangi izoh yozing:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Tahrirlashga qaytish",
                        callback_data="edit_preview"
                    )
                ]
            ]
        )
    )
@dp.callback_query(F.data == "edit_cash")
async def edit_cash_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer()
        return

    user_data[user_id]["sale_type"] = "Naqdga"
    user_data[user_id]["price"] = ""
    user_data[user_id]["editing_price"] = True

    await callback.answer()
    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "💵 <b>Yangi akkaunt narxini yuboring</b>\n\n"
        "Masalan: <b>250.000</b> so‘m",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Tahrirlashga qaytish",
                        callback_data="edit_preview"
                    )
                ]
            ]
        )
    )
@dp.callback_query(F.data == "edit_comment")
async def edit_comment_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer()
        return

    await callback.answer()

    user_data[user_id]["editing_comment"] = True
    user_data[user_id]["editing_price"] = False

    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "📝 <b>Yangi izoh yozing</b>\n\n"
        "Akkaunt haqida yangi ma’lumot yozing:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Tahrirlashga qaytish",
                        callback_data="edit_preview"
                    )
                ]
            ]
        )
    )
@dp.callback_query(F.data == "payment_done")
async def payment_done_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    await callback.answer()

    await delete_previous_message(user_id)

    await send_new_message(
        user_id,
        "⏳ <b>To‘lov tekshirilmoqda...</b>\n\n"
        "💳 To‘lovingiz qabul qilindi.\n"
        "Iltimos, biroz kuting."
    )

# =========================================================
# BOTNI ISHGA TUSHIRISH
# =========================================================

async def main():
    logging.basicConfig(
        level=logging.INFO
    )

    print("✅ EFShopUzBot ishga tushdi!")

    await dp.start_polling(bot)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())